"""Tests for ops DLQ routes (E2-S1): list DLQ entries + requeue."""

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
    return lambda: {"sub": "test-user", "roles": [role]}


def _raise_forbidden():
    raise HTTPException(status_code=403, detail="forbidden")


# ---------------------------------------------------------------------------
# GET /pp/ops/dlq
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_list_dlq_forbidden_for_viewer(app, client):
    app.dependency_overrides[require_role("developer")] = _raise_forbidden
    try:
        resp = await client.get("/api/pp/ops/dlq")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_dlq_ok_for_developer(app, client):
    from clients.plant_client import get_plant_client

    entries = [
        {
            "dlq_id": "dlq-1",
            "hired_agent_id": "ha-1",
            "failed_at": "2026-01-01T00:00:00Z",
            "hook_stage": "pre_pump",
            "error_message": "timeout",
            "retry_count": 3,
        }
    ]
    plant = _make_plant(200, entries)
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        resp = await client.get("/api/pp/ops/dlq")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert body[0]["dlq_id"] == "dlq-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_dlq_forwards_filters(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [])
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        await client.get("/api/pp/ops/dlq?agent_type=marketing&hired_agent_id=ha-1&limit=20")
        call_kwargs = plant._request.call_args
        params = call_kwargs.kwargs.get("params") or {}
        assert params.get("agent_type") == "marketing"
        assert params.get("hired_agent_id") == "ha-1"
        assert params.get("limit") == 20
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_dlq_503_on_plant_error(app, client):
    from clients.plant_client import PlantAPIError, get_plant_client

    plant = SimpleNamespace(_request=AsyncMock(side_effect=PlantAPIError("timeout")))
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        resp = await client.get("/api/pp/ops/dlq")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /pp/ops/dlq/{id}/requeue
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_requeue_forbidden_for_developer(app, client):
    app.dependency_overrides[require_role("admin")] = _raise_forbidden
    try:
        resp = await client.post("/api/pp/ops/dlq/dlq-1/requeue")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_requeue_ok_for_admin(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"status": "queued", "dlq_id": "dlq-1"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        resp = await client.post("/api/pp/ops/dlq/dlq-1/requeue")
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_requeue_503_on_plant_error(app, client):
    from clients.plant_client import PlantAPIError, get_plant_client

    plant = SimpleNamespace(_request=AsyncMock(side_effect=PlantAPIError("plant down")))
    app.dependency_overrides[get_plant_client] = lambda: plant
    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        resp = await client.post("/api/pp/ops/dlq/dlq-1/requeue")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()

