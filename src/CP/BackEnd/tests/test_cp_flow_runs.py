"""Tests for CP BackEnd flow-run + component-run proxy routes — EXEC-ENGINE-001 Iteration 6, E14-S2.

E14-S2-T1: GET /cp/flow-runs authenticated → proxied list returned
E14-S2-T2: GET /cp/flow-runs/{id} where customer_id ≠ user → 403 Forbidden
E14-S2-T3: POST /cp/approvals/{id}/approve where customer_id ≠ user → 403 Forbidden
E14-S2-T4: Unauthenticated request to any route → 401 Unauthorized
E14-S2-T5: GET /cp/component-runs?flow_run_id=X — customer owns the flow run → proxied list returned
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _mock_httpx_get(responses: list[tuple[int, dict | list]]) -> AsyncMock:
    """Return an httpx.AsyncClient mock that returns given responses in sequence for GET."""
    call_count = 0
    mock_responses = []
    for status_code, body in responses:
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = status_code
        mock_resp.json.return_value = body
        mock_resp.text = str(body)
        mock_responses.append(mock_resp)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def _get_side_effect(*args, **kwargs):
        nonlocal call_count
        resp = mock_responses[min(call_count, len(mock_responses) - 1)]
        call_count += 1
        return resp

    mock_client.get = AsyncMock(side_effect=_get_side_effect)
    mock_client.post = AsyncMock(
        return_value=_make_response(200, {"status": "ok"})
    )
    return mock_client


def _make_response(status_code: int, body: dict | list) -> MagicMock:
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_resp.text = str(body)
    return mock_resp


MOCK_FLOW_RUNS = [
    {"id": "fr-1", "customer_id": "user-abc", "status": "completed"},
    {"id": "fr-2", "customer_id": "user-abc", "status": "running"},
]

MOCK_COMPONENT_RUNS = [
    {"id": "cr-1", "flow_run_id": "fr-1", "step_name": "Pump", "status": "completed"},
]


# ─── E14-S2-T4: Unauthenticated requests return 401 ──────────────────────────

@pytest.mark.unit
def test_list_flow_runs_requires_auth(client, monkeypatch):
    """GET /cp/flow-runs without auth returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.get("/api/cp/flow-runs")
    assert resp.status_code == 401


@pytest.mark.unit
def test_get_flow_run_requires_auth(client, monkeypatch):
    """GET /cp/flow-runs/{id} without auth returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.get("/api/cp/flow-runs/fr-1")
    assert resp.status_code == 401


@pytest.mark.unit
def test_approve_flow_run_requires_auth(client, monkeypatch):
    """POST /cp/approvals/{id}/approve without auth returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.post("/api/cp/approvals/fr-1/approve")
    assert resp.status_code == 401


@pytest.mark.unit
def test_reject_flow_run_requires_auth(client, monkeypatch):
    """POST /cp/approvals/{id}/reject without auth returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.post("/api/cp/approvals/fr-1/reject")
    assert resp.status_code == 401


@pytest.mark.unit
def test_list_component_runs_requires_auth(client, monkeypatch):
    """GET /cp/component-runs without auth returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.get("/api/cp/component-runs?flow_run_id=fr-1")
    assert resp.status_code == 401


# ─── E14-S2-T1: GET /cp/flow-runs proxies list ───────────────────────────────

@pytest.mark.unit
def test_list_flow_runs_proxies_to_plant(client, auth_headers, monkeypatch):
    """GET /cp/flow-runs with auth proxies to Plant and returns flow runs list."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    mock_client = _mock_httpx_get([(200, MOCK_FLOW_RUNS)])

    with patch("api.cp_flow_runs.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/flow-runs", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ─── E14-S2-T2: GET /cp/flow-runs/{id} ownership check → 403 ────────────────

@pytest.mark.unit
def test_get_flow_run_returns_403_when_not_owner(client, auth_headers, monkeypatch):
    """GET /cp/flow-runs/{id} returns 403 when customer_id does not match user."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    # Flow run owned by a different customer
    other_user_flow_run = {"id": "fr-1", "customer_id": "other-user-999", "status": "completed"}
    mock_client = _mock_httpx_get([(200, other_user_flow_run)])

    with patch("api.cp_flow_runs.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/flow-runs/fr-1", headers=auth_headers)

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Access denied"


