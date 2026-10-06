"""Tugas terjadwal (CLAUDE.md §3: APScheduler): peringatan kasus merah, pengingat jurnal,
laporan mingguan.

Jalan di dalam proses API (lifespan, RUN_JOBS=true). Aman kalau ada lebih dari satu proses:
peringatan merah mengunci barisnya (SKIP LOCKED), tugas harian/mingguan memakai kunci Redis per
jadwal. Log hanya jumlah & jenis error — tanpa isi pesan atau PII (§7).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio import Redis
from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dashboard import Aggregate, build_aggregate
from app.bot import send_text
from app.bot.logic import TG
from app.db import SessionLocal
from app.models import (
    Case,
    CaseStatus,
    ChannelLink,
    JournalEntry,
    Kelurahan,
    RiskLevel,
    Role,
    User,
    UserStatus,
)
from app.redis import redis
from app.services.chat import WIB
from app.services.email import send_plain
from app.settings import CONFIG_DIR, settings

log = logging.getLogger(__name__)
EMAILS = yaml.safe_load((CONFIG_DIR / "emails.yaml").read_text("utf-8"))
Sessions = async_sessionmaker[AsyncSession]
Mailer = Callable[[str, str, str], Awaitable[None]]
TgSender = Callable[[int, str], Awaitable[bool]]


def _link(path: str) -> str:
    return f"{settings.frontend_origin.rstrip('/')}{path}"


async def _alert_recipients(session: AsyncSession, kelurahan_id: int) -> list[str]:
    """Pendamping kelurahan itu + semua konselor, yang aktif & tidak mematikan notifikasi."""
    rows = await session.execute(
        select(User.email, User.settings).where(
            User.status == UserStatus.active,
            User.email.is_not(None),
            or_(
                (User.role == Role.pendamping) & (User.kelurahan_id == kelurahan_id),
                User.role == Role.konselor,
            ),
        )
    )
    return [email for email, prefs in rows.all() if email and prefs.get("notif_red", True)]


async def red_alerts(sessions: Sessions = SessionLocal, mail: Mailer = send_plain) -> int:
    """Kasus merah berstatus "baru" yang belum diberitahukan → email ke staf (tiap menit).

    Gagal kirim ke salah satu penerima = kasus dicoba lagi menit berikutnya (lebih baik dobel
    daripada terlewat).
    """
    sent = 0
    async with sessions() as session:
        rows = await session.execute(
            select(Case, Kelurahan.name)
            .join(Kelurahan, Kelurahan.id == Case.kelurahan_id)
            .where(
                Case.level == RiskLevel.merah,
                Case.status == CaseStatus.baru,
                Case.red_alerted_at.is_(None),
            )
            .with_for_update(of=Case, skip_locked=True)
        )
        tpl = EMAILS["red_alert"]
        for case, kel in rows.all():
            subject = tpl["subject"].format(kelurahan=kel)
            body = tpl["body"].format(kelurahan=kel, link=_link("/staf"))
            ok = True
            for email in await _alert_recipients(session, case.kelurahan_id):
                try:
                    await mail(email, subject, body)
                    sent += 1
                except Exception as e:  # noqa: BLE001 — dicoba lagi di putaran berikutnya
                    ok = False
                    log.warning("red_alert_failed case_id=%s error=%s", case.id, type(e).__name__)
            if ok:
                case.red_alerted_at = datetime.now(UTC)
        await session.commit()
    if sent:
        log.info("red_alerts sent=%d", sent)
    return sent


async def journal_reminders(
    sessions: Sessions = SessionLocal, r: Redis = redis, send: TgSender = send_text
) -> int:
    """19.00 WIB: remaja aktif yang menautkan Telegram & belum isi jurnal hari ini.

    Bisa dimatikan remaja dengan /pengingat (settings.journal_reminder = false).
    """
    today = datetime.now(WIB).date()
    if not await r.set(f"job:journal_reminder:{today}", "1", nx=True, ex=2 * 86400):
        return 0  # proses lain sudah menjalankan jadwal hari ini
    async with sessions() as session:
        rows = (
            await session.execute(
                select(ChannelLink.telegram_id, User.pseudonym, User.settings)
                .join(User, User.id == ChannelLink.user_id)
                .where(
                    User.status == UserStatus.active,
                    ~exists().where(
                        JournalEntry.user_id == User.id, JournalEntry.entry_date == today
                    ),
                )
            )
        ).all()
    sent = 0
    for tg_id, nick, prefs in rows:
        if prefs.get("journal_reminder", True) is False:
            continue
        text = TG["reminder"].format(nama=nick or "kamu", link=_link("/jurnal"))
        sent += await send(tg_id, text)
        await asyncio.sleep(0.05)  # ponytail: jauh di bawah batas Telegram ~30 pesan/detik
    log.info("journal_reminders sent=%d", sent)
    return sent


def report_text(agg: Aggregate) -> tuple[str, str]:
    """(subjek, isi) laporan mingguan dari agregat dasbor kota — aturan k ≥ 10 sudah berlaku."""
    t = EMAILS["weekly_report"]
    periode = f"{agg.start:%d/%m} – {agg.end:%d/%m/%Y}"
    lines = [t["intro"].format(periode=periode, k=agg.min_cell), ""]
    if agg.kpis is None:
        lines += [t["not_enough"].format(k=agg.min_cell), ""]
    else:
        k = agg.kpis
        handled = "–" if k.handled_15m_pct is None else f"{k.handled_15m_pct}%"
        lines.append(
            t["kpis"].format(
                active=k.active_users, sessions=k.sessions, handled=handled, referrals=k.referrals
            )
        )
        top = sorted(
            (x for x in agg.kelurahan if x.risk_pct is not None), key=lambda x: -(x.risk_pct or 0)
        )
        if top:
            lines += [t["top_kelurahan"], *(f"- {x.name}: {x.risk_pct}%" for x in top[:3]), ""]
        if agg.topics:
            lines += [t["top_topics"], *(f"- {x.label}: {x.pct}%" for x in agg.topics[:3]), ""]
    lines.append(t["footer"].format(link=_link("/kota")))
    return t["subject"].format(periode=periode), "\n".join(lines)


async def weekly_report(
    sessions: Sessions = SessionLocal, r: Redis = redis, mail: Mailer = send_plain
) -> int:
    """Senin 07.00 WIB: ringkasan 7 hari sebelumnya ke admin kota."""
    today = datetime.now(WIB).date()
    if not await r.set(f"job:weekly_report:{today}", "1", nx=True, ex=8 * 86400):
        return 0
    end = today - timedelta(days=1)
    async with sessions() as session:
        agg = await build_aggregate(session, end - timedelta(days=6), end)
        recipients = (
            await session.execute(
                select(User.email).where(
                    User.role == Role.admin_kota,
                    User.status == UserStatus.active,
                    User.email.is_not(None),
                )
            )
        ).scalars()
        emails = [e for e in recipients if e]
    subject, body = report_text(agg)
    sent = 0
    for email in emails:
        try:
            await mail(email, subject, body)
            sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("weekly_report_failed error=%s", type(e).__name__)
    log.info("weekly_report sent=%d", sent)
    return sent


def start() -> AsyncIOScheduler:
    """Dipanggil dari lifespan FastAPI (harus di dalam event loop yang berjalan)."""
    scheduler = AsyncIOScheduler(timezone=WIB)
    scheduler.add_job(
        red_alerts, IntervalTrigger(minutes=1), id="red_alerts", max_instances=1, coalesce=True
    )
    scheduler.add_job(
        journal_reminders,
        CronTrigger(hour=19, minute=0, timezone=WIB),
        id="journal_reminders",
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        weekly_report,
        CronTrigger(day_of_week="mon", hour=7, minute=0, timezone=WIB),
        id="weekly_report",
        misfire_grace_time=6 * 3600,
    )
    scheduler.start()
    return scheduler
