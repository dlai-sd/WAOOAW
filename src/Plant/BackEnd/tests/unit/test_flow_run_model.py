"""Unit tests for FlowRunModel (EXEC-ENGINE-001 E1-S1).

Tests model instantiation, default values, status transitions, and constraint
declarations — no live database connection required.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest tests/unit/test_flow_run_model.py -v --cov=models --cov-fail-under=80
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models.flow_run import FlowRunModel, FLOW_RUN_STATUSES


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_flow_run(
    id: str = "fr-001",
    hired_instance_id: str = "hired-001",
    skill_id: str = "skill-001",
    flow_name: str = "share_trader_flow",
    status: str = "pending",
    idempotency_key: str = "fr-idem-001",
) -> FlowRunModel:
    now = datetime.now(timezone.utc)
    return FlowRunModel(
        id=id,
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        flow_name=flow_name,
        status=status,
        idempotency_key=idempotency_key,
        started_at=now,
        updated_at=now,
    )


# ── E1-S1-T1: Create FlowRunModel with status "pending" ──────────────────────

@pytest.mark.unit
def test_flow_run_model_default_status():
    """E1-S1-T1: FlowRunModel can be instantiated with status='pending'."""
    run = _make_flow_run()
    assert run.id == "fr-001"
    assert run.hired_instance_id == "hired-001"
    assert run.skill_id == "skill-001"
    assert run.flow_name == "share_trader_flow"
    assert run.status == "pending"
    assert run.idempotency_key == "fr-idem-001"
    assert run.completed_at is None
    assert run.error_details is None
    assert run.current_step is None


# ── E1-S1-T2: All 6 status values accepted ───────────────────────────────────

@pytest.mark.unit
@pytest.mark.parametrize("status", FLOW_RUN_STATUSES)
def test_flow_run_model_all_statuses(status: str):
    """E1-S1-T2: All 6 statuses in FLOW_RUN_STATUSES can be assigned."""
    run = _make_flow_run(status=status)
    assert run.status == status


# ── E1-S1-T3: idempotency_key uniqueness is declared ─────────────────────────

@pytest.mark.unit
def test_flow_run_model_idempotency_key_unique_declared():
    """E1-S1-T3: UniqueConstraint on idempotency_key is declared in __table_args__."""
    table_args = FlowRunModel.__table_args__
    # The unique constraint may be on the column itself or in __table_args__
    # Check that idempotency_key column has unique=True OR a UniqueConstraint exists
    col = FlowRunModel.__table__.c["idempotency_key"]
    table_arg_names = {getattr(arg, "name", "") for arg in table_args}
    assert col.unique or "uq_flow_runs_idempotency_key" in table_arg_names


@pytest.mark.unit
def test_flow_run_model_tablename():
    """FlowRunModel.__tablename__ == 'flow_runs'."""
    assert FlowRunModel.__tablename__ == "flow_runs"


@pytest.mark.unit
def test_flow_run_model_repr():
    """FlowRunModel __repr__ includes expected fields."""
    run = _make_flow_run()
    r = repr(run)
    assert "fr-001" in r
    assert "hired-001" in r
    assert "pending" in r


@pytest.mark.unit
def test_flow_run_statuses_tuple_length():
    """FLOW_RUN_STATUSES contains exactly 6 entries."""
    assert len(FLOW_RUN_STATUSES) == 6


@pytest.mark.unit
def test_flow_run_model_with_run_context():
    """FlowRunModel accepts run_context dict."""
    now = datetime.now(timezone.utc)
    run = FlowRunModel(
        id="fr-002",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="test_flow",
        status="running",
        idempotency_key="fr-idem-002",
        started_at=now,
        updated_at=now,
        run_context={"symbol": "BTCUSD", "quantity": 1},
    )
    assert run.run_context == {"symbol": "BTCUSD", "quantity": 1}


@pytest.mark.unit
def test_flow_run_model_error_details_field():
    """FlowRunModel.error_details can store a dict."""
    now = datetime.now(timezone.utc)
    run = FlowRunModel(
        id="fr-003",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="test_flow",
        status="failed",
        idempotency_key="fr-idem-003",
        started_at=now,
        updated_at=now,
        error_details={"message": "timeout"},
    )
    assert run.error_details == {"message": "timeout"}
