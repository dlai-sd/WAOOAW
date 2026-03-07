"""Tests for CP BackEnd approval-queue proxy routes — CP-MOULD-1 Iteration 1, Epic E2.

E2-S1: GET /cp/hired-agents/{id}/approval-queue
E2-S2: POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/approve
       POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/reject

Run:
    pytest src/CP/BackEnd/tests/test_cp_approvals_proxy.py -v
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _mock_plant_http(status_code: int, json_body: dict | list) -> AsyncMock:
    """Return an httpx.AsyncClient mock that returns the given response."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body
    mock_response.text = str(json_body)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.patch = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


PENDING_DELIVERABLES = [
    {
        "deliverable_id": "dlv-001",
        "hired_agent_id": "ha-1",
        "status": "pending_review",
        "title": "Draft post for Monday",
    }
]

# ─── E2-S1: GET approval-queue ────────────────────────────────────────────────

@pytest.mark.unit
def test_approval_queue_requires_auth(client, monkeypatch):
    """GET /approval-queue without Authorization header returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.get("/api/cp/hired-agents/ha-1/approval-queue")
    assert resp.status_code == 401


@pytest.mark.unit
def test_approval_queue_proxies_to_plant(client, monkeypatch):
    """GET /approval-queue with auth returns pending deliverables."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    mock_client = _mock_plant_http(200, PENDING_DELIVERABLES)

    with patch("api.cp_approvals_proxy.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/hired-agents/ha-1/approval-queue",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["deliverable_id"] == "dlv-001"


@pytest.mark.unit
def test_approval_queue_missing_plant_url_returns_503(client, monkeypatch):
    """GET /approval-queue when PLANT_GATEWAY_URL is missing returns 503."""
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)
    resp = client.get(
        "/api/cp/hired-agents/ha-1/approval-queue",
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 503


@pytest.mark.unit
def test_approval_queue_plant_unreachable_returns_502(client, monkeypatch):
    """GET /approval-queue when Plant is unreachable returns 502."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_approvals_proxy.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/hired-agents/ha-1/approval-queue",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 502


# ─── E2-S2: POST approve ──────────────────────────────────────────────────────

@pytest.mark.unit
def test_approve_deliverable_requires_auth(client, monkeypatch):
    """POST .../approve without Authorization header returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.post("/api/cp/hired-agents/ha-1/approval-queue/dlv-001/approve")
    assert resp.status_code == 401


@pytest.mark.unit
def test_approve_deliverable_proxies_to_plant(client, monkeypatch):
    """POST .../approve with auth returns 200 and patches Plant deliverable status to approved."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    approve_response = {"deliverable_id": "dlv-001", "status": "approved"}
    mock_client = _mock_plant_http(200, approve_response)

    with patch("api.cp_approvals_proxy.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/api/cp/hired-agents/ha-1/approval-queue/dlv-001/approve",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # Verify Plant was called with correct body
    call_kwargs = mock_client.patch.call_args
    assert call_kwargs is not None
    body_sent = call_kwargs.kwargs.get("json", {})
    assert body_sent.get("status") == "approved"
    assert body_sent.get("hired_agent_id") == "ha-1"


# ─── E2-S2: POST reject ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_reject_deliverable_requires_auth(client, monkeypatch):
    """POST .../reject without Authorization header returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.post("/api/cp/hired-agents/ha-1/approval-queue/dlv-001/reject")
    assert resp.status_code == 401


@pytest.mark.unit
def test_reject_deliverable_proxies_to_plant(client, monkeypatch):
    """POST .../reject with auth returns 200 and patches Plant deliverable status to rejected."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    reject_response = {"deliverable_id": "dlv-001", "status": "rejected"}
    mock_client = _mock_plant_http(200, reject_response)

    with patch("api.cp_approvals_proxy.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/api/cp/hired-agents/ha-1/approval-queue/dlv-001/reject",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    # Verify Plant was called with correct body
    call_kwargs = mock_client.patch.call_args
    assert call_kwargs is not None
    body_sent = call_kwargs.kwargs.get("json", {})
    assert body_sent.get("status") == "rejected"
    assert body_sent.get("hired_agent_id") == "ha-1"


# ─── Router registration ──────────────────────────────────────────────────────

@pytest.mark.unit
def test_cp_approvals_proxy_router_registered_in_main():
    """Verify cp_approvals_proxy router is included in the FastAPI app."""
    from main import app
    routes = [r.path for r in app.routes]
    approval_routes = [r for r in routes if "approval-queue" in r]
    assert len(approval_routes) > 0, "cp_approvals_proxy router must be registered in main.py"
