"""Tes jalan di Postgres sungguhan (DB terpisah) dengan migrasi Alembic asli.

Butuh `docker compose up -d postgres` dan database `amandjiwa_test` (lihat TEST_DATABASE_URL).
"""

import asyncio
import base64
import os
import secrets
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path
from typing import Any

# Env diset SEBELUM app diimpor: tes tidak boleh menyentuh DB dev atau secret asli.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://amandjiwa:amandjiwa@127.0.0.1:5433/amandjiwa_test"
)
os.environ["MESSAGE_ENC_KEY"] = base64.b64encode(os.urandom(32)).decode()
os.environ["JWT_SECRET"] = secrets.token_urlsafe(48)
# Tes tidak pernah memanggil LLM sungguhan; test_llm memakai tiruan.
os.environ["NVIDIA_API_KEY"] = ""
os.environ["DEMO_MODE"] = "false"  # test_demo menyalakannya sendiri
os.environ["RUN_JOBS"] = "false"  # tes memanggil fungsi job langsung
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = ""  # tes bootstrap mengisinya sendiri
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = ""
os.environ["TELEGRAM_BOT_TOKEN"] = ""  # tes tidak pernah memanggil API Telegram sungguhan
os.environ["TELEGRAM_WEBHOOK_SECRET"] = ""
os.environ["REDIS_URL"] = REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6379/15")

import pyotp  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from redis.asyncio import Redis  # noqa: E402
from sqlalchemy import ColumnElement, text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Role, User  # noqa: E402
from app.redis import get_redis  # noqa: E402
from app.services.auth import hash_password  # noqa: E402
from app.services.crypto import email_lookup_hash, encrypt  # noqa: E402

KROBOKAN, MANYARAN = 10, 11  # id dari seed migrasi 0001
STAFF_EMAIL = "dimas@example.com"
STAFF_PASSWORD = "kata-sandi-staf-panjang"

# NullPool: koneksi tidak dipakai ulang, jadi aman lintas event loop (tiap tes punya loop sendiri).
engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
TestSession = async_sessionmaker(engine, expire_on_commit=False)
_TABLES = ", ".join(t.name for t in Base.metadata.sorted_tables if t.name != "kelurahan")


async def _session() -> AsyncIterator[Any]:
    async with TestSession() as s:
        yield s


app.dependency_overrides[get_session] = _session


@pytest.fixture(scope="session")
def _migrated_db() -> None:
    async def reset() -> None:
        async with engine.begin() as c:
            await c.execute(text("DROP SCHEMA public CASCADE"))
            await c.execute(text("CREATE SCHEMA public"))

    asyncio.run(reset())
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")


@pytest.fixture
def db(_migrated_db: None) -> None:
    """DB tes bersih. Dipakai hanya oleh tes yang butuh DB; tes pipeline murni tidak."""

    async def truncate() -> None:
        async with engine.begin() as c:
            await c.execute(text(f"TRUNCATE {_TABLES} RESTART IDENTITY CASCADE"))

    asyncio.run(truncate())


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    # Klien baru per tes: koneksi redis.asyncio terikat ke event loop tes.
    r = Redis.from_url(REDIS_URL, decode_responses=True)
    await r.flushdb()
    yield r
    await r.aclose()


@pytest.fixture
async def client(db: None, redis_client: Redis) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_redis] = lambda: redis_client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_redis, None)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


TEEN_PASSWORD = "kata-sandi-remaja"


def teen_where(sub: str) -> ColumnElement[bool]:
    """Kondisi WHERE untuk akun remaja yang dibuat account(client, sub)."""
    return User.email_hash == email_lookup_hash(f"{sub}@example.com")


async def account(client: AsyncClient, sub: str = "teen-1") -> dict[str, str]:
    """Akun remaja email+password (profil belum diisi) → header Bearer. Sudah ada = masuk."""
    body = {"email": f"{sub}@example.com", "password": TEEN_PASSWORD}
    r = await client.post("/auth/teen/register", json=body)
    if r.status_code == 409:
        r = await client.post("/auth/teen/login", json=body)
    assert r.status_code in (200, 201), r.text
    return bearer(r.json()["access_token"])


def assent_body(**override: object) -> dict[str, object]:
    body = {
        "pseudonym": "Bintang Senja",
        "avatar": 0,
        "kelurahan_id": KROBOKAN,
        "birth_year": date.today().year - 16,
        "agree": True,
    }
    return body | override


async def make_staff(role: Role, kelurahan_id: int | None = None, email: str = STAFF_EMAIL) -> str:
    """Buat staf dengan STAFF_PASSWORD. Kembalikan secret TOTP-nya."""
    secret = pyotp.random_base32()
    async with TestSession() as s:
        s.add(
            User(
                role=role,
                email=email,
                display_name="Kak Dimas P.",
                password_hash=hash_password(STAFF_PASSWORD),
                totp_secret_enc=encrypt(secret),
                kelurahan_id=kelurahan_id,
            )
        )
        await s.commit()
    return secret


async def staff_login(client: AsyncClient, secret: str, email: str = STAFF_EMAIL) -> dict[str, Any]:
    r = await client.post("/auth/staff/login", json={"email": email, "password": STAFF_PASSWORD})
    pre = r.json()["pre_auth_token"]
    r = await client.post(
        "/auth/staff/totp", json={"pre_auth_token": pre, "code": pyotp.TOTP(secret).now()}
    )
    assert r.status_code == 200, r.text
    body: dict[str, Any] = r.json()
    return body
