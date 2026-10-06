"""Mode polling khusus dev lokal (webhook butuh URL HTTPS publik, disiapkan di M7).

uv run python -m app.bot.polling
"""

import asyncio
import logging

from app.bot import dispatcher, get_bot

# aiogram hanya mencatat id update & durasi, bukan isi pesan (§7).
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def main() -> None:
    bot = get_bot()
    if bot is None:
        raise SystemExit("TELEGRAM_BOT_TOKEN belum diisi di .env")
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
