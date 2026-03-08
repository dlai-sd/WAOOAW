"""Unit tests for deliverable hook in flow_executor.py (EXEC-ENGINE-001 E6-S2).

Verifies that execute_sequential_flow writes a DeliverableModel row on successful
completion and does NOT write one when any step fails.

Tests:
  E6-S2-T1: All steps succeed + goal_instance_id present → DeliverableModel added
  E6-S2-T2: goal_instance_id="goal-123" → deliverable.goal_instance_id == "goal-123"
  E6-S2-T3: Step fails → no DeliverableModel created
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, ComponentOutput
from models.flow_run import FlowRunModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_flow_run(run_context: dict | None = None) -> FlowRunModel:
    now = datetime.now(timezone.utc)
    ctx = run_context if run_context is not None else {
        "customer_id": "cust-001",
        "auto_execute": True,
        "deliverable_type": "trade_execution",
        "goal_instance_id": "goal-001",
    }
    return FlowRunModel(
        id="fr-deliv-001",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="ExecuteTradeFlow",
        status="running",
        idempotency_key="idem-deliv-001",
        started_at=now,
        updated_at=now,
        run_context=ctx,
    )


def _make_db() -> MagicMock:
    db = MagicMock()
    db.commit = MagicMock()
    return db


def _ok_component(data: dict | None = None) -> MagicMock:
    comp = MagicMock()
    comp.safe_execute = AsyncMock(
        return_value=ComponentOutput(
            success=True, data=data or {"trade": "done"}
        )
    )
    return comp


def _fail_component() -> MagicMock:
    comp = MagicMock()
    comp.safe_execute = AsyncMock(
        return_value=ComponentOutput(success=False, error_message="failed")
    )
    return comp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_deliverable_created_on_success():
    """E6-S2-T1: Successful flow + goal_instance_id → DeliverableModel added."""
    flow_run = _make_flow_run()
    db = _make_db()
    steps = [{"component_type": "DeltaPublisher", "step_name": "step_1"}]

    added_objects: list = []
    db.add = lambda obj: added_objects.append(obj)

    with patch("flow_executor.get_component", return_value=_ok_component()):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db))

    deliverables = [o for o in added_objects if type(o).__name__ == "DeliverableModel"]
    assert len(deliverables) == 1, f"Expected 1 DeliverableModel, got {len(deliverables)}"
    assert deliverables[0].goal_template_id == "trade_execution"


@pytest.mark.unit
def test_deliverable_goal_instance_id_from_context():
    """E6-S2-T2: goal_instance_id from run_context is stored on the deliverable."""
    flow_run = _make_flow_run(run_context={
        "customer_id": "cust-001",
        "auto_execute": True,
        "deliverable_type": "trade_execution",
        "goal_instance_id": "goal-123",
    })
    db = _make_db()
    steps = [{"component_type": "DeltaPublisher", "step_name": "step_1"}]

    added_objects: list = []
    db.add = lambda obj: added_objects.append(obj)

    with patch("flow_executor.get_component", return_value=_ok_component()):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db))

    deliverables = [o for o in added_objects if type(o).__name__ == "DeliverableModel"]
    assert len(deliverables) == 1
    assert deliverables[0].goal_instance_id == "goal-123"


@pytest.mark.unit
def test_no_deliverable_when_goal_instance_id_missing():
    """No deliverable created when goal_instance_id is absent from run_context."""
    flow_run = _make_flow_run(run_context={
        "customer_id": "cust-001",
        "auto_execute": True,
        "deliverable_type": "trade_execution",
        # goal_instance_id intentionally omitted
    })
    db = _make_db()
    steps = [{"component_type": "DeltaPublisher", "step_name": "step_1"}]

    added_objects: list = []
    db.add = lambda obj: added_objects.append(obj)

    with patch("flow_executor.get_component", return_value=_ok_component()):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db))

    deliverables = [o for o in added_objects if type(o).__name__ == "DeliverableModel"]
    assert len(deliverables) == 0


@pytest.mark.unit
def test_no_deliverable_on_step_failure():
    """E6-S2-T3: Failed step → no DeliverableModel created."""
    flow_run = _make_flow_run()
    db = _make_db()
    steps = [{"component_type": "DeltaPublisher", "step_name": "step_1"}]

    added_objects: list = []
    db.add = lambda obj: added_objects.append(obj)

    with patch("flow_executor.get_component", return_value=_fail_component()):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db))

    deliverables = [o for o in added_objects if type(o).__name__ == "DeliverableModel"]
    assert len(deliverables) == 0
