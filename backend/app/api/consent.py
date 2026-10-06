"""Onboarding remaja: persetujuan remaja (assent) + persetujuan orang tua/wali (§7)."""

import logging
import re
from datetime import UTC, date, datetime, timedelta
from typing import Literal, Self

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_teen, teen_sub
from app.api.me import MeOut, me_out
from app.db import get_session
from app.models import (
    ConsentStatus,
    GuardianConsent,
    GuardianRelation,
    Kelurahan,
    Role,
    User,
    UserStatus,
)
from app.pipeline.responder import HOTLINES, Hotline
from app.services.auth import hash_link_token, new_link_token
from app.services.crypto import encrypt
from app.services.email import send_guardian_request
from app.settings import settings

router = APIRouter(tags=["consent"])
log = logging.getLogger(__name__)

GUARDIAN_LINK_DAYS = 7  # asumsi; CLAUDE.md tidak menentukan masa berlaku
RESEND_COOLDOWN = timedelta(seconds=60)
_CONTACT_LIKE = re.compile(r"@|\d{5,}")


def needs_guardian(birth_year: int, today: date) -> bool:
    """Hanya tahun lahir yang diketahui, jadi yang lahir di (tahun ini - 18) bisa saja masih 17.

    Dibuat konservatif: kalau mungkin di bawah 18, wajib izin wali.
    """
    return today.year - birth_year <= 18


class KelurahanOut(BaseModel):
    id: int
    name: str


