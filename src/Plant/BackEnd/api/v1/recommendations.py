"""Trade recommendations route (TRADER-FULL-1 It2 S3)."""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import Depends

from core.database import get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from services.recommendation_engine import TradeRecommendation, get_recommendation_engine

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["recommendations"])


@router.get(
    "/{hired_instance_id}/recommendations",
    response_model=Dict[str, Any],
)
async def get_recommendations(
    hired_instance_id: str,
    sample_size: int = 20,
    db=Depends(get_read_db_session),
) -> Dict[str, Any]:
    """Return RSI threshold recommendations for the hired agent.

    Uses the engine selected by RECOMMENDATION_ENGINE env var (default: rule_based).
    Falls back to rule_based for unrecognised engine names.
    """
    engine = get_recommendation_engine()
    rec: TradeRecommendation = await engine.generate(
        hired_instance_id=hired_instance_id,
        db=db,
        sample_size=sample_size,
    )
    return {
        "hired_instance_id": hired_instance_id,
        "current_rsi_buy_threshold": rec.current_rsi_buy_threshold,
        "current_rsi_sell_threshold": rec.current_rsi_sell_threshold,
        "suggested_rsi_buy_threshold": rec.suggested_rsi_buy_threshold,
        "suggested_rsi_sell_threshold": rec.suggested_rsi_sell_threshold,
        "confidence": rec.confidence,
        "rationale": rec.rationale,
        "sample_size": rec.sample_size,
        "engine": rec.engine,
    }