@pytest.mark.unit
def test_get_flow_run_returns_200_when_owner(client, auth_headers, monkeypatch):
    """GET /cp/flow-runs/{id} returns 200 when customer_id matches user."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    owned_flow_run = {"id": "fr-1", "customer_id": user_id, "status": "completed"}
    mock_client = _mock_httpx_get([(200, owned_flow_run)])

    with patch("api.cp_flow_runs.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/flow-runs/fr-1", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["id"] == "fr-1"


# ─── E14-S2-T3: POST /cp/approvals/{id}/approve ownership check → 403 ────────

@pytest.mark.unit
def test_approve_flow_run_returns_403_when_not_owner(client, auth_headers, monkeypatch):
    """POST /cp/approvals/{id}/approve returns 403 when customer_id does not match user."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    other_user_flow_run = {"id": "fr-1", "customer_id": "other-user-999", "status": "awaiting_approval"}
    mock_client = _mock_httpx_get([(200, other_user_flow_run)])

    with patch("api.cp_flow_runs.httpx.AsyncClient", return_value=mock_client):
        resp = client.post("/api/cp/approvals/fr-1/approve", headers=auth_headers)

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Access denied"


@pytest.mark.unit
def test_reject_flow_run_returns_403_when_not_owner(client, auth_headers, monkeypatch):
    """POST /cp/approvals/{id}/reject returns 403 when customer_id does not match user."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    other_user_flow_run = {"id": "fr-1", "customer_id": "other-user-999", "status": "awaiting_approval"}
    mock_client = _mock_httpx_get([(200, other_user_flow_run)])

    with patch("api.cp_flow_runs.httpx.AsyncClient", return_value=mock_client):
        resp = client.post("/api/cp/approvals/fr-1/reject", headers=auth_headers)

    assert resp.status_code == 403


# ─── E14-S2-T5: GET /cp/component-runs owned flow → proxied list ─────────────

@pytest.mark.unit
def test_list_component_runs_proxies_when_owner(client, auth_headers, monkeypatch):
    """GET /cp/component-runs?flow_run_id=X returns component runs when user owns the flow run."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    owned_flow_run = {"id": "fr-1", "customer_id": user_id, "status": "completed"}
    mock_client = _mock_httpx_get(
        [(200, owned_flow_run), (200, MOCK_COMPONENT_RUNS)]
    )

    with patch("api.cp_flow_runs.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/component-runs?flow_run_id=fr-1", headers=auth_headers)

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.unit
def test_list_component_runs_returns_403_when_not_owner(client, auth_headers, monkeypatch):
    """GET /cp/component-runs returns 403 when user does not own the flow run."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    other_user_flow_run = {"id": "fr-1", "customer_id": "other-user-999", "status": "completed"}
    mock_client = _mock_httpx_get([(200, other_user_flow_run)])

    with patch("api.cp_flow_runs.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/component-runs?flow_run_id=fr-1", headers=auth_headers)

    assert resp.status_code == 403


# ─── 503 when PLANT_GATEWAY_URL is missing ────────────────────────────────────

@pytest.mark.unit
def test_list_flow_runs_returns_503_when_plant_url_missing(client, auth_headers, monkeypatch):
    """GET /cp/flow-runs returns 503 when PLANT_GATEWAY_URL is not configured."""
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)
    resp = client.get("/api/cp/flow-runs", headers=auth_headers)
    assert resp.status_code == 503


# ─── Router registration ──────────────────────────────────────────────────────

@pytest.mark.unit
def test_cp_flow_runs_router_registered_in_main():
    """Verify cp_flow_runs router is included in the FastAPI app."""
    from main import app
    routes = [r.path for r in app.routes]
    flow_run_routes = [r for r in routes if "/cp/flow-runs" in r or "/cp/component-runs" in r or "/cp/approvals" in r]
    assert len(flow_run_routes) > 0, "cp_flow_runs router must be registered in main.py"