class AssentIn(BaseModel):
    pseudonym: str = Field(min_length=1, max_length=20)
    avatar: int = Field(ge=0, le=7)
    kelurahan_id: int
    birth_year: int
    agree: Literal[True]

    @field_validator("pseudonym")
    @classmethod
    def _pseudonym(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nama samaran belum diisi.")
        if _CONTACT_LIKE.search(v):  # jangan sampai email / no. HP masuk sebagai nama
            raise ValueError("Pakai nama samaran aja, tanpa email atau nomor HP.")
        return v

    @field_validator("birth_year")
    @classmethod
    def _age_13_to_19(cls, v: int) -> int:
        year = date.today().year
        if not year - 19 <= v <= year - 13:
            raise ValueError("AmanDjiwa untuk remaja 13–19 tahun.")
        return v


class GuardianRequestIn(BaseModel):
    email: EmailStr


class GuardianDecisionIn(BaseModel):
    decision: Literal["approve", "decline", "revoke"]
    guardian_name: str | None = Field(default=None, max_length=120)
    relation: GuardianRelation | None = None

    @model_validator(mode="after")
    def _approve_needs_identity(self) -> Self:
        if self.decision == "approve" and not (
            self.guardian_name and self.guardian_name.strip() and self.relation
        ):
            raise ValueError("Nama lengkap dan hubungan dengan anak wajib diisi.")
        return self


class GuardianDecisionOut(BaseModel):
    status: ConsentStatus


class GuardianStatusOut(BaseModel):
    status: Literal["pending", "approved", "declined", "revoked", "expired"]


@router.get("/hotlines")
async def list_hotlines() -> list[Hotline]:
    """Publik: landing & layar menunggu butuh nomor bantuan sebelum login (§6.6: dari YAML)."""
    return list(HOTLINES)


@router.get("/kelurahan")
async def list_kelurahan(session: AsyncSession = Depends(get_session)) -> list[KelurahanOut]:
    rows = (await session.execute(select(Kelurahan).order_by(Kelurahan.name))).scalars()
    return [KelurahanOut(id=k.id, name=k.name) for k in rows]


@router.post("/consent/assent", status_code=201)
async def assent(
    body: AssentIn,
    sub: str = Depends(teen_sub),
    session: AsyncSession = Depends(get_session),
) -> MeOut:
    if (await session.execute(select(User.id).where(User.auth_id == sub))).first():
        raise HTTPException(409, "Profil sudah ada.")
    if await session.get(Kelurahan, body.kelurahan_id) is None:
        raise HTTPException(422, "Kelurahan tidak dikenal.")
    minor = needs_guardian(body.birth_year, date.today())
    user = User(
        role=Role.remaja,
        auth_id=sub,
        pseudonym=body.pseudonym,
        avatar=body.avatar,
        kelurahan_id=body.kelurahan_id,
        birth_year=body.birth_year,
        assented_at=datetime.now(UTC),
        status=UserStatus.pending_guardian if minor else UserStatus.active,
    )
    session.add(user)
    await session.commit()
    return await me_out(session, user)


@router.post("/consent/guardian", status_code=202)
async def request_guardian(
    body: GuardianRequestIn,
    user: User = Depends(current_teen),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Kirim (ulang) email persetujuan. Dipakai juga untuk 'Ganti email orang tua'."""
    if user.status != UserStatus.pending_guardian:
        raise HTTPException(409, "Akunmu tidak butuh persetujuan wali.")
    last = (
        await session.execute(
            select(GuardianConsent.created_at)
            .where(GuardianConsent.user_id == user.id)
            .order_by(GuardianConsent.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if last is not None and datetime.now(UTC) - last < RESEND_COOLDOWN:
        raise HTTPException(429, "Tunggu sebentar sebelum kirim ulang ya.")

    # Tautan lama yang belum dijawab dibatalkan; hanya tautan terbaru yang berlaku.
    await session.execute(
        delete(GuardianConsent).where(
            GuardianConsent.user_id == user.id, GuardianConsent.status == ConsentStatus.pending
        )
    )
    token, token_hash = new_link_token()
    session.add(
        GuardianConsent(
            user_id=user.id,
            token_hash=token_hash,
            email_enc=encrypt(body.email),
            expires_at=datetime.now(UTC) + timedelta(days=GUARDIAN_LINK_DAYS),
        )
    )
    await session.flush()
    try:
        await send_guardian_request(
            body.email, f"{settings.frontend_origin}/persetujuan-wali/{token}", GUARDIAN_LINK_DAYS
        )
    except OSError as e:
        await session.rollback()
        log.error("guardian_email_failed user_id=%s error=%s", user.id, type(e).__name__)
        raise HTTPException(503, "Email belum terkirim. Coba lagi ya.") from None
    await session.commit()


async def _consent_by_token(session: AsyncSession, token: str) -> GuardianConsent:
    consent = (
        await session.execute(
            select(GuardianConsent).where(GuardianConsent.token_hash == hash_link_token(token))
        )
    ).scalar_one_or_none()
    if consent is None:
        raise HTTPException(404, "Tautan tidak valid.")
    return consent


@router.get("/consent/guardian/{token}")
async def guardian_status(
    token: str, session: AsyncSession = Depends(get_session)
) -> GuardianStatusOut:
    """Status tautan untuk halaman ortu: form, sudah disetujui (bisa dicabut), atau kedaluwarsa."""
    consent = await _consent_by_token(session, token)
    if consent.status == ConsentStatus.pending and consent.expires_at <= datetime.now(UTC):
        return GuardianStatusOut(status="expired")
    return GuardianStatusOut(status=consent.status.value)


@router.post("/consent/guardian/{token}")
async def guardian_decision(
    token: str, body: GuardianDecisionIn, session: AsyncSession = Depends(get_session)
) -> GuardianDecisionOut:
    consent = await _consent_by_token(session, token)
    user = await session.get(User, consent.user_id)
    assert user is not None  # FK cascade: consent tidak bisa ada tanpa user

    if body.decision == "revoke":
        if consent.status != ConsentStatus.approved:
            raise HTTPException(409, "Belum ada persetujuan yang bisa dicabut.")
        consent.status = ConsentStatus.revoked
        user.status = UserStatus.pending_guardian
    else:
        if consent.status != ConsentStatus.pending:
            raise HTTPException(409, "Tautan ini sudah dipakai.")
        if consent.expires_at <= datetime.now(UTC):
            raise HTTPException(410, "Tautan sudah kedaluwarsa. Minta anak mengirim ulang.")
        if body.decision == "approve":
            assert body.guardian_name is not None  # dijamin validator
            consent.status = ConsentStatus.approved
            consent.guardian_name_enc = encrypt(body.guardian_name.strip())
            consent.relation = body.relation
            user.status = UserStatus.active
        else:
            consent.status = ConsentStatus.declined
    consent.decided_at = datetime.now(UTC)
    await session.commit()
    return GuardianDecisionOut(status=consent.status)
