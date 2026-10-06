"""Dasbor kota (CLAUDE.md §7, §9): HANYA agregat anonim, tanpa isi chat, tanpa identitas.

Aturan k-anonim: sel (kelurahan, minggu tren, total kecamatan, topik) dengan < MIN_CELL pengguna
dikembalikan sebagai null. Endpoint ini tidak pernah mengembalikan baris individu; data per
pengguna hanya dipakai di dalam query untuk menghitung jumlah.
"""

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Select, case, distinct, func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.cases import detected_at
from app.api.deps import current_staff
from app.db import get_session
from app.models import (
    Case,
    CaseStatus,
    Conversation,
    Emotion,
    JournalEntry,
    Kelurahan,
    Message,
    RiskAssessment,
    RiskLevel,
    Role,
    Sender,
    User,
)
from app.pipeline.markers import TOPIC_LABELS
from app.services.chat import WIB
from app.settings import settings

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
MIN_CELL = 10  # k ≥ 10 (§7)
MAX_DAYS = 185
HANDLED_TARGET = timedelta(minutes=15)  # KPI "Kasus tertangani < 15 menit"
LEVELS = [RiskLevel.hijau, RiskLevel.kuning, RiskLevel.oranye, RiskLevel.merah]
_RANK = case({lv: i for i, lv in enumerate(LEVELS)}, value=RiskAssessment.level)


class Kpis(BaseModel):
    active_users: int
    active_users_change_pct: int | None  # vs periode sebelumnya yang sama panjang
    sessions: int  # ponytail: sesi = hari (WIB) seorang remaja mengirim pesan
    handled_15m_pct: int | None  # kasus oranye/merah yang disapa < 15 menit sejak terdeteksi
    referrals: int


class KelurahanStat(BaseModel):
    id: int
    name: str
    users: int | None  # None = disembunyikan (< MIN_CELL)
    risk_pct: int | None  # % pengguna dengan level tertinggi oranye/merah
    levels: dict[RiskLevel, int] | None  # distribusi % level tertinggi per pengguna


class TrendWeek(BaseModel):
    week: date  # Senin
    pct: dict[Emotion, int] | None  # % entri jurnal per emosi; None = < MIN_CELL pengguna


class TopicStat(BaseModel):
    key: str
    label: str
    pct: int


class Aggregate(BaseModel):
    start: date
    end: date
    min_cell: int
    demo: bool  # DEMO_MODE: semua angka dari seed sintetis
    kpis: Kpis | None  # None = total kecamatan < MIN_CELL pengguna
    kelurahan: list[KelurahanStat]
    trend: list[TrendWeek]
    topics: list[TopicStat]


def _bounds(start: date, end: date) -> tuple[datetime, datetime]:
    """Rentang tanggal WIB inklusif → [awal, akhir) bertimezone untuk kolom timestamp."""
    return datetime.combine(start, time(), WIB), datetime.combine(
        end + timedelta(days=1), time(), WIB
    )


def _pct(part: int, whole: int) -> int:
    return round(part * 100 / whole) if whole else 0


def _per_user_levels(start: date, end: date) -> Select[tuple[int | None, int, int]]:
    """(kelurahan_id, peringkat level tertinggi, jumlah pengguna) untuk remaja aktif di periode.

    Aktif = punya asesmen (pesan / skrining) atau entri jurnal. Jurnal tanpa asesmen = hijau.
    """
    lo, hi = _bounds(start, end)
    activity = union_all(
        select(RiskAssessment.user_id.label("uid"), _RANK.label("rank")).where(
            RiskAssessment.created_at >= lo, RiskAssessment.created_at < hi
        ),
        select(JournalEntry.user_id, literal(0)).where(
            JournalEntry.entry_date >= start, JournalEntry.entry_date <= end
        ),
    ).subquery()
    per_user = (
        select(activity.c.uid, func.max(activity.c.rank).label("rank"))
        .group_by(activity.c.uid)
        .subquery()
    )
    return (
        select(User.kelurahan_id, per_user.c.rank, func.count())
        .join(User, User.id == per_user.c.uid)
        .where(User.role == Role.remaja)
        .group_by(User.kelurahan_id, per_user.c.rank)
    )


async def _kpis(session: AsyncSession, start: date, end: date, active: int) -> Kpis:
    lo, hi = _bounds(start, end)
    days = (end - start).days + 1
    prev_start, prev_end = start - timedelta(days=days), start - timedelta(days=1)
    prev = sum(n for _, _, n in (await session.execute(_per_user_levels(prev_start, prev_end))))

    local_day = func.date(func.timezone("Asia/Jakarta", Message.created_at))
    user_days = (
        select(Conversation.user_id, local_day)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Message.sender == Sender.remaja, Message.created_at >= lo, Message.created_at < hi)
        .distinct()
        .subquery()
    )
    sessions = (await session.execute(select(func.count()).select_from(user_days))).scalar_one()

    high = (
        await session.execute(
            select(detected_at, Case.handled_at).where(
                Case.level.in_([RiskLevel.oranye, RiskLevel.merah]),
                detected_at >= lo,
                detected_at < hi,
            )
        )
    ).all()
    fast = sum(1 for d, h in high if h is not None and h - d <= HANDLED_TARGET)
    referrals = (
        await session.execute(
            # ponytail: waktu rujukan = updated_at; tambah kolom referred_at kalau kasus
            # yang sudah dirujuk mulai sering diubah lagi.
            select(func.count()).where(
                Case.status == CaseStatus.dirujuk, Case.updated_at >= lo, Case.updated_at < hi
            )
        )
    ).scalar_one()
    return Kpis(
        active_users=active,
        active_users_change_pct=_pct(active - prev, prev) if prev >= MIN_CELL else None,
        sessions=sessions,
        handled_15m_pct=_pct(fast, len(high)) if high else None,
        referrals=referrals,
    )


