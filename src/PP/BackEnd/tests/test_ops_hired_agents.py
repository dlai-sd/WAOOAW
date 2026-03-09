"""Tests for ops_hired_agents proxy routes (E2-S1)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_plant(status_code: int, body):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_resp.text = str(body)
    return SimpleNamespace(_request=AsyncMock(return_value=mock_resp))


@pytest.mark.unit
async def test_list_hired_agents_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [{"hired_instance_id": "inst-1", "agent_id": "agent-1"}])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents?subscription_id=sub-1")
        assert resp.status_code == 200
        assert resp.json()[0]["hired_instance_id"] == "inst-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agents_forwards_query_params(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [{"hired_instance_id": "inst-1"}])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        await client.get("/api/pp/ops/hired-agents?subscription_id=sub-1")
        call_kwargs = plant._request.call_args
        assert call_kwargs.kwargs.get("path") == "/api/v1/hired-agents/by-subscription/sub-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agents_wraps_single_object_response(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"hired_instance_id": "inst-1", "agent_id": "agent-1"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents?subscription_id=sub-1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["hired_instance_id"] == "inst-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agents_returns_400_without_ids(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents")
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agents_by_customer_id(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [{"hired_instance_id": "inst-2"}])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        await client.get("/api/pp/ops/hired-agents?customer_id=C1")
        call_kwargs = plant._request.call_args
        assert call_kwargs.kwargs.get("path") == "/api/v1/hired-agents/by-customer/C1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agents_503_on_plant_error(app, client):
    from clients.plant_client import PlantAPIError, get_plant_client

    plant = SimpleNamespace(_request=AsyncMock(side_effect=PlantAPIError("timeout")))
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents?subscription_id=sub-1")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_hired_agent_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"hired_instance_id": "inst-1", "agent_id": "agent-1"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/inst-1")
        assert resp.status_code == 200
        assert resp.json()["hired_instance_id"] == "inst-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agent_deliverables_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"hired_instance_id": "inst-1", "deliverables": []})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/inst-1/deliverables")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agent_goals_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"hired_instance_id": "inst-1", "goals": []})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/inst-1/goals")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_hired_agent_deliverables_passthrough_404(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(404, {"detail": "not found"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/missing/deliverables")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
