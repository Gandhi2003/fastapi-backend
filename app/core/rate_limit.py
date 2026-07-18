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
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.seconds)
        if current > self.times:
            ttl = await redis.ttl(key)
            raise RateLimitError(
                f"Rate limit exceeded. Retry in {ttl}s.",
                details={"retry_after_seconds": ttl},
            )
