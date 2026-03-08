"""Unit tests for flow_executor.py — sequential runner (EXEC-ENGINE-001 E4-S1).

Tests:
  E4-S1-T1: 3 mock components all succeed → flow_run.status="completed"
  E4-S1-T2: step index 1 fails → flow_run.status="failed", step 2 not executed
  E4-S1-T3: gate at index 1, auto_execute=false → status="awaiting_approval" after step 0
  E4-S1-T4: gate at index 1, auto_execute=true → all 3 steps run, status="completed"
  E4-S1-T5: previous_step_output chaining — step N+1 receives step N's data
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

def _make_flow_run(auto_execute: bool = True) -> FlowRunModel:
    now = datetime.now(timezone.utc)
    return FlowRunModel(
        id="fr-exec-001",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="test_flow",
        status="running",
        idempotency_key="idem-exec-001",
        started_at=now,
        updated_at=now,
        run_context={"customer_id": "cust-1", "auto_execute": auto_execute},
    )


def _make_db() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


def _make_steps(count: int = 3) -> list[dict]:
    return [
        {"component_type": f"Comp{i}", "step_name": f"step_{i}"}
        for i in range(count)
    ]


def _ok_component(data: dict | None = None) -> MagicMock:
    comp = MagicMock()
    comp.safe_execute = AsyncMock(
        return_value=ComponentOutput(success=True, data=data or {})
    )
    return comp


def _fail_component(msg: str = "err") -> MagicMock:
    comp = MagicMock()
    comp.safe_execute = AsyncMock(
        return_value=ComponentOutput(success=False, error_message=msg)
    )
    return comp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_sequential_all_success():
    """E4-S1-T1: All 3 steps succeed → status=completed."""
    flow_run = _make_flow_run()
    db = _make_db()
    steps = _make_steps(3)

    with patch("flow_executor.get_component", side_effect=[_ok_component(), _ok_component(), _ok_component()]):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db))

    assert flow_run.status == "completed"


@pytest.mark.unit
def test_sequential_step_fails_stops_execution():
    """E4-S1-T2: Step index 1 fails → status=failed, step 2 not executed."""
    flow_run = _make_flow_run()
    db = _make_db()
    steps = _make_steps(3)

    call_count = 0

    def _side_effect(comp_type):
        nonlocal call_count
        call_count += 1
        return _fail_component("err") if call_count == 2 else _ok_component()

    with patch("flow_executor.get_component", side_effect=_side_effect):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db))

    assert flow_run.status == "failed"
    assert call_count == 2  # step 2 (index 2) not reached


@pytest.mark.unit
def test_sequential_approval_gate_halts_when_not_auto():
    """E4-S1-T3: Gate at index 1, auto_execute=False → awaiting_approval after step 0."""
    flow_run = _make_flow_run(auto_execute=False)
    db = _make_db()
    steps = _make_steps(3)

    call_count = 0

    def _side_effect(comp_type):
        nonlocal call_count
        call_count += 1
        return _ok_component()

    with patch("flow_executor.get_component", side_effect=_side_effect):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db, approval_gate_index=1))

    assert flow_run.status == "awaiting_approval"
    assert call_count == 1  # only step 0 ran before gate


@pytest.mark.unit
def test_sequential_approval_gate_skipped_when_auto_execute():
    """E4-S1-T4: Gate at index 1, auto_execute=True → all 3 steps run, status=completed."""
    flow_run = _make_flow_run(auto_execute=True)
    db = _make_db()
    steps = _make_steps(3)

    call_count = 0

    def _side_effect(comp_type):
        nonlocal call_count
        call_count += 1
        return _ok_component()

    with patch("flow_executor.get_component", side_effect=_side_effect):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db, approval_gate_index=1))

    assert flow_run.status == "completed"
    assert call_count == 3


@pytest.mark.unit
def test_sequential_previous_step_output_chaining():
    """E4-S1-T5: Step N+1 receives previous_step_output equal to step N's result.data."""
    flow_run = _make_flow_run()
    db = _make_db()
    steps = [
        {"component_type": "CompA", "step_name": "step_a"},
        {"component_type": "CompB", "step_name": "step_b"},
    ]

    # Step A returns known data; capture what Step B receives
    a_data = {"step_a_key": "step_a_val"}
    captured_b_input: list[ComponentInput] = []

    comp_a = MagicMock()
    comp_a.safe_execute = AsyncMock(
        return_value=ComponentOutput(success=True, data=a_data)
    )

    async def _capture_b(inp: ComponentInput) -> ComponentOutput:
        captured_b_input.append(inp)
        return ComponentOutput(success=True, data={})

    comp_b = MagicMock()
    comp_b.safe_execute = _capture_b

    with patch("flow_executor.get_component", side_effect=[comp_a, comp_b]):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_sequential_flow  # noqa: PLC0415
            asyncio.run(execute_sequential_flow(flow_run, steps, db))

    assert len(captured_b_input) == 1
    assert captured_b_input[0].previous_step_output == a_data
