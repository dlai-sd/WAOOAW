"""
reconciliation_service — INFRA-ROUTING-1 daily drift sweep.

Scans all PerformanceStat rows, reads matching Firestore documents,
compares posts_count as the primary reconciliation field, and logs
a structured summary.  Designed to run as a scheduled Cloud Run Job
(one-off invocation) or triggered from a PP admin route.

Never writes to SQL from this service — SQL is read-only authoritative source.
Repair action: re-trigger after_stat_write() for drifted rows.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.firestore_client import get_document
from core.logging import PiiMaskingFilter
from core.metrics import firestore_drift_total
from models.performance_stat import PerformanceStatModel
from services.performance_stat_router import after_stat_write, _FIRESTORE_COLLECTION

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


async def run_reconciliation_sweep(db: AsyncSession) -> dict:
    """
    Sweep all PerformanceStat rows and re-sync drifted Firestore documents.

    Returns:
        dict with keys: total_checked, drifted, repaired, errors
    """
    result = await db.execute(select(PerformanceStatModel))
    stats = result.scalars().all()

    total = len(stats)
    drifted = 0
    repaired = 0
    errors = 0

    for stat in stats:
        try:
            hired_agent_id = stat.hired_instance_id
            fs_doc = await get_document(_FIRESTORE_COLLECTION, str(hired_agent_id))
            # posts_published lives inside metrics JSONB; posts_count is the denormalised key in Firestore
            sql_posts = stat.metrics.get("posts_published", 0) if stat.metrics else 0
            fs_posts = fs_doc.get("posts_count") if fs_doc else None
            if fs_posts != sql_posts:
                drifted += 1
                firestore_drift_total.labels(collection=_FIRESTORE_COLLECTION).inc()
                ok: bool = await after_stat_write(hired_agent_id, stat)
                if ok:
                    repaired += 1
        except Exception as exc:
            errors += 1
            logger.error(
                "reconciliation_service: error for stat=%s — %s",
                getattr(stat, "id", "?"),
                exc,
            )

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_checked": total,
        "drifted": drifted,
        "repaired": repaired,
        "errors": errors,
    }
    logger.info("reconciliation_service: sweep complete %s", summary)
    return summary
