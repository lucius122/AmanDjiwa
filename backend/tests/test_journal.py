from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import Case, JournalEntry, RiskAssessment, RiskLevel, User
from app.services.chat import WIB, negative_day_ratio
from tests.conftest import TestSession, account, assent_body, teen_where

pytestmark = pytest.mark.anyio
ADULT = date.today().year - 19


async def _teen(client: AsyncClient, sub: str = "jurnal-1") -> dict[str, str]:
    h = await account(client, sub)
    body = assent_body(birth_year=ADULT)
    assert (await client.post("/consent/assent", json=body, headers=h)).status_code == 201
    return h


async def _save(client: AsyncClient, h: dict[str, str], **body: object) -> dict[str, object]:
    r = await client.post("/journal", json={"emotion": "senang", "intensity": 3, **body}, headers=h)
    assert r.status_code == 200, r.text
    out: dict[str, object] = r.json()
    return out


async def test_one_entry_per_day_second_save_updates(client: AsyncClient) -> None:
    h = await _teen(client)
    await _save(client, h, emotion="cemas", intensity=2)
    out = await _save(client, h, emotion="sedih", intensity=4, note="  capek sama tugas  ")
    assert out["help"] is False
    entries = (await client.get("/journal", headers=h)).json()
    assert len(entries) == 1
    today = datetime.now(WIB).date().isoformat()
    assert entries[0] == {
        "entry_date": today,
        "emotion": "sedih",
        "intensity": 4,
        "note": "capek sama tugas",
    }


async def test_note_encrypted_and_private(client: AsyncClient) -> None:
    mine, other = await _teen(client, "jurnal-a"), await _teen(client, "jurnal-b")
    await _save(client, mine, note="rahasia banget")
    assert (await client.get("/journal", headers=other)).json() == []
    async with TestSession() as s:
        (row,) = (await s.execute(select(JournalEntry))).scalars()
    assert row.note_enc is not None and b"rahasia" not in row.note_enc


async def test_days_window(client: AsyncClient) -> None:
    h = await _teen(client)
    async with TestSession() as s:
        user = (await s.execute(select(User).where(teen_where("jurnal-1")))).scalar_one()
        today = datetime.now(WIB).date()
        for back in (3, 13, 14, 40):
            s.add(
                JournalEntry(
                    user_id=user.id,
                    entry_date=today - timedelta(days=back),
                    emotion="netral",
                    intensity=1,
                )
            )
        await s.commit()
    assert len((await client.get("/journal", headers=h)).json()) == 2  # 3 & 13 hari lalu
    assert len((await client.get("/journal?days=60", headers=h)).json()) == 4
    assert (await client.get("/journal?days=0", headers=h)).status_code == 422


@pytest.mark.parametrize(
    "bad",
    [{"intensity": 0}, {"intensity": 6}, {"emotion": "galau"}, {"note": "x" * 1001}],
)
async def test_invalid_input(client: AsyncClient, bad: dict[str, object]) -> None:
    h = await _teen(client)
    body = {"emotion": "senang", "intensity": 3} | bad
    assert (await client.post("/journal", json=body, headers=h)).status_code == 422


async def test_pending_guardian_cannot_journal(client: AsyncClient) -> None:
    h = await account(client, "minor")
    await client.post("/consent/assent", json=assent_body(), headers=h)  # 16 th → menunggu wali
    body = {"emotion": "senang", "intensity": 3}
    assert (await client.post("/journal", json=body, headers=h)).status_code == 403


async def test_crisis_note_opens_help_and_flags_case_without_note_text(client: AsyncClient) -> None:
    h = await _teen(client)
    out = await _save(client, h, emotion="sedih", intensity=5, note="rasanya pengen mati aja")
    assert out["help"] is True
    async with TestSession() as s:
        (case,) = (await s.execute(select(Case))).scalars()
        (a,) = (await s.execute(select(RiskAssessment))).scalars()
    assert case.level == RiskLevel.merah
    assert a.case_id == case.id and a.message_id is None  # tidak ada teks yang bisa dibaca staf
    assert a.triggers[0] == "jurnal"


async def test_journal_feeds_14_day_trajectory(client: AsyncClient) -> None:
    h = await _teen(client)
    await _save(client, h, emotion="sedih", intensity=4)
    async with TestSession() as s:
        user = (await s.execute(select(User).where(teen_where("jurnal-1")))).scalar_one()
        assert await negative_day_ratio(s, user) == 1.0
