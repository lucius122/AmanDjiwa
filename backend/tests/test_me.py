from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models import (
    Case,
    CaseNote,
    Channel,
    ChannelLink,
    Conversation,
    Emotion,
    EmotionScore,
    Instrument,
    JournalEntry,
    Message,
    RiskAssessment,
    RiskLevel,
    Screening,
    Sender,
    User,
)
from app.services.crypto import encrypt
from tests.conftest import KROBOKAN, TestSession, assent_body, teen_headers

pytestmark = pytest.mark.anyio
TABLES = [
    User,
    Conversation,
    Message,
    EmotionScore,
    RiskAssessment,
    JournalEntry,
    Screening,
    ChannelLink,
    Case,
    CaseNote,
]


async def _fill_everything(sub: str, telegram_id: int) -> None:
    async with TestSession() as s:
        u = (await s.execute(select(User).where(User.auth_id == sub))).scalar_one()
        conv = Conversation(user_id=u.id, channel=Channel.web)
        s.add(conv)
        await s.flush()
        msg = Message(conversation_id=conv.id, sender=Sender.remaja, encrypted_text=encrypt("halo"))
        case = Case(user_id=u.id, kelurahan_id=KROBOKAN, level=RiskLevel.merah)
        s.add_all([msg, case])
        await s.flush()
        s.add_all(
            [
                EmotionScore(message_id=msg.id, scores={"sedih": 0.9}),
                RiskAssessment(user_id=u.id, message_id=msg.id, level=RiskLevel.merah, ter_score=1),
                JournalEntry(
                    user_id=u.id, entry_date=date.today(), emotion=Emotion.sedih, intensity=4
                ),
                Screening(user_id=u.id, instrument=Instrument.phq9),
                ChannelLink(user_id=u.id, telegram_id=telegram_id),
                CaseNote(case_id=case.id, text_enc=encrypt("catatan")),
            ]
        )
        await s.commit()


async def test_delete_me_removes_all_my_data_only(client: AsyncClient) -> None:
    mine, other = teen_headers("hapus-aku"), teen_headers("tetap-ada")
    for i, (sub, h) in enumerate([("hapus-aku", mine), ("tetap-ada", other)]):
        assert (
            await client.post("/consent/assent", json=assent_body(), headers=h)
        ).status_code == 201
        await _fill_everything(sub, telegram_id=1000 + i)

    assert (await client.delete("/me", headers=mine)).status_code == 204
    assert (await client.get("/me", headers=mine)).status_code == 404

    async with TestSession() as s:
        for model in TABLES:  # yang tersisa hanya milik "tetap-ada"
            count = (await s.execute(select(func.count()).select_from(model))).scalar_one()
            assert count == 1, model.__name__
    assert (await client.get("/me", headers=other)).status_code == 200
