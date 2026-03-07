"""Tests for CP BackEnd scheduler proxy routes — CP-MOULD-1 Iteration 1, Epic E1.

E1-S1: GET /cp/hired-agents/{id}/scheduler-summary + GET /cp/hired-agents/{id}/trial-budget
E1-S2: POST /cp/hired-agents/{id}/pause + POST /cp/hired-agents/{id}/resume

Run:
    pytest src/CP/BackEnd/tests/test_cp_scheduler.py -v
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
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ─── E1-S1: scheduler-summary ─────────────────────────────────────────────────

@pytest.mark.unit
def test_scheduler_summary_requires_auth(client, monkeypatch):
    """GET /scheduler-summary without Authorization header returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.get("/api/cp/hired-agents/ha-1/scheduler-summary")
    assert resp.status_code == 401


@pytest.mark.unit
def test_scheduler_summary_proxies_to_plant(client, monkeypatch):
    """GET /scheduler-summary with auth forwards to Plant and returns 200."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    scheduler_data = {"scheduler": "ok", "next_run": "2026-03-07T10:00:00Z"}
    mock_client = _mock_plant_http(200, scheduler_data)

    with patch("api.cp_scheduler.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/hired-agents/ha-1/scheduler-summary",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200
    assert resp.json()["scheduler"] == "ok"


@pytest.mark.unit
def test_scheduler_summary_missing_plant_url_returns_503(client, monkeypatch):
    """GET /scheduler-summary when PLANT_GATEWAY_URL is missing returns 503."""
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)
    resp = client.get(
        "/api/cp/hired-agents/ha-1/scheduler-summary",
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 503


@pytest.mark.unit
def test_scheduler_summary_plant_error_returns_502(client, monkeypatch):
    """GET /scheduler-summary when Plant is unreachable returns 502."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_scheduler.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/hired-agents/ha-1/scheduler-summary",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 502


# ─── E1-S1: trial-budget ──────────────────────────────────────────────────────

@pytest.mark.unit
def test_trial_budget_requires_auth(client, monkeypatch):
    """GET /trial-budget without Authorization header returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.get("/api/cp/hired-agents/ha-1/trial-budget")
    assert resp.status_code == 401


@pytest.mark.unit
def test_trial_budget_proxies_to_plant(client, monkeypatch):
    """GET /trial-budget with auth forwards to Plant and returns 200."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    budget_data = {"tasks_used": 3, "trial_task_limit": 10, "trial_ends_at": "2026-03-14T00:00:00Z"}
    mock_client = _mock_plant_http(200, budget_data)

    with patch("api.cp_scheduler.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/hired-agents/ha-1/trial-budget",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200
    assert resp.json()["tasks_used"] == 3


# ─── E1-S2: pause ─────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_pause_requires_auth(client, monkeypatch):
    """POST /pause without Authorization header returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.post("/api/cp/hired-agents/ha-1/pause")
    assert resp.status_code == 401


@pytest.mark.unit
def test_pause_proxies_to_plant(client, monkeypatch):
    """POST /pause with auth forwards to Plant and returns 200."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    pause_response = {"hired_agent_id": "ha-1", "status": "paused"}
    mock_client = _mock_plant_http(200, pause_response)

    with patch("api.cp_scheduler.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/api/cp/hired-agents/ha-1/pause",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


# ─── E1-S2: resume ────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_resume_requires_auth(client, monkeypatch):
    """POST /resume without Authorization header returns 401."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resp = client.post("/api/cp/hired-agents/ha-1/resume")
    assert resp.status_code == 401


@pytest.mark.unit
def test_resume_proxies_to_plant(client, monkeypatch):
    """POST /resume with auth forwards to Plant and returns 200."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    resume_response = {"hired_agent_id": "ha-1", "status": "active"}
    mock_client = _mock_plant_http(200, resume_response)

    with patch("api.cp_scheduler.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/api/cp/hired-agents/ha-1/resume",
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


# ─── Router registration ──────────────────────────────────────────────────────

@pytest.mark.unit
def test_cp_scheduler_router_registered_in_main():
    """Verify cp_scheduler router is included in the FastAPI app."""
    from main import app
    routes = [r.path for r in app.routes]
    scheduler_routes = [r for r in routes if "scheduler-summary" in r or "trial-budget" in r]
    assert len(scheduler_routes) > 0, "cp_scheduler router must be registered in main.py"

    pause_resume_routes = [r for r in routes if "/pause" in r or "/resume" in r]
    assert len(pause_resume_routes) > 0, "pause/resume routes must be registered in main.py"
