"""Admin kota mengelola akun staf; staf memasang authenticator sendiri saat login pertama."""

from typing import Any

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import AuditLog, Role
from tests.conftest import KROBOKAN, TestSession, bearer, make_staff, staff_login

pytestmark = pytest.mark.anyio
NEW = {"display_name": "Kak Rina", "email": "Rina@Example.com", "role": "pendamping"}


async def _admin(client: AsyncClient) -> dict[str, str]:
    secret = await make_staff(Role.admin_kota, email="admin@example.com")
    return bearer((await staff_login(client, secret, email="admin@example.com"))["access_token"])


async def _create(client: AsyncClient, h: dict[str, str], **body: str) -> dict[str, Any]:
    r = await client.post("/admin/staff", json=NEW | {"kelurahan_id": KROBOKAN} | body, headers=h)
    assert r.status_code == 201, r.text
    out: dict[str, Any] = r.json()
    return out


async def _first_login(client: AsyncClient, email: str, password: str) -> dict[str, Any]:
    r = await client.post("/auth/staff/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    out: dict[str, Any] = r.json()
    return out


async def test_only_admin_kota_manages_staff(client: AsyncClient) -> None:
    secret = await make_staff(Role.pendamping, KROBOKAN, email="p@example.com")
    h = bearer((await staff_login(client, secret, email="p@example.com"))["access_token"])
    assert (await client.get("/admin/staff", headers=h)).status_code == 403
    assert (await client.post("/admin/staff", json=NEW, headers=h)).status_code == 403
    assert (await client.get("/admin/staff")).status_code == 401


async def test_create_validates_and_lists(client: AsyncClient) -> None:
    h = await _admin(client)
    no_kel = await client.post("/admin/staff", json=NEW, headers=h)
    assert no_kel.status_code == 422  # pendamping wajib kelurahan
    created = await _create(client, h)
    acc = created["account"]
    assert acc["email"] == "rina@example.com" and acc["needs_setup"] is True
    assert len(created["temp_password"]) >= 12
    konselor = await _create(client, h, email="k@example.com", role="konselor")
    assert konselor["account"]["kelurahan_id"] is None
    dup = await client.post("/admin/staff", json=NEW | {"kelurahan_id": KROBOKAN}, headers=h)
    assert dup.status_code == 409
    emails = {a["email"] for a in (await client.get("/admin/staff", headers=h)).json()}
    assert emails == {"admin@example.com", "rina@example.com", "k@example.com"}


async def test_first_login_sets_own_authenticator_and_password(client: AsyncClient) -> None:
    created = await _create(client, await _admin(client))
    temp = created["temp_password"]
    first = await _first_login(client, "rina@example.com", temp)
    assert first["setup_required"] is True
    pre = first["pre_auth_token"]
    # Token pengaturan tidak bisa dipakai sebagai token TOTP biasa.
    r = await client.post("/auth/staff/totp", json={"pre_auth_token": pre, "code": "123456"})
    assert r.status_code == 401

    start = (await client.post("/auth/staff/setup/start", json={"pre_auth_token": pre})).json()
    assert "secret=" in start["otpauth_uri"]
    code = pyotp.TOTP(start["secret"]).now()
    finish = {"pre_auth_token": pre, "code": code, "new_password": temp}
    same = await client.post("/auth/staff/setup/finish", json=finish)
    assert same.status_code == 422  # wajib password baru
    wrong = await client.post(
        "/auth/staff/setup/finish", json=finish | {"code": "000000", "new_password": "x" * 12}
    )
    assert wrong.status_code == 401
    ok = await client.post(
        "/auth/staff/setup/finish", json=finish | {"new_password": "password-baru-rina"}
    )
    assert ok.status_code == 200 and ok.json()["role"] == "pendamping"

    again = await _first_login(client, "rina@example.com", "password-baru-rina")
    assert again["setup_required"] is False  # login berikutnya: password + kode biasa
    r = await client.post("/auth/staff/login", json={"email": "rina@example.com", "password": temp})
    assert r.status_code == 401  # password sementara tidak berlaku lagi


async def test_disable_enable_and_reset_are_audited(client: AsyncClient) -> None:
    h = await _admin(client)
    created = await _create(client, h)
    staff_id = created["account"]["id"]

    r = await client.patch(f"/admin/staff/{staff_id}", json={"status": "disabled"}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "disabled"
    login = {"email": "rina@example.com", "password": created["temp_password"]}
    assert (await client.post("/auth/staff/login", json=login)).status_code == 401
    await client.patch(f"/admin/staff/{staff_id}", json={"status": "active"}, headers=h)

    reset = (await client.post(f"/admin/staff/{staff_id}/reset", headers=h)).json()
    assert reset["temp_password"] != created["temp_password"]
    assert reset["account"]["needs_setup"] is True
    assert (await client.post("/auth/staff/login", json=login)).status_code == 401
    fresh = await _first_login(client, "rina@example.com", reset["temp_password"])
    assert fresh["setup_required"] is True

    async with TestSession() as s:
        rows = (await s.execute(select(AuditLog.action, AuditLog.target_id))).all()
    actions = [a for a, target in rows if target is not None]
    assert actions == ["staff_create", "staff_disable", "staff_enable", "staff_reset"]


async def test_admin_cannot_disable_or_reset_self(client: AsyncClient) -> None:
    h = await _admin(client)
    me = next(a for a in (await client.get("/admin/staff", headers=h)).json())
    r = await client.patch(f"/admin/staff/{me['id']}", json={"status": "disabled"}, headers=h)
    assert r.status_code == 409
    assert (await client.post(f"/admin/staff/{me['id']}/reset", headers=h)).status_code == 409
