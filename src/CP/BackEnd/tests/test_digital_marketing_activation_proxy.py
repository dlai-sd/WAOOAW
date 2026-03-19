from __future__ import annotations

import pytest


class _FakePlantClient:
    def __init__(self, response_status: int = 200, response_json: dict | None = None) -> None:
        self.calls = []
        self._status = response_status
        self._json = response_json if response_json is not None else {}


    async def request_json(
        self,
        *,
        method: str,
        path: str,
        headers: dict | None = None,
        json_body: dict | None = None,
        params: dict | None = None,
    ):
        self.calls.append(
            {
                "method": method,
                "path": path,
                "headers": headers or {},
                "json": json_body,
                "params": params or {},
            }
        )
        return type(
            "R",
            (),
            {
                "status_code": self._status,
                "json": self._json,
                "headers": {},
            },
        )()


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
    from api.digital_marketing_activation import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(response_status=200, response_json=payload)
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.get("/api/cp/digital-marketing-activation/HAI-1", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == payload
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["path"] == "api/v1/hired-agents/HAI-1/digital-marketing-activation"
    assert fake.calls[0]["params"]["customer_id"].startswith("CUST-")
    app.dependency_overrides.clear()


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
    from api.digital_marketing_activation import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(response_status=200, response_json=payload)
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.post(
        "/api/cp/digital-marketing-activation/HAI-1/generate-theme-plan",
        headers=auth_headers,
        json={"campaign_setup": {"schedule": {"posts_per_week": 3}}},
    )

    assert response.status_code == 200
    assert response.json()["master_theme"] == "Trust-first growth"
    assert len(response.json()["derived_themes"]) == 3
    assert fake.calls[0]["method"] == "POST"
    assert fake.calls[0]["path"] == "api/v1/digital-marketing-activation/HAI-1/generate-theme-plan"
    assert fake.calls[0]["json"]["campaign_setup"]["schedule"]["posts_per_week"] == 3
    assert fake.calls[0]["json"]["customer_id"].startswith("CUST-")
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_generate_theme_plan_proxy_surfaces_upstream_failure_without_secret_leak(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")
    payload = {"detail": "XAI_API_KEY is not set. Set EXECUTOR_BACKEND=deterministic or provide the key."}
    from api.digital_marketing_activation import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(response_status=503, response_json=payload)
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.post(
        "/api/cp/digital-marketing-activation/HAI-1/generate-theme-plan",
        headers=auth_headers,
        json={},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "UPSTREAM_ERROR"
    assert "sk-" not in response.text
    app.dependency_overrides.clear()
