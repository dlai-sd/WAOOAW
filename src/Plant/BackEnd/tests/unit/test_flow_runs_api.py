"""Unit tests for POST /flow-runs + GET /flow-runs/{id} (EXEC-ENGINE-001 E6-S1).

Uses FastAPI TestClient with overridden DB dependencies (no live Postgres).

Tests:
  E6-S1-T1: POST flow_name="MarketAnalysisFlow" → 201, id + status="pending"
  E6-S1-T2: POST unknown flow_name → 400
  E6-S1-T3: GET /{id} existing → 200 with status and current_step
  E6-S1-T4: GET /{id} unknown → 404
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.flow_runs import component_runs_router, router, skill_runs_router
from models.flow_run import FlowRunModel


# ---------------------------------------------------------------------------
# Minimal isolated app
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(router)
_app.include_router(skill_runs_router)
_app.include_router(component_runs_router)


def _null_db():
    """Mock DB session — add/commit/refresh are no-ops; execute returns empty."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def _execute(stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        return result

    db.execute = _execute
    return db


def _db_with_row(row: FlowRunModel):
    """Mock DB session that returns *row* from execute()."""
    db = AsyncMock()

    async def _execute(stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = row
        return result

    db.execute = _execute
    return db


def _db_with_rows(rows: list[FlowRunModel]):
    db = AsyncMock()

    async def _execute(stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        return result

    db.execute = _execute
    return db


def _db_with_component_rows(flow_row: FlowRunModel, component_rows: list[dict]):
    db = AsyncMock()
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            result.scalar_one_or_none.return_value = flow_row
        else:
            result.scalars.return_value.all.return_value = component_rows
        call_count += 1
        return result

    db.execute = _execute
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_create_flow_run_valid():
    """E6-S1-T1: POST valid flow → 201, response has id and status=pending."""
    from core.database import get_db_session

    _app.dependency_overrides[get_db_session] = _null_db

    with patch("api.v1.flow_runs.execute_sequential_flow", new_callable=MagicMock):
        with TestClient(_app) as client:
            resp = client.post(
                "/flow-runs/",
                json={
                    "hired_instance_id": "hired-001",
                    "flow_name": "MarketAnalysisFlow",
                    "run_context": {"skill_id": "skill-001"},
                },
                headers={"X-Correlation-ID": "test-corr-001"},
            )
    _app.dependency_overrides.clear()

    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["status"] == "pending"


@pytest.mark.unit
def test_create_flow_run_unknown_flow():
    """E6-S1-T2: POST with unknown flow_name → 400."""
    from core.database import get_db_session

    _app.dependency_overrides[get_db_session] = _null_db

    with TestClient(_app) as client:
        resp = client.post(
            "/flow-runs/",
            json={
                "hired_instance_id": "hired-001",
                "flow_name": "NoSuchFlow",
                "run_context": {},
            },
            headers={"X-Correlation-ID": "test-corr-002"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 400


@pytest.mark.unit
def test_get_flow_run_found():
    """E6-S1-T3: GET existing id → 200 with status and current_step."""
    from core.database import get_read_db_session

    now = datetime.now(timezone.utc)
    fake_row = FlowRunModel(
        id="fr-found-001",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="MarketAnalysisFlow",
        status="running",
        current_step="step_1",
        idempotency_key="idem-found-001",
        started_at=now,
        updated_at=now,
        run_context={},
    )

    _app.dependency_overrides[get_read_db_session] = lambda: _db_with_row(fake_row)

    with TestClient(_app) as client:
        resp = client.get(
            "/flow-runs/fr-found-001",
            headers={"X-Correlation-ID": "test-corr-003"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "running"
    assert body["current_step"] == "step_1"


@pytest.mark.unit
def test_get_flow_run_not_found():
    """E6-S1-T4: GET unknown id → 404."""
    from core.database import get_read_db_session

    _app.dependency_overrides[get_read_db_session] = _null_db

    with TestClient(_app) as client:
        resp = client.get(
            "/flow-runs/does-not-exist-999",
            headers={"X-Correlation-ID": "test-corr-004"},
        )
    _app.dependency_overrides.clear()

    assert resp.status_code == 404


@pytest.mark.unit
def test_list_flow_runs_filters_by_customer_id():
    """GET /flow-runs filters the backing store by run_context.customer_id."""
    from core.database import get_read_db_session

    now = datetime.now(timezone.utc)
    mine = FlowRunModel(
        id="fr-mine-001",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="MarketAnalysisFlow",
        status="completed",
        current_step="done",
        idempotency_key="idem-mine-001",
        started_at=now,
        updated_at=now,
        run_context={"customer_id": "cust-1"},
    )
    other = FlowRunModel(
        id="fr-other-001",
        hired_instance_id="hired-002",
        skill_id="skill-002",
        flow_name="MarketAnalysisFlow",
        status="running",
        current_step="step_1",
        idempotency_key="idem-other-001",
        started_at=now,
        updated_at=now,
        run_context={"customer_id": "cust-2"},
    )

    _app.dependency_overrides[get_read_db_session] = lambda: _db_with_rows([mine, other])

    with TestClient(_app) as client:
        resp = client.get("/flow-runs?customer_id=cust-1")
    _app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert [row["id"] for row in data] == ["fr-mine-001"]


@pytest.mark.unit
def test_list_component_runs_returns_rows_for_parent_flow():
    """GET /flow-runs/component-runs returns component trace rows for the parent flow run."""
    from core.database import get_read_db_session

    now = datetime.now(timezone.utc)
    flow_row = FlowRunModel(
        id="fr-1",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="MarketAnalysisFlow",
        status="completed",
        current_step="done",
        idempotency_key="idem-1",
        started_at=now,
        updated_at=now,
        run_context={"customer_id": "cust-1"},
    )
    component = MagicMock()
    component.id = "cr-1"
    component.flow_run_id = "fr-1"
    component.component_type = "Pump"
    component.step_name = "pump"
    component.status = "completed"
    component.input_context = {"goal": "x"}
    component.output = {"draft": "ok"}
    component.duration_ms = 42
    component.started_at = now
    component.completed_at = now
    component.error_message = None

    _app.dependency_overrides[get_read_db_session] = lambda: _db_with_component_rows(flow_row, [component])

    with TestClient(_app) as client:
        resp = client.get("/flow-runs/component-runs?flow_run_id=fr-1")
    _app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "cr-1"


@pytest.mark.unit
def test_component_runs_alias_returns_rows_for_parent_flow():
    """GET /component-runs shares the same backing implementation as /flow-runs/component-runs."""
    from core.database import get_read_db_session

    now = datetime.now(timezone.utc)
    flow_row = FlowRunModel(
        id="fr-1",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="MarketAnalysisFlow",
        status="completed",
        current_step="done",
        idempotency_key="idem-1",
        started_at=now,
        updated_at=now,
        run_context={"customer_id": "cust-1"},
    )
    component = MagicMock()
    component.id = "cr-1"
    component.flow_run_id = "fr-1"
    component.component_type = "Pump"
    component.step_name = "pump"
    component.status = "completed"
    component.input_context = {"goal": "x"}
    component.output = {"draft": "ok"}
    component.duration_ms = 42
    component.started_at = now
    component.completed_at = now
    component.error_message = None

    _app.dependency_overrides[get_read_db_session] = lambda: _db_with_component_rows(flow_row, [component])

    with TestClient(_app) as client:
        resp = client.get("/component-runs?flow_run_id=fr-1")
    _app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "cr-1"


@pytest.mark.unit
def test_skill_runs_aliases_share_flow_run_backing_store():
    """POST/GET skill-runs aliases stay wired to the existing flow_runs storage."""
    from core.database import get_db_session, get_read_db_session

    now = datetime.now(timezone.utc)
    fake_row = FlowRunModel(
        id="fr-skill-001",
        hired_instance_id="hired-001",
        skill_id="skill-001",
        flow_name="MarketAnalysisFlow",
        status="running",
        current_step="step_1",
        idempotency_key="idem-skill-001",
        started_at=now,
        updated_at=now,
        run_context={"customer_id": "cust-1"},
    )

    _app.dependency_overrides[get_db_session] = _null_db
    _app.dependency_overrides[get_read_db_session] = lambda: _db_with_row(fake_row)

    with patch("api.v1.flow_runs.execute_sequential_flow", new_callable=MagicMock):
        with TestClient(_app) as client:
            create_resp = client.post(
                "/skill-runs",
                json={
                    "hired_instance_id": "hired-001",
                    "flow_name": "MarketAnalysisFlow",
                    "run_context": {"skill_id": "skill-001", "customer_id": "cust-1"},
                },
            )
            get_resp = client.get("/skill-runs/fr-skill-001")
    _app.dependency_overrides.clear()

    assert create_resp.status_code == 201
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == "fr-skill-001"
    assert get_resp.json()["customer_id"] == "cust-1"