async def _trend(session: AsyncSession, start: date, end: date) -> list[TrendWeek]:
    week = func.date_trunc("week", JournalEntry.entry_date).cast(JournalEntry.entry_date.type)
    in_range = (JournalEntry.entry_date >= start, JournalEntry.entry_date <= end)
    counts: dict[date, dict[Emotion, int]] = {}
    for w, emotion, n in await session.execute(
        select(week, JournalEntry.emotion, func.count())
        .where(*in_range)
        .group_by(week, JournalEntry.emotion)
    ):
        counts.setdefault(w, {})[emotion] = n
    users = dict(
        (
            await session.execute(
                select(week, func.count(distinct(JournalEntry.user_id)))
                .where(*in_range)
                .group_by(week)
            )
        ).all()
    )
    monday = start - timedelta(days=start.weekday())
    weeks = [monday + timedelta(weeks=i) for i in range((end - monday).days // 7 + 1)]
    out = []
    for w in weeks:
        c, total = counts.get(w, {}), sum(counts.get(w, {}).values())
        visible = users.get(w, 0) >= MIN_CELL
        out.append(
            TrendWeek(
                week=w, pct={e: _pct(c.get(e, 0), total) for e in Emotion} if visible else None
            )
        )
    return out


async def _topics(session: AsyncSession, start: date, end: date) -> list[TopicStat]:
    """Pangsa topik pemicu; satu pengguna dihitung sekali per topik."""
    lo, hi = _bounds(start, end)
    items = (
        select(
            RiskAssessment.user_id.label("uid"),
            func.jsonb_array_elements_text(RiskAssessment.triggers).label("t"),
        )
        .where(RiskAssessment.created_at >= lo, RiskAssessment.created_at < hi)
        .subquery()
    )
    pairs = select(items.c.uid, items.c.t).where(items.c.t.like("topik:%")).distinct().subquery()
    users = (await session.execute(select(func.count(distinct(pairs.c.uid))))).scalar_one()
    if users < MIN_CELL:
        return []
    rows = (await session.execute(select(pairs.c.t, func.count()).group_by(pairs.c.t))).all()
    total = sum(n for _, n in rows)
    stats = [
        TopicStat(key=key, label=TOPIC_LABELS[key], pct=_pct(n, total))
        for t, n in rows
        if (key := t.removeprefix("topik:")) in TOPIC_LABELS
    ]
    return sorted(stats, key=lambda s: -s.pct)


@router.get("/aggregate")
async def aggregate(
    start: date | None = Query(None, alias="from"),
    end: date | None = Query(None, alias="to"),
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> Aggregate:
    if staff.role != Role.admin_kota:
        raise HTTPException(403, "Dasbor kota hanya untuk admin kota.")
    end = end or datetime.now(WIB).date()
    start = start or end - timedelta(weeks=8) + timedelta(days=1)
    if not 0 <= (end - start).days <= MAX_DAYS:
        raise HTTPException(422, f"Rentang tanggal harus 1–{MAX_DAYS + 1} hari.")

    by_kel: dict[int, list[int]] = {}
    for kel_id, rank, n in await session.execute(_per_user_levels(start, end)):
        if kel_id is not None:
            by_kel.setdefault(kel_id, [0, 0, 0, 0])[rank] += n
    kelurahan = []
    for kel in (await session.execute(select(Kelurahan).order_by(Kelurahan.name))).scalars():
        counts = by_kel.get(kel.id, [0, 0, 0, 0])
        users = sum(counts)
        if users < MIN_CELL:
            kelurahan.append(
                KelurahanStat(id=kel.id, name=kel.name, users=None, risk_pct=None, levels=None)
            )
            continue
        levels = {lv: _pct(n, users) for lv, n in zip(LEVELS, counts, strict=True)}
        levels[RiskLevel.hijau] = 100 - sum(v for lv, v in levels.items() if lv != RiskLevel.hijau)
        kelurahan.append(
            KelurahanStat(
                id=kel.id,
                name=kel.name,
                users=users,
                risk_pct=_pct(counts[2] + counts[3], users),
                levels=levels,
            )
        )
    active = sum(sum(c) for c in by_kel.values())
    return Aggregate(
        start=start,
        end=end,
        min_cell=MIN_CELL,
        demo=settings.demo_mode,
        kpis=await _kpis(session, start, end, active) if active >= MIN_CELL else None,
        kelurahan=kelurahan,
        trend=await _trend(session, start, end),
        topics=await _topics(session, start, end),
    )
