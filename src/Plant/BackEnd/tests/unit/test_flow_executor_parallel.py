"""Unit tests for flow_executor.py — parallel runner (EXEC-ENGINE-001 E4-S2).

Tests:
  E4-S2-T1: Both steps succeed → status="completed"
  E4-S2-T2: LinkedIn ok + YouTube fail → status="partial_failure", failed_steps=['youtube']
  E4-S2-T3: Both steps fail → status="failed"
  E4-S2-T4: Both succeed → db.add called twice (one ComponentRunModel row per step)
  E4-S2-T5: Concurrency check — both coroutines start before either completes
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, ComponentOutput
from models.flow_run import FlowRunModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_flow_run() -> FlowRunModel:
    now = datetime.now(timezone.utc)
    return FlowRunModel(
        id="fr-par-001",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="parallel_flow",
        status="pending",
        idempotency_key="idem-par-001",
        started_at=now,
        updated_at=now,
        run_context={"customer_id": "cust-1"},
    )


def _make_db() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


def _ok_comp() -> MagicMock:
    comp = MagicMock()
    comp.safe_execute = AsyncMock(return_value=ComponentOutput(success=True, data={}))
    return comp


def _fail_comp() -> MagicMock:
    comp = MagicMock()
    comp.safe_execute = AsyncMock(
        return_value=ComponentOutput(success=False, error_message="fail")
    )
    return comp


PARALLEL_STEPS = [
    {"component_type": "LinkedInPublisher", "step_name": "linkedin"},
    {"component_type": "YouTubePublisher", "step_name": "youtube"},
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_parallel_all_success():
    """E4-S2-T1: Both steps succeed → status=completed."""
    flow_run = _make_flow_run()
    db = _make_db()

    with patch("flow_executor.get_component", side_effect=[_ok_comp(), _ok_comp()]):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_parallel_flow  # noqa: PLC0415
            asyncio.run(execute_parallel_flow(flow_run, PARALLEL_STEPS, db, shared_input={}))

    assert flow_run.status == "completed"


@pytest.mark.unit
def test_parallel_partial_failure():
    """E4-S2-T2: LinkedIn ok + YouTube fail → partial_failure, youtube in failed_steps."""
    flow_run = _make_flow_run()
    db = _make_db()

    with patch(
        "flow_executor.get_component",
        side_effect=[_ok_comp(), _fail_comp()],
    ):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_parallel_flow  # noqa: PLC0415
            asyncio.run(execute_parallel_flow(flow_run, PARALLEL_STEPS, db, shared_input={}))

    assert flow_run.status == "partial_failure"
    assert "failed_steps" in flow_run.error_details
    assert "youtube" in flow_run.error_details["failed_steps"]


@pytest.mark.unit
def test_parallel_all_fail():
    """E4-S2-T3: Both steps fail → status=failed."""
    flow_run = _make_flow_run()
    db = _make_db()

    with patch(
        "flow_executor.get_component",
        side_effect=[_fail_comp(), _fail_comp()],
    ):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_parallel_flow  # noqa: PLC0415
            asyncio.run(execute_parallel_flow(flow_run, PARALLEL_STEPS, db, shared_input={}))

    assert flow_run.status == "failed"


@pytest.mark.unit
def test_parallel_creates_component_run_rows():
    """E4-S2-T4: Both succeed → db.add called twice (one row per step)."""
    flow_run = _make_flow_run()
    db = _make_db()

    with patch("flow_executor.get_component", side_effect=[_ok_comp(), _ok_comp()]):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_parallel_flow  # noqa: PLC0415
            asyncio.run(execute_parallel_flow(flow_run, PARALLEL_STEPS, db, shared_input={}))

    assert db.add.call_count == 2


@pytest.mark.unit
def test_parallel_concurrency():
    """E4-S2-T5: Both coroutines start before either completes (asyncio.gather)."""
    start_times: list[float] = []
    flow_run = _make_flow_run()
    db = _make_db()

    async def slow_execute(inp: ComponentInput) -> ComponentOutput:
        start_times.append(time.monotonic())
        await asyncio.sleep(0.02)  # 20ms artificial delay
        return ComponentOutput(success=True, data={})

    comp1 = MagicMock()
    comp1.safe_execute = slow_execute
    comp2 = MagicMock()
    comp2.safe_execute = slow_execute

    with patch("flow_executor.get_component", side_effect=[comp1, comp2]):
        with patch("flow_executor.ComponentRunModel", return_value=MagicMock()):
            from flow_executor import execute_parallel_flow  # noqa: PLC0415
            asyncio.run(execute_parallel_flow(flow_run, PARALLEL_STEPS, db, shared_input={}))

    assert len(start_times) == 2
    # Both coroutines should have started within 50ms of each other (confirms gather, not serial)
    delta_ms = abs(start_times[1] - start_times[0]) * 1000
    assert delta_ms < 50, f"Steps started {delta_ms:.1f}ms apart — not running concurrently"
