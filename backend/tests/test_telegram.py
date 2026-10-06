import re
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy import select

from app.bot import logic
from app.models import Case, ChannelLink, RiskLevel
from app.pipeline import NO_MODELS
from app.services import auth as auth_mod
from tests.conftest import KROBOKAN, TestSession, assent_body, teen_headers

pytestmark = pytest.mark.anyio
TG_ID = 777001


async def _linked_teen(client: AsyncClient, r: Redis) -> str:
    h = teen_headers("tg-teen")
    body = assent_body(birth_year=date.today().year - 19, pseudonym="Ombak Tenang")
    assert (await client.post("/consent/assent", json=body, headers=h)).status_code == 201
    link = (await client.post("/telegram/link-token", headers=h)).json()
    async with TestSession() as s:
        outs = await logic.on_start(r, s, TG_ID, link["code"])
    assert outs[0].text.startswith("Akunmu sudah tersambung, Ombak Tenang.")
    return str(link["code"])


async def test_link_code_is_one_time_and_expires(client: AsyncClient, redis_client: Redis) -> None:
    h = teen_headers("tg-teen")
    body = assent_body(birth_year=date.today().year - 19)
    await client.post("/consent/assent", json=body, headers=h)
    link = (await client.post("/telegram/link-token", headers=h)).json()
    assert re.fullmatch(r"DJW-[A-Z2-9]{6}", link["code"])
    assert link["bot_username"] == "AmanDjiwa_bot"
    assert link["deep_link"] == f"https://t.me/AmanDjiwa_bot?start={link['code']}"
    assert 0 < await redis_client.ttl(f"tg:link:{link['code']}") <= 15 * 60
    async with TestSession() as s:
        assert "tersambung" in (await logic.on_start(redis_client, s, TG_ID, link["code"]))[0].text
        again = await logic.on_start(redis_client, s, 999, link["code"])
    assert again[0].text == logic.TG["link_invalid"]
    async with TestSession() as s:
        assert (await s.execute(select(ChannelLink.telegram_id))).scalars().all() == [TG_ID]


async def test_pending_teen_cannot_get_link_code(client: AsyncClient) -> None:
    h = teen_headers("minor")
    await client.post("/consent/assent", json=assent_body(), headers=h)
    assert (await client.post("/telegram/link-token", headers=h)).status_code == 403


async def test_start_code_guessing_is_rate_limited(db: None, redis_client: Redis) -> None:
    async with TestSession() as s:
        for _ in range(5):
            assert (await logic.on_start(redis_client, s, 5, "DJW-AAAAAA"))[0].text == logic.TG[
                "link_invalid"
            ]
        assert (await logic.on_start(redis_client, s, 5, "DJW-AAAAAA"))[0].text == logic.TG[
            "rate_limited"
        ]


async def test_linked_crisis_shows_card_hotlines_and_connect(
    client: AsyncClient, redis_client: Redis
) -> None:
    await _linked_teen(client, redis_client)
    async with TestSession() as s:
        outs = await logic.on_text(redis_client, s, TG_ID, "aku pengen mati aja", NO_MODELS)
    card = next(o for o in outs if o.text.startswith("Kamu nggak harus hadapi ini sendirian"))
    assert "TODO_VERIFY" not in card.text and logic.TG["hotline_unverified"] in card.text
    assert card.buttons == [[("Hubungkan aku ke pendamping", "connect")]]
    async with TestSession() as s:
        (case,) = (await s.execute(select(Case))).scalars()
    assert case.level == RiskLevel.merah


async def test_unlinked_crisis_still_gets_hotlines_without_case(
    db: None, redis_client: Redis
) -> None:
    async with TestSession() as s:
        outs = await logic.on_text(redis_client, s, 123, "pengen bundir", NO_MODELS)
        assert "TODO_VERIFY" not in outs[0].text and outs[0].buttons == []
        assert logic.TG["hotline_unverified"] in outs[0].text
        assert outs[-1].text == logic.TG["not_linked"]
        assert (await s.execute(select(Case))).scalars().all() == []
        normal = await logic.on_text(redis_client, s, 123, "halo", NO_MODELS)
    assert [o.text for o in normal] == [logic.TG["not_linked"]]


