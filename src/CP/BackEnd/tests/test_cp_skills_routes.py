from __future__ import annotations

# Auth pattern mirrors test_hired_agents_proxy.py:
#   - Use the shared `client` fixture (TestClient, no overrides)
#   - Use the shared `auth_headers` fixture (real JWT via mocked Google verify)
# This keeps auth logic real and prevents coverage gaming via dependency bypass.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


def _mock_httpx_get(status_code: int, json_body: dict | list) -> AsyncMock:
    """Return a context-manager mock for httpx.AsyncClient."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body
    mock_response.text = str(json_body)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.delete = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ── GET /api/cp/hired-agents/{id}/skills ─────────────────────────────────────

@pytest.mark.unit
def test_list_hired_agent_skills_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    hop1_response = {"agent_id": "AGT-001", "hired_instance_id": "HIRED-001"}
    hop2_response = [{"skill_id": "SK-001", "name": "content-publisher"}]

    call_count = 0

    def side_effect_get(url, **kwargs):
        nonlocal call_count
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.text = "ok"
        mock_resp.status_code = 200
        mock_resp.json.return_value = hop1_response if call_count == 0 else hop2_response
        call_count += 1
        return mock_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=side_effect_get)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/hired-agents/HIRED-001/skills", headers=auth_headers)

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.unit
def test_list_hired_agent_skills_not_found(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"detail": "not found"}
    mock_resp.text = "not found"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/hired-agents/HIRED-MISSING/skills", headers=auth_headers)

    assert resp.status_code == 404


# ── GET /api/cp/skills/{skill_id} ─────────────────────────────────────────────

@pytest.mark.unit
def test_get_skill_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    skill_payload = {"skill_id": "SK-001", "name": "content-publisher", "goal_schema": {"fields": []}}
    mock_client = _mock_httpx_get(200, skill_payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/skills/SK-001", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["skill_id"] == "SK-001"


# ── GET /api/cp/hired-agents/{id}/platform-connections ───────────────────────

@pytest.mark.unit
def test_list_platform_connections_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    payload = [{"connection_id": "CONN-001", "platform_name": "linkedin"}]
    mock_client = _mock_httpx_get(200, payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/hired-agents/HIRED-001/platform-connections", headers=auth_headers
        )

    assert resp.status_code == 200


# ── POST /api/cp/hired-agents/{id}/platform-connections ──────────────────────

@pytest.mark.unit
def test_create_platform_connection_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    payload = {"connection_id": "CONN-002", "platform_name": "twitter"}
    mock_client = _mock_httpx_get(201, payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.post(
            "/api/cp/hired-agents/HIRED-001/platform-connections",
            headers=auth_headers,
            json={
                "platform_name": "twitter",
                "connection_type": "oauth2",
                "credentials": {},
                "metadata": {},
            },
        )

    assert resp.status_code in (200, 201)


# ── DELETE /api/cp/hired-agents/{id}/platform-connections/{conn_id} ──────────

@pytest.mark.unit
def test_delete_platform_connection_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 204
    mock_resp.text = ""

    mock_client = AsyncMock()
    mock_client.delete = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.delete(
            "/api/cp/hired-agents/HIRED-001/platform-connections/CONN-001",
            headers=auth_headers,
        )

    assert resp.status_code == 204


# ── GET /api/cp/hired-agents/{id}/performance-stats ──────────────────────────

@pytest.mark.unit
def test_get_performance_stats_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    payload = [{"stat_date": "2026-03-01", "metric_key": "posts_published", "metric_value": 5.0}]
    mock_client = _mock_httpx_get(200, payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.get(
            "/api/cp/hired-agents/HIRED-001/performance-stats", headers=auth_headers
        )

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Misconfiguration guard ────────────────────────────────────────────────────

@pytest.mark.unit
def test_missing_plant_gateway_url_returns_5xx(client, auth_headers, monkeypatch):
    """When PLANT_GATEWAY_URL is absent the route must return 500/502, not crash."""
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)

    resp = client.get("/api/cp/skills/SK-001", headers=auth_headers)

    assert resp.status_code in (500, 502, 503)


# ── PATCH /api/cp/hired-agents/{id}/skills/{skill_id}/goal-config ─────────────

@pytest.mark.unit
def test_save_goal_config_success(client, auth_headers, monkeypatch):
    """Two-hop PATCH: hop-1 resolves agent_id, hop-2 persists goal_config."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    hire_payload = {"agent_id": "AGT-001", "hired_instance_id": "HIRED-001"}
    patch_response = {
        "id": "LINK-1",
        "agent_id": "AGT-001",
        "skill_id": "SK-001",
        "is_primary": True,
        "ordinal": 0,
        "skill_name": "Content Writer",
        "skill_category": "marketing",
        "goal_schema": {"type": "object"},
        "goal_config": {"topic": "AI trends"},
    }

    call_count = 0

    def _side_effect(url, **kwargs):
        nonlocal call_count
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_resp.json.return_value = hire_payload if call_count == 0 else patch_response
        call_count += 1
        return mock_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=_side_effect)
    mock_client.patch = AsyncMock(side_effect=_side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.patch(
            "/api/cp/hired-agents/HIRED-001/skills/SK-001/goal-config",
            json={"goal_config": {"topic": "AI trends"}},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["goal_config"] == {"topic": "AI trends"}
    assert data["skill_name"] == "Content Writer"


@pytest.mark.unit
def test_save_goal_config_hired_agent_not_found(client, auth_headers, monkeypatch):
    """When hop-1 (hired agent lookup) returns 404 the route must propagate 404."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"detail": "not found"}
    mock_resp.text = "not found"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.patch(
            "/api/cp/hired-agents/HIRED-MISSING/skills/SK-001/goal-config",
            json={"goal_config": {}},
            headers=auth_headers,
        )

    assert resp.status_code == 404


@pytest.mark.unit
def test_save_goal_config_skill_not_attached(client, auth_headers, monkeypatch):
    """When hop-2 (plant PATCH) returns 404 the route must propagate 404."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    hire_payload = {"agent_id": "AGT-001"}
    not_found_resp = {"detail": "Skill not attached to this agent"}

    call_count = 0

    def _side_effect(url, **kwargs):
        nonlocal call_count
        mock_resp = MagicMock(spec=httpx.Response)
        if call_count == 0:
            mock_resp.status_code = 200
            mock_resp.json.return_value = hire_payload
        else:
            mock_resp.status_code = 404
            mock_resp.json.return_value = not_found_resp
        mock_resp.text = str(mock_resp.json.return_value)
        call_count += 1
        return mock_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=_side_effect)
    mock_client.patch = AsyncMock(side_effect=_side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.patch(
            "/api/cp/hired-agents/HIRED-001/skills/SK-MISSING/goal-config",
            json={"goal_config": {}},
            headers=auth_headers,
        )

    assert resp.status_code == 404

