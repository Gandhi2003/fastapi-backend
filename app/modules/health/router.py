"""Health & readiness probes for Kubernetes / load balancers.

  * /health/live    — liveness: process is up (no dependencies checked).
  * /health/ready   — readiness: DB + Redis reachable; gate traffic on this.
Separating the two prevents a transient DB blip from killing healthy pods.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import db_session
from app.common.schemas.response import ResponseEnvelope, ok
from app.core.config import settings
from app.core.redis import RedisClient, get_redis

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def liveness() -> ResponseEnvelope[dict[str, str]]:
    return ok({"status": "alive", "app": settings.APP_NAME, "env": settings.ENVIRONMENT})


@router.get("/ready")
async def readiness(
    session: AsyncSession = Depends(db_session),
    redis: RedisClient = Depends(get_redis),
) -> ResponseEnvelope[dict[str, object]]:
    checks: dict[str, str] = {}
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "down"
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "down"

    healthy = all(v == "ok" for v in checks.values())
    return ok({"status": "ready" if healthy else "degraded", "checks": checks})
