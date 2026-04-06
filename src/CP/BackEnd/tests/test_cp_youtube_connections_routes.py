from __future__ import annotations

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


def test_start_youtube_connect_proxies_authenticated_customer(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_youtube_connections import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_status=201,
        response_json={
            "state": "state-123",
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?state=state-123",
            "expires_at": "2026-03-16T12:00:00Z",
        },
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.post(
        "/api/cp/youtube-connections/connect/start",
        headers=auth_headers,
        json={"redirect_uri": "https://cp.demo.waooaw.com/oauth/youtube/callback"},
    )

    assert resp.status_code == 201
    assert resp.json()["state"] == "state-123"
    assert fake.calls[0]["path"] == "api/v1/customer-platform-connections/youtube/connect/start"
    customer_id = fake.calls[0]["json"]["customer_id"]
    assert not customer_id.startswith("CUST-"), f"customer_id must be raw WAOOAW user ID, got: {customer_id}"
    app.dependency_overrides.clear()


def test_finalize_youtube_connect_proxies_code_exchange(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_youtube_connections import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_json={
            "id": "cred-1",
            "platform_key": "youtube",
            "display_name": "Channel One",
            "connection_status": "connected",
        }
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.post(
        "/api/cp/youtube-connections/connect/finalize",
        headers=auth_headers,
        json={
            "state": "state-123",
            "code": "google-auth-code",
            "redirect_uri": "https://cp.demo.waooaw.com/oauth/youtube/callback",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == "cred-1"
    assert fake.calls[0]["json"]["code"] == "google-auth-code"
    customer_id = fake.calls[0]["json"]["customer_id"]
    assert not customer_id.startswith("CUST-"), f"finalize must forward raw WAOOAW customer ID, got: {customer_id}"
    app.dependency_overrides.clear()


def test_list_youtube_connections_forwards_customer_scope(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_youtube_connections import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_json=[
            {"id": "cred-1", "platform_key": "youtube", "display_name": "Channel One"}
        ]
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.get("/api/cp/youtube-connections", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "cred-1"
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["params"] == {"platform_key": "youtube"}
    assert "CUST-" not in fake.calls[0]["path"], f"list path must use raw customer ID, got: {fake.calls[0]['path']}"
    app.dependency_overrides.clear()


def test_get_youtube_connection_proxies_single_connection(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_youtube_connections import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_json={"id": "cred-1", "platform_key": "youtube", "display_name": "Channel One"}
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.get("/api/cp/youtube-connections/cred-1", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["id"] == "cred-1"
    assert fake.calls[0]["path"].endswith("/cred-1")
    assert "CUST-" not in fake.calls[0]["path"], f"get path must use raw customer ID, got: {fake.calls[0]['path']}"
    app.dependency_overrides.clear()


def test_attach_youtube_connection_proxies_hired_agent_binding(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_youtube_connections import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_json={
            "id": "conn-1",
            "hired_instance_id": "HIRED-1",
            "skill_id": "skill-1",
            "platform_key": "youtube",
            "status": "connected",
        }
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.post(
        "/api/cp/youtube-connections/cred-1/attach",
        headers=auth_headers,
        json={
            "hired_instance_id": "HIRED-1",
            "skill_id": "skill-1",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["id"] == "conn-1"
    assert fake.calls[0]["path"] == "api/v1/customer-platform-connections/cred-1/attach"
    assert fake.calls[0]["json"]["platform_key"] == "youtube"
    customer_id = fake.calls[0]["json"]["customer_id"]
    assert not customer_id.startswith("CUST-"), f"attach must forward raw WAOOAW customer ID, got: {customer_id}"
    app.dependency_overrides.clear()


def test_validate_youtube_connection_proxies_customer_credential_check(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_youtube_connections import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_json={
            "id": "cred-1",
            "platform_key": "youtube",
            "display_name": "Channel One",
            "channel_count": 1,
            "total_video_count": 42,
            "recent_short_count": 7,
            "recent_long_video_count": 35,
            "subscriber_count": 1200,
            "view_count": 54000,
        }
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.post(
        "/api/cp/youtube-connections/cred-1/validate",
        headers=auth_headers,
        json={},
    )

    assert resp.status_code == 200
    assert resp.json()["total_video_count"] == 42
    assert fake.calls[0]["path"] == "api/v1/customer-platform-connections/cred-1/validate"
    customer_id = fake.calls[0]["json"]["customer_id"]
    assert not customer_id.startswith("CUST-"), f"validate must forward raw WAOOAW customer ID, got: {customer_id}"
    app.dependency_overrides.clear()


def test_start_youtube_connect_surfaces_upstream_oauth_config_error(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from api.cp_youtube_connections import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        response_status=503,
        response_json={"detail": "YouTube OAuth is not configured on the Plant backend."},
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.post(
        "/api/cp/youtube-connections/connect/start",
        headers=auth_headers,
        json={"redirect_uri": "https://cp.demo.waooaw.com/oauth/youtube/callback"},
    )

    assert resp.status_code == 503
    assert resp.json()["detail"]["detail"] == "YouTube OAuth is not configured on the Plant backend."
    app.dependency_overrides.clear()