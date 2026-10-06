"""Login staf: email + password → TOTP → JWT berisi role & kelurahan_id (§3 Auth).

Akun yang dibuat/di-reset admin kota belum punya authenticator: setelah password sementara benar,
staf wajib memasang authenticator sendiri dan mengganti password (admin tidak pernah melihat kunci
2FA-nya). Kunci yang sedang dipasang disimpan sementara di Redis, bukan di DB.
"""

import uuid

import jwt
import pyotp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_staff
from app.db import get_session
from app.models import Kelurahan, Role, User, UserStatus
from app.redis import get_redis
from app.services.audit import record_access
from app.services.auth import (
    ACCESS_TTL,
    PRE_SETUP_TTL,
    PRE_TOTP_TTL,
    hash_password,
    is_locked,
    issue_token,
    read_token,
    register_failure,
    totp_step_if_valid,
    verify_password,
)
from app.services.crypto import decrypt, encrypt

router = APIRouter(prefix="/auth/staff", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=256)


class LoginOut(BaseModel):
    pre_auth_token: str
    setup_required: bool = False  # login pertama: pasang authenticator + ganti password


class SetupStartIn(BaseModel):
    pre_auth_token: str


class SetupStartOut(BaseModel):
    secret: str  # "kunci penyiapan" untuk aplikasi authenticator
    otpauth_uri: str


class SetupFinishIn(BaseModel):
    pre_auth_token: str
    code: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=12, max_length=256)


class TotpIn(BaseModel):
    pre_auth_token: str
    code: str = Field(pattern=r"^\d{6}$")


class StaffOut(BaseModel):
    role: Role
    display_name: str | None
    kelurahan_id: int | None
    kelurahan_name: str | None


class TokenOut(StaffOut):
    access_token: str


def _too_many() -> HTTPException:
    return HTTPException(429, "Terlalu banyak percobaan. Coba lagi 15 menit lagi.")


async def _staff_out(session: AsyncSession, user: User) -> StaffOut:
    kel = await session.get(Kelurahan, user.kelurahan_id) if user.kelurahan_id else None
    return StaffOut(
        role=user.role,
        display_name=user.display_name,
        kelurahan_id=user.kelurahan_id,
        kelurahan_name=kel.name if kel else None,
    )


@router.post("/login")
async def login(body: LoginIn, session: AsyncSession = Depends(get_session)) -> LoginOut:
    user = (
        await session.execute(
            select(User).where(User.email == body.email.lower(), User.role != Role.remaja)
        )
    ).scalar_one_or_none()
    password_ok = verify_password(user.password_hash if user else None, body.password)
    if user is not None and is_locked(user):
        raise _too_many()
    if user is None or not password_ok or user.status != UserStatus.active:
        if user is not None:
            await register_failure(session, user)
        raise HTTPException(401, "Email atau password salah.")
    if user.totp_secret_enc is None:  # akun baru / di-reset admin kota
        return LoginOut(
            pre_auth_token=issue_token(user.id, "pre_setup", PRE_SETUP_TTL), setup_required=True
        )
    return LoginOut(pre_auth_token=issue_token(user.id, "pre_totp", PRE_TOTP_TTL))


@router.post("/totp")
async def totp(body: TotpIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    try:
        payload = read_token(body.pre_auth_token, "pre_totp")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Sesi login habis. Masukkan email dan password lagi.") from None
    user = await session.get(User, uuid.UUID(payload["sub"]))
    if user is None or user.totp_secret_enc is None or user.status != UserStatus.active:
        raise HTTPException(401, "Sesi login habis. Masukkan email dan password lagi.")
    if is_locked(user):
        raise _too_many()

    step = totp_step_if_valid(decrypt(user.totp_secret_enc), body.code, user.totp_last_step)
    if step is None:
        await register_failure(session, user)
        raise HTTPException(401, "Kode salah atau sudah dipakai.")

    user.totp_last_step = step
    return await _signed_in(session, user, "staff_login")


async def _signed_in(session: AsyncSession, user: User, action: str) -> TokenOut:
    user.failed_logins = 0
    user.locked_until = None
    await record_access(session, user.id, action)
    await session.commit()
    token = issue_token(
        user.id, "access", ACCESS_TTL, role=user.role.value, kelurahan_id=user.kelurahan_id
    )
    out = await _staff_out(session, user)
    return TokenOut(access_token=token, **out.model_dump())


async def _setup_user(session: AsyncSession, pre_auth_token: str) -> User:
    try:
        payload = read_token(pre_auth_token, "pre_setup")
    except jwt.InvalidTokenError:
        raise HTTPException(
            401, "Sesi pengaturan habis. Masuk lagi dengan password sementara."
        ) from None
    user = await session.get(User, uuid.UUID(payload["sub"]))
    if user is None or user.status != UserStatus.active or user.totp_secret_enc is not None:
        raise HTTPException(401, "Sesi pengaturan habis. Masuk lagi dengan password sementara.")
    if is_locked(user):
        raise _too_many()
    return user


@router.post("/setup/start")
async def setup_start(
    body: SetupStartIn,
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> SetupStartOut:
    """Buat kunci authenticator baru untuk dipindai/diketik staf (berlaku 15 menit)."""
    user = await _setup_user(session, body.pre_auth_token)
    secret = pyotp.random_base32()
    await r.set(f"staff-setup:{user.id}", secret, ex=int(PRE_SETUP_TTL.total_seconds()))
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email or "", issuer_name="AmanDjiwa")
    return SetupStartOut(secret=secret, otpauth_uri=uri)


@router.post("/setup/finish")
async def setup_finish(
    body: SetupFinishIn,
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> TokenOut:
    user = await _setup_user(session, body.pre_auth_token)
    secret = await r.get(f"staff-setup:{user.id}")
    if secret is None:
        raise HTTPException(401, "Sesi pengaturan habis. Masuk lagi dengan password sementara.")
    step = totp_step_if_valid(secret, body.code, 0)
    if step is None:
        await register_failure(session, user)
        raise HTTPException(401, "Kode salah. Cek jam di HP dan aplikasi authenticator-nya.")
    if verify_password(user.password_hash, body.new_password):
        raise HTTPException(422, "Pakai password baru, bukan password sementara.")
    user.totp_secret_enc = encrypt(secret)
    user.totp_last_step = step
    user.password_hash = hash_password(body.new_password)
    await r.delete(f"staff-setup:{user.id}")
    return await _signed_in(session, user, "staff_setup")


@router.get("/me")
async def staff_me(
    user: User = Depends(current_staff), session: AsyncSession = Depends(get_session)
) -> StaffOut:
    return await _staff_out(session, user)


class StaffSettings(BaseModel):
    """Halaman "Pengaturan" (default ikut prototipe)."""

    notif_red: bool = True  # notifikasi kasus merah
    sound: bool = False  # bunyi peringatan
    compact: bool = True  # sembunyikan cuplikan pesan sampai diklik


@router.get("/settings")
async def get_settings(user: User = Depends(current_staff)) -> StaffSettings:
    return StaffSettings(**user.settings)


@router.put("/settings")
async def put_settings(
    body: StaffSettings,
    user: User = Depends(current_staff),
    session: AsyncSession = Depends(get_session),
) -> StaffSettings:
    user.settings = body.model_dump()
    await session.commit()
    return body
