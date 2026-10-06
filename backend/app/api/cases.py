"""Dasbor pendamping/konselor (CLAUDE.md §9): antrian, detail kasus, tindak lanjut, jadwal.

Semua query kasus lewat `case_scope` (§7): pendamping hanya kelurahannya, konselor hanya
oranye/merah, admin_kota 403. Kasus di luar scope = 404 (tidak membocorkan keberadaannya).
Isi pesan hanya pesan pemicu, dan setiap pembukaan kasus/pesan tercatat di audit_logs.
"""

import uuid
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from typing import Literal, Self

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, Field, model_validator
from redis.asyncio import Redis
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import case_scope, current_staff
from app.db import get_session
from app.dialog import mark_connected
from app.models import (
    Case,
    CaseNote,
    CaseStatus,
    Channel,
    Emotion,
    FollowUp,
    Instrument,
    Kelurahan,
    Message,
    RiskAssessment,
    RiskLevel,
    Role,
    Screening,
    Sender,
    User,
)
from app.pipeline.markers import LABELS, TOPIC_LABELS, TRIGGER_LABELS
from app.pipeline.responder import BANK
from app.redis import get_redis
from app.screening import gad7, phq9
from app.services import chat as store
from app.services.audit import record_access
from app.services.crypto import decrypt, encrypt
from app.settings import CONFIG_DIR

router = APIRouter(tags=["cases"])
LOG = yaml.safe_load((CONFIG_DIR / "staff.yaml").read_text("utf-8"))["case_log"]
CLOSED = (CaseStatus.selesai, CaseStatus.dirujuk)
MAX_TRIGGER_MESSAGES = 10

# Waktu pertama kasus mencapai level sekarang ("12 mnt sejak terdeteksi"). Pesan berikutnya yang
# ikut ditautkan tidak me-reset hitungan ini.
detected_at = func.coalesce(
    select(func.min(RiskAssessment.created_at))
    .where(RiskAssessment.case_id == Case.id, RiskAssessment.level == Case.level)
    .correlate(Case)
    .scalar_subquery(),
    Case.created_at,
)


class CaseRow(BaseModel):
    id: uuid.UUID
    pseudonym: str
    kelurahan: str
    level: RiskLevel
    status: CaseStatus
    detected_at: datetime


class EmotionDays(BaseModel):
    emotion: Emotion
    days: int


class ScreeningOut(BaseModel):
    total: int | None  # None = "Belum lengkap"
    severity: str | None  # kunci BANDS di screening/, label tampilan di frontend


class NoteOut(BaseModel):
    id: uuid.UUID
    text: str
    author: str | None
    created_at: datetime


class CaseDetail(CaseRow):
    age: int | None
    referred_to: str | None
    trajectory: list[int | None]  # 14 hari lama → baru, −2..+2, None = tidak ada data
    trajectory_from: date
    dominant: list[EmotionDays]  # maks 2, jumlah hari sebagai emosi dominan
    phq9: ScreeningOut
    gad7: ScreeningOut
    markers: list[str]
    notes: list[NoteOut]


class TriggerMessage(BaseModel):
    text: str
    created_at: datetime


class TriggerMessagesOut(BaseModel):
    messages: list[TriggerMessage]
    accessed_at: datetime  # label "Akses tercatat · {nama}, {jam}"
    accessed_by: str | None


