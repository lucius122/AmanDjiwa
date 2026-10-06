"""Primitif keamanan: hash password, TOTP, JWT staf, verifikasi token Supabase remaja."""

import hashlib
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.settings import settings

ACCESS_TTL = timedelta(hours=8)
PRE_TOTP_TTL = timedelta(minutes=5)
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
    """Raise jwt.InvalidTokenError kalau tidak valid. Token Supabase (punya aud) ditolak di sini."""
    payload: dict[str, Any] = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("typ") != typ:
        raise jwt.InvalidTokenError("tipe token salah")
    return payload


_jwks = (
    jwt.PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")
    if settings.supabase_url
    else None
)


def read_supabase_sub(token: str) -> str:
    """Verifikasi access token Supabase Auth, kembalikan user id (sub). Sinkron: JWKS bisa fetch.

    Jalur dipilih dari `alg` di header: project baru menandatangani dengan kunci asimetris
    (ES256/RS256, via JWKS), project lama dengan HS256 + JWT secret. Jalur HS256 hanya memakai
    secret dari config, tidak pernah kunci publik JWKS (mencegah algorithm confusion).
    """
    opts: dict[str, Any] = {"audience": "authenticated"}
    if settings.supabase_url:
        opts["issuer"] = f"{settings.supabase_url}/auth/v1"
    alg = jwt.get_unverified_header(token).get("alg")
    if alg == "HS256" and settings.supabase_jwt_secret:
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **opts)
    elif alg in ("ES256", "RS256") and _jwks:
        key = _jwks.get_signing_key_from_jwt(token).key
        payload = jwt.decode(token, key, algorithms=["ES256", "RS256"], **opts)
    else:
        raise jwt.InvalidTokenError(f"token {alg} tidak bisa diverifikasi dengan konfigurasi ini")
    if payload.get("is_anonymous"):  # remaja wajib login email OTP / Google (§3)
        raise jwt.InvalidTokenError("akun anonim tidak diizinkan")
    return str(payload["sub"])


def new_link_token() -> tuple[str, str]:
    """Token acak untuk tautan email. Yang disimpan di DB hanya hash-nya."""
    token = secrets.token_urlsafe(32)
    return token, hash_link_token(token)


def hash_link_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
