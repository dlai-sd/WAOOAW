from __future__ import annotations

import httpx
import pytest

import main_proxy


@pytest.mark.unit
async def test_proxy_forwards_request(client, monkeypatch):
    main_proxy.PLANT_GATEWAY_URL = "http://plant-gateway"

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["method"] = method
        seen["url"] = url
        seen["headers"] = headers
        seen["content"] = content
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main_proxy.http_client, "request", fake_request)

    resp = await client.get("/api/foo/bar?x=1")
    assert resp.status_code == 200
    assert resp.text == "ok"

    assert seen["method"] == "GET"
    assert seen["url"] == "http://plant-gateway/api/foo/bar?x=1"
    assert seen["headers"]["X-Gateway-Type"] == "PP"


@pytest.mark.unit
async def test_proxy_strips_inbound_metering_headers(client, monkeypatch):
    main_proxy.PLANT_GATEWAY_URL = "http://plant-gateway"

    seen = {}

    async def fake_request(*, method, url, headers, content, follow_redirects):
        seen["headers"] = headers
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"})

    monkeypatch.setattr(main_proxy.http_client, "request", fake_request)

    resp = await client.get(
        "/api/foo",
        headers={
            "X-Metering-Timestamp": "123",
            "X-Metering-Tokens-In": "1",
            "X-Metering-Tokens-Out": "2",
            "X-Metering-Model": "demo",
            "X-Metering-Cache-Hit": "0",
            "X-Metering-Cost-USD": "0.100000",
            "X-Metering-Signature": "abc",
            "Authorization": "Bearer test",
        },
    )
    assert resp.status_code == 200

    forwarded_lower = {k.lower() for k in seen["headers"].keys()}
    assert "authorization" in forwarded_lower
    assert not any(k.startswith("x-metering-") for k in forwarded_lower)


@pytest.mark.unit
async def test_proxy_handles_gateway_unavailable(client, monkeypatch):
    req = httpx.Request("GET", "http://plant-gateway/api/foo")

    async def fake_request(*args, **kwargs):
        raise httpx.RequestError("boom", request=req)

    monkeypatch.setattr(main_proxy.http_client, "request", fake_request)

    resp = await client.get("/api/foo")
    assert resp.status_code == 503
    data = resp.json()
    assert data["error"] == "Gateway Unavailable"


@pytest.mark.unit
async def test_proxy_handles_unexpected_error(client, monkeypatch):
    async def fake_request(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(main_proxy.http_client, "request", fake_request)

    resp = await client.get("/api/foo")
    assert resp.status_code == 500
    data = resp.json()
    assert data["error"] == "Proxy Error"
