"""Mode polling khusus dev lokal (webhook butuh URL HTTPS publik, disiapkan di M7).

uv run python -m app.bot.polling
"""

import asyncio

from app.bot import dispatcher, get_bot


async def main() -> None:
    bot = get_bot()
    if bot is None:
        raise SystemExit("TELEGRAM_BOT_TOKEN belum diisi di .env")
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
