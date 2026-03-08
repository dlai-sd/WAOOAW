"""POST /flow-runs + GET /flow-runs/{id} (EXEC-ENGINE-001 E6-S1).

POST  /flow-runs/       — create a FlowRunModel row and dispatch the named flow
                          as a FastAPI background task.
GET   /flow-runs/{id}   — return current status of a flow run (read replica).

Uses waooaw_router() (never bare APIRouter) per NFR gate P-3.
GET routes use get_read_db_session() per NFR rule 2.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter, get_logger
from core.routing import waooaw_router
from flow_executor import execute_sequential_flow
from models.flow_run import FlowRunModel
from share_trader_flows import FLOW_REGISTRY

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/flow-runs", tags=["flow-runs"])


class FlowRunRequest(BaseModel):
    hired_instance_id: str
    flow_name: str
    run_context: dict


@router.post("/", status_code=201)
async def create_flow_run(
    body: FlowRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a FlowRun record and dispatch the named flow as a background task."""
    flow_def = FLOW_REGISTRY.get(body.flow_name)
    if not flow_def:
        raise HTTPException(status_code=400, detail=f"Unknown flow: {body.flow_name}")

    flow_run = FlowRunModel(
        id=str(uuid.uuid4()),
        hired_instance_id=body.hired_instance_id,
        skill_id=body.run_context.get("skill_id", ""),
        flow_name=body.flow_name,
        status="pending",
        run_context=body.run_context,
        idempotency_key=body.run_context.get("idempotency_key", str(uuid.uuid4())),
        started_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(flow_run)
    await db.commit()
    await db.refresh(flow_run)

    background_tasks.add_task(
        execute_sequential_flow,
        flow_run,
        flow_def["sequential_steps"],
        db,
        flow_def.get("approval_gate_index"),
    )
    return {"id": flow_run.id, "status": flow_run.status}


@router.get("/{flow_run_id}")
async def get_flow_run(
    flow_run_id: str,
    db: AsyncSession = Depends(get_read_db_session),
):
    """Return current status and step for a FlowRun (read-replica)."""
    result = await db.execute(
        select(FlowRunModel).where(FlowRunModel.id == flow_run_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="flow_run not found")
    return {
        "id": row.id,
        "status": row.status,
        "current_step": row.current_step,
        "flow_name": row.flow_name,
    }
