"""Tests for ops diagnostic routes (E1, E2-S2): construct-health, scheduler-diagnostics,
scheduler pause/resume, and hook-trace."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from core.authorization import require_role


def _make_plant(status_code: int, body):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_resp.text = str(body)
    mock_resp.content = b"ok"
    return SimpleNamespace(_request=AsyncMock(return_value=mock_resp))


def _bypass_role(role: str):
    """Return a lambda that bypasses require_role for the given role name."""
    return lambda: {"sub": "test-user", "roles": [role]}


def _raise_forbidden():
    raise HTTPException(status_code=403, detail="forbidden")


# ---------------------------------------------------------------------------
# GET construct-health
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_construct_health_forbidden_without_role(app, client):
    app.dependency_overrides[require_role("developer")] = _raise_forbidden
    try:
        resp = await client.get("/api/pp/ops/hired-agents/ha-1/construct-health")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_construct_health_ok_for_developer(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"scheduler": "healthy", "pump": "healthy"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        resp = await client.get("/api/pp/ops/hired-agents/ha-1/construct-health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scheduler"] == "healthy"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_construct_health_503_on_plant_error(app, client):
    from clients.plant_client import PlantAPIError, get_plant_client

    plant = SimpleNamespace(_request=AsyncMock(side_effect=PlantAPIError("timeout")))
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        resp = await client.get("/api/pp/ops/hired-agents/ha-1/construct-health")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET scheduler-diagnostics
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_scheduler_diagnostics_forbidden_without_role(app, client):
    app.dependency_overrides[require_role("developer")] = _raise_forbidden
    try:
        resp = await client.get("/api/pp/ops/hired-agents/ha-1/scheduler-diagnostics")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_scheduler_diagnostics_ok(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"cron": "ok", "next_run": "2026-01-01T00:00:00Z"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        resp = await client.get("/api/pp/ops/hired-agents/ha-1/scheduler-diagnostics")
        assert resp.status_code == 200
        assert resp.json()["cron"] == "ok"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST scheduler/pause + scheduler/resume
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_scheduler_pause_forbidden_for_non_admin(app, client):
    app.dependency_overrides[require_role("admin")] = _raise_forbidden
    try:
        resp = await client.post("/api/pp/ops/hired-agents/ha-1/scheduler/pause")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_scheduler_pause_ok_for_admin(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"status": "paused"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        resp = await client.post("/api/pp/ops/hired-agents/ha-1/scheduler/pause")
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_scheduler_resume_forbidden_for_non_admin(app, client):
    app.dependency_overrides[require_role("admin")] = _raise_forbidden
    try:
        resp = await client.post("/api/pp/ops/hired-agents/ha-1/scheduler/resume")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_scheduler_resume_ok_for_admin(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"status": "running"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        resp = await client.post("/api/pp/ops/hired-agents/ha-1/scheduler/resume")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET hook-trace
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_hook_trace_forbidden_without_role(app, client):
    app.dependency_overrides[require_role("developer")] = _raise_forbidden
    try:
        resp = await client.get("/api/pp/ops/hired-agents/ha-1/hook-trace")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_hook_trace_ok(app, client):
    from clients.plant_client import get_plant_client

    events = [
        {
            "event_id": "ev-1",
            "stage": "pre_pump",
            "hired_agent_id": "ha-1",
            "agent_type": "marketing",
            "result": "proceed",
            "reason": "ok",
            "emitted_at": "2026-01-01T00:00:00Z",
            "payload_summary": "x" * 100,
        }
    ]
    plant = _make_plant(200, events)
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        resp = await client.get("/api/pp/ops/hired-agents/ha-1/hook-trace")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert body[0]["event_id"] == "ev-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_hook_trace_forwards_query_params(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [])
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        await client.get(
            "/api/pp/ops/hired-agents/ha-1/hook-trace?stage=pre_pump&result=proceed&limit=10"
        )
        call_kwargs = plant._request.call_args
        params = call_kwargs.kwargs.get("params")
        assert params is not None
        assert params.get("stage") == "pre_pump"
        assert params.get("result") == "proceed"
        assert params.get("limit") == 10
    finally:
        app.dependency_overrides.clear()

