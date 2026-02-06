from __future__ import annotations

import httpx
import pytest

import main


@pytest.mark.unit
def test_auth_routes_are_local_and_not_proxied(client, monkeypatch):
    async def fake_request(*args, **kwargs):
        raise AssertionError("proxy_to_gateway should not be called for /api/auth/*")

    monkeypatch.setattr(main.http_client, "request", fake_request)

    resp = client.get("/api/auth/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("service") == "authentication"


@pytest.mark.unit
def test_non_auth_api_routes_are_proxied(client, monkeypatch):
    main.PLANT_GATEWAY_URL = "http://plant-gateway"

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["method"] = method
        seen["url"] = url
        seen["headers"] = headers
        seen["content"] = content
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main.http_client, "request", fake_request)

    resp = client.get("/api/v1/agents?x=1")
    assert resp.status_code == 200
    assert resp.text == "ok"

    assert seen["method"] == "GET"
    assert seen["url"] == "http://plant-gateway/api/v1/agents?x=1"
    assert seen["headers"]["X-Gateway-Type"] == "CP"
