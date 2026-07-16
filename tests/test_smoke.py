"""Smoke tests: prove the app boots and the liveness probe responds.

The liveness endpoint deliberately touches no external dependencies, so this
runs without a database or Redis. Add per-module tests alongside this file as
the API surface grows.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
async def test_liveness(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health/live")

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "alive"