class CaseAction(BaseModel):
    action: Literal["contacted", "done", "refer"]
    note: str = Field("", max_length=2000)
    referred_to: str | None = Field(None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def _refer_needs_target(self) -> Self:
        if (self.action == "refer") != (self.referred_to is not None):
            raise ValueError("referred_to wajib (dan hanya) untuk action=refer")
        return self


class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class FollowUpIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    scheduled_at: AwareDatetime
    ends_at: AwareDatetime | None = None
    case_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _ends_after_start(self) -> Self:
        if self.ends_at is not None and self.ends_at <= self.scheduled_at:
            raise ValueError("ends_at harus setelah scheduled_at")
        return self


class FollowUpOut(BaseModel):
    id: uuid.UUID
    title: str
    scheduled_at: datetime
    ends_at: datetime | None
    case_id: uuid.UUID | None


def _rows_query(staff: User) -> Select[tuple[Case, str | None, str, datetime]]:
    return (
        case_scope(staff)
        .add_columns(User.pseudonym, Kelurahan.name, detected_at)
        .join(User, User.id == Case.user_id)
        .join(Kelurahan, Kelurahan.id == Case.kelurahan_id)
    )


def _row(case: Case, pseudonym: str | None, kelurahan: str, detected: datetime) -> CaseRow:
    return CaseRow(
        id=case.id,
        pseudonym=pseudonym or "",
        kelurahan=kelurahan,
        level=case.level,
        status=case.status,
        detected_at=detected,
    )


async def _scoped(session: AsyncSession, staff: User, case_id: uuid.UUID) -> Case:
    case = (await session.execute(case_scope(staff).where(Case.id == case_id))).scalar_one_or_none()
    if case is None:
        raise HTTPException(404, "Kasus tidak ditemukan.")
    return case


def _point(emotion: str | None, intensity: int | None) -> int | None:
    """Emosi harian → titik lintasan. Intensitas jurnal 4–5 = ±2; obrolan selalu ±1."""
    if emotion is None:
        return None
    sign = {Emotion.senang: 1, Emotion.netral: 0}.get(Emotion(emotion), -1)
    return sign * (2 if intensity is not None and intensity >= 4 else 1)


def _marker_label(key: str) -> str | None:
    if key.startswith("topik:"):
        return TOPIC_LABELS.get(key.removeprefix("topik:"))
    return LABELS.get(key) or TRIGGER_LABELS.get(key)


async def _screening(session: AsyncSession, user_id: uuid.UUID, inst: Instrument) -> ScreeningOut:
    """Skor lengkap terakhir. Belum pernah lengkap (mis. baru PHQ-4) = "Belum lengkap" (§6.5)."""
    total = (
        await session.execute(
            select(Screening.total)
            .where(
                Screening.user_id == user_id,
                Screening.instrument == inst,
                Screening.completed_at.is_not(None),
            )
            .order_by(Screening.completed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if total is None:
        return ScreeningOut(total=None, severity=None)
    severity = phq9.severity if inst == Instrument.phq9 else gad7.severity
    return ScreeningOut(total=total, severity=severity(total))


async def _notes(session: AsyncSession, case_id: uuid.UUID) -> list[NoteOut]:
    rows = await session.execute(
        select(CaseNote, User.display_name)
        .outerjoin(User, User.id == CaseNote.author_id)
        .where(CaseNote.case_id == case_id)
        .order_by(CaseNote.created_at)
    )
    return [
        NoteOut(id=n.id, text=decrypt(n.text_enc), author=a, created_at=n.created_at)
        for n, a in rows.all()
    ]


def _add_note(session: AsyncSession, case: Case, staff: User, text: str) -> None:
    session.add(CaseNote(case_id=case.id, author_id=staff.id, text_enc=encrypt(text)))


@router.get("/cases")
async def list_cases(
    status: list[CaseStatus] | None = Query(None),
    level: list[RiskLevel] | None = Query(None),
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> list[CaseRow]:
    """Baris antrian tanpa isi pesan. Urutan tampilan (baru dulu, merah dulu) diatur frontend."""
    query = _rows_query(staff)
    if status:
        query = query.where(Case.status.in_(status))
    if level:
        query = query.where(Case.level.in_(level))
    # ponytail: batas 200 baris per permintaan; tambah paginasi kalau satu kelurahan lewat itu.
    rows = await session.execute(query.order_by(Case.updated_at.desc()).limit(200))
    return [_row(*r) for r in rows.all()]


@router.get("/cases/{case_id}")
async def get_case(
    case_id: uuid.UUID,
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> CaseDetail:
    found = (await session.execute(_rows_query(staff).where(Case.id == case_id))).first()
    if found is None:
        raise HTTPException(404, "Kasus tidak ditemukan.")
    case = found[0]
    teen = await session.get(User, case.user_id)
    assert teen is not None
    days = await store.daily_emotions(session, teen.id)
    today = datetime.now(store.WIB).date()
    triggers = (
        await session.execute(
            select(RiskAssessment.triggers)
            .where(RiskAssessment.case_id == case.id)
            .order_by(RiskAssessment.created_at)
        )
    ).scalars()
    labels = (_marker_label(k) for t in triggers for k in t)
    await record_access(session, staff.id, "view_case", case.id)
    await session.commit()
    return CaseDetail(
        **_row(*found).model_dump(),
        age=today.year - teen.birth_year if teen.birth_year else None,
        referred_to=case.referred_to,
        trajectory=[_point(e, i) for e, i in days],
        trajectory_from=today - timedelta(days=store.TRAJECTORY_DAYS - 1),
        dominant=[
            EmotionDays(emotion=Emotion(e), days=n)
            for e, n in Counter(e for e, _ in days if e).most_common(2)
        ],
        phq9=await _screening(session, teen.id, Instrument.phq9),
        gad7=await _screening(session, teen.id, Instrument.gad7),
        markers=list(dict.fromkeys(label for label in labels if label)),
        notes=await _notes(session, case.id),
    )


@router.get("/cases/{case_id}/messages")
async def get_trigger_messages(
    case_id: uuid.UUID,
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> TriggerMessagesOut:
    """Hanya pesan yang memicu deteksi (desain). Obrolan lain & isi jurnal tetap privat."""
    case = await _scoped(session, staff, case_id)
    rows = await session.execute(
        select(Message)
        .join(RiskAssessment, RiskAssessment.message_id == Message.id)
        .where(RiskAssessment.case_id == case.id, Message.sender == Sender.remaja)
        .order_by(Message.seq.desc())
        .limit(MAX_TRIGGER_MESSAGES)
    )
    messages = [
        TriggerMessage(text=decrypt(m.encrypted_text), created_at=m.created_at)
        for m in list(rows.scalars())[::-1]
    ]
    await record_access(session, staff.id, "view_case_messages", case.id)
    await session.commit()
    return TriggerMessagesOut(
        messages=messages, accessed_at=datetime.now(UTC), accessed_by=staff.display_name
    )


@router.patch("/cases/{case_id}")
async def update_case(
    case_id: uuid.UUID,
    body: CaseAction,
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> CaseDetail:
    """Tombol "Sudah dihubungi" / "Tandai selesai" / "Rujuk" (alur status ikut prototipe)."""
    case = await _scoped(session, staff, case_id)
    if case.status in CLOSED:
        raise HTTPException(409, "Kasus ini sudah ditutup.")
    note = body.note.strip()
    greet_teen = False
    if body.action == "contacted":
        if case.status != CaseStatus.baru:
            raise HTTPException(409, "Kasus ini sudah ditangani.")
        greet_teen = case.handled_at is None  # sekali per kasus, bukan tiap naik level
        case.status = CaseStatus.ditangani
        case.handled_at = case.handled_at or datetime.now(UTC)
        case.assigned_to = staff.id
        log = LOG["contacted"]
    elif body.action == "done":
        if case.status != CaseStatus.ditangani:
            raise HTTPException(409, "Hubungi remaja dulu sebelum menandai selesai.")
        case.status = CaseStatus.selesai
        log = LOG["done"]
    else:
        assert body.referred_to is not None
        case.status = CaseStatus.dirujuk
        case.referred_to = body.referred_to.strip()
        log = LOG["refer"].format(tujuan=case.referred_to)
        # TODO_VERIFY: kanal pengiriman ringkasan ke tujuan rujukan belum ada; baru dicatat.
    _add_note(session, case, staff, f"{log}. {note}" if note else log)

    teen = await session.get(User, case.user_id)
    assert teen is not None
    if greet_teen:
        await _greet(session, staff, teen, case)
    await session.commit()
    if greet_teen:
        await mark_connected(r, teen.id)
    return await get_case(case.id, staff, session)


async def _greet(session: AsyncSession, staff: User, teen: User, case: Case) -> None:
    """ "Sapaan otomatis" dari bank respons ke chat remaja, atas nama staf (bukan bot)."""
    kel = await session.get(Kelurahan, case.kelurahan_id)
    key = "pendamping_greeting" if staff.role == Role.pendamping else "konselor_greeting"
    text = BANK["dialog"][key].format(
        nama=teen.pseudonym or "kamu",
        pendamping=staff.display_name or "kakak pendamping",
        kelurahan=kel.name if kel else "",
    )
    conv = await store.conversation_for(session, teen, Channel.web)
    await store.save_message(session, conv, Sender.pendamping, text, author_id=staff.id)
    # TODO: kirim juga lewat bot Telegram kalau remaja menautkan akun (bot belum aktif).


@router.post("/cases/{case_id}/notes", status_code=201)
async def add_note(
    case_id: uuid.UUID,
    body: NoteIn,
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> list[NoteOut]:
    case = await _scoped(session, staff, case_id)
    _add_note(session, case, staff, body.text.strip())
    await session.commit()
    return await _notes(session, case.id)


@router.get("/follow-ups")
async def list_follow_ups(
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> list[FollowUpOut]:
    """Agenda milik staf ini mulai hari ini (WIB)."""
    today = datetime.now(store.WIB).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = await session.execute(
        select(FollowUp)
        .where(FollowUp.staff_id == staff.id, FollowUp.scheduled_at >= today)
        .order_by(FollowUp.scheduled_at)
        .limit(50)
    )
    return [_follow_up(f) for f in rows.scalars()]


@router.post("/follow-ups", status_code=201)
async def add_follow_up(
    body: FollowUpIn,
    staff: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> FollowUpOut:
    if body.case_id is not None:
        await _scoped(session, staff, body.case_id)
    item = FollowUp(
        staff_id=staff.id,
        case_id=body.case_id,
        scheduled_at=body.scheduled_at,
        ends_at=body.ends_at,
        title_enc=encrypt(body.title.strip()),
    )
    session.add(item)
    await session.commit()
    return _follow_up(item)


def _follow_up(f: FollowUp) -> FollowUpOut:
    return FollowUpOut(
        id=f.id,
        title=decrypt(f.title_enc),
        scheduled_at=f.scheduled_at,
        ends_at=f.ends_at,
        case_id=f.case_id,
    )
