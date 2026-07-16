"""Async engine and session factory.

A single engine (and its connection pool) lives for the lifetime of the process.
`AsyncSessionLocal` produces short-lived sessions — one per request or per task.

Pool sizing matters in production: total Postgres connections ≈
(DB_POOL_SIZE + DB_MAX_OVERFLOW) x number_of_app_processes. Keep that under the
Postgres `max_connections` (use PgBouncer in front for large fleets).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # transparently recycle dead connections
    pool_recycle=1800,  # avoid stale connections behind proxies
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # objects remain usable after commit (no lazy reload)
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency yielding a session scoped to a single request."""
    async with AsyncSessionLocal() as session:
        yield session
