"""Shared async Redis client.

One connection pool per process, reused for: session store, JWT denylist (token
revocation), rate-limit counters, and lightweight caching. Created at startup and
closed on shutdown via the lifespan handler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redis.asyncio import Redis, from_url

from app.core.config import settings

# redis-py's ``Redis`` is generic to type checkers (via types-redis) but is NOT a
# subscriptable/generic class at runtime. FastAPI evaluates annotations with
# ``get_type_hints``, so a bare ``Redis[str]`` in a dependency signature would
# raise at import. This alias keeps the precise type for mypy and a plain class
# at runtime.
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
    """FastAPI dependency — returns the shared client."""
    if _redis is None:
        return init_redis()
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
