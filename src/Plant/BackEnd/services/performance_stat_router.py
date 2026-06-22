"""
performance_stat_router — INFRA-ROUTING-1 dual-write adapter for PerformanceStat.

Wraps the SQL persistence path for performance stats and adds an async
Firestore secondary write when DATA_ROUTER_MODE is dual_write, shadow_read,
or firestore.

Firestore schema (collection: agent_performance):
  Document ID: str(hired_instance_id)
  Fields:
    hired_instance_id: str
    skill_id: str
    platform_key: str
    stat_date: str (ISO 8601)
    metrics: dict  (mirrors the JSONB metrics column from PerformanceStatModel)
    posts_count: int  (denormalised from metrics["posts_published"] for fast shadow compare)
    updated_at: str (ISO 8601 UTC)

PII: no customer email, phone, or name is stored in Firestore documents.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from core.datastore_router import datastore_router
from core.firestore_client import get_document, set_document
from core.logging import PiiMaskingFilter
from core.metrics import firestore_drift_total, firestore_shadow_reads_total

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

_FIRESTORE_COLLECTION = "agent_performance"


def _to_firestore_doc(hired_agent_id: UUID, stat: Any) -> dict:
    """Convert a PerformanceStatModel ORM row to a Firestore-safe dict (no PII).

    PerformanceStatModel stores all metrics inside a JSONB column called `metrics`.
    We denormalise `posts_count` at the top level for fast shadow-compare without
    needing to deserialise the full metrics dict on every comparison.
    """
    metrics: dict = stat.metrics or {} if hasattr(stat, "metrics") else {}
    return {
        "hired_instance_id": str(hired_agent_id),
        "skill_id": getattr(stat, "skill_id", None),
        "platform_key": getattr(stat, "platform_key", None),
        "stat_date": stat.stat_date.isoformat() if hasattr(stat, "stat_date") and stat.stat_date else None,
        "metrics": metrics,
        # Denormalised for shadow compare — mirrors posts_published from metrics JSONB
        "posts_count": metrics.get("posts_published", 0),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def after_stat_write(hired_agent_id: UUID, stat: Any) -> bool:
    """
    Called after a PerformanceStatModel SQL write.
    Fires an async Firestore secondary write if the routing policy requires it.
    Failures are logged but never raise — SQL path is authoritative.

    Returns:
        True  — write succeeded or routing mode is sql (no-op, treated as success)
        False — Firestore write failed (circuit open or network error)
    """
    if not datastore_router.writes_to_firestore(_FIRESTORE_COLLECTION):
        return True  # sql mode is a successful no-op
    doc_id = str(hired_agent_id)
    doc = _to_firestore_doc(hired_agent_id, stat)
    ok = await set_document(_FIRESTORE_COLLECTION, doc_id, doc)
    if not ok:
        logger.warning(
            "performance_stat_router: Firestore secondary write skipped for agent=%s (circuit open or error)",
            doc_id,
        )
    return ok


async def read_stat_from_firestore(hired_agent_id: UUID) -> Optional[dict]:
    """
    Returns the Firestore document for this agent's performance, or None.
    Only used when DATA_ROUTER_MODE=firestore.
    """
    if not datastore_router.reads_from_firestore(_FIRESTORE_COLLECTION):
        return None
    return await get_document(_FIRESTORE_COLLECTION, str(hired_agent_id))


async def shadow_compare(hired_agent_id: UUID, sql_result: Any) -> None:
    """
    Background task: read Firestore and compare with SQL result.
    Emits drift metric on mismatch. Never raises — shadow mode must be invisible to callers.
    Called via asyncio.create_task() immediately after SQL read returns.
    """
    if not datastore_router.shadow_mode(_FIRESTORE_COLLECTION):
        return
    firestore_shadow_reads_total.labels(collection=_FIRESTORE_COLLECTION).inc()
    try:
        fs_doc = await get_document(_FIRESTORE_COLLECTION, str(hired_agent_id))
        if fs_doc is None:
            # No Firestore document yet — expected until dual_write has run once
            return
        # posts_count is denormalised into the Firestore doc by _to_firestore_doc();
        # on the SQL side, posts_published lives inside the metrics JSONB column.
        sql_posts = (
            sql_result.metrics.get("posts_published")
            if sql_result and hasattr(sql_result, "metrics") and sql_result.metrics
            else None
        )
        fs_posts = fs_doc.get("posts_count")  # key set by _to_firestore_doc()
        if sql_posts != fs_posts:
            firestore_drift_total.labels(collection=_FIRESTORE_COLLECTION).inc()
            logger.warning(
                "shadow_compare: drift detected for agent=%s sql_posts=%s fs_posts=%s",
                str(hired_agent_id), sql_posts, fs_posts,
            )
    except Exception as exc:
        logger.error("shadow_compare: error — %s", exc)
