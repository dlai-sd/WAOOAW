"""Tests for CP BackEnd campaign proxy routes — PLANT-CONTENT-1 Iteration 4, Epic E8.

E8-S1-T1: Mock Plant POST /api/v1/campaigns → 201, CP proxies it
E8-S1-T2: No auth header → 401
E8-S1-T3: Plant unreachable → 502

Run:
    docker compose -f docker-compose.test.yml run cp-test \\
      pytest src/CP/BackEnd/tests/test_campaigns_proxy.py -v \\
      --cov=src/CP/BackEnd/api/campaigns --cov-fail-under=80
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


# ─── Helpers ──────────────────────────────────────────────────────────────────

CAMPAIGN_PAYLOAD = {
    "hired_instance_id": "hired-001",
    "customer_id": "cust-001",
    "brief": {
        "theme": "Hire AI Agents — WAOOAW",
        "start_date": "2026-03-06",
        "duration_days": 7,
        "destinations": [{"destination_type": "simulated"}],
        "schedule": {"times_per_day": 1, "preferred_hours_utc": [9]},
        "brand_name": "WAOOAW",
        "audience": "SMB founders",
        "tone": "inspiring",
        "approval_mode": "per_item",
    },
}

MOCK_CAMPAIGN_RESPONSE = {
    "campaign": {
        "campaign_id": "test-campaign-id",
        "hired_instance_id": "hired-001",
        "customer_id": "cust-001",
        "status": "draft",
        "cost_estimate": {
            "total_theme_items": 7,
            "total_posts": 7,
            "llm_calls": 8,
            "cost_per_call_usd": 0.0,
            "total_cost_usd": 0.0,
            "total_cost_inr": 0.0,
            "model_used": "deterministic",
        },
        "brief": CAMPAIGN_PAYLOAD["brief"],
        "created_at": "2026-03-06T09:00:00Z",
        "updated_at": "2026-03-06T09:00:00Z",
    },
    "theme_items": [],
    "cost_estimate": {
        "total_theme_items": 7,
        "total_posts": 7,
        "llm_calls": 8,
        "cost_per_call_usd": 0.0,
        "total_cost_usd": 0.0,
        "total_cost_inr": 0.0,
        "model_used": "deterministic",
    },
    "message": "Campaign created",
}


def _mock_plant_client(status_code: int, json_body: dict | list) -> AsyncMock:
    """Return an httpx.AsyncClient mock that returns the given response."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body
    mock_response.text = str(json_body)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.patch = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ─── E8-S1-T1: POST /campaigns proxies to Plant and returns 201 ──────────────

@pytest.mark.unit
def test_create_campaign_proxies_to_plant(client, auth_headers, monkeypatch):
    """E8-S1-T1: POST /api/cp/campaigns with valid JWT proxies to Plant and returns 201."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    mock_client = _mock_plant_client(201, MOCK_CAMPAIGN_RESPONSE)

    with patch("api.campaigns.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/api/cp/campaigns",
            json=CAMPAIGN_PAYLOAD,
            headers=auth_headers,
        )

    # CP should forward the 201 from Plant
    assert resp.status_code == 201
    data = resp.json()
    assert "campaign" in data or "campaign_id" in str(data)


# ─── E8-S1-T2: No auth header → 401 ──────────────────────────────────────────

@pytest.mark.unit
def test_create_campaign_without_auth_returns_401(client, monkeypatch):
    """E8-S1-T2: POST /api/cp/campaigns without Authorization → 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    resp = client.post("/api/cp/campaigns", json=CAMPAIGN_PAYLOAD)
    assert resp.status_code == 401


@pytest.mark.unit
def test_get_campaign_without_auth_returns_401(client, monkeypatch):
    """GET /api/cp/campaigns/{id} without Authorization → 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    resp = client.get("/api/cp/campaigns/some-campaign-id")
    assert resp.status_code == 401


@pytest.mark.unit
def test_list_theme_items_without_auth_returns_401(client, monkeypatch):
    """GET /api/cp/campaigns/{id}/theme-items without Authorization → 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    resp = client.get("/api/cp/campaigns/some-campaign-id/theme-items")
    assert resp.status_code == 401


# ─── E8-S1-T3: Plant unreachable → 502 ───────────────────────────────────────

@pytest.mark.unit
def test_create_campaign_plant_unreachable_returns_502(client, auth_headers, monkeypatch):
    """E8-S1-T3: POST /api/cp/campaigns when Plant is unreachable → 502."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    async def _raise_connect_error(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=_raise_connect_error)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.campaigns.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/api/cp/campaigns",
            json=CAMPAIGN_PAYLOAD,
            headers=auth_headers,
        )

    assert resp.status_code == 502


# ─── GET /campaigns/{id} proxies correctly ───────────────────────────────────

@pytest.mark.unit
def test_get_campaign_proxies_to_plant(client, auth_headers, monkeypatch):
    """GET /api/cp/campaigns/{id} proxies to Plant and returns campaign data."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    campaign_data = {
        "campaign_id": "test-campaign-id",
        "status": "draft",
        "hired_instance_id": "hired-001",
        "customer_id": "cust-001",
    }
    mock_client = _mock_plant_client(200, campaign_data)

    with patch("api.campaigns.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/campaigns/test-campaign-id",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    assert resp.json()["campaign_id"] == "test-campaign-id"


# ─── GET /campaigns/{id}/theme-items proxies correctly ───────────────────────

@pytest.mark.unit
def test_list_theme_items_proxies_to_plant(client, auth_headers, monkeypatch):
    """GET /api/cp/campaigns/{id}/theme-items proxies to Plant."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    theme_items_data = [
        {"theme_item_id": "item-001", "day_number": 1, "review_status": "pending_review"}
    ]
    mock_client = _mock_plant_client(200, theme_items_data)

    with patch("api.campaigns.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/campaigns/test-campaign-id/theme-items",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ─── GET /campaigns/{id}/posts proxies correctly ─────────────────────────────

@pytest.mark.unit
def test_list_posts_proxies_to_plant(client, auth_headers, monkeypatch):
    """GET /api/cp/campaigns/{id}/posts proxies to Plant."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    posts_data = [
        {"post_id": "post-001", "review_status": "pending_review", "publish_status": "not_published"}
    ]
    mock_client = _mock_plant_client(200, posts_data)

    with patch("api.campaigns.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/campaigns/test-campaign-id/posts",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ─── PATCH /campaigns/{id}/theme-items/{item_id} proxies correctly ───────────

@pytest.mark.unit
def test_patch_theme_item_proxies_to_plant(client, auth_headers, monkeypatch):
    """PATCH /api/cp/campaigns/{id}/theme-items/{item_id} proxies to Plant."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    patched = {"theme_item_id": "item-001", "review_status": "approved"}
    mock_client = _mock_plant_client(200, patched)

    with patch("api.campaigns.httpx.AsyncClient", return_value=mock_client):
        resp = client.patch(
            "/api/cp/campaigns/test-campaign-id/theme-items/item-001",
            json={"decision": "approved"},
            headers=auth_headers,
        )

    assert resp.status_code == 200


# ─── Router is registered in main.py ─────────────────────────────────────────

@pytest.mark.unit
def test_campaigns_router_registered_in_main():
    """Verify campaigns router is included in the FastAPI app."""
    from main import app
    routes = [r.path for r in app.routes]
    campaign_routes = [r for r in routes if "campaigns" in r]
    assert len(campaign_routes) > 0, "campaigns router must be registered in main.py"
