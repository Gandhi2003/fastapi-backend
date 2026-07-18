"""Redis-backed fixed-window rate limiter exposed as a FastAPI dependency.

Self-contained (no slowapi global state), so it composes cleanly with the rest
of the DI graph and is easy to unit-test. Keyed by client IP + route; auth
routes use a tighter limit to blunt credential-stuffing.

Usage in a router:
    @router.post("/login", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
"""

from __future__ import annotations

from fastapi import Depends, Request

from app.core.exceptions import RateLimitError
from app.core.redis import RedisClient, get_redis


class RateLimiter:
    def __init__(self, times: int, seconds: int) -> None:
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request, redis: RedisClient = Depends(get_redis)) -> None:
        client = request.client.host if request.client else "anonymous"
        key = f"ratelimit:{client}:{request.url.path}"
        # INCR + first-hit EXPIRE = atomic fixed window.
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.seconds)
        if current > self.times:
            ttl = await redis.ttl(key)
            raise RateLimitError(
                f"Rate limit exceeded. Retry in {ttl}s.",
                details={"retry_after_seconds": ttl},
            )
