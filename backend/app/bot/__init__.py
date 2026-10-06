"""Kabel aiogram 3 (CLAUDE.md §3). Logika ada di bot/logic.py; di sini hanya I/O Telegram."""

from functools import cache

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import logic
from app.bot.logic import OutMsg
from app.db import SessionLocal
from app.pipeline import default_models
from app.redis import redis
from app.settings import settings

router = Router()


def _markup(msg: OutMsg) -> InlineKeyboardMarkup | None:
    if not msg.buttons:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=data) for label, data in row]
            for row in msg.buttons
        ]
    )


async def _send(message: Message, outs: list[OutMsg]) -> None:
    for out in outs:
        await message.answer(out.text, reply_markup=_markup(out))


@router.message(CommandStart())
async def on_start(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    async with SessionLocal() as session:
        outs = await logic.on_start(redis, session, message.from_user.id, command.args)
    await _send(message, outs)


@router.message(F.text)
async def on_text(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return
    async with SessionLocal() as session:
        outs = await logic.on_text(
            redis, session, message.from_user.id, message.text, default_models()
        )
    await _send(message, outs)


@router.callback_query()
async def on_callback(cb: CallbackQuery) -> None:
    await cb.answer()
    if cb.data is None or not isinstance(cb.message, Message):
        return
    async with SessionLocal() as session:
        outs = await logic.on_callback(redis, session, cb.from_user.id, cb.data, default_models())
    await _send(cb.message, outs)


dispatcher = Dispatcher()
dispatcher.include_router(router)


@cache
def get_bot() -> Bot | None:
    return Bot(settings.telegram_bot_token) if settings.telegram_bot_token else None
