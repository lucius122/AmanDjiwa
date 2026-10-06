"""Primitif keamanan: hash password, TOTP, JWT (staf & remaja), batas salah password."""

import hashlib
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import jwt
import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.settings import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models import User

ACCESS_TTL = timedelta(hours=8)
PRE_TOTP_TTL = timedelta(minutes=5)
PRE_SETUP_TTL = timedelta(minutes=15)  # login pertama staf: pasang authenticator + ganti password
TEEN_TTL = timedelta(days=7)  # sesi remaja; "Keluar" di menu Aku menghapusnya dari perangkat
MAX_FAILED_LOGINS = 5
LOCK_TIME = timedelta(minutes=15)

_ph = PasswordHasher()
_DUMMY_HASH = _ph.hash(secrets.token_hex(16))  # email tak dikenal tetap "membayar" waktu verify


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _ph.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, InvalidHashError):
        return False


def totp_step_if_valid(secret: str, code: str, last_step: int) -> int | None:
    """Kembalikan time-step yang cocok (toleransi ±1 langkah), atau None.

    Step harus lebih besar dari last_step supaya kode yang sama tidak bisa dipakai dua kali.
    """
    totp = pyotp.TOTP(secret)
    now = int(time.time()) // totp.interval
    for step in (now - 1, now, now + 1):
        if step > last_step and secrets.compare_digest(totp.generate_otp(step), code):
            return step
    return None


def issue_token(sub: uuid.UUID, typ: str, ttl: timedelta, **claims: str | int | None) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(sub), "typ": typ, "iat": now, "exp": now + ttl, **claims}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def read_token(token: str, typ: str) -> dict[str, Any]:
    """Raise jwt.InvalidTokenError kalau tidak valid atau tipenya lain (remaja ≠ staf)."""
    payload: dict[str, Any] = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("typ") != typ:
        raise jwt.InvalidTokenError("tipe token salah")
    return payload


def is_locked(user: "User") -> bool:
    return user.locked_until is not None and user.locked_until > datetime.now(UTC)


async def register_failure(session: "AsyncSession", user: "User") -> None:
    """Salah password/kode ke-5 → akun dikunci 15 menit. Dipakai login staf dan remaja."""
    user.failed_logins += 1
    if user.failed_logins >= MAX_FAILED_LOGINS:
        user.locked_until = datetime.now(UTC) + LOCK_TIME
        user.failed_logins = 0
    await session.commit()


_TEMP_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"  # tanpa 0/O, 1/l/I


def new_temp_password() -> str:
    """Password sementara akun staf baru/di-reset (ditampilkan sekali ke admin kota).

    12 karakter tanpa huruf yang mirip, karena biasanya dibacakan / disalin manual.
    """
    return "".join(secrets.choice(_TEMP_ALPHABET) for _ in range(12))


def new_link_token() -> tuple[str, str]:
    """Token acak untuk tautan email. Yang disimpan di DB hanya hash-nya."""
    token = secrets.token_urlsafe(32)
    return token, hash_link_token(token)


def hash_link_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
