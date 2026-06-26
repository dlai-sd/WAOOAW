"""Trade performance review route (TRADER-FULL-1 It2 S1)."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select

from core.database import get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.performance_stat import PerformanceStatModel

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["trade-performance"])

EXECUTE_TRADE_SKILL = "execute-trade-order"


class TradePerformanceSummary(BaseModel):
    hired_instance_id: str
    period_days: int
    trades_count: int
    pnl_pct_avg: float
    win_rate: float
    stop_loss_count: int
    profit_count: int
    last_stat_date: Optional[date]


@router.get(
    "/{hired_instance_id}/trade-performance",
    response_model=TradePerformanceSummary,
)
async def get_trade_performance(
    hired_instance_id: str,
    period_days: int = 90,
    db=Depends(get_read_db_session),  # read replica
) -> TradePerformanceSummary:
    """Aggregate trade performance stats for a hired agent over the given period.

    Returns an all-zero summary when no stats exist (never 500).
    """
    since = date.today() - timedelta(days=period_days)
    result = await db.execute(
        select(PerformanceStatModel)
        .where(
            PerformanceStatModel.hired_instance_id == hired_instance_id,
            PerformanceStatModel.skill_id == EXECUTE_TRADE_SKILL,
            PerformanceStatModel.stat_date >= since,
        )
        .order_by(PerformanceStatModel.stat_date.desc())
    )
    rows: List[PerformanceStatModel] = result.scalars().all()

    if not rows:
        return TradePerformanceSummary(
            hired_instance_id=hired_instance_id,
            period_days=period_days,
            trades_count=0,
            pnl_pct_avg=0.0,
            win_rate=0.0,
            stop_loss_count=0,
            profit_count=0,
            last_stat_date=None,
        )

    m: List[Dict[str, Any]] = [r.metrics or {} for r in rows]
    return TradePerformanceSummary(
        hired_instance_id=hired_instance_id,
        period_days=period_days,
        trades_count=sum(x.get("trades_count", 0) for x in m),
        pnl_pct_avg=round(sum(x.get("pnl_pct", 0.0) for x in m) / len(m), 2),
        win_rate=round(sum(x.get("win_rate", 0.0) for x in m) / len(m), 2),
        stop_loss_count=sum(x.get("stop_loss_count", 0) for x in m),
        profit_count=sum(x.get("profit_count", 0) for x in m),
        last_stat_date=rows[0].stat_date,
    )
