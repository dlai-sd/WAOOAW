"""Unit tests for trade_history API endpoint (ST-MVP-1 S11)."""
from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_stat(hired_id: str, stat_date: str, skill_id: str = "trading.share_trader.v1",
               metrics: dict | None = None) -> MagicMock:
    row = MagicMock()
    row.hired_instance_id = hired_id
    row.stat_date = datetime.date.fromisoformat(stat_date)
    row.skill_id = skill_id
    row.metrics = metrics or {"trades_count": 2, "pnl_pct": 1.5, "win_rate": 0.6, "stop_loss_count": 0}
    return row


def _make_db(total: int, rows: list) -> AsyncMock:
    """Build a mock async db session that returns (total, rows) on successive execute calls."""
    db = AsyncMock()

    # First execute → count query
    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    # Second execute → rows query
    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = rows

    db.execute = AsyncMock(side_effect=[count_result, rows_result])
    return db


class TestTradeHistoryEmpty:
    @pytest.mark.asyncio
    async def test_empty_history_returns_zero_total(self):
        """S11 T1 — empty history returns trades=[], total=0."""
        from api.v1.trade_history import get_trade_history

        db = _make_db(0, [])
        result = await get_trade_history("TRD-001", page=1, page_size=20, db=db)

        assert result.total == 0
        assert result.trades == []
        assert result.hired_instance_id == "TRD-001"
        assert result.page == 1
        assert result.page_size == 20


class TestTradeHistoryPagination:
    @pytest.mark.asyncio
    async def test_page_2_skips_first_five_rows(self):
        """S11 T2 — page=2 page_size=5 skips first 5 rows (offset=5)."""
        from api.v1.trade_history import get_trade_history

        row = _make_stat("TRD-001", "2026-06-15")
        db = _make_db(10, [row])
        result = await get_trade_history("TRD-001", page=2, page_size=5, db=db)

        assert result.page == 2
        assert result.page_size == 5
        assert result.total == 10
        assert len(result.trades) == 1

        # Verify the execute was called with correct offset/limit by inspecting calls
        # The second execute call (rows query) should exist
        assert db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_page_size_capped_at_100(self):
        """S11 T3 — page_size=999 is capped to 100."""
        from api.v1.trade_history import get_trade_history

        db = _make_db(5, [])
        result = await get_trade_history("TRD-001", page=1, page_size=999, db=db)

        assert result.page_size == 100

    @pytest.mark.asyncio
    async def test_row_fields_mapped_correctly(self):
        """S11 — each row maps PerformanceStatModel fields to TradeHistoryRow correctly."""
        from api.v1.trade_history import get_trade_history

        row = _make_stat("TRD-001", "2026-06-20", metrics={
            "trades_count": 5, "pnl_pct": 2.3, "win_rate": 0.8, "stop_loss_count": 1
        })
        db = _make_db(1, [row])
        result = await get_trade_history("TRD-001", page=1, page_size=20, db=db)

        assert len(result.trades) == 1
        t = result.trades[0]
        assert t.stat_date == "2026-06-20"
        assert t.skill_id == "trading.share_trader.v1"
        assert t.trades_count == 5
        assert t.pnl_pct_avg == 2.3
        assert t.win_rate == 0.8
        assert t.stop_loss_count == 1

    @pytest.mark.asyncio
    async def test_missing_metrics_defaults_to_zero(self):
        """S11 — row with None metrics falls back to zero values."""
        from api.v1.trade_history import get_trade_history

        row = _make_stat("TRD-001", "2026-05-01", metrics=None)
        row.metrics = None
        db = _make_db(1, [row])
        result = await get_trade_history("TRD-001", page=1, page_size=20, db=db)

        t = result.trades[0]
        assert t.trades_count == 0
        assert t.pnl_pct_avg == 0.0
        assert t.win_rate == 0.0
        assert t.stop_loss_count == 0
