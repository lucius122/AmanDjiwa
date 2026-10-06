import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.api import consent as consent_api
from app.models import GuardianConsent
from tests.conftest import TestSession, account, assent_body

pytestmark = pytest.mark.anyio
YEAR = date.today().year
PARENT = "ortu@example.com"


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    sent: list[tuple[str, str]] = []

    async def fake_send(to: str, link: str, days: int) -> None:
        sent.append((to, link))

    monkeypatch.setattr(consent_api, "send_guardian_request", fake_send)
    return sent


async def _register(client: AsyncClient, **override: object) -> dict[str, str]:
    h = await account(client)
    r = await client.post("/consent/assent", json=assent_body(**override), headers=h)
    assert r.status_code == 201, r.text
    return h


async def _guardian_token(
    client: AsyncClient, h: dict[str, str], outbox: list[tuple[str, str]]
) -> str:
    assert (
        await client.post("/consent/guardian", json={"email": PARENT}, headers=h)
    ).status_code == 202
    to, link = outbox[-1]
    assert to == PARENT and "/persetujuan-wali/" in link
    return link.rsplit("/", 1)[1]


@pytest.mark.parametrize(
    ("age", "status"),
    [(16, "pending_guardian"), (18, "pending_guardian"), (19, "active")],  # 18: bisa jadi masih 17
)
async def test_assent_sets_guardian_requirement(client: AsyncClient, age: int, status: str) -> None:
    r = await client.post(
        "/consent/assent", json=assent_body(birth_year=YEAR - age), headers=await account(client)
    )
    assert r.status_code == 201
    assert r.json()["status"] == status
    assert r.json()["kelurahan_name"] == "Krobokan"


@pytest.mark.parametrize(
    "override",
    [
        {"pseudonym": "budi@gmail.com"},
        {"pseudonym": "08123456789"},
        {"pseudonym": "   "},
        {"birth_year": YEAR - 12},
        {"birth_year": YEAR - 20},
        {"agree": False},
        {"avatar": 8},
        {"kelurahan_id": 999},
    ],
)
async def test_assent_rejects_invalid_input(client: AsyncClient, override: dict[str, Any]) -> None:
    r = await client.post(
        "/consent/assent", json=assent_body(**override), headers=await account(client)
    )
    assert r.status_code == 422


async def test_assent_twice_conflicts(client: AsyncClient) -> None:
    h = await _register(client)
    assert (await client.post("/consent/assent", json=assent_body(), headers=h)).status_code == 409


async def test_guardian_approve_then_revoke(
    client: AsyncClient, outbox: list[tuple[str, str]]
) -> None:
    h = await _register(client)
    url = f"/consent/guardian/{await _guardian_token(client, h, outbox)}"

    assert (await client.post(url, json={"decision": "approve"})).status_code == 422  # tanpa nama
    r = await client.post(
        url, json={"decision": "approve", "guardian_name": "Siti Aminah", "relation": "orang_tua"}
    )
    assert r.json() == {"status": "approved"}
    assert (await client.get("/me", headers=h)).json()["status"] == "active"
    assert (await client.post(url, json={"decision": "decline"})).status_code == 409  # sekali pakai

    async with TestSession() as s:
        row = (await s.execute(select(GuardianConsent))).scalar_one()
        assert PARENT.encode() not in row.email_enc
        assert row.guardian_name_enc is not None and b"Siti" not in row.guardian_name_enc

    assert (await client.post(url, json={"decision": "revoke"})).json() == {"status": "revoked"}
    assert (await client.get("/me", headers=h)).json()["status"] == "pending_guardian"


async def test_expired_guardian_link(client: AsyncClient, outbox: list[tuple[str, str]]) -> None:
    h = await _register(client)
    token = await _guardian_token(client, h, outbox)
    async with TestSession() as s:
        await s.execute(
            update(GuardianConsent).values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        await s.commit()
    r = await client.post(f"/consent/guardian/{token}", json={"decision": "decline"})
    assert r.status_code == 410


async def test_guardian_resend_has_cooldown(
    client: AsyncClient, outbox: list[tuple[str, str]]
) -> None:
    h = await _register(client)
    await _guardian_token(client, h, outbox)
    r = await client.post("/consent/guardian", json={"email": PARENT}, headers=h)
    assert r.status_code == 429


async def test_adult_does_not_need_guardian(
    client: AsyncClient, outbox: list[tuple[str, str]]
) -> None:
    h = await _register(client, birth_year=YEAR - 19)
    r = await client.post("/consent/guardian", json={"email": PARENT}, headers=h)
    assert r.status_code == 409
    assert outbox == []


async def test_logs_contain_no_token_or_email(
    client: AsyncClient, outbox: list[tuple[str, str]], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    h = await _register(client)
    token = await _guardian_token(client, h, outbox)
    await client.post(f"/consent/guardian/{token}", json={"decision": "decline"})

    assert "POST /consent/guardian/{token} 200" in caplog.text  # pola route, bukan path asli
    assert token not in caplog.text
    assert PARENT not in caplog.text
    assert "Bintang Senja" not in caplog.text


async def test_guardian_link_status_for_parent_page(
    client: AsyncClient, outbox: list[tuple[str, str]]
) -> None:
    h = await _register(client)
    token = await _guardian_token(client, h, outbox)
    url = f"/consent/guardian/{token}"
    assert (await client.get(url)).json() == {"status": "pending"}
    body = {"decision": "approve", "guardian_name": "Siti", "relation": "wali"}
    await client.post(url, json=body)
    assert (await client.get(url)).json() == {"status": "approved"}
    assert (await client.get("/consent/guardian/tidak-ada")).status_code == 404


async def test_expired_link_status(client: AsyncClient, outbox: list[tuple[str, str]]) -> None:
    h = await _register(client)
    token = await _guardian_token(client, h, outbox)
    async with TestSession() as s:
        await s.execute(
            update(GuardianConsent).values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        await s.commit()
    assert (await client.get(f"/consent/guardian/{token}")).json() == {"status": "expired"}


async def test_public_hotlines_come_from_yaml(client: AsyncClient) -> None:
    hotlines = (await client.get("/hotlines")).json()
    assert [h["id"] for h in hotlines] == ["darurat", "kesehatan_jiwa"]
    assert all(h["number"] == "TODO_VERIFY" for h in hotlines)  # belum diverifikasi (§6.6)
