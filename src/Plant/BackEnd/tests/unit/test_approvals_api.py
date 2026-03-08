"""Unit tests for approvals endpoints (EXEC-ENGINE-001 E8-S2).

Tests:
  E8-S2-T1: Create FlowRunModel with status="awaiting_approval",
             call POST /approvals/{id}/approve
             → HTTP 200, DB row status="running", run_context["auto_execute"]=True
  E8-S2-T2: Create row with status="awaiting_approval", call /reject
             → HTTP 200, DB row status="failed", error_details["reason"]="customer_rejected"
  E8-S2-T3: Call approve on flow_run.status="running" (not awaiting)
             → HTTP 409
  E8-S2-T4: Call reject on flow_run.status="completed"
             → HTTP 409
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.approvals import router
from models.flow_run import FlowRunModel


# ---------------------------------------------------------------------------
# Minimal isolated app
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(router)


def _db_with_row(row: FlowRunModel | None):
    """Mock AsyncSession that returns *row* from execute()."""
    db = AsyncMock()
    db.commit = AsyncMock()

    async def _execute(stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = row
        return result

    db.execute = _execute
    return db


def _make_flow_run(status: str, run_context: dict | None = None) -> FlowRunModel:
    now = datetime.now(timezone.utc)
    return FlowRunModel(
        id="fr-approval-001",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="ContentCreationFlow",
        status=status,
        run_context=run_context or {},
        idempotency_key="idem-appr-001",
        started_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_approve_awaiting_flow_run():
    """E8-S2-T1: Approve awaiting_approval run → 200, status=running, auto_execute=True."""
    from core.database import get_db_session

    row = _make_flow_run(status="awaiting_approval", run_context={"skill_id": "s1"})
    _app.dependency_overrides[get_db_session] = lambda: _db_with_row(row)

    with TestClient(_app) as client:
        resp = client.post(
            "/approvals/fr-approval-001/approve",
            headers={"X-Correlation-ID": "test-appr-001"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert row.status == "running"
    assert row.run_context.get("auto_execute") is True


@pytest.mark.unit
def test_reject_awaiting_flow_run():
    """E8-S2-T2: Reject awaiting_approval run → 200, status=failed, reason=customer_rejected."""
    from core.database import get_db_session

    row = _make_flow_run(status="awaiting_approval")
    _app.dependency_overrides[get_db_session] = lambda: _db_with_row(row)

    with TestClient(_app) as client:
        resp = client.post(
            "/approvals/fr-approval-001/reject",
            headers={"X-Correlation-ID": "test-appr-002"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert row.status == "failed"
    assert row.error_details == {"reason": "customer_rejected"}


@pytest.mark.unit
def test_approve_already_running_returns_409():
    """E8-S2-T3: Approve a run not in awaiting_approval → HTTP 409."""
    from core.database import get_db_session

    row = _make_flow_run(status="running")
    _app.dependency_overrides[get_db_session] = lambda: _db_with_row(row)

    with TestClient(_app) as client:
        resp = client.post(
            "/approvals/fr-approval-001/approve",
            headers={"X-Correlation-ID": "test-appr-003"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 409


@pytest.mark.unit
def test_reject_completed_run_returns_409():
    """E8-S2-T4: Reject a completed run → HTTP 409."""
    from core.database import get_db_session

    row = _make_flow_run(status="completed")
    _app.dependency_overrides[get_db_session] = lambda: _db_with_row(row)

    with TestClient(_app) as client:
        resp = client.post(
            "/approvals/fr-approval-001/reject",
            headers={"X-Correlation-ID": "test-appr-004"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 409


@pytest.mark.unit
def test_approve_not_found_returns_409():
    """Approve a non-existent flow run → HTTP 409 (row is None)."""
    from core.database import get_db_session

    _app.dependency_overrides[get_db_session] = lambda: _db_with_row(None)

    with TestClient(_app) as client:
        resp = client.post(
            "/approvals/does-not-exist/approve",
            headers={"X-Correlation-ID": "test-appr-005"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 409
