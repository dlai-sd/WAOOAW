"""Tax report endpoint — monthly/quarterly P&L aggregation (ST-MVP-1 S12)."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from core.database import get_read_db_session
from core.logging import PiiMaskingFilter, get_logger
from core.routing import waooaw_router
from models.performance_stat import PerformanceStatModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["tax-report"])

_QUARTER_MONTHS: Dict[str, tuple] = {
    "Q1": (1, 2, 3),
    "Q2": (4, 5, 6),
    "Q3": (7, 8, 9),
    "Q4": (10, 11, 12),
}


@router.get("/{hired_instance_id}/tax-report")
async def get_tax_report(
    hired_instance_id: str,
    year: int = Query(..., ge=2024, le=2030),
    period: str = Query("monthly", pattern="^(monthly|quarterly)$"),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    quarter: Optional[str] = Query(default=None, pattern="^Q[1-4]$"),
    db=Depends(get_read_db_session),
) -> Dict[str, Any]:
    """Monthly or quarterly P&L tax report for Indian crypto income tax filing (ST-MVP-1 S12)."""
    # Determine date range from period parameters
    if period == "monthly":
        if month is None:
            raise HTTPException(status_code=422, detail="month required for period=monthly")
        start = date(year, month, 1)
        end = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
    else:
        if quarter is None:
            raise HTTPException(status_code=422, detail="quarter required for period=quarterly")
        months = _QUARTER_MONTHS[quarter]
        start = date(year, months[0], 1)
        end = date(year, months[-1] + 1, 1) if months[-1] < 12 else date(year + 1, 1, 1)

    result = await db.execute(
        select(PerformanceStatModel)
        .where(
            PerformanceStatModel.hired_instance_id == hired_instance_id,
            PerformanceStatModel.stat_date >= start,
            PerformanceStatModel.stat_date < end,
        )
        .order_by(PerformanceStatModel.stat_date)
    )
    rows = result.scalars().all()

    if not rows:
        return {
            "hired_instance_id": hired_instance_id,
            "period": period,
            "year": year,
            "total_trades": 0,
            "total_pnl_pct": 0.0,
            "profitable_trades": 0,
            "loss_trades": 0,
            "stop_loss_exits": 0,
            "trades": [],
        }

    metrics = [r.metrics or {} for r in rows]
    trades_data = [
        {
            "date": str(r.stat_date),
            "skill_id": r.skill_id,
            "trades_count": (r.metrics or {}).get("trades_count", 0),
            "pnl_pct": (r.metrics or {}).get("pnl_pct", 0.0),
            "win_rate": (r.metrics or {}).get("win_rate", 0.0),
            "stop_loss_count": (r.metrics or {}).get("stop_loss_count", 0),
        }
        for r in rows
    ]

    return {
        "hired_instance_id": hired_instance_id,
        "period": period,
        "year": year,
        "total_trades": sum(m.get("trades_count", 0) for m in metrics),
        "total_pnl_pct": round(sum(m.get("pnl_pct", 0.0) for m in metrics), 4),
        "profitable_trades": sum(1 for m in metrics if m.get("pnl_pct", 0.0) > 0),
        "loss_trades": sum(1 for m in metrics if m.get("pnl_pct", 0.0) < 0),
        "stop_loss_exits": sum(m.get("stop_loss_count", 0) for m in metrics),
        "trades": trades_data,
    }
