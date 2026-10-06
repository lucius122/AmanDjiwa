"""Kelola akun staf oleh admin kota (keputusan 2026-10-06): tambah, nonaktifkan, reset.

Akun baru / hasil reset mendapat password sementara (ditampilkan SEKALI ke admin) dan belum punya
authenticator; staf memasangnya sendiri saat login pertama, jadi admin tidak pernah memegang
kunci 2FA staf. Semua perubahan tercatat di audit_logs (target_id = akun yang diubah).
Data remaja tidak pernah disentuh router ini.
"""

import uuid
from datetime import datetime
from typing import Literal, Self

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_admin
from app.db import get_session
from app.models import Kelurahan, Role, User, UserStatus
from app.services.audit import record_access
from app.services.auth import hash_password, new_temp_password
from app.settings import settings

router = APIRouter(prefix="/admin/staff", tags=["admin"])
StaffRole = Literal["pendamping", "konselor", "admin_kota"]


class StaffAccount(BaseModel):
    id: uuid.UUID
    display_name: str | None
    email: str | None
    role: Role
    kelurahan_id: int | None
    kelurahan_name: str | None
    status: UserStatus
    needs_setup: bool  # belum memasang authenticator (login pertama)
    created_at: datetime


class StaffCreateIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=64)
    email: EmailStr
    role: StaffRole
    kelurahan_id: int | None = None

    @model_validator(mode="after")
    def _pendamping_needs_kelurahan(self) -> Self:
        if self.role == "pendamping" and self.kelurahan_id is None:
            raise ValueError("Pendamping wajib punya kelurahan.")
        if self.role != "pendamping":
            self.kelurahan_id = None  # konselor & admin kota tidak terikat kelurahan
        return self


class StaffWithPassword(BaseModel):
    account: StaffAccount
    temp_password: str  # tampilkan sekali; staf wajib menggantinya saat login pertama


class StaffStatusIn(BaseModel):
    status: Literal["active", "disabled"]


async def _out(session: AsyncSession, user: User) -> StaffAccount:
    kel = await session.get(Kelurahan, user.kelurahan_id) if user.kelurahan_id else None
    return StaffAccount(
        id=user.id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        kelurahan_id=user.kelurahan_id,
        kelurahan_name=kel.name if kel else None,
        status=user.status,
        needs_setup=settings.staff_totp and user.totp_secret_enc is None,
        created_at=user.created_at,
    )


async def _staff(session: AsyncSession, staff_id: uuid.UUID) -> User:
    user = await session.get(User, staff_id)
    if user is None or user.role == Role.remaja:
        raise HTTPException(404, "Akun staf tidak ditemukan.")
    return user


@router.get("")
async def list_staff(
    _: User = Depends(current_admin), session: AsyncSession = Depends(get_session)
) -> list[StaffAccount]:
    rows = await session.execute(
        select(User).where(User.role != Role.remaja).order_by(User.role, User.display_name)
    )
    return [await _out(session, u) for u in rows.scalars()]


@router.post("", status_code=201)
async def create_staff(
    body: StaffCreateIn,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> StaffWithPassword:
    email = body.email.strip().lower()
    if (await session.execute(select(User.id).where(User.email == email))).first():
        raise HTTPException(409, "Email ini sudah dipakai akun staf lain.")
    if body.kelurahan_id is not None and await session.get(Kelurahan, body.kelurahan_id) is None:
        raise HTTPException(422, "Kelurahan tidak dikenal.")
    password = new_temp_password()
    user = User(
        role=Role(body.role),
        email=email,
        display_name=body.display_name.strip(),
        kelurahan_id=body.kelurahan_id,
        password_hash=hash_password(password),
        status=UserStatus.active,
    )
    session.add(user)
    await session.flush()
    await record_access(session, admin.id, "staff_create", target_id=user.id)
    await session.commit()
    return StaffWithPassword(account=await _out(session, user), temp_password=password)


@router.patch("/{staff_id}")
async def set_status(
    staff_id: uuid.UUID,
    body: StaffStatusIn,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> StaffAccount:
    user = await _staff(session, staff_id)
    if user.id == admin.id:  # pelaku selalu admin aktif, jadi minimal satu admin kota tersisa
        raise HTTPException(409, "Kamu tidak bisa menonaktifkan akunmu sendiri.")
    user.status = UserStatus(body.status)
    action = "staff_disable" if body.status == "disabled" else "staff_enable"
    await record_access(session, admin.id, action, target_id=user.id)
    await session.commit()
    return await _out(session, user)


@router.post("/{staff_id}/reset")
async def reset_staff(
    staff_id: uuid.UUID,
    admin: User = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
) -> StaffWithPassword:
    """Lupa password / HP hilang: password sementara baru + authenticator dipasang ulang."""
    user = await _staff(session, staff_id)
    if user.id == admin.id:
        raise HTTPException(409, "Minta admin kota lain untuk mereset akunmu.")
    password = new_temp_password()
    user.password_hash = hash_password(password)
    user.totp_secret_enc = None
    user.totp_last_step = 0
    user.failed_logins, user.locked_until = 0, None
    await record_access(session, admin.id, "staff_reset", target_id=user.id)
    await session.commit()
    return StaffWithPassword(account=await _out(session, user), temp_password=password)
