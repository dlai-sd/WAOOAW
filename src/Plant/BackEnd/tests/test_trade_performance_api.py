"""Unit tests for Trade Performance API (TRADER-FULL-1 It2 S1)."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_stat(
    hired_instance_id: str = "trader-001",
    skill_id: str = "execute-trade-order",
    stat_date: date | None = None,
    metrics: dict | None = None,
):
    rec = MagicMock()
    rec.hired_instance_id = hired_instance_id
    rec.skill_id = skill_id
    rec.stat_date = stat_date or date.today()
    rec.metrics = metrics or {
        "trades_count": 5,
        "pnl_pct": 2.5,
        "win_rate": 0.6,
        "stop_loss_count": 1,
        "profit_count": 3,
    }
    return rec


def _build_app(db_rows=None):
    from api.v1.trade_performance import router
    from core.database import get_read_db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    class _FakeDb:
        async def execute(self, stmt):
            result = MagicMock()
            result.scalars.return_value.all.return_value = db_rows or []
            return result

        async def close(self):
            pass

    async def _fake_db():
        yield _FakeDb()

    app.dependency_overrides[get_read_db_session] = _fake_db
    return app


@pytest.fixture
async def client_empty():
    app = _build_app(db_rows=[])
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def client_with_rows():
    rows = [
        _make_stat(
            stat_date=date.today() - timedelta(days=i),
            metrics={
                "trades_count": 3,
                "pnl_pct": 1.5,
                "win_rate": 0.5,
                "stop_loss_count": 1,
                "profit_count": 2,
            },
        )
        for i in range(3)
    ]
    app = _build_app(db_rows=rows)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trade_performance_empty_returns_zeros(client_empty):
    """Empty stats table returns all-zero summary (no 500)."""
    resp = await client_empty.get(
        "/api/v1/hired-agents/trader-001/trade-performance"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["hired_instance_id"] == "trader-001"
    assert body["trades_count"] == 0
    assert body["pnl_pct_avg"] == 0.0
    assert body["win_rate"] == 0.0
    assert body["stop_loss_count"] == 0
    assert body["profit_count"] == 0
    assert body["last_stat_date"] is None


@pytest.mark.asyncio
async def test_trade_performance_aggregates_correctly(client_with_rows):
    """Aggregation sums counts and averages rates across rows."""
    resp = await client_with_rows.get(
        "/api/v1/hired-agents/trader-001/trade-performance"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["trades_count"] == 9   # 3 rows × 3
    assert body["stop_loss_count"] == 3  # 3 rows × 1
    assert body["profit_count"] == 6    # 3 rows × 2
    # win_rate average: avg(0.5, 0.5, 0.5) = 0.5
    assert body["win_rate"] == 0.5
    # pnl_pct_avg: avg(1.5, 1.5, 1.5) = 1.5
    assert body["pnl_pct_avg"] == 1.5


@pytest.mark.asyncio
async def test_trade_performance_uses_period_days_param(client_empty):
    """period_days param is accepted without error."""
    resp = await client_empty.get(
        "/api/v1/hired-agents/trader-001/trade-performance?period_days=30"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["period_days"] == 30
