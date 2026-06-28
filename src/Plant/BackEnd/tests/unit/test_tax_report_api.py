"""Unit tests for tax_report API endpoint (ST-MVP-1 S12)."""
from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_stat(stat_date: str, metrics: dict | None = None) -> MagicMock:
    row = MagicMock()
    row.stat_date = datetime.date.fromisoformat(stat_date)
    row.skill_id = "trading.share_trader.v1"
    row.metrics = metrics or {"trades_count": 1, "pnl_pct": 1.0, "win_rate": 0.5, "stop_loss_count": 0}
    return row


def _make_db(rows: list) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute = AsyncMock(return_value=result)
    return db


class TestTaxReportEmpty:
    @pytest.mark.asyncio
    async def test_empty_period_returns_zero_totals(self):
        """S12 T1 — month with no data returns total_trades: 0, never 500."""
        from api.v1.tax_report import get_tax_report

        db = _make_db([])
        result = await get_tax_report(
            "TRD-001", year=2026, period="monthly", month=3, db=db
        )

        assert result["total_trades"] == 0
        assert result["total_pnl_pct"] == 0.0
        assert result["trades"] == []
        assert result["hired_instance_id"] == "TRD-001"


class TestTaxReportMonthly:
    @pytest.mark.asyncio
    async def test_monthly_aggregates_three_rows(self):
        """S12 T2 — monthly report aggregates 3 rows correctly."""
        from api.v1.tax_report import get_tax_report

        rows = [
            _make_stat("2026-06-01", {"trades_count": 3, "pnl_pct": 2.0, "win_rate": 0.67, "stop_loss_count": 0}),
            _make_stat("2026-06-10", {"trades_count": 2, "pnl_pct": -0.5, "win_rate": 0.5, "stop_loss_count": 1}),
            _make_stat("2026-06-20", {"trades_count": 5, "pnl_pct": 1.0, "win_rate": 0.8, "stop_loss_count": 0}),
        ]
        db = _make_db(rows)
        result = await get_tax_report(
            "TRD-001", year=2026, period="monthly", month=6, db=db
        )

        assert result["total_trades"] == 10  # 3+2+5
        assert result["total_pnl_pct"] == round(2.0 - 0.5 + 1.0, 4)
        assert result["profitable_trades"] == 2  # pnl_pct > 0
        assert result["loss_trades"] == 1         # pnl_pct < 0
        assert result["stop_loss_exits"] == 1
        assert len(result["trades"]) == 3

    @pytest.mark.asyncio
    async def test_monthly_missing_month_raises_422(self):
        """S12 T4 — missing month for period=monthly raises HTTP 422."""
        from fastapi import HTTPException
        from api.v1.tax_report import get_tax_report

        db = _make_db([])
        with pytest.raises(HTTPException) as exc_info:
            await get_tax_report("TRD-001", year=2026, period="monthly", month=None, db=db)
        assert exc_info.value.status_code == 422


class TestTaxReportQuarterly:
    @pytest.mark.asyncio
    async def test_q2_quarterly_covers_april_june(self):
        """S12 T3 — Q2 quarterly returns only April–June records."""
        from api.v1.tax_report import get_tax_report

        # These rows represent April–June (Q2) stats
        rows = [
            _make_stat("2026-04-15", {"trades_count": 4, "pnl_pct": 3.0, "win_rate": 0.75, "stop_loss_count": 0}),
            _make_stat("2026-05-20", {"trades_count": 2, "pnl_pct": -1.0, "win_rate": 0.5, "stop_loss_count": 1}),
        ]
        db = _make_db(rows)
        result = await get_tax_report(
            "TRD-001", year=2026, period="quarterly", quarter="Q2", db=db
        )

        assert result["period"] == "quarterly"
        assert result["year"] == 2026
        assert result["total_trades"] == 6
        assert result["stop_loss_exits"] == 1

    @pytest.mark.asyncio
    async def test_quarterly_missing_quarter_raises_422(self):
        """S12 — missing quarter for period=quarterly raises HTTP 422."""
        from fastapi import HTTPException
        from api.v1.tax_report import get_tax_report

        db = _make_db([])
        with pytest.raises(HTTPException) as exc_info:
            await get_tax_report("TRD-001", year=2026, period="quarterly", quarter=None, db=db)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_q4_wraps_december_correctly(self):
        """S12 — Q4 (Oct–Dec) uses year+1 January as end date without crashing."""
        from api.v1.tax_report import get_tax_report

        rows = [_make_stat("2026-12-01")]
        db = _make_db(rows)
        # Should not raise on December month boundary
        result = await get_tax_report(
            "TRD-001", year=2026, period="quarterly", quarter="Q4", db=db
        )
        assert result["total_trades"] == 1
