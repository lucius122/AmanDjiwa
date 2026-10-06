"""Login staf: email + password → TOTP → JWT berisi role & kelurahan_id (§3 Auth)."""

import uuid
from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_staff
from app.db import get_session
from app.models import Kelurahan, Role, User, UserStatus
from app.services.audit import record_access
from app.services.auth import (
    ACCESS_TTL,
    LOCK_TIME,
    MAX_FAILED_LOGINS,
    PRE_TOTP_TTL,
    issue_token,
    read_token,
    totp_step_if_valid,
    verify_password,
)
from app.services.crypto import decrypt

router = APIRouter(prefix="/auth/staff", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=256)


class LoginOut(BaseModel):
    pre_auth_token: str


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


def _locked(user: User) -> bool:
    return user.locked_until is not None and user.locked_until > datetime.now(UTC)


def _too_many() -> HTTPException:
    return HTTPException(429, "Terlalu banyak percobaan. Coba lagi 15 menit lagi.")


async def _register_failure(session: AsyncSession, user: User) -> None:
    # Dihitung di password DAN TOTP; baru di-reset setelah TOTP sukses, supaya
    # pemegang password curian tidak bisa menebak TOTP tanpa batas.
    user.failed_logins += 1
    if user.failed_logins >= MAX_FAILED_LOGINS:
        user.locked_until = datetime.now(UTC) + LOCK_TIME
        user.failed_logins = 0
    await session.commit()


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
    if user is not None and _locked(user):
        raise _too_many()
    if user is None or not password_ok or user.status != UserStatus.active:
        if user is not None:
            await _register_failure(session, user)
        raise HTTPException(401, "Email atau password salah.")
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
    if _locked(user):
        raise _too_many()

    step = totp_step_if_valid(decrypt(user.totp_secret_enc), body.code, user.totp_last_step)
    if step is None:
        await _register_failure(session, user)
        raise HTTPException(401, "Kode salah atau sudah dipakai.")

    user.totp_last_step = step
    user.failed_logins = 0
    user.locked_until = None
    await record_access(session, user.id, "staff_login")
    await session.commit()
    token = issue_token(
        user.id, "access", ACCESS_TTL, role=user.role.value, kelurahan_id=user.kelurahan_id
    )
    out = await _staff_out(session, user)
    return TokenOut(access_token=token, **out.model_dump())


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
