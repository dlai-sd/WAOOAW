"""flow_executor.py — FlowRun executor: sequential step runner + parallel (fan-out) runner.

This module combines what would be:
  engine/__init__.py       — empty package init (E4-S1)
  engine/flow_executor.py  — execute_sequential_flow + execute_parallel_flow (E4-S1, E4-S2)

execute_sequential_flow():
    Iterates sequential_steps in order, checking an optional approval gate.
    Writes a ComponentRunModel record per step.
    On first failure: sets flow_run.status = "failed" and returns.

execute_parallel_flow():
    Dispatches all parallel_steps concurrently via asyncio.gather().
    all ok → "completed" | some ok → "partial_failure" | none ok → "failed"

Import path:
    from flow_executor import execute_sequential_flow, execute_parallel_flow
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from components import ComponentInput, get_component
from core.logging import PiiMaskingFilter, get_logger
from models.component_run import ComponentRunModel
from models.deliverable import DeliverableModel
from models.flow_run import FlowRunModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


async def execute_sequential_flow(
    flow_run: FlowRunModel,
    sequential_steps: list[dict],
    db: Session,
    approval_gate_index: int | None = None,
) -> None:
    """Execute steps in order. Halt at approval gate when auto_execute is False.

    Args:
        flow_run: The FlowRunModel row to update in place.
        sequential_steps: Ordered list of {"component_type": ..., "step_name": ...} dicts.
        db: SQLAlchemy Session (write replica — caller provides).
        approval_gate_index: If set, pause at this step index when auto_execute=False.
    """
    prev_output = flow_run.run_context.get("previous_step_output")
    for idx, step in enumerate(sequential_steps):
        if approval_gate_index is not None and idx == approval_gate_index:
            if not flow_run.run_context.get("auto_execute", False):
                flow_run.status = "awaiting_approval"
                flow_run.current_step = step["step_name"]
                flow_run.updated_at = datetime.now(timezone.utc)
                db.commit()
                return
        flow_run.current_step = step["step_name"]
        db.commit()
        comp = get_component(step["component_type"])
        comp_input = ComponentInput(
            flow_run_id=flow_run.id,
            customer_id=flow_run.run_context.get("customer_id", ""),
            skill_config=flow_run.run_context.get("skill_config", {}),
            run_context=flow_run.run_context,
            previous_step_output=prev_output,
        )
        comp_run = ComponentRunModel(
            id=str(uuid.uuid4()),
            flow_run_id=flow_run.id,
            component_type=step["component_type"],
            step_name=step["step_name"],
            status="running",
            input_context=comp_input.__dict__,
            started_at=datetime.now(timezone.utc),
        )
        db.add(comp_run)
        db.commit()
        result = await comp.safe_execute(comp_input)
        comp_run.status = "completed" if result.success else "failed"
        comp_run.output = result.data
        comp_run.error_message = result.error_message
        comp_run.duration_ms = result.duration_ms
        comp_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        if not result.success:
            flow_run.status = "failed"
            flow_run.error_details = {"step": step["step_name"], "error": result.error_message}
            flow_run.updated_at = datetime.now(timezone.utc)
            db.commit()
            return
        prev_output = result.data
    flow_run.status = "completed"
    flow_run.completed_at = datetime.now(timezone.utc)
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
    # E6-S2: write deliverable record on successful flow completion.
    # Only created when goal_instance_id is present in run_context so FK is satisfied.
    goal_instance_id = flow_run.run_context.get("goal_instance_id")
    if goal_instance_id:
        _deliverable = DeliverableModel(
            deliverable_id=str(uuid.uuid4()),
            hired_instance_id=flow_run.run_context.get(
                "hired_instance_id", flow_run.hired_instance_id
            ),
            goal_instance_id=goal_instance_id,
            goal_template_id=flow_run.run_context.get("deliverable_type", "trade_execution"),
            title=f"Flow result: {flow_run.flow_name}",
            payload=prev_output or {},
            review_status="pending_review",
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(_deliverable)
        db.commit()


async def execute_parallel_flow(
    flow_run: FlowRunModel,
    parallel_steps: list[dict],
    db: Session,
    shared_input: dict,
) -> None:
    """Execute all steps concurrently via asyncio.gather(). Set status from collective outcomes.

    Args:
        flow_run: The FlowRunModel row to update in place.
        parallel_steps: List of {"component_type": ..., "step_name": ...} dicts (all run concurrently).
        db: SQLAlchemy Session (write replica — caller provides).
        shared_input: Dict passed as previous_step_output to every parallel step.
    """
    flow_run.status = "running"
    db.commit()

    async def run_one(step: dict) -> tuple[str, bool, dict]:
        comp = get_component(step["component_type"])
        comp_input = ComponentInput(
            flow_run_id=flow_run.id,
            customer_id=flow_run.run_context.get("customer_id", ""),
            skill_config=flow_run.run_context.get("skill_config", {}),
            run_context=flow_run.run_context,
            previous_step_output=shared_input,
        )
        comp_run = ComponentRunModel(
            id=str(uuid.uuid4()),
            flow_run_id=flow_run.id,
            component_type=step["component_type"],
            step_name=step["step_name"],
            status="running",
            input_context=comp_input.__dict__,
            started_at=datetime.now(timezone.utc),
        )
        db.add(comp_run)
        db.commit()
        result = await comp.safe_execute(comp_input)
        comp_run.status = "completed" if result.success else "failed"
        comp_run.output = result.data
        comp_run.error_message = result.error_message
        comp_run.duration_ms = result.duration_ms
        comp_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        return step["step_name"], result.success, result.data

    outcomes = await asyncio.gather(*[run_one(s) for s in parallel_steps])
    all_ok = all(ok for _, ok, _ in outcomes)
    any_ok = any(ok for _, ok, _ in outcomes)
    if all_ok:
        flow_run.status = "completed"
    elif any_ok:
        flow_run.status = "partial_failure"
        flow_run.error_details = {"failed_steps": [n for n, ok, _ in outcomes if not ok]}
    else:
        flow_run.status = "failed"
    flow_run.completed_at = datetime.now(timezone.utc)
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
