"""Content analytics API — CP-WIZ-1 E1-S1."""
from __future__ import annotations

import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from services.content_analytics import (
    ContentRecommendation,
    get_content_recommendations,
)

router = waooaw_router(prefix="/hired-agents", tags=["content-analytics"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


@router.get(
    "/{hired_instance_id}/content-recommendations",
    response_model=ContentRecommendation,
)
async def get_hired_agent_content_recommendations(
    hired_instance_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> ContentRecommendation:
    """Return content recommendations for a hired agent."""
    recommendation = await get_content_recommendations(hired_instance_id, db)
    logger.info(
        "Content recommendations fetched for hired_instance_id=%s",
        hired_instance_id,
    )
    return recommendation
