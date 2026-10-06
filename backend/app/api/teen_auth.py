"""Login remaja dengan email + password di database sendiri (keputusan 2026-10-06, ganti Supabase).

Email tidak disimpan polos (§7): email_hash (HMAC) untuk mencari akun, email_enc (AES-GCM) hanya
untuk mengirim link reset password. Akun baru berstatus "onboarding" sampai profil & janji diisi
(POST /consent/assent). Salah password 5x → dikunci 15 menit (sama dengan staf).
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Role, User, UserStatus
from app.redis import get_redis, hit_rate_limit
from app.services.auth import (
    TEEN_TTL,
    hash_link_token,
    hash_password,
    is_locked,
    issue_token,
    new_link_token,
    register_failure,
    verify_password,
)
from app.services.crypto import decrypt, email_lookup_hash, encrypt
from app.services.email import EMAILS, send_plain
from app.settings import settings

router = APIRouter(prefix="/auth/teen", tags=["auth-remaja"])
log = logging.getLogger(__name__)
RESET_MINUTES = 30
WRONG = "Email atau password salah."


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TeenToken(BaseModel):
    access_token: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=8, max_length=128)


def _token(user: User) -> TeenToken:
    return TeenToken(access_token=issue_token(user.id, "teen", TEEN_TTL))


@router.post("/register", status_code=201)
async def register(body: Credentials, session: AsyncSession = Depends(get_session)) -> TeenToken:
    email_hash = email_lookup_hash(body.email)
    if (await session.execute(select(User.id).where(User.email_hash == email_hash))).first():
        raise HTTPException(409, "Email ini sudah terdaftar. Silakan masuk.")
    user = User(
        role=Role.remaja,
        status=UserStatus.onboarding,
        email_hash=email_hash,
        email_enc=encrypt(body.email.strip().lower()),
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.commit()
    return _token(user)


@router.post("/login")
async def login(body: Credentials, session: AsyncSession = Depends(get_session)) -> TeenToken:
    user = (
        await session.execute(
            select(User).where(
                User.email_hash == email_lookup_hash(body.email), User.role == Role.remaja
            )
        )
    ).scalar_one_or_none()
    password_ok = verify_password(user.password_hash if user else None, body.password)
    if user is not None and is_locked(user):
        raise HTTPException(429, "Terlalu banyak percobaan. Coba lagi 15 menit lagi.")
    if user is None or not password_ok or user.status == UserStatus.disabled:
        if user is not None:
            await register_failure(session, user)
        raise HTTPException(401, WRONG)
    user.failed_logins, user.locked_until = 0, None
    await session.commit()
    return _token(user)


@router.post("/forgot", status_code=202)
async def forgot(
    body: ForgotIn,
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> None:
    """Selalu 202, ada akunnya atau tidak: tidak membocorkan siapa yang memakai AmanDjiwa."""
    email_hash = email_lookup_hash(body.email)
    if await hit_rate_limit(r, f"rl:pwreset:{email_hash}", limit=3, window_s=3600):
        return
    user = (
        await session.execute(
            select(User).where(User.email_hash == email_hash, User.role == Role.remaja)
        )
    ).scalar_one_or_none()
    if user is None or user.email_enc is None or user.status == UserStatus.disabled:
        return
    token, token_hash = new_link_token()
    await r.set(f"pwreset:{token_hash}", str(user.id), ex=RESET_MINUTES * 60)
    tpl = EMAILS["password_reset"]
    link = f"{settings.frontend_origin}/reset-password/{token}"
    try:
        await send_plain(
            decrypt(user.email_enc),
            tpl["subject"],
            tpl["body"].format(link=link, minutes=RESET_MINUTES),
        )
    except OSError as e:
        log.error("password_reset_email_failed user_id=%s error=%s", user.id, type(e).__name__)


@router.post("/reset")
async def reset(
    body: ResetIn,
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> TeenToken:
    """Tautan sekali pakai (30 menit). Berhasil = langsung masuk."""
    user_id = await r.getdel(f"pwreset:{hash_link_token(body.token)}")
    user = await session.get(User, uuid.UUID(user_id)) if user_id else None
    if user is None or user.status == UserStatus.disabled:
        raise HTTPException(410, "Tautan sudah tidak berlaku. Minta tautan baru ya.")
    user.password_hash = hash_password(body.password)
    user.failed_logins, user.locked_until = 0, None
    await session.commit()
    # ponytail: token sesi lama (maks. 7 hari) tidak dicabut; tambah token_version kalau perlu.
    return _token(user)
