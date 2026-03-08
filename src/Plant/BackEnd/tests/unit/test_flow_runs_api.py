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

from api.v1.flow_runs import router
from models.flow_run import FlowRunModel


# ---------------------------------------------------------------------------
# Minimal isolated app
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(router)


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
