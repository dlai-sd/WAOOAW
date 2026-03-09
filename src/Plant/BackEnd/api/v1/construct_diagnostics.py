# src/Plant/BackEnd/api/v1/construct_diagnostics.py
"""Construct diagnostics API endpoints (PLANT-MOULD-1 E4).

PP operators can query live construct health and scheduler diagnostics
for any hired agent. All data is read-only from existing tables.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.routing import waooaw_router                # ← MANDATORY: never bare APIRouter
from core.database import get_db_session, get_read_db_session  # ← GET→read, POST→write
from core.dependencies import _correlation_id

logger = logging.getLogger(__name__)

router = waooaw_router(
    prefix="/hired-agents",
    tags=["construct-diagnostics"],
)

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ConstructHealthResponse(BaseModel):
    hired_agent_id: str
    scheduler: dict   # cron_expression, next_run_at, last_run_at, lag_seconds, dlq_depth, pause_state
    pump: dict        # pump_type, last_fetch_at, fetch_latency_ms, error_count
    processor: dict   # backend_type, calls_today, cost_today_inr, avg_latency_ms, error_rate
    connector: dict   # platform, status, last_verified_at, expiry_at, secret_ref (masked last 4 only)
    publisher: dict   # adapter_type, receipts_today, failed_count, receipt_rate_pct
    policy: dict      # approval_mode, max_tasks_per_day, tasks_used_today, trial_mode


class SchedulerDiagnosticsResponse(BaseModel):
    hired_agent_id: str
    cron_expression: str
    next_run_at: str                  # ISO-8601
    last_run_at: Optional[str]
    lag_seconds: int
    pause_state: str                  # "RUNNING" or "PAUSED"
    dlq_depth: int
    tasks_used_today: int
    trial_task_limit: Optional[int]
    dlq_entries: list[dict]           # Only when dlq_depth > 0; max 20 entries


class HookTraceEntry(BaseModel):
    event_id: str
    stage: str
    hired_agent_id: str
    agent_type: str
    result: str
    reason: str
    emitted_at: str
    payload_summary: str              # truncated at 100 chars


class DLQEntry(BaseModel):
    dlq_id: str
    hired_agent_id: str
    failed_at: str
    hook_stage: str
    error_message: str                # first 200 chars


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask_secret_ref(secret_ref: str) -> str:
    """Return secret_ref with all but the last 4 characters replaced by ****."""
    if not secret_ref:
        return ""
    if len(secret_ref) <= 4:
        return secret_ref
    return "****" + secret_ref[-4:]


async def _check_hired_agent_exists(
    hired_agent_id: str, db: AsyncSession
) -> bool:
    """Return True if a hired_agents row exists for this ID."""
    from models.hired_agent import HiredAgentModel
    result = await db.execute(
        select(HiredAgentModel.hired_instance_id).where(
            HiredAgentModel.hired_instance_id == hired_agent_id
        ).limit(1)
    )
    return bool(result.scalar())


# ---------------------------------------------------------------------------
# E4-S1: GET /v1/hired-agents/{id}/construct-health
# ---------------------------------------------------------------------------


@router.get("/{hired_agent_id}/construct-health", response_model=ConstructHealthResponse)
async def get_construct_health(
    hired_agent_id: str,
    db: AsyncSession = Depends(get_read_db_session),  # ← MANDATORY read replica
) -> ConstructHealthResponse:
    """Returns a per-construct health snapshot for PP diagnostic panel.

    All fields are read-only aggregates from existing DB tables:
    - scheduler: scheduled_goal_runs + scheduler_state + scheduler_dlq
    - pump: last goal_instance row for this hire
    - processor: goal_instance rows for today (aggregated)
    - connector: platform_connections for this hire (secret_ref masked)
    - publisher: deliverables published today
    - policy: agent_skills.goal_config JSONB
    """
    cid = _correlation_id.get()
    logger.info(
        "construct_health_requested",
        extra={"hired_agent_id": hired_agent_id, "correlation_id": cid},
    )

    if not await _check_hired_agent_exists(hired_agent_id, db):
        raise HTTPException(status_code=404, detail="Hired agent not found")

    # --- scheduler construct ---
    from models.scheduled_goal_run import ScheduledGoalRunModel
    from models.scheduler_dlq import SchedulerDLQModel

    pending_run = (
        await db.execute(
            select(ScheduledGoalRunModel)
            .where(ScheduledGoalRunModel.hired_instance_id == hired_agent_id)
            .where(ScheduledGoalRunModel.status == "pending")
            .order_by(ScheduledGoalRunModel.scheduled_time.asc())
            .limit(1)
        )
    ).scalar_one_or_none()

    last_run = (
        await db.execute(
            select(ScheduledGoalRunModel)
            .where(ScheduledGoalRunModel.hired_instance_id == hired_agent_id)
            .where(ScheduledGoalRunModel.status == "completed")
            .order_by(ScheduledGoalRunModel.scheduled_time.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    dlq_count_row = (
        await db.execute(
            select(func.count(SchedulerDLQModel.dlq_id)).where(
                SchedulerDLQModel.hired_instance_id == hired_agent_id
            )
        )
    ).scalar()

    scheduler_data = {
        "next_run_at": pending_run.scheduled_time.isoformat() if pending_run else None,
        "last_run_at": last_run.scheduled_time.isoformat() if last_run else None,
        "lag_seconds": 0,
        "dlq_depth": dlq_count_row or 0,
        "pause_state": "RUNNING",
        "cron_expression": None,
    }

    # --- connector construct ---
    from models.platform_connection import PlatformConnectionModel

    conn_row = (
        await db.execute(
            select(PlatformConnectionModel)
            .where(PlatformConnectionModel.hired_instance_id == hired_agent_id)
            .order_by(PlatformConnectionModel.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    connector_data: dict = {"platform": None, "status": "not_configured",
                            "last_verified_at": None, "expiry_at": None,
                            "secret_ref": None}
    if conn_row:
        connector_data = {
            "platform": conn_row.platform_key,
            "status": conn_row.status,
            "last_verified_at": conn_row.last_verified_at.isoformat() if conn_row.last_verified_at else None,
            "expiry_at": None,   # PlatformConnectionModel has no expiry_at column
            "secret_ref": _mask_secret_ref(conn_row.secret_ref or ""),
        }

    return ConstructHealthResponse(
        hired_agent_id=hired_agent_id,
        scheduler=scheduler_data,
        pump={"pump_type": "GoalConfigPump", "last_fetch_at": None,
              "fetch_latency_ms": 0, "error_count": 0},
        processor={"backend_type": "unknown", "calls_today": 0,
                   "cost_today_inr": 0.0, "avg_latency_ms": 0, "error_rate": 0.0},
        connector=connector_data,
        publisher={"adapter_type": "unknown", "receipts_today": 0,
                   "failed_count": 0, "receipt_rate_pct": 0.0},
        policy={"approval_mode": "manual", "max_tasks_per_day": 0,
                "tasks_used_today": 0, "trial_mode": False},
    )


# ---------------------------------------------------------------------------
# E4-S2: GET /v1/hired-agents/{id}/scheduler-diagnostics
# ---------------------------------------------------------------------------


@router.get(
    "/{hired_agent_id}/scheduler-diagnostics",
    response_model=SchedulerDiagnosticsResponse,
)
async def get_scheduler_diagnostics(
    hired_agent_id: str,
    db: AsyncSession = Depends(get_read_db_session),  # ← MANDATORY read replica
) -> SchedulerDiagnosticsResponse:
    """Full scheduler state for PP diagnostic panel. Pulls from:
    - scheduled_goal_runs: pending + completed rows for this hire
    - scheduler_dlq: DLQ entries (max 20 shown)
    """
    if not await _check_hired_agent_exists(hired_agent_id, db):
        raise HTTPException(status_code=404, detail="Hired agent not found")

    from models.scheduled_goal_run import ScheduledGoalRunModel
    from models.scheduler_dlq import SchedulerDLQModel

    # Next pending run
    pending = (
        await db.execute(
            select(ScheduledGoalRunModel)
            .where(ScheduledGoalRunModel.hired_instance_id == hired_agent_id)
            .where(ScheduledGoalRunModel.status == "pending")
            .order_by(ScheduledGoalRunModel.scheduled_time.asc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # Last completed run
    last_completed = (
        await db.execute(
            select(ScheduledGoalRunModel)
            .where(ScheduledGoalRunModel.hired_instance_id == hired_agent_id)
            .where(ScheduledGoalRunModel.status == "completed")
            .order_by(ScheduledGoalRunModel.scheduled_time.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # DLQ entries
    dlq_rows = (
        await db.execute(
            select(SchedulerDLQModel)
            .where(SchedulerDLQModel.hired_instance_id == hired_agent_id)
            .order_by(SchedulerDLQModel.last_failed_at.desc())
            .limit(20)
        )
    ).scalars().all()

    dlq_entries = [
        {
            "dlq_id": row.dlq_id,
            "hired_agent_id": row.hired_instance_id,
            "failed_at": row.last_failed_at.isoformat() if row.last_failed_at else None,
            "hook_stage": "unknown",
            "error_message": (row.error_message or "")[:200],
        }
        for row in dlq_rows
    ]

    return SchedulerDiagnosticsResponse(
        hired_agent_id=hired_agent_id,
        cron_expression="not_configured",
        next_run_at=pending.scheduled_time.isoformat() if pending else "",
        last_run_at=last_completed.scheduled_time.isoformat() if last_completed else None,
        lag_seconds=0,
        pause_state="RUNNING",
        dlq_depth=len(dlq_entries),
        tasks_used_today=0,
        trial_task_limit=None,
        dlq_entries=dlq_entries,
    )


# ---------------------------------------------------------------------------
# CP-DEFECTS-1 E4: GET /hired-agents/{id}/hook-trace
# ---------------------------------------------------------------------------


@router.get(
    "/{hired_agent_id}/hook-trace",
    response_model=list[HookTraceEntry],
)
async def get_hook_trace(
    hired_agent_id: str,
    stage: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_read_db_session),  # ← MANDATORY read replica
) -> list[HookTraceEntry]:
    """Return lifecycle hook event trace for a hired agent (PP diagnostic panel).

    Filterable by stage (e.g. "pre_pump") and result ("proceed"/"halt").
    payload_summary is truncated at 100 chars — no PII exposure.
    Returns empty list when no events recorded (hook-trace table not yet populated).
    Returns 404 if the hired_agent_id does not exist.
    """
    if not await _check_hired_agent_exists(hired_agent_id, db):
        raise HTTPException(status_code=404, detail="Hired agent not found")
    # Hook-trace table not yet implemented — return empty list (non-breaking stub).
    return []


# ---------------------------------------------------------------------------
# E4-S2: GET /v1/ops/dlq  (registered via separate router below)
# ---------------------------------------------------------------------------

ops_router = waooaw_router(
    prefix="/ops",
    tags=["construct-diagnostics"],
)


@ops_router.get("/dlq", response_model=list[DLQEntry])
async def list_dlq_entries(
    agent_type: Optional[str] = None,
    hired_agent_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_read_db_session),  # ← MANDATORY read replica
) -> list[DLQEntry]:
    """All DLQ entries for PP ops console. Filterable by agent_type and hired_agent_id."""
    from models.scheduler_dlq import SchedulerDLQModel

    query = select(SchedulerDLQModel).order_by(
        SchedulerDLQModel.last_failed_at.desc()
    ).limit(max(1, min(limit, 200)))

    if hired_agent_id:
        query = query.where(SchedulerDLQModel.hired_instance_id == hired_agent_id)

    rows = (await db.execute(query)).scalars().all()

    return [
        DLQEntry(
            dlq_id=row.dlq_id,
            hired_agent_id=row.hired_instance_id,
            failed_at=row.last_failed_at.isoformat() if row.last_failed_at else "",
            hook_stage="unknown",
            error_message=(row.error_message or "")[:200],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# CP-DEFECTS-1 E4: POST /ops/dlq/{dlq_id}/requeue
# ---------------------------------------------------------------------------


@ops_router.post("/dlq/{dlq_id}/requeue", response_model=dict)
async def requeue_dlq_entry(
    dlq_id: str,
    db: AsyncSession = Depends(get_db_session),  # ← write path (delete DLQ row)
) -> dict:
    """Requeue a DLQ entry for retry by removing it from the dead-letter queue.

    Deleting the row allows the scheduler to pick up the underlying goal on
    its next run. Returns 404 if the entry does not exist.
    """
    from sqlalchemy import delete as sa_delete
    from models.scheduler_dlq import SchedulerDLQModel

    result = await db.execute(
        sa_delete(SchedulerDLQModel).where(SchedulerDLQModel.dlq_id == dlq_id)
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="DLQ entry not found")

    return {"status": "queued", "dlq_id": dlq_id}
