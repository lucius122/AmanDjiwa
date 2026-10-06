"""Admin kota pertama dari env: hanya kalau belum ada admin, lalu wajib atur akun saat login."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app import bootstrap
from app.models import Role, User
from tests.conftest import TestSession, make_staff

pytestmark = pytest.mark.anyio
EMAIL, PASSWORD = "Admin.Kota@Example.com", "sementara-awal-123"


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bootstrap.settings, "bootstrap_admin_email", EMAIL)
    monkeypatch.setattr(bootstrap.settings, "bootstrap_admin_password", PASSWORD)


async def _admins() -> int:
    async with TestSession() as s:
        q = select(func.count()).where(User.role == Role.admin_kota)
        return int((await s.execute(q)).scalar_one())


async def test_creates_first_admin_that_must_set_up_on_login(
    client: AsyncClient, env: None
) -> None:
    assert await bootstrap.ensure_first_admin(TestSession) is True
    assert await bootstrap.ensure_first_admin(TestSession) is False  # sudah ada admin
    assert await _admins() == 1
    r = await client.post("/auth/staff/login", json={"email": EMAIL.lower(), "password": PASSWORD})
    assert r.status_code == 200 and r.json()["setup_required"] is True


async def test_ignored_when_an_admin_already_exists(db: None, env: None) -> None:
    await make_staff(Role.admin_kota, email="sudah@example.com")
    assert await bootstrap.ensure_first_admin(TestSession) is False
    assert await _admins() == 1


async def test_needs_both_values_and_long_password(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert await bootstrap.ensure_first_admin(TestSession) is False  # env kosong
    monkeypatch.setattr(bootstrap.settings, "bootstrap_admin_email", EMAIL)
    monkeypatch.setattr(bootstrap.settings, "bootstrap_admin_password", "pendek")
    assert await bootstrap.ensure_first_admin(TestSession) is False
    assert await _admins() == 0
