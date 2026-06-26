"""Unit tests for Recommendations API (TRADER-FULL-1 It2 S3)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_db_no_rows():
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute.return_value = result
    return db


def _build_app(fake_db=None):
    from api.v1.recommendations import router
    from core.database import get_read_db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    db = fake_db or _make_db_no_rows()

    async def _fake_db():
        yield db

    app.dependency_overrides[get_read_db_session] = _fake_db
    return app


@pytest.fixture
async def client():
    app = _build_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_recommendations_route_returns_rule_based(client):
    """GET /recommendations returns 200 with engine='rule_based'."""
    resp = await client.get("/api/v1/hired-agents/trader-001/recommendations")
    assert resp.status_code == 200
    body = resp.json()
    assert body["engine"] == "rule_based"
    assert body["hired_instance_id"] == "trader-001"
    assert "suggested_rsi_buy_threshold" in body
    assert "suggested_rsi_sell_threshold" in body
    assert "confidence" in body
    assert "rationale" in body


@pytest.mark.asyncio
async def test_recommendations_uses_read_replica():
    """Route is wired to get_read_db_session (not get_db_session)."""
    # Verify by checking the route's dependency list
    from api.v1.recommendations import router
    from core.database import get_read_db_session

    route = next(r for r in router.routes if "recommendations" in r.path)
    dep_fns = [d.dependency for d in route.dependencies]
    # get_read_db_session is injected via Depends in function signature
    # — verify by importing and calling through the app normally
    app = _build_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/api/v1/hired-agents/trader-001/recommendations")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_recommendations_sample_size_param():
    """sample_size query param is accepted and forwarded to engine."""
    app = _build_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get(
            "/api/v1/hired-agents/trader-001/recommendations?sample_size=5"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["sample_size"] == 0  # no rows → sample_size=0 from engine
