from __future__ import annotations

import httpx
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


async def test_api_health_returns_200(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "healthy"
    assert body.get("service") == "pp-proxy"


async def test_api_health_is_not_proxied(client, monkeypatch):
    import main_proxy

    async def fail_proxy_request(*args, **kwargs):
        raise AssertionError("/api/health should not be proxied")

    monkeypatch.setattr(main_proxy.http_client, "request", fail_proxy_request)

    resp = await client.get("/api/health")
    assert resp.status_code == 200


# ── E9: deep health probe tests ───────────────────────────────────────────────

async def test_health_plant_gateway_healthy(client, monkeypatch):
    """When Plant Gateway returns 200, health reports healthy."""
    import main_proxy

    _mock_response = MagicMock()
    _mock_response.status_code = 200

    _mock_client = AsyncMock()
    _mock_client.__aenter__ = AsyncMock(return_value=_mock_client)
    _mock_client.__aexit__ = AsyncMock(return_value=False)
    _mock_client.get = AsyncMock(return_value=_mock_response)

    with patch("main_proxy.httpx.AsyncClient", return_value=_mock_client):
        resp = await client.get("/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["service"] == "pp-backend"
    assert body["components"]["plant_gateway"] == "healthy"


async def test_health_plant_gateway_degraded(client, monkeypatch):
    """When Plant Gateway is unreachable, health reports degraded (still HTTP 200)."""
    import httpx as _httpx

    _mock_client = AsyncMock()
    _mock_client.__aenter__ = AsyncMock(return_value=_mock_client)
    _mock_client.__aexit__ = AsyncMock(return_value=False)
    _mock_client.get = AsyncMock(side_effect=_httpx.ConnectError("refused"))

    with patch("main_proxy.httpx.AsyncClient", return_value=_mock_client):
        resp = await client.get("/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["components"]["plant_gateway"] == "degraded"
