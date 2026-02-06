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


@pytest.mark.unit
def test_proxy_strips_inbound_metering_headers(client, monkeypatch):
    main.PLANT_GATEWAY_URL = "http://plant-gateway"

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["headers"] = headers
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main.http_client, "request", fake_request)

    resp = client.get(
        "/api/v1/agents",
        headers={
            "X-Metering-Envelope": "spoofed",
            "X-Metering-Signature": "spoofed",
            "X-Other": "ok",
        },
    )
    assert resp.status_code == 200

    lowered = {str(k).lower(): v for k, v in seen["headers"].items()}
    assert "x-metering-envelope" not in lowered
    assert "x-metering-signature" not in lowered
    assert lowered.get("x-other") == "ok"


@pytest.mark.unit
def test_proxy_forwards_correlation_id_when_present(client, monkeypatch):
    main.PLANT_GATEWAY_URL = "http://plant-gateway"

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["headers"] = headers
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main.http_client, "request", fake_request)

    resp = client.get("/api/v1/agents", headers={"X-Correlation-ID": "corr-123"})
    assert resp.status_code == 200
    assert seen["headers"].get("X-Correlation-ID") == "corr-123"


@pytest.mark.unit
def test_proxy_generates_correlation_id_when_missing(client, monkeypatch):
    main.PLANT_GATEWAY_URL = "http://plant-gateway"

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["headers"] = headers
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main.http_client, "request", fake_request)

    resp = client.get("/api/v1/agents")
    assert resp.status_code == 200

    correlation_id = seen["headers"].get("X-Correlation-ID")
    assert isinstance(correlation_id, str)
    assert correlation_id


@pytest.mark.unit
def test_proxy_forwards_debug_trace_when_requested(client, monkeypatch):
    main.PLANT_GATEWAY_URL = "http://plant-gateway"

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["headers"] = headers
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main.http_client, "request", fake_request)

    resp = client.get("/api/v1/agents", headers={"X-Debug-Trace": "1"})
    assert resp.status_code == 200
    assert seen["headers"].get("X-Debug-Trace") == "1"


@pytest.mark.unit
def test_proxy_enables_debug_trace_when_debug_verbose(client, monkeypatch):
    main.PLANT_GATEWAY_URL = "http://plant-gateway"

    monkeypatch.setattr(main, "DEBUG_VERBOSE", True)

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["headers"] = headers
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main.http_client, "request", fake_request)

    resp = client.get("/api/v1/agents")
    assert resp.status_code == 200
    assert seen["headers"].get("X-Debug-Trace") == "1"
