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
from typing import Any

from fastapi import BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter, get_logger
from core.routing import waooaw_router
from flow_executor import execute_parallel_flow, execute_sequential_flow
from marketing_agent_flows import MARKETING_FLOW_REGISTRY
from models.component_run import ComponentRunModel
from models.flow_run import FlowRunModel
from share_trader_flows import FLOW_REGISTRY

# Merge Marketing Agent flows into the combined registry (E8-S1).
FLOW_REGISTRY = {**FLOW_REGISTRY, **MARKETING_FLOW_REGISTRY}

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/flow-runs", tags=["flow-runs"])
skill_runs_router = waooaw_router(prefix="/skill-runs", tags=["skill-runs"])
component_runs_router = waooaw_router(prefix="/component-runs", tags=["component-runs"])


class FlowRunRequest(BaseModel):
    hired_instance_id: str
    flow_name: str
    run_context: dict


def _serialize_flow_run(row: FlowRunModel) -> dict[str, Any]:
    run_context = dict(row.run_context or {})
    return {
        "id": row.id,
        "status": row.status,
        "current_step": row.current_step,
        "flow_name": row.flow_name,
        "skill_id": row.skill_id,
        "hired_instance_id": row.hired_instance_id,
        "customer_id": run_context.get("customer_id"),
        "run_context": run_context,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
    }


def _serialize_component_run(row: ComponentRunModel) -> dict[str, Any]:
    return {
        "id": row.id,
        "flow_run_id": row.flow_run_id,
        "component_type": row.component_type,
        "step_name": row.step_name,
        "status": row.status,
        "input_context": dict(row.input_context or {}),
        "output": dict(row.output or {}) if isinstance(row.output, dict) else row.output,
        "duration_ms": row.duration_ms,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "error_message": row.error_message,
    }


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

    if "parallel_steps" in flow_def:
        # Fan-out parallel flow (e.g. PublishingFlow)
        shared_input = body.run_context.get("shared_input", {})
        background_tasks.add_task(
            execute_parallel_flow,
            flow_run,
            flow_def["parallel_steps"],
            db,
            shared_input,
        )
    else:
        # Sequential flow with optional approval gate
        background_tasks.add_task(
            execute_sequential_flow,
            flow_run,
            flow_def["sequential_steps"],
            db,
            flow_def.get("approval_gate_index"),
        )
    return {"id": flow_run.id, "status": flow_run.status}


@router.get("")
async def list_flow_runs(
    customer_id: str | None = None,
    hired_instance_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_read_db_session),
):
    """List flow runs from the flow_runs backing store.

    Customer scoping currently derives from run_context.customer_id because the
    backing table has not yet been renamed or expanded for SkillRun semantics.
    """
    stmt = select(FlowRunModel)
    if hired_instance_id:
        stmt = stmt.where(FlowRunModel.hired_instance_id == hired_instance_id)
    if status:
        stmt = stmt.where(FlowRunModel.status == status)

    result = await db.execute(stmt.order_by(FlowRunModel.updated_at.desc()))
    rows = result.scalars().all()
    serialized = [_serialize_flow_run(row) for row in rows]
    if customer_id:
        serialized = [
            row for row in serialized
            if row.get("customer_id") == customer_id
        ]
    return serialized


@router.get("/component-runs")
async def list_component_runs(
    flow_run_id: str,
    db: AsyncSession = Depends(get_read_db_session),
):
    result = await db.execute(
        select(FlowRunModel).where(FlowRunModel.id == flow_run_id)
    )
    flow_run = result.scalar_one_or_none()
    if flow_run is None:
        raise HTTPException(status_code=404, detail="flow_run not found")

    component_result = await db.execute(
        select(ComponentRunModel)
        .where(ComponentRunModel.flow_run_id == flow_run_id)
        .order_by(ComponentRunModel.started_at)
    )
    return [_serialize_component_run(row) for row in component_result.scalars().all()]


@component_runs_router.get("")
async def list_component_runs_alias(
    flow_run_id: str,
    db: AsyncSession = Depends(get_read_db_session),
):
    return await list_component_runs(flow_run_id=flow_run_id, db=db)


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
    return _serialize_flow_run(row)


@skill_runs_router.post("", status_code=201)
async def create_skill_run(
    body: FlowRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    return await create_flow_run(body=body, background_tasks=background_tasks, db=db)


@skill_runs_router.get("")
async def list_skill_runs(
    customer_id: str | None = None,
    hired_instance_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_read_db_session),
):
    return await list_flow_runs(
        customer_id=customer_id,
        hired_instance_id=hired_instance_id,
        status=status,
        db=db,
    )


@skill_runs_router.get("/{skill_run_id}")
async def get_skill_run(
    skill_run_id: str,
    db: AsyncSession = Depends(get_read_db_session),
):
    return await get_flow_run(flow_run_id=skill_run_id, db=db)
