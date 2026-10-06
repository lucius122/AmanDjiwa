"""Login remaja email+password di DB sendiri: privasi email, batas salah password, reset."""

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select

from app.api import teen_auth
from app.models import User, UserStatus
from app.services.auth import MAX_FAILED_LOGINS
from app.services.crypto import decrypt
from tests.conftest import TEEN_PASSWORD, TestSession, account, assent_body, bearer, teen_where

pytestmark = pytest.mark.anyio
EMAIL = "Rani.Uji@Example.com"


async def _register(client: AsyncClient, email: str = EMAIL) -> dict[str, str]:
    r = await client.post("/auth/teen/register", json={"email": email, "password": TEEN_PASSWORD})
    assert r.status_code == 201, r.text
    return bearer(r.json()["access_token"])


async def _login(client: AsyncClient, password: str, email: str = EMAIL) -> Response:
    return await client.post("/auth/teen/login", json={"email": email, "password": password})


async def test_register_then_profile_then_chat(client: AsyncClient) -> None:
    h = await _register(client)
    assert (await client.get("/me", headers=h)).status_code == 404  # lanjut ke langkah profil
    assert (await client.get("/chat/history", headers=h)).status_code == 403
    assert (
        await client.post("/consent/assent", json=assent_body(birth_year=2007), headers=h)
    ).status_code == 201
    assert (await client.get("/me", headers=h)).json()["status"] == "active"
    assert (await client.get("/chat/history", headers=h)).status_code == 200


async def test_email_is_never_stored_in_plain_text(client: AsyncClient) -> None:
    await _register(client)
    async with TestSession() as s:
        (user,) = (await s.execute(select(User))).scalars().all()
    assert user.email is None and user.status == UserStatus.onboarding
    assert user.email_hash and "rani" not in user.email_hash
    assert user.email_enc and b"rani" not in user.email_enc.lower()
    assert decrypt(user.email_enc) == EMAIL.lower()


async def test_duplicate_email_case_insensitive(client: AsyncClient) -> None:
    await _register(client)
    r = await client.post(
        "/auth/teen/register", json={"email": EMAIL.upper(), "password": TEEN_PASSWORD}
    )
    assert r.status_code == 409


async def test_wrong_password_looks_like_unknown_email_and_locks(client: AsyncClient) -> None:
    await _register(client)
    unknown = await _login(client, TEEN_PASSWORD, email="tidak-ada@example.com")
    wrong = await _login(client, "password-salah")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()
    for _ in range(MAX_FAILED_LOGINS - 1):
        await _login(client, "password-salah")
    assert (await _login(client, TEEN_PASSWORD)).status_code == 429  # dikunci 15 menit


async def test_teen_token_cannot_be_used_as_staff_and_vice_versa(client: AsyncClient) -> None:
    h = await account(client)
    assert (await client.get("/auth/staff/me", headers=h)).status_code == 401
    assert (await client.get("/cases", headers=h)).status_code == 401


async def test_forgot_and_reset_password(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[tuple[str, str]] = []

    async def fake_send(to: str, subject: str, body: str) -> None:
        sent.append((to, body))

    monkeypatch.setattr(teen_auth, "send_plain", fake_send)
    await _register(client)
    unknown = await client.post("/auth/teen/forgot", json={"email": "tidak-ada@example.com"})
    assert unknown.status_code == 202 and sent == []  # tidak membocorkan siapa yang terdaftar
    assert (await client.post("/auth/teen/forgot", json={"email": EMAIL})).status_code == 202
    to, body = sent[0]
    assert to == EMAIL.lower() and "/reset-password/" in body
    token = body.split("/reset-password/")[1].split()[0]

    r = await client.post(
        "/auth/teen/reset", json={"token": token, "password": "password-baru-123"}
    )
    assert r.status_code == 200 and r.json()["access_token"]
    assert (await _login(client, TEEN_PASSWORD)).status_code == 401
    assert (await _login(client, "password-baru-123")).status_code == 200
    again = await client.post("/auth/teen/reset", json={"token": token, "password": "lagi-12345"})
    assert again.status_code == 410  # sekali pakai


async def test_deleted_account_cannot_log_in(client: AsyncClient) -> None:
    h = await account(client, "pergi")
    assert (await client.delete("/me", headers=h)).status_code == 204
    async with TestSession() as s:
        assert (await s.execute(select(User).where(teen_where("pergi")))).first() is None
    r = await client.post(
        "/auth/teen/login", json={"email": "pergi@example.com", "password": TEEN_PASSWORD}
    )
    assert r.status_code == 401
