"""Database-related dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session


async def db_session() -> AsyncGenerator[AsyncSession]:
    """Re-exported request-scoped session dependency.

    A single session per request is the unit of work boundary for read-mostly
    endpoints; for multi-repository writes, services use UnitOfWork explicitly.
    """
    async for session in get_session():
        yield session
