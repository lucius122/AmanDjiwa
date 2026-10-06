import logging
from datetime import date
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

import app.pipeline as pipeline
from app.models import Case, CaseStatus, Message, RiskAssessment, RiskLevel, Screening
from tests.conftest import KROBOKAN, TestSession, assent_body, teen_headers

pytestmark = pytest.mark.anyio
ADULT = date.today().year - 19  # langsung aktif, tanpa izin wali


async def _teen(client: AsyncClient, sub: str = "teen-chat", **override: object) -> dict[str, str]:
    h = teen_headers(sub)
    body = assent_body(birth_year=ADULT, **override)
    assert (await client.post("/consent/assent", json=body, headers=h)).status_code == 201
    return h


async def _say(client: AsyncClient, h: dict[str, str], text: str) -> dict[str, Any]:
    r = await client.post("/chat/message", json={"text": text}, headers=h)
    assert r.status_code == 200, r.text
    body: dict[str, Any] = r.json()
    return body


async def _act(
    client: AsyncClient, h: dict[str, str], type_: str, value: int | None = None
) -> dict[str, Any]:
    r = await client.post("/chat/action", json={"type": type_, "value": value}, headers=h)
    assert r.status_code == 200, r.text
    body: dict[str, Any] = r.json()
    return body


async def _cases() -> list[Case]:
    async with TestSession() as s:
        return list((await s.execute(select(Case))).scalars())


async def test_pending_guardian_cannot_chat(client: AsyncClient) -> None:
    h = teen_headers("minor")
    await client.post("/consent/assent", json=assent_body(), headers=h)  # 16 th → pending
    assert (await client.post("/chat/message", json={"text": "halo"}, headers=h)).status_code == 403
    assert (await client.get("/chat/history", headers=h)).status_code == 403


async def test_history_is_encrypted_and_in_order(client: AsyncClient) -> None:
    h = await _teen(client)
    turn = await _say(client, h, "lagi capek nih")
    assert turn["messages"][0]["text"].startswith("Kedengarannya berat ya")
    history = (await client.get("/chat/history", headers=h)).json()["messages"]
    assert [m["sender"] for m in history] == ["bot", "remaja", "bot"]  # sapaan, aku, balasan
    assert history[0]["text"] == "Hai! Aku Djiwa. Gimana harimu hari ini?"
    async with TestSession() as s:
        raw = [m.encrypted_text for m in (await s.execute(select(Message))).scalars()]
    assert raw and all(b"capek" not in blob for blob in raw)
    assert await _cases() == []  # hijau tidak membuat kasus


async def test_crisis_creates_red_case_linked_to_trigger(client: AsyncClient) -> None:
    h = await _teen(client)
    turn = await _say(client, h, "aku pengen mati aja")
    assert turn["messages"][-1]["kind"] == "crisis_card"
    assert turn["card"]["title"] == "Kamu nggak harus hadapi ini sendirian"
    assert turn["hotlines"] and turn["offer_connect"]
    (case,) = await _cases()
    assert (case.level, case.status, case.kelurahan_id) == (
        RiskLevel.merah,
        CaseStatus.baru,
        KROBOKAN,
    )
    async with TestSession() as s:
        linked = (
            (await s.execute(select(RiskAssessment).where(RiskAssessment.case_id == case.id)))
            .scalars()
            .all()
        )
    assert len(linked) == 1 and linked[0].message_id is not None
    kinds = [m["kind"] for m in (await client.get("/chat/history", headers=h)).json()["messages"]]
    assert kinds[-1] == "crisis_card"


async def test_case_escalates_and_reopens(client: AsyncClient) -> None:
    h = await _teen(client)
    await _say(client, h, "aku cemas banget, takut, panik terus")  # kuning (emosi kuat)
    first = await _cases()
    assert len(first) == 1 and first[0].level == RiskLevel.kuning
    async with TestSession() as s:
        case = await s.get(Case, first[0].id)
        assert case is not None
        case.status = CaseStatus.ditangani
        await s.commit()
    await _say(client, h, "udah gak kuat lagi, pengen bundir")
    (case_after,) = await _cases()  # tetap satu kasus terbuka
    assert (case_after.level, case_after.status) == (RiskLevel.merah, CaseStatus.baru)


