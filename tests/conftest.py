"""Shared pytest fixtures.

Environment defaults are set *before* any ``app`` module is imported, because
``app.core.config`` instantiates ``settings`` at import time and several fields
are required. CI provides these via the workflow env; these ``setdefault`` calls
make the suite runnable locally too.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_USER", "crm")
os.environ.setdefault("POSTGRES_PASSWORD", "crm_password")
os.environ.setdefault("POSTGRES_DB", "crm_test")
os.environ.setdefault("REDIS_HOST", "localhost")

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """An HTTP client bound to the ASGI app, with lifespan run (Redis pool, etc.)."""
    from app.main import create_app

    app = create_app()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
