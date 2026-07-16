"""Shared async Redis client.

One connection pool per process, reused for: session store, JWT denylist (token
revocation), rate-limit counters, and lightweight caching. Created at startup and
closed on shutdown via the lifespan handler.
"""

from __future__ import annotations

from redis.asyncio import Redis, from_url

from app.core.config import settings

_redis: Redis | None = None


def init_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
        )
    return _redis


def get_redis() -> Redis:
    """FastAPI dependency — returns the shared client."""
    if _redis is None:
        return init_redis()
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
