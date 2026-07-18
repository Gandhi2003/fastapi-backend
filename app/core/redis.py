from __future__ import annotations

from typing import TYPE_CHECKING

from redis.asyncio import Redis, from_url

from app.core.config import settings

if TYPE_CHECKING:
    RedisClient = Redis[str]
else:
    RedisClient = Redis

_redis: RedisClient | None = None


def init_redis() -> RedisClient:
    global _redis
    if _redis is None:
        _redis = from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
        )
    return _redis


def get_redis() -> RedisClient:
    if _redis is None:
        return init_redis()
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
