"""Seed demo: hanya dengan DEMO_MODE, isinya cukup untuk semua dasbor, reset hanya data demo."""

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app import demo
from app.models import Role, User
from app.settings import settings
from tests.conftest import KROBOKAN, TestSession, account, assent_body

pytestmark = pytest.mark.anyio


async def _login(client: AsyncClient, x: demo.StaffLogin) -> dict[str, str]:
    r = await client.post("/auth/staff/login", json={"email": x.email, "password": x.password})
    code = pyotp.parse_uri(x.otpauth).now()  # type: ignore[attr-defined]
    r = await client.post(
        "/auth/staff/totp", json={"pre_auth_token": r.json()["pre_auth_token"], "code": code}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_demo_code_logs_in_only_demo_accounts(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with TestSession() as s:
        with pytest.raises(RuntimeError):  # belum di-seed: tidak ada akun yang bisa dibuatkan kode
            await demo.current_code(s, Role.pendamping)
    monkeypatch.setattr(settings, "demo_mode", True)
    async with TestSession() as s:
        logins = {x.role: x for x in await demo.seed(s)}
        code, left = await demo.current_code(s, Role.pendamping)
    assert code.isdigit() and len(code) == 6 and 0 < left <= 30
    x = logins[Role.pendamping]
    r = await client.post("/auth/staff/login", json={"email": x.email, "password": x.password})
    r = await client.post(
        "/auth/staff/totp", json={"pre_auth_token": r.json()["pre_auth_token"], "code": code}
    )
    assert r.status_code == 200 and r.json()["role"] == "pendamping"


async def test_seed_requires_demo_mode(db: None) -> None:
    async with TestSession() as s:
        with pytest.raises(RuntimeError):
            await demo.seed(s)


async def test_seed_fills_dashboards_and_reset_keeps_real_data(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await client.post("/consent/assent", json=assent_body(), headers=await account(client, "asli"))
    monkeypatch.setattr(settings, "demo_mode", True)
    async with TestSession() as s:
        logins = {x.role: x for x in await demo.seed(s)}

    queue = (
        await client.get("/cases", headers=await _login(client, logins[Role.pendamping]))
    ).json()
    open_cases = [c["pseudonym"] for c in queue if c["status"] in ("baru", "ditangani")]
    assert sorted(open_cases) == ["Awan Teduh", "Kopi Susu", "Langit Biru", "Mie Ayam", "Pelangi"]
    assert {c["kelurahan"] for c in queue} == {"Krobokan"}

    body = (
        await client.get(
            "/dashboard/aggregate", headers=await _login(client, logins[Role.admin_kota])
        )
    ).json()
    assert body["demo"] is True and body["kpis"] is not None and body["topics"]
    hidden = {k["name"] for k in body["kelurahan"] if k["users"] is None}
    assert hidden == set(demo.HIDDEN)

    async with TestSession() as s:
        await demo.reset(s)
        users = (await s.execute(select(User.pseudonym, User.kelurahan_id))).all()
        staff = (await s.execute(select(func.count()).where(User.role != Role.remaja))).scalar()
    assert users == [("Bintang Senja", KROBOKAN)] and staff == 0  # akun remaja asli tetap ada
