"""Telegram (CLAUDE.md §9): POST /telegram/link-token, POST /telegram/webhook."""

import secrets

from aiogram.types import Update
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from redis.asyncio import Redis

from app.api.deps import active_teen
from app.bot import dispatcher, get_bot
from app.bot.logic import LINK_TTL, create_link_code
from app.models import User
from app.redis import get_redis, hit_rate_limit
from app.settings import settings

router = APIRouter(prefix="/telegram", tags=["telegram"])


class LinkOut(BaseModel):
    code: str
    bot_username: str
    deep_link: str
    expires_in: int


@router.post("/link-token")
async def link_token(user: User = Depends(active_teen), r: Redis = Depends(get_redis)) -> LinkOut:
    if await hit_rate_limit(r, f"rl:tg-link:{user.id}", limit=5):
        raise HTTPException(429, "Tunggu sebentar sebelum minta kode baru ya.")
    code = await create_link_code(r, user.id)
    return LinkOut(
        code=code,
        bot_username=settings.telegram_bot_username,
        deep_link=f"https://t.me/{settings.telegram_bot_username}?start={code}",
        expires_in=LINK_TTL,
    )


@router.post("/webhook")
async def webhook(
    request: Request,
    secret: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict[str, bool]:
    expected = settings.telegram_webhook_secret
    if not expected or secret is None or not secrets.compare_digest(secret, expected):
        raise HTTPException(403, "forbidden")
    bot = get_bot()
    if bot is None:
        raise HTTPException(503, "bot belum dikonfigurasi")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}
