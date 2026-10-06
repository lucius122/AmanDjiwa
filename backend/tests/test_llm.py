"""LLM hanya untuk level hijau (§6.3–6.4), dipseudonimisasi, selalu bisa mundur ke bank respons."""

from datetime import date
from typing import Any

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import Case, CaseStatus, RiskLevel, User
from app.pipeline import llm
from tests.conftest import KROBOKAN, TestSession, assent_body, teen_headers

pytestmark = pytest.mark.anyio
ADULT = date.today().year - 19


class FakeLLM:
    def __init__(
        self, reply: str = "Wah, seru juga ya. Terus gimana rasanya?", finish: str = "stop"
    ) -> None:
        self.calls: list[list[dict[str, str]]] = []
        self.reply, self.finish = reply, finish

    async def __call__(self, messages: list[dict[str, str]]) -> tuple[str, str]:
        self.calls.append(messages)
        return self.reply, self.finish


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeLLM:
    f = FakeLLM()
    monkeypatch.setattr(llm.settings, "nvidia_api_key", "uji")
    monkeypatch.setattr(llm, "_complete", f)
    return f


async def _teen(client: AsyncClient, nick: str = "Bintang Senja") -> dict[str, str]:
    h = teen_headers("llm-1")
    body = assent_body(birth_year=ADULT, pseudonym=nick)
    assert (await client.post("/consent/assent", json=body, headers=h)).status_code == 201
    return h


async def _say(client: AsyncClient, h: dict[str, str], text: str) -> dict[str, Any]:
    r = await client.post("/chat/message", json={"text": text}, headers=h)
    assert r.status_code == 200, r.text
    out: dict[str, Any] = r.json()
    return out


def test_messages_are_pseudonymized() -> None:
    history = [("user", "aku Bintang Senja, wa 081234567890"), ("assistant", "Halo Bintang Senja!")]
    msgs = llm.build_messages(history, "emailku budi@mail.com", nickname="Bintang Senja")
    assert msgs[0]["role"] == "system"
    sent = " ".join(m["content"] for m in msgs[1:])
    for secret in ("081234567890", "budi@mail.com", "Bintang Senja"):
        assert secret not in sent
    assert "[NOMOR]" in sent and "[EMAIL]" in sent


@pytest.mark.parametrize(
    "reply",
    [
        "Coba minum 5 mg melatonin ya",
        "Aku manusia kok, tenang",
        "Kayaknya kamu mengalami depresi",
        "",
    ],
)
def test_guard_rejects_forbidden_replies(reply: str) -> None:
    assert not llm.acceptable(reply)


async def test_green_message_uses_llm_with_history(client: AsyncClient, fake: FakeLLM) -> None:
    h = await _teen(client)
    await _say(client, h, "halo")
    turn = await _say(client, h, "lagi gabut abis ulangan")
    assert turn["messages"][0]["text"] == fake.reply
    last_call = fake.calls[-1]
    assert last_call[-1] == {"role": "user", "content": "lagi gabut abis ulangan"}
    assert {"role": "user", "content": "halo"} in last_call  # konteks giliran sebelumnya ikut


@pytest.mark.parametrize("text", ["aku pengen mati aja", "aku cemas banget, takut, panik terus"])
async def test_non_green_never_calls_llm(client: AsyncClient, fake: FakeLLM, text: str) -> None:
    h = await _teen(client)
    turn = await _say(client, h, text)
    assert fake.calls == []
    assert turn["messages"][0]["text"] != fake.reply


async def test_intents_still_win_over_llm(client: AsyncClient, fake: FakeLLM) -> None:
    h = await _teen(client)
    assert (await _say(client, h, "cek perasaan"))["screening"] is not None
    assert (await _say(client, h, "mau latihan napas"))["client_action"] == "open_napas"
    assert fake.calls == []


@pytest.mark.parametrize(
    "reply,finish", [("Coba minum 5 mg melatonin", "stop"), ("Kalimat yang terpotong", "length")]
)
async def test_rejected_reply_falls_back_to_bank(
    client: AsyncClient, fake: FakeLLM, reply: str, finish: str
) -> None:
    fake.reply, fake.finish = reply, finish
    h = await _teen(client)
    turn = await _say(client, h, "lagi capek nih")
    assert turn["messages"][0]["text"].startswith("Kedengarannya berat ya")


async def test_llm_error_falls_back_to_bank(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken(_: list[dict[str, str]]) -> tuple[str, str]:
        raise httpx.ReadTimeout("lambat")

    monkeypatch.setattr(llm.settings, "nvidia_api_key", "uji")
    monkeypatch.setattr(llm, "_complete", broken)
    h = await _teen(client)
    assert (await _say(client, h, "lagi capek nih"))["messages"][0]["text"].startswith(
        "Kedengarannya"
    )


async def test_open_high_risk_case_keeps_bank_only(client: AsyncClient, fake: FakeLLM) -> None:
    h = await _teen(client)
    async with TestSession() as s:
        user = (await s.execute(select(User).where(User.auth_id == "llm-1"))).scalar_one()
        s.add(
            Case(
                user_id=user.id,
                kelurahan_id=KROBOKAN,
                level=RiskLevel.oranye,
                status=CaseStatus.ditangani,
            )
        )
        await s.commit()
    await _say(client, h, "lagi gabut")
    assert fake.calls == []


async def test_no_key_means_no_llm(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    f = FakeLLM()
    monkeypatch.setattr(llm, "_complete", f)  # key kosong dari conftest
    h = await _teen(client)
    await _say(client, h, "lagi gabut")
    assert f.calls == []
