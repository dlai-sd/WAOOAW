"""Unit tests for ComponentRunModel (EXEC-ENGINE-001 E1-S2).

Tests model instantiation, field defaults, status values, and FK
declaration — no live database connection required.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest tests/unit/test_component_run_model.py -v --cov=models --cov-fail-under=80
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models.component_run import ComponentRunModel, COMPONENT_RUN_STATUSES


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_component_run(
    id: str = "cr-001",
    flow_run_id: str = "fr-001",
    component_type: str = "pump",
    step_name: str = "fetch_candles",
    status: str = "pending",
) -> ComponentRunModel:
    now = datetime.now(timezone.utc)
    return ComponentRunModel(
        id=id,
        flow_run_id=flow_run_id,
        component_type=component_type,
        step_name=step_name,
        status=status,
        started_at=now,
    )


# ── E1-S2-T1: Create ComponentRunModel with a parent flow_run_id ─────────────

@pytest.mark.unit
def test_component_run_model_basic_fields():
    """E1-S2-T1: ComponentRunModel has correct fields after instantiation."""
    run = _make_component_run()
    assert run.id == "cr-001"
    assert run.flow_run_id == "fr-001"
    assert run.component_type == "pump"
    assert run.step_name == "fetch_candles"
    assert run.status == "pending"
    assert run.output is None
    assert run.duration_ms is None
    assert run.error_message is None
    assert run.completed_at is None


# ── E1-S2-T2: Completed run stores output and duration_ms ────────────────────

@pytest.mark.unit
def test_component_run_model_completed_fields():
    """E1-S2-T2: status='completed', output and duration_ms are persisted."""
    now = datetime.now(timezone.utc)
    run = ComponentRunModel(
        id="cr-002",
        flow_run_id="fr-001",
        component_type="pump",
        step_name="fetch_candles",
        status="completed",
        started_at=now,
        completed_at=now,
        output={"candles": []},
        duration_ms=120,
    )
    assert run.status == "completed"
    assert run.output == {"candles": []}
    assert run.duration_ms == 120
    assert run.completed_at is not None


# ── E1-S2-T3: Failed run stores error_message ────────────────────────────────

@pytest.mark.unit
def test_component_run_model_failed_fields():
    """E1-S2-T3: status='failed' and error_message are persisted."""
    now = datetime.now(timezone.utc)
    run = ComponentRunModel(
        id="cr-003",
        flow_run_id="fr-001",
        component_type="pump",
        step_name="fetch_candles",
        status="failed",
        started_at=now,
        error_message="timeout",
    )
    assert run.status == "failed"
    assert run.error_message == "timeout"


# ── E1-S2-T4: FK to flow_runs is declared ────────────────────────────────────

@pytest.mark.unit
def test_component_run_model_fk_declared():
    """E1-S2-T4: ForeignKey to flow_runs.id is declared on flow_run_id column."""
    col = ComponentRunModel.__table__.c["flow_run_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "flow_runs.id" in fk_targets


@pytest.mark.unit
def test_component_run_model_tablename():
    """ComponentRunModel.__tablename__ == 'component_runs'."""
    assert ComponentRunModel.__tablename__ == "component_runs"


@pytest.mark.unit
def test_component_run_model_repr():
    """ComponentRunModel __repr__ includes expected fields."""
    run = _make_component_run()
    r = repr(run)
    assert "cr-001" in r
    assert "fr-001" in r
    assert "pump" in r
    assert "pending" in r


@pytest.mark.unit
@pytest.mark.parametrize("status", COMPONENT_RUN_STATUSES)
def test_component_run_model_all_statuses(status: str):
    """All 4 component run statuses are assignable."""
    run = _make_component_run(status=status)
    assert run.status == status
