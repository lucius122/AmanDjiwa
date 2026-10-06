"""Chat web remaja (CLAUDE.md §9): POST /chat/message, POST /chat/action, GET /chat/history."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import active_teen
from app.db import get_session
from app.dialog import (
    Action,
    ChatTurn,
    Dialog,
    DialogError,
    ScreeningQuestion,
    load_state,
    question_of,
)
from app.models import Channel, Kelurahan, MessageKind, Sender, User
from app.pipeline import default_models
from app.pipeline.responder import BANK, CrisisCard, Hotline, ReplyContext, crisis_reply
from app.redis import get_redis, hit_rate_limit
from app.services import chat as store

router = APIRouter(prefix="/chat", tags=["chat"])
RATE_LIMIT_PER_MIN = 20


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ActionIn(BaseModel):
    type: Action
    value: int | None = None


class HistoryItem(BaseModel):
    id: uuid.UUID
    sender: Sender
    kind: MessageKind
    text: str
    created_at: datetime
    author: str | None = None  # nama pendamping untuk pesan sender=pendamping


class HistoryOut(BaseModel):
    messages: list[HistoryItem]
    card: CrisisCard  # isi kartu untuk pesan ber-kind crisis_card
    hotlines: list[Hotline]
    connected: bool
    screening: ScreeningQuestion | None
    followup_offer: bool


async def _limit(r: Redis, user: User) -> None:
    if await hit_rate_limit(r, f"rl:chat:{user.id}", RATE_LIMIT_PER_MIN):
        raise HTTPException(429, BANK["rate_limited"])


@router.post("/message")
async def post_message(
    body: MessageIn,
    user: User = Depends(active_teen),
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> ChatTurn:
    await _limit(r, user)
    return await Dialog(session, r, user, default_models()).handle_text(body.text.strip())


@router.post("/action")
async def post_action(
    body: ActionIn,
    user: User = Depends(active_teen),
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> ChatTurn:
    await _limit(r, user)
    try:
        return await Dialog(session, r, user, default_models()).handle_action(body.type, body.value)
    except DialogError as e:
        raise HTTPException(409, str(e)) from None


@router.get("/history")
async def get_history(
    user: User = Depends(active_teen),
    session: AsyncSession = Depends(get_session),
    r: Redis = Depends(get_redis),
) -> HistoryOut:
    await store.conversation_for(session, user, Channel.web)  # sapaan pertama kalau baru
    await session.commit()
    st = await load_state(r, user.id)
    kel = await session.get(Kelurahan, user.kelurahan_id)
    crisis = crisis_reply(
        ReplyContext(nickname=user.pseudonym or "kamu", kelurahan=kel.name if kel else "")
    )
    assert crisis.card is not None  # respons merah selalu punya kartu
    rows = await store.history(session, user)
    return HistoryOut(
        messages=[
            HistoryItem(id=i, sender=s, kind=k, text=t, created_at=c, author=a)
            for i, s, k, t, c, a in rows
        ],
        card=crisis.card,
        hotlines=list(crisis.hotlines),
        connected=st.connected,
        screening=question_of(st),
        followup_offer=st.stage == "followup_offer",
    )
