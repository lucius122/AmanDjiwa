"""Redis: state percakapan, rate limit, token tautan Telegram (§3)."""

from redis.asyncio import Redis

from app.settings import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> Redis:
    return redis


async def hit_rate_limit(r: Redis, key: str, limit: int, window_s: int = 60) -> bool:
    """True kalau batas terlampaui (jendela tetap per `window_s` detik)."""
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, window_s)
    return count > limit
