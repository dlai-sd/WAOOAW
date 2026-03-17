from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class _FakePlantClient:
    def __init__(self, response_status: int = 200, response_json: Any = None) -> None:
        self.calls = []
        self._status = response_status
        self._json = response_json if response_json is not None else {}

    async def request_json(
        self,
        *,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Any = None,
        params: Optional[Dict[str, str]] = None,
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


def _studio_payload() -> dict[str, Any]:
    return {
        "hired_instance_id": "HAI-123",
        "subscription_id": "SUB-123",
        "agent_id": "AGT-MKT-DMA-001",
        "agent_type_id": "marketing.digital_marketing.v1",
        "customer_id": "CUST-user-123",
        "mode": "activation",
        "selection_required": False,
        "current_step": "connection",
        "steps": [
            {
                "key": "identity",
                "title": "Identity and voice",
                "complete": True,
                "blocked": False,
                "summary": "Business-facing name and theme are ready.",
            },
            {
                "key": "connection",
                "title": "Connection",
                "complete": False,
                "blocked": False,
                "summary": "No verified publishing connection is attached yet.",
            },
        ],
        "identity": {
            "nickname": "Growth Copilot",
            "theme": "default",
            "complete": True,
        },
        "connection": {
            "platform_key": "youtube",
            "skill_id": "default",
            "connection_id": None,
            "customer_platform_credential_id": None,
            "status": "missing",
            "complete": False,
            "summary": "No verified publishing connection is attached yet.",
        },
        "operating_plan": {
            "complete": False,
            "goals_completed": False,
            "goal_count": 0,
            "skill_config_count": 0,
            "summary": "Operating plan still needs customer input before review.",
        },
        "review": {
            "complete": False,
            "summary": "This agent still has incomplete steps before review.",
        },
        "configured": False,
        "goals_completed": False,
        "trial_status": "not_started",
        "subscription_status": "active",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def test_get_hired_agent_studio_proxies_customer_scope(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_hired_agent_studio import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(response_json=_studio_payload())
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.get("/api/cp/hired-agents/HAI-123/studio", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["hired_instance_id"] == "HAI-123"
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["path"] == "api/v1/hired-agents/HAI-123/studio"
    assert fake.calls[0]["params"]["customer_id"].startswith("CUST-")


def test_patch_hired_agent_studio_forwards_body_and_customer_id(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_hired_agent_studio import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(response_json=_studio_payload())
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.patch(
        "/api/cp/hired-agents/HAI-123/studio",
        headers=auth_headers,
        json={
            "identity": {
                "nickname": "Pipeline Pilot",
                "theme": "dark",
            },
            "review": {
                "goals_completed": True,
                "finalize": True,
            },
        },
    )

    assert resp.status_code == 200
    assert fake.calls[0]["method"] == "PATCH"
    assert fake.calls[0]["json"]["identity"]["nickname"] == "Pipeline Pilot"
    assert fake.calls[0]["json"]["review"]["finalize"] is True
    assert fake.calls[0]["json"]["customer_id"].startswith("CUST-")


def test_hired_agent_studio_propagates_upstream_not_found(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_hired_agent_studio import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(response_status=404, response_json={"detail": "Hired agent instance not found."})
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.get("/api/cp/hired-agents/HAI-missing/studio", headers=auth_headers)

    assert resp.status_code == 404
    assert resp.json()["detail"] == {"detail": "Hired agent instance not found."}