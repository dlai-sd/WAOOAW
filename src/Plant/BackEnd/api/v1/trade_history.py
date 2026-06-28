"""Trade history endpoint — paginated list of per-day performance stats (ST-MVP-1 S11)."""
from __future__ import annotations

from typing import List

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import func, select

from core.database import get_read_db_session
from core.logging import PiiMaskingFilter, get_logger
from core.routing import waooaw_router
from models.performance_stat import PerformanceStatModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["trade-history"])


class TradeHistoryRow(BaseModel):
    stat_date: str
    skill_id: str
    trades_count: int
    pnl_pct_avg: float
    win_rate: float
    stop_loss_count: int


class TradeHistoryResponse(BaseModel):
    hired_instance_id: str
    trades: List[TradeHistoryRow]
    total: int
    page: int
    page_size: int


@router.get("/{hired_instance_id}/trade-history", response_model=TradeHistoryResponse)
async def get_trade_history(
    hired_instance_id: str,
    page: int = 1,
    page_size: int = 20,
    db=Depends(get_read_db_session),
) -> TradeHistoryResponse:
    """Paginated trade-history list sourced from PerformanceStatModel (ST-MVP-1 S11)."""
    page_size = min(max(page_size, 1), 100)
    offset = (max(page, 1) - 1) * page_size

    total_result = await db.execute(
        select(func.count()).select_from(PerformanceStatModel).where(
            PerformanceStatModel.hired_instance_id == hired_instance_id
        )
    )
    total = total_result.scalar_one()

    rows_result = await db.execute(
        select(PerformanceStatModel)
        .where(PerformanceStatModel.hired_instance_id == hired_instance_id)
        .order_by(PerformanceStatModel.stat_date.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = rows_result.scalars().all()

    trades = [
        TradeHistoryRow(
            stat_date=str(r.stat_date),
            skill_id=r.skill_id,
            trades_count=(r.metrics or {}).get("trades_count", 0),
            pnl_pct_avg=(r.metrics or {}).get("pnl_pct", 0.0),
            win_rate=(r.metrics or {}).get("win_rate", 0.0),
            stop_loss_count=(r.metrics or {}).get("stop_loss_count", 0),
        )
        for r in rows
    ]

    return TradeHistoryResponse(
        hired_instance_id=hired_instance_id,
        trades=trades,
        total=total,
        page=page,
        page_size=page_size,
    )
