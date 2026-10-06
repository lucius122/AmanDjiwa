"""Jurnal emosi remaja (CLAUDE.md §9): POST /journal, GET /journal?days=14."""

import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import active_teen
from app.db import get_session
from app.models import Emotion, JournalEntry, RiskAssessment, RiskLevel, User
from app.pipeline import analyze, default_models
from app.services.chat import WIB, upsert_case
from app.services.crypto import decrypt, encrypt

router = APIRouter(prefix="/journal", tags=["journal"])
log = logging.getLogger(__name__)


class JournalIn(BaseModel):
    emotion: Emotion
    intensity: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=1000)


class JournalEntryOut(BaseModel):
    entry_date: date
    emotion: Emotion
    intensity: int
    note: str | None


class JournalSaveOut(BaseModel):
    entry: JournalEntryOut
    help: bool  # catatan menunjukkan bahaya → UI membuka "Butuh bantuan sekarang?"


def _out(e: JournalEntry) -> JournalEntryOut:
    note = decrypt(e.note_enc) if e.note_enc else None
    return JournalEntryOut(
        entry_date=e.entry_date, emotion=e.emotion, intensity=e.intensity, note=note
    )


async def _note_needs_help(session: AsyncSession, user: User, note: str) -> bool:
    """Catatan jurnal ikut diperiksa detektor krisis (§6.1).

    Kalau berbahaya: kasus merah dibuat supaya pendamping bisa menyapa, TAPI isi catatan tidak
    ditautkan ke kasus (desain: "Obrolan dan jurnalmu cuma bisa kamu lihat").
    """
    try:
        analysis = await analyze(note, models=default_models())
    except Exception as e:  # noqa: BLE001 — ragu = tampilkan bantuan (fail-safe §6.2)
        log.error("journal_crisis_check_failed user_id=%s error=%s", user.id, type(e).__name__)
        return True
    if not analysis.crisis.is_crisis:
        return False
    assessment = RiskAssessment(
        user_id=user.id,
        level=RiskLevel.merah,
        ter_score=analysis.ter,
        triggers=["jurnal", *analysis.crisis.categories],
    )
    session.add(assessment)
    await session.flush()
    await upsert_case(session, user, RiskLevel.merah, assessment)
    return True


@router.post("")
async def save_entry(
    body: JournalIn,
    user: User = Depends(active_teen),
    session: AsyncSession = Depends(get_session),
) -> JournalSaveOut:
    """Satu entri per hari (WIB); simpan lagi di hari yang sama = "Perbarui jurnal"."""
    today = datetime.now(WIB).date()
    note = (body.note or "").strip() or None
    entry = (
        await session.execute(
            select(JournalEntry).where(
                JournalEntry.user_id == user.id, JournalEntry.entry_date == today
            )
        )
    ).scalar_one_or_none()
    if entry is None:
        # ponytail: dua simpan bersamaan bisa bentrok di UNIQUE (user, tanggal); pakai
        # INSERT ... ON CONFLICT kalau itu mulai terjadi.
        entry = JournalEntry(user_id=user.id, entry_date=today)
        session.add(entry)
    entry.emotion, entry.intensity = body.emotion, body.intensity
    entry.note_enc = encrypt(note) if note else None
    help_needed = await _note_needs_help(session, user, note) if note else False
    await session.commit()
    return JournalSaveOut(entry=_out(entry), help=help_needed)


@router.get("")
async def list_entries(
    days: int = Query(default=14, ge=1, le=90),
    user: User = Depends(active_teen),
    session: AsyncSession = Depends(get_session),
) -> list[JournalEntryOut]:
    since = datetime.now(WIB).date() - timedelta(days=days - 1)
    rows = await session.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == user.id, JournalEntry.entry_date >= since)
        .order_by(JournalEntry.entry_date)
    )
    return [_out(e) for e in rows.scalars()]
