"""Dependency auth + RBAC. Semua pembatasan akses ditegakkan di sini, bukan di frontend (§7)."""

import uuid

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Case, RiskLevel, Role, User, UserStatus
from app.services.auth import read_token

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(401, "Sesi tidak valid. Silakan masuk lagi.")


def _credentials(cred: HTTPAuthorizationCredentials | None) -> str:
    if cred is None:
        raise _unauthorized()
    return cred.credentials


async def current_staff(
    request: Request,
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        payload = read_token(_credentials(cred), "access")
    except jwt.InvalidTokenError:
        raise _unauthorized() from None
    user = await session.get(User, uuid.UUID(payload["sub"]))
    if user is None or user.role == Role.remaja or user.status != UserStatus.active:
        raise _unauthorized()
    request.state.user_id = user.id
    return user


async def current_teen(
    request: Request,
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Akun remaja dari token sesi kita sendiri (email+password). Profil bisa belum lengkap."""
    try:
        payload = read_token(_credentials(cred), "teen")
    except jwt.InvalidTokenError:
        raise _unauthorized() from None
    user = await session.get(User, uuid.UUID(payload["sub"]))
    if user is None or user.role != Role.remaja or user.status == UserStatus.disabled:
        raise _unauthorized()
    request.state.user_id = user.id
    return user


async def active_teen(user: User = Depends(current_teen)) -> User:
    """Remaja yang boleh chat: profil lengkap dan bukan `pending_guardian` (§7)."""
    if user.status == UserStatus.onboarding:
        raise HTTPException(403, "Lengkapi profilmu dulu ya.")
    if user.status != UserStatus.active:
        raise HTTPException(403, "Akunmu masih menunggu persetujuan orang tua/wali.")
    return user


async def current_admin(user: User = Depends(current_staff)) -> User:
    """Hanya admin kota (kelola akun staf)."""
    if user.role != Role.admin_kota:
        raise HTTPException(403, "Hanya admin kota yang bisa mengelola akun staf.")
    return user


def case_scope(staff: User) -> Select[tuple[Case]]:
    """Query dasar kasus yang boleh dilihat staf ini (§1 RBAC, §7)."""
    query = select(Case)
    if staff.role == Role.pendamping:
        return query.where(Case.kelurahan_id == staff.kelurahan_id)
    if staff.role == Role.konselor:
        return query.where(Case.level.in_([RiskLevel.oranye, RiskLevel.merah]))
    raise HTTPException(403, "Dasbor kota hanya menerima data agregat.")
