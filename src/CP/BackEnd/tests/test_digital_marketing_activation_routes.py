from __future__ import annotations

from typing import Any, Dict, Optional

import pytest


pytestmark = pytest.mark.unit


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


def test_get_activation_workspace_proxies_customer_scope(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.digital_marketing_activation import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_json={
            "hired_instance_id": "HIRED-1",
            "customer_id": "user-1",
            "agent_type_id": "marketing.digital_marketing.v1",
            "workspace": {"brand_name": "WAOOAW"},
            "readiness": {
                "brief_complete": True,
                "youtube_selected": False,
                "youtube_connection_ready": True,
                "configured": True,
                "can_finalize": True,
                "missing_requirements": [],
            },
            "updated_at": "2026-03-19T12:00:00Z",
        }
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.get("/api/cp/digital-marketing-activation/HIRED-1", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["workspace"]["brand_name"] == "WAOOAW"
    assert fake.calls[0]["path"] == "api/v1/hired-agents/HIRED-1/digital-marketing-activation"
    assert fake.calls[0]["params"]["customer_id"]
    assert not fake.calls[0]["params"]["customer_id"].startswith("CUST-")
    app.dependency_overrides.clear()


def test_put_activation_workspace_proxies_workspace_payload(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.digital_marketing_activation import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_json={
            "hired_instance_id": "HIRED-1",
            "customer_id": "user-1",
            "agent_type_id": "marketing.digital_marketing.v1",
            "workspace": {"brand_name": "WAOOAW", "platforms_enabled": ["youtube"]},
            "readiness": {
                "brief_complete": True,
                "youtube_selected": True,
                "youtube_connection_ready": False,
                "configured": False,
                "can_finalize": False,
                "missing_requirements": ["youtube_connection"],
            },
            "updated_at": "2026-03-19T12:00:00Z",
        }
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.put(
        "/api/cp/digital-marketing-activation/HIRED-1",
        headers=auth_headers,
        json={"workspace": {"brand_name": "WAOOAW", "platforms_enabled": ["youtube"]}},
    )

    assert resp.status_code == 200
    assert resp.json()["readiness"]["youtube_connection_ready"] is False
    assert fake.calls[0]["json"]["workspace"]["platforms_enabled"] == ["youtube"]
    assert fake.calls[0]["json"]["customer_id"]
    assert not fake.calls[0]["json"]["customer_id"].startswith("CUST-")
    app.dependency_overrides.clear()