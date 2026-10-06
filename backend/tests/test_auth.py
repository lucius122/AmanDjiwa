import os

import jwt
import pyotp
import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select

from app.models import AuditLog, Role
from app.services.auth import MAX_FAILED_LOGINS
from tests.conftest import (
    KROBOKAN,
    STAFF_EMAIL,
    STAFF_PASSWORD,
    TestSession,
    bearer,
    make_staff,
    staff_login,
    teen_headers,
)

pytestmark = pytest.mark.anyio


async def _login(
    client: AsyncClient, email: str = STAFF_EMAIL, password: str = STAFF_PASSWORD
) -> Response:
    return await client.post("/auth/staff/login", json={"email": email, "password": password})


async def test_login_then_totp_issues_scoped_token(client: AsyncClient) -> None:
    secret = await make_staff(Role.pendamping, KROBOKAN)
    body = await staff_login(client, secret)

    claims = jwt.decode(body["access_token"], os.environ["JWT_SECRET"], algorithms=["HS256"])
    assert (claims["typ"], claims["role"], claims["kelurahan_id"]) == ("access", "pendamping", 10)
    assert body["kelurahan_name"] == "Krobokan"
    me = await client.get("/auth/staff/me", headers=bearer(body["access_token"]))
    assert me.json()["display_name"] == "Kak Dimas P."
    async with TestSession() as s:
        assert (await s.execute(select(AuditLog.action))).scalars().all() == ["staff_login"]


async def test_unknown_email_and_wrong_password_look_identical(client: AsyncClient) -> None:
    await make_staff(Role.konselor)
    unknown = await _login(client, email="tidak.ada@example.com")
    wrong = await _login(client, password="salah-salah-salah")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


async def test_account_locks_after_repeated_failures(client: AsyncClient) -> None:
    await make_staff(Role.konselor)
    for _ in range(MAX_FAILED_LOGINS):
        assert (await _login(client, password="salah")).status_code == 401
    assert (await _login(client)).status_code == 429  # password benar pun ditolak saat terkunci


async def test_totp_code_cannot_be_replayed(client: AsyncClient) -> None:
    secret = await make_staff(Role.konselor)
    code = pyotp.TOTP(secret).now()
    for expected in (200, 401):
        pre = (await _login(client)).json()["pre_auth_token"]
        r = await client.post("/auth/staff/totp", json={"pre_auth_token": pre, "code": code})
        assert r.status_code == expected


async def test_pre_totp_token_is_not_an_access_token(client: AsyncClient) -> None:
    await make_staff(Role.konselor)
    pre = (await _login(client)).json()["pre_auth_token"]
    assert (await client.get("/auth/staff/me", headers=bearer(pre))).status_code == 401


async def test_teen_and_staff_tokens_do_not_cross(client: AsyncClient) -> None:
    secret = await make_staff(Role.pendamping, KROBOKAN)
    staff = (await staff_login(client, secret))["access_token"]
    assert (await client.get("/me", headers=bearer(staff))).status_code == 401
    assert (await client.get("/auth/staff/me", headers=teen_headers())).status_code == 401
