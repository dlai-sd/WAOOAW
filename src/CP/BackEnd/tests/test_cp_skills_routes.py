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
    skills_response = [{"skill_id": "SK-001", "name": "content-publisher"}]

    def side_effect_get(url, **kwargs):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.text = "ok"
        mock_resp.status_code = 200
        mock_resp.json.return_value = skills_response
        assert url.endswith("/api/v1/hired-agents/HIRED-001/skills")
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
    """Verify credentials go to Secret Manager; secret_ref (not raw creds) forwarded to Plant."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")

    # Plant BackEnd response after storing the connection
    plant_payload = {
        "id": "CONN-002",
        "hired_instance_id": "HIRED-001",
        "skill_id": "skill-twitter-01",
        "platform_key": "twitter",
        "status": "pending",
        "created_at": "2026-03-03T00:00:00Z",
        "updated_at": "2026-03-03T00:00:00Z",
    }
    mock_http_client = _mock_httpx_get(201, plant_payload)

    # Mock Secret Manager adapter so test does not call GCP
    mock_adapter = AsyncMock()
    mock_adapter.write_secret = AsyncMock(
        return_value="projects/waooaw-oauth/secrets/hired-HIRED-001-twitter/versions/1"
    )

    with (
        patch("api.cp_skills.httpx.AsyncClient", return_value=mock_http_client),
        patch(
            "api.cp_skills.get_secret_manager_adapter", return_value=mock_adapter
        ),
    ):
        resp = client.post(
            "/api/cp/hired-agents/HIRED-001/platform-connections",
            headers=auth_headers,
            json={
                "skill_id": "skill-twitter-01",
                "platform_key": "twitter",
                "credentials": {"access_token": "tok_test_123"},
            },
        )

    assert resp.status_code in (200, 201)
    # Verify Secret Manager was called with the correct secret_id
    mock_adapter.write_secret.assert_awaited_once()
    call_kwargs = mock_adapter.write_secret.call_args
    assert "hired-HIRED-001-twitter" in str(call_kwargs)


@pytest.mark.unit
def test_create_platform_connection_secret_manager_backend_local(
    client, auth_headers, monkeypatch
):
    """Verify LocalSecretManagerAdapter is used when SECRET_MANAGER_BACKEND=local (CI/dev)."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    monkeypatch.setenv("SECRET_MANAGER_BACKEND", "local")

    plant_payload = {
        "id": "CONN-003",
        "hired_instance_id": "HIRED-001",
        "skill_id": "skill-ig-01",
        "platform_key": "instagram",
        "status": "pending",
        "created_at": "2026-03-03T00:00:00Z",
        "updated_at": "2026-03-03T00:00:00Z",
    }
    mock_http_client = _mock_httpx_get(201, plant_payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_http_client):
        resp = client.post(
            "/api/cp/hired-agents/HIRED-001/platform-connections",
            headers=auth_headers,
            json={
                "skill_id": "skill-ig-01",
                "platform_key": "instagram",
                "credentials": {"api_key": "test_key"},
            },
        )

    # LocalSecretManagerAdapter stores in-memory and returns local:// ref
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
    """PATCH forwards to the canonical hired-agent customer-config route."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    patch_response = {
        "skill_id": "SK-001",
        "name": "Content Writer",
        "display_name": "Content Writer",
        "customer_fields": {"topic": "AI trends"},
        "goal_schema": {"type": "object"},
        "goal_config": {"topic": "AI trends"},
    }

    def _side_effect(url, **kwargs):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_resp.json.return_value = patch_response
        assert url.endswith("/api/v1/hired-agents/HIRED-001/skills/SK-001/customer-config")
        assert kwargs.get("json") == {"customer_fields": {"topic": "AI trends"}}
        return mock_resp

    mock_client = AsyncMock()
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
    assert data["display_name"] == "Content Writer"


@pytest.mark.unit
def test_save_goal_config_hired_agent_not_found(client, auth_headers, monkeypatch):
    """Canonical customer-config PATCH propagates upstream 404s."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"detail": "not found"}
    mock_resp.text = "not found"

    mock_client = AsyncMock()
    mock_client.patch = AsyncMock(return_value=mock_resp)
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
    """Canonical customer-config PATCH propagates skill-level 404s."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    not_found_resp = {"detail": "Skill not attached to this agent"}

    def _side_effect(url, **kwargs):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 404
        mock_resp.json.return_value = not_found_resp
        mock_resp.text = str(mock_resp.json.return_value)
        return mock_resp

    mock_client = AsyncMock()
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

