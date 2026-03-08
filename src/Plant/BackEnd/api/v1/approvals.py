"""Approvals endpoints — approve or reject a flow run at an approval gate (EXEC-ENGINE-001 E8-S2).

POST /v1/approvals/{flow_run_id}/approve
    Transitions flow_run.status "awaiting_approval" → "running".
    Sets auto_execute=True in run_context so remaining steps execute on next trigger.
    Returns HTTP 409 if flow_run is not in "awaiting_approval" status.

POST /v1/approvals/{flow_run_id}/reject
    Transitions flow_run.status "awaiting_approval" → "failed".
    Sets error_details.reason = "customer_rejected".
    Returns HTTP 409 if flow_run is not in "awaiting_approval" status.

CP BackEnd proxy for these routes is added in Iteration 6 (E14-S2).
Uses waooaw_router() — no bare APIRouter.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.logging import PiiMaskingFilter, get_logger
from core.routing import waooaw_router
from models.flow_run import FlowRunModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/approvals", tags=["approvals"])


@router.post("/{flow_run_id}/approve")
async def approve_flow_run(
    flow_run_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Approve a flow run that is waiting at an approval gate.

    Transitions status to "running" and sets auto_execute=True in run_context
    so the executor skips the gate on the next execution cycle.
    """
    result = await db.execute(
        select(FlowRunModel).where(FlowRunModel.id == flow_run_id)
    )
    flow_run = result.scalar_one_or_none()
    if not flow_run or flow_run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Not awaiting approval")
    flow_run.status = "running"
    flow_run.run_context = {**flow_run.run_context, "auto_execute": True}
    flow_run.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": flow_run_id, "status": flow_run.status}


@router.post("/{flow_run_id}/reject")
async def reject_flow_run(
    flow_run_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Reject a flow run that is waiting at an approval gate.

    Transitions status to "failed" and records the rejection reason in error_details.
    """
    result = await db.execute(
        select(FlowRunModel).where(FlowRunModel.id == flow_run_id)
    )
    flow_run = result.scalar_one_or_none()
    if not flow_run or flow_run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Not awaiting approval")
    flow_run.status = "failed"
    flow_run.error_details = {"reason": "customer_rejected"}
    flow_run.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": flow_run_id, "status": flow_run.status}