async def test_screening_low_result(client: AsyncClient) -> None:
    h = await _teen(client)
    turn = await _say(client, h, "Cek perasaanku dong (skrining)")
    q = turn["screening"]
    assert turn["messages"][0]["text"].startswith("Boleh. Ada 4 pertanyaan")
    assert (q["n"], q["total"], q["instrument"], q["item"]) == (1, 4, "phq9", 2)
    assert (
        q["text"]
        == "Dalam 2 minggu terakhir, seberapa sering kamu merasa sedih, murung, atau putus asa?"
    )
    for _ in range(3):
        turn = await _act(client, h, "answer", 0)
    turn = await _act(client, h, "skip")
    assert turn["screening"] is None
    assert turn["messages"][0]["text"].endswith("Ini bukan diagnosis, cuma gambaran awal.")
    assert "cukup oke" in turn["messages"][0]["text"]
    history = [m["text"] for m in (await client.get("/chat/history", headers=h)).json()["messages"]]
    assert "Tidak pernah" in history and "Lewati" in history
    async with TestSession() as s:
        rows = {x.instrument: x for x in (await s.execute(select(Screening))).scalars()}
    assert rows["phq9"].answers == {"2": 0, "1": 0} and rows["phq9"].total is None
    assert await _cases() == []


async def test_positive_screen_followup_and_item9_is_crisis(client: AsyncClient) -> None:
    h = await _teen(client)
    await _say(client, h, "cek perasaan")
    for value in (2, 2, 0, 0):  # PHQ-2 = 4 → positif; GAD-2 = 0
        turn = await _act(client, h, "answer", value)
    assert turn["followup_offer"] and turn["screening"] is None
    turn = await _act(client, h, "continue")
    assert (turn["screening"]["total"], turn["screening"]["item"]) == (7, 3)  # item 3–9 PHQ-9
    for _ in range(6):
        turn = await _act(client, h, "answer", 1)
    assert turn["screening"]["item"] == 9
    turn = await _act(client, h, "answer", 1)  # pikiran lebih baik mati: "beberapa hari"
    assert turn["card"] is not None and turn["screening"] is None
    (case,) = await _cases()
    assert case.level == RiskLevel.merah
    async with TestSession() as s:
        a = (
            await s.execute(select(RiskAssessment).where(RiskAssessment.case_id == case.id))
        ).scalar_one()
        phq = (
            await s.execute(select(Screening).where(Screening.instrument == "phq9"))
        ).scalar_one()
    assert a.triggers == ["phq9_item9"]
    assert phq.total == 2 + 2 + 6 * 1 + 1


async def test_crisis_message_during_screening_stops_screening(client: AsyncClient) -> None:
    h = await _teen(client)
    await _say(client, h, "cek perasaan")
    turn = await _say(client, h, "sebenernya aku pengen ngilang aja selamanya")
    assert turn["card"] is not None and turn["screening"] is None
    r = await client.post("/chat/action", json={"type": "answer", "value": 1}, headers=h)
    assert r.status_code == 409


async def test_text_during_screening_keeps_question_card(client: AsyncClient) -> None:
    h = await _teen(client)
    await _say(client, h, "cek perasaan")
    turn = await _say(client, h, "bentar ya")
    assert turn["screening"]["n"] == 1
    turn = await _act(client, h, "stop")
    assert (
        turn["messages"][0]["text"] == "Oke, kita ngobrol biasa aja ya."
        and turn["screening"] is None
    )


async def test_connect_to_pendamping_once(client: AsyncClient) -> None:
    h = await _teen(client)
    turn = await _act(client, h, "connect")
    assert turn["connected"] and "kakak pendamping di Krobokan" in turn["messages"][0]["text"]
    assert (await _act(client, h, "connect"))["messages"] == []  # tidak dobel
    (case,) = await _cases()
    assert case.level == RiskLevel.oranye
    assert (await client.get("/chat/history", headers=h)).json()["connected"]


async def test_breathing_intent_opens_sheet(client: AsyncClient) -> None:
    h = await _teen(client)
    turn = await _say(client, h, "mau latihan napas")
    assert turn["client_action"] == "open_napas"


async def test_rate_limit(client: AsyncClient) -> None:
    h = await _teen(client)
    for _ in range(20):
        await _say(client, h, "halo")
    r = await client.post("/chat/message", json={"text": "halo"}, headers=h)
    assert r.status_code == 429 and "Pelan-pelan" in r.json()["detail"]


async def test_pipeline_failure_still_answers_with_hotlines(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = await _teen(client)

    def boom(_: str) -> None:
        raise RuntimeError("rusak")

    monkeypatch.setattr(pipeline, "normalize", boom)
    turn = await _say(client, h, "halo")
    assert turn["hotlines"] and turn["offer_connect"] and turn["messages"]


async def test_chat_logs_contain_no_message_text(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    h = await _teen(client, pseudonym="Rahasia Banget")
    await _say(client, h, "aku pengen mati aja, nomorku 081234567890")
    for secret in ("pengen mati", "081234567890", "Rahasia Banget"):
        assert secret not in caplog.text