async def test_screening_over_telegram_buttons(client: AsyncClient, redis_client: Redis) -> None:
    await _linked_teen(client, redis_client)
    async with TestSession() as s:
        outs = await logic.on_text(redis_client, s, TG_ID, "cek perasaan", NO_MODELS)
    question = outs[-1]
    assert question.text.startswith("Pertanyaan 1 dari 4\nDalam 2 minggu terakhir")
    assert question.buttons[0] == [("Tidak pernah", "ans:0")]
    assert question.buttons[-1] == [("Lewati dulu", "skip"), ("Berhenti", "stop")]
    async with TestSession() as s:
        nxt = await logic.on_callback(redis_client, s, TG_ID, "ans:1", NO_MODELS)
        assert nxt[-1].text.startswith("Pertanyaan 2 dari 4")
        assert (
            await logic.on_callback(redis_client, s, TG_ID, "ans:99", NO_MODELS) == []
        )  # di luar 0–3
        assert await logic.on_callback(redis_client, s, TG_ID, "bogus", NO_MODELS) == []


async def test_webhook_requires_secret(client: AsyncClient) -> None:
    assert (await client.post("/telegram/webhook", json={})).status_code == 403
    r = await client.post(
        "/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "salah"}
    )
    assert r.status_code == 403


def test_supabase_jwks_es256_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    """Project Supabase baru menandatangani token dengan kunci asimetris (JWKS)."""
    key = ec.generate_private_key(ec.SECP256R1())
    url = "https://contoh.supabase.co"
    now = datetime.now(UTC)
    claims = {"sub": "abc", "aud": "authenticated", "iss": f"{url}/auth/v1",
              "exp": now + timedelta(minutes=5)}  # fmt: skip
    token = jwt.encode(claims, key, algorithm="ES256", headers={"kid": "k1"})

    class FakeJwks:
        def get_signing_key_from_jwt(self, _: str) -> SimpleNamespace:
            return SimpleNamespace(key=key.public_key())

    # Secret tetap terisi (mis. salah isi Key ID): token ES256 tetap harus lewat JWKS.
    monkeypatch.setattr(
        auth_mod.settings, "supabase_jwt_secret", "a3c1e2f0-0000-4000-8000-000000000000"
    )
    monkeypatch.setattr(auth_mod.settings, "supabase_url", url)
    monkeypatch.setattr(auth_mod, "_jwks", FakeJwks())
    assert auth_mod.read_supabase_sub(token) == "abc"
    anon = jwt.encode(claims | {"is_anonymous": True}, key, algorithm="ES256")
    with pytest.raises(jwt.InvalidTokenError):
        auth_mod.read_supabase_sub(anon)
    wrong_issuer = jwt.encode(claims | {"iss": "https://lain.supabase.co/auth/v1"}, key, "ES256")
    with pytest.raises(jwt.InvalidTokenError):
        auth_mod.read_supabase_sub(wrong_issuer)


async def test_pendamping_greeting_also_goes_to_telegram(
    client: AsyncClient, redis_client: Redis, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api import cases as cases_api
    from app.models import Role
    from tests.conftest import bearer, make_staff, staff_login

    await _linked_teen(client, redis_client)
    async with TestSession() as s:
        await logic.on_text(redis_client, s, TG_ID, "aku pengen mati aja", NO_MODELS)
    sent: list[tuple[int, str]] = []

    async def fake_send(tg_id: int, text: str) -> bool:
        sent.append((tg_id, text))
        return False  # gagal kirim pun tidak boleh menggagalkan aksi pendamping

    monkeypatch.setattr(cases_api, "send_text", fake_send)
    secret = await make_staff(Role.pendamping, KROBOKAN)
    h = bearer((await staff_login(client, secret))["access_token"])
    (row,) = (await client.get("/cases", headers=h)).json()
    r = await client.patch(f"/cases/{row['id']}", json={"action": "contacted"}, headers=h)
    assert r.status_code == 200
    assert sent and sent[0][0] == TG_ID
    assert sent[0][1].startswith("Kak Dimas P. · pendamping\nHai Ombak Tenang, aku Kak Dimas P.")
