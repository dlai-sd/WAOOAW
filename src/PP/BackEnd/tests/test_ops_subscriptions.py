"""Tests for ops_subscriptions proxy routes (E1-S1)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_plant(status_code: int, body):
    """Return a mock PlantAPIClient whose _request returns a controlled response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_resp.text = str(body)
    plant = SimpleNamespace(_request=AsyncMock(return_value=mock_resp))
    return plant


@pytest.mark.unit
async def test_list_subscriptions_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [{"subscription_id": "sub-1", "status": "active"}])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions?customer_id=C1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["subscription_id"] == "sub-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_subscriptions_forwards_query_params(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        await client.get("/api/pp/ops/subscriptions?customer_id=C1&status=active")
        call_kwargs = plant._request.call_args
        assert call_kwargs.kwargs.get("path").endswith("/by-customer/C1")
        assert call_kwargs.kwargs.get("params") == {"status": "active"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_subscriptions_returns_400_without_customer_id(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions")
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_subscriptions_503_on_plant_error(app, client):
    from clients.plant_client import PlantAPIError, get_plant_client

    plant = SimpleNamespace(_request=AsyncMock(side_effect=PlantAPIError("circuit open")))
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_subscription_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"subscription_id": "sub-1", "status": "active"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions/sub-1")
        assert resp.status_code == 200
        assert resp.json()["subscription_id"] == "sub-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_subscription_passthrough_404(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(404, {"detail": "not found"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions/does-not-exist")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_subscription_uses_payments_path(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"subscription_id": "sub-1", "status": "active"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        await client.get("/api/pp/ops/subscriptions/sub-1")
        call_kwargs = plant._request.call_args
        assert call_kwargs.kwargs.get("path") == "/api/v1/payments/subscriptions/sub-1"
    finally:
        app.dependency_overrides.clear()
