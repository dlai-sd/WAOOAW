"""Performance Stats API — PLANT-SKILLS-1 E4-S2

GET  /v1/hired-agents/{hired_instance_id}/performance-stats  — filtered list, max 90 rows
POST /v1/hired-agents/{hired_instance_id}/performance-stats  — upsert by composite key

Query params for GET:
  skill_id, platform_key, from_date (YYYY-MM-DD), to_date (YYYY-MM-DD)
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.performance_stat import PerformanceStatModel

router = waooaw_router(prefix="/v1/hired-agents", tags=["performance-stats"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class PerformanceStatResponse(BaseModel):
    id: str
    hired_instance_id: str
    skill_id: str
    platform_key: str
    stat_date: date
    metrics: Dict[str, Any]
    collected_at: datetime


class UpsertPerformanceStatRequest(BaseModel):
    skill_id: str
    platform_key: str
    stat_date: date
    # metrics shape depends on skill type:
    #   social: { "impressions": int, "clicks": int, "engagement_rate": float, "posts_published": int }
    #   trading: { "trades_count": int, "pnl_pct": float, "win_rate": float, "stop_loss_count": int, "profit_count": int }
    metrics: Dict[str, Any]


def _to_response(stat: PerformanceStatModel) -> PerformanceStatResponse:
    return PerformanceStatResponse(
        id=stat.id,
        hired_instance_id=stat.hired_instance_id,
        skill_id=stat.skill_id,
        platform_key=stat.platform_key,
        stat_date=stat.stat_date,
        metrics=stat.metrics or {},
        collected_at=stat.collected_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/{hired_instance_id}/performance-stats",
    response_model=List[PerformanceStatResponse],
)
async def get_performance_stats(
    hired_instance_id: str,
    skill_id: Optional[str] = None,
    platform_key: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_read_db_session),
) -> List[PerformanceStatResponse]:
    """Return performance stats for a hired agent, filtered and ordered by date desc.

    Returns empty list for unknown hired_instance_id (not 404).
    Max 90 rows returned.
    """
    query = (
        select(PerformanceStatModel)
        .where(PerformanceStatModel.hired_instance_id == hired_instance_id)
    )
    if skill_id:
        query = query.where(PerformanceStatModel.skill_id == skill_id)
    if platform_key:
        query = query.where(PerformanceStatModel.platform_key == platform_key)
    if from_date:
        query = query.where(PerformanceStatModel.stat_date >= from_date)
    if to_date:
        query = query.where(PerformanceStatModel.stat_date <= to_date)

    query = query.order_by(PerformanceStatModel.stat_date.desc()).limit(90)
    result = await db.execute(query)
    stats = result.scalars().all()
    return [_to_response(s) for s in stats]


@router.post(
    "/{hired_instance_id}/performance-stats",
    response_model=PerformanceStatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_performance_stat(
    hired_instance_id: str,
    body: UpsertPerformanceStatRequest,
    db: AsyncSession = Depends(get_db_session),
) -> PerformanceStatResponse:
    """Upsert a performance stat row.

    Keyed on (hired_instance_id, skill_id, platform_key, stat_date).
    If row already exists, updates metrics and collected_at.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        pg_insert(PerformanceStatModel)
        .values(
            id=str(uuid.uuid4()),
            hired_instance_id=hired_instance_id,
            skill_id=body.skill_id,
            platform_key=body.platform_key,
            stat_date=body.stat_date,
            metrics=body.metrics,
            collected_at=now,
        )
        .on_conflict_do_update(
            constraint="uq_perf_stats_hired_skill_platform_date",
            set_={
                "metrics": body.metrics,
                "collected_at": now,
            },
        )
        .returning(PerformanceStatModel)
    )
    result = await db.execute(stmt)
    await db.commit()
    stat = result.scalars().first()
    logger.info(
        "Performance stat upserted: hired=%s skill=%s platform=%s date=%s",
        hired_instance_id,
        body.skill_id,
        body.platform_key,
        body.stat_date,
    )
    return _to_response(stat)
