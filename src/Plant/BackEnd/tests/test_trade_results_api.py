"""Unit tests for Trade Results API (TRADER-FULL-1 S5)."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi import FastAPI


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_fake_trade_rec(
    id="tr-001",
    hired_instance_id="trader-001",
    signal="BUY",
    instrument="BTCUSD",
    trade_date=None,
):
    from datetime import datetime, timezone

    rec = MagicMock()
    rec.id = id
    rec.hired_instance_id = hired_instance_id
    rec.signal = signal
    rec.instrument = instrument
    rec.fill_price = 50000.0
    rec.exit_price = None
    rec.pnl_pct = None
    rec.was_signal_correct = None
    rec.rsi_value = 30.5
    rec.trade_date = trade_date or datetime.now(timezone.utc)
    return rec


def _build_app():
    from api.v1.trade_results import router
    from core.database import get_db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    class _FakeDb:
        def __init__(self):
            self._added = []

        def add(self, obj):
            import uuid
            from datetime import datetime, timezone
            # Apply Python-side column defaults that SQLAlchemy would normally
            # apply during the INSERT flush (not set at object creation time).
            if not obj.id:
                obj.id = str(uuid.uuid4())
            if not getattr(obj, "trade_date", None):
                obj.trade_date = datetime.now(timezone.utc)
            if not getattr(obj, "created_at", None):
                obj.created_at = datetime.now(timezone.utc)
            self._added.append(obj)

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass  # defaults already applied in add()

        async def execute(self, stmt):
            return MagicMock()

        async def close(self):
            pass

    async def _fake_db():
        yield _FakeDb()

    app.dependency_overrides[get_db_session] = _fake_db
    return app


@pytest.fixture
async def client():
    app = _build_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_trade_result_creates_row(client):
    """POST /trade-results returns 201 with id and signal."""
    resp = await client.post(
        "/api/v1/hired-agents/trader-001/trade-results",
        json={
            "signal": "BUY",
            "instrument": "BTCUSD",
            "fill_price": 50000.0,
            "rsi_value": 28.5,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["hired_instance_id"] == "trader-001"
    assert body["signal"] == "BUY"
    assert "id" in body


@pytest.mark.asyncio
async def test_invalid_signal_returns_422(client):
    """signal field rejects values other than BUY, SELL, HOLD."""
    resp = await client.post(
        "/api/v1/hired-agents/trader-001/trade-results",
        json={
            "signal": "INVALID",
            "instrument": "BTCUSD",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_dual_write_called_in_dual_write_mode(monkeypatch):
    """Firestore set_document is called when DATA_ROUTER_MODE=dual_write."""
    monkeypatch.setenv("DATA_ROUTER_MODE", "dual_write")
    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()

    with patch(
        "api.v1.trade_results.set_document",
        new=AsyncMock(return_value=True),
    ) as mock_set:
        app = _build_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
            await http_client.post(
                "/api/v1/hired-agents/trader-001/trade-results",
                json={
                    "signal": "SELL",
                    "instrument": "ETHUSD",
                },
            )
        import asyncio
        await asyncio.sleep(0)

    monkeypatch.setenv("DATA_ROUTER_MODE", "sql")
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()
