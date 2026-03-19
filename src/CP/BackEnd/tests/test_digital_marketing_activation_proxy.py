from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


def _mock_plant_client(status_code: int, json_body: dict) -> AsyncMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_body
    response.text = str(json_body)

    client = AsyncMock()
    client.request = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.unit
def test_get_workspace_proxy_returns_identical_payload(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    payload = {
        "hired_instance_id": "HAI-1",
        "help_visible": False,
        "activation_complete": False,
        "induction": {"brand_name": "WAOOAW"},
        "prepare_agent": {"selected_platforms": ["youtube"], "platform_steps": [], "all_selected_platforms_completed": False},
        "campaign_setup": {"master_theme": "", "derived_themes": [], "schedule": {"start_date": "", "posts_per_week": 0, "preferred_days": [], "preferred_hours_utc": []}},
        "updated_at": "2026-03-18T09:00:00Z",
    }
    mock_client = _mock_plant_client(200, payload)

    with patch("api.digital_marketing_activation.httpx.AsyncClient", return_value=mock_client):
        response = client.get("/api/cp/digital-marketing-activation/HAI-1", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == payload


@pytest.mark.unit
def test_generate_theme_plan_proxy_returns_identical_payload(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    payload = {
        "campaign_id": "CAM-1",
        "master_theme": "Trust-first growth",
        "derived_themes": [
            {"title": "Proof", "description": "Show results", "frequency": "weekly"},
            {"title": "Education", "description": "Teach the market", "frequency": "weekly"},
            {"title": "CTA", "description": "Drive action", "frequency": "weekly"},
        ],
        "workspace": {"hired_instance_id": "HAI-1", "help_visible": True, "activation_complete": False, "induction": {}, "prepare_agent": {"selected_platforms": ["youtube"], "platform_steps": [], "all_selected_platforms_completed": False}, "campaign_setup": {"campaign_id": "CAM-1", "master_theme": "Trust-first growth", "derived_themes": [], "schedule": {"start_date": "", "posts_per_week": 0, "preferred_days": [], "preferred_hours_utc": []}}, "updated_at": "2026-03-18T09:00:00Z"},
    }
    mock_client = _mock_plant_client(200, payload)

    with patch("api.digital_marketing_activation.httpx.AsyncClient", return_value=mock_client):
        response = client.post(
            "/api/cp/digital-marketing-activation/HAI-1/generate-theme-plan",
            headers=auth_headers,
            json={"campaign_setup": {"schedule": {"posts_per_week": 3}}},
        )

    assert response.status_code == 200
    assert response.json()["master_theme"] == "Trust-first growth"
    assert len(response.json()["derived_themes"]) == 3


@pytest.mark.unit
def test_generate_theme_plan_proxy_surfaces_upstream_failure_without_secret_leak(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    payload = {"detail": "XAI_API_KEY is not set. Set EXECUTOR_BACKEND=deterministic or provide the key."}
    mock_client = _mock_plant_client(503, payload)

    with patch("api.digital_marketing_activation.httpx.AsyncClient", return_value=mock_client):
        response = client.post(
            "/api/cp/digital-marketing-activation/HAI-1/generate-theme-plan",
            headers=auth_headers,
            json={},
        )

    assert response.status_code == 503
    assert "XAI_API_KEY" in response.json()["detail"]
    assert "sk-" not in response.text
