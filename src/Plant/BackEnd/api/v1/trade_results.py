"""Trade result routes for Share Trader (TRADER-FULL-1 S5)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import Depends
from pydantic import BaseModel, Field

from core.database import get_db_session
from core.datastore_router import datastore_router
from core.firestore_client import set_document
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.trade_result import TradeResultModel

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["trade-results"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class RecordTradeResultRequest(BaseModel):
    signal: str = Field(..., pattern="^(BUY|SELL|HOLD)$")
    instrument: str = Field(..., min_length=1)
    fill_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    was_signal_correct: Optional[bool] = None
    rsi_value: Optional[float] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/{hired_instance_id}/trade-results", status_code=201)
async def record_trade_result(
    hired_instance_id: str,
    body: RecordTradeResultRequest,
    db=Depends(get_db_session),
) -> Dict[str, Any]:
    rec = TradeResultModel(
        hired_instance_id=hired_instance_id,
        signal=body.signal,
        instrument=body.instrument,
        fill_price=body.fill_price,
        exit_price=body.exit_price,
        pnl_pct=body.pnl_pct,
        was_signal_correct=body.was_signal_correct,
        rsi_value=body.rsi_value,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    # Dual-write to Firestore
    if datastore_router.writes_to_firestore("trade_results"):
        asyncio.create_task(
            set_document(
                "trade_results",
                rec.id,
                {
                    "id": rec.id,
                    "hired_instance_id": str(hired_instance_id),
                    "signal": rec.signal,
                    "instrument": rec.instrument,
                    "pnl_pct": rec.pnl_pct,
                    "was_signal_correct": rec.was_signal_correct,
                    "trade_date": rec.trade_date.isoformat(),
                },
            )
        )
    return {
        "id": rec.id,
        "hired_instance_id": hired_instance_id,
        "signal": rec.signal,
    }
