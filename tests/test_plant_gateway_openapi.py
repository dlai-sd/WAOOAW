from __future__ import annotations

import importlib
import time

import httpx
import jwt
from fastapi.testclient import TestClient


def _import_gateway_main():
    for module_name in ("src.Plant.Gateway.main", "main"):
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
    raise ModuleNotFoundError("Could not import Plant Gateway module (tried src.Plant.Gateway.main and main)")


def test_gateway_openapi_uses_backend_id_token_when_configured(monkeypatch) -> None:
    """Ensure /openapi.json fetches backend spec with Cloud Run ID token.

    This prevents 500s in demo/prod where Plant Backend is IAM-protected.
    """

    # Import inside the test so monkeypatching is visible.
    gateway_main = _import_gateway_main()

    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_URL", "https://plant-backend.example")
    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_USE_ID_TOKEN", True)

    async def fake_get_backend_id_token() -> str:
        return "test-id-token"

    monkeypatch.setattr(gateway_main, "_get_backend_id_token", fake_get_backend_id_token)

    async def fake_get(url: str, headers=None, params=None):
        assert url == "https://plant-backend.example/openapi.json"
        assert headers and headers.get("Authorization") == "Bearer test-id-token"
        req = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={
                "openapi": "3.0.0",
                "info": {"title": "Plant", "version": "1"},
                "paths": {},
            },
            request=req,
        )

    monkeypatch.setattr(gateway_main.http_client, "get", fake_get)

    with TestClient(gateway_main.app) as client:
        res = client.get("/openapi.json")

    assert res.status_code == 200
    data = res.json()
    assert data["openapi"] == "3.0.0"
    assert data["servers"][0]["url"].startswith("http")


def test_gateway_openapi_returns_502_when_id_token_unavailable(monkeypatch) -> None:
    gateway_main = _import_gateway_main()

    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_URL", "https://plant-backend.example")
    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_USE_ID_TOKEN", True)

    async def fake_get_backend_id_token():
        return None

    monkeypatch.setattr(gateway_main, "_get_backend_id_token", fake_get_backend_id_token)

    with TestClient(gateway_main.app) as client:
        res = client.get("/openapi.json")

    assert res.status_code == 502
    body = res.json()
    assert body.get("error") == "upstream_auth_unavailable"


def test_gateway_openapi_returns_502_when_backend_openapi_errors(monkeypatch) -> None:
    gateway_main = _import_gateway_main()

    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_URL", "https://plant-backend.example")
    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_USE_ID_TOKEN", False)

    async def fake_get(url: str, headers=None, params=None):
        req = httpx.Request("GET", url)
        return httpx.Response(
            403,
            json={"detail": "Forbidden"},
            request=req,
        )

    monkeypatch.setattr(gateway_main.http_client, "get", fake_get)

    with TestClient(gateway_main.app) as client:
        res = client.get("/openapi.json")

    assert res.status_code == 502
    body = res.json()
    assert body.get("type", "").endswith("/bad-gateway")


def test_gateway_proxy_uses_backend_id_token_and_preserves_original_auth(monkeypatch) -> None:
    monkeypatch.setenv("JWT_PUBLIC_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ISSUER", "waooaw.com")
    monkeypatch.delenv("JWT_AUDIENCE", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("GW_ALWAYS_VALIDATE_WITH_PLANT", "false")
    monkeypatch.setenv("GW_ALLOW_PLANT_CUSTOMER_ENRICHMENT", "false")

    gateway_main = _import_gateway_main()
    gateway_main = importlib.reload(gateway_main)

    now = int(time.time())
    user_token = jwt.encode(
        {
            "user_id": "user-123",
            "email": "user@example.com",
            "roles": ["user"],
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-123",
        },
        "test-secret",
        algorithm="HS256",
    )

    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_URL", "https://plant-backend.example")
    monkeypatch.setattr(gateway_main, "PLANT_BACKEND_USE_ID_TOKEN", True)

    async def fake_get_backend_id_token() -> str:
        return "backend-id-token"

    monkeypatch.setattr(gateway_main, "_get_backend_id_token", fake_get_backend_id_token)

    async def fake_request(method: str, url: str, headers=None, content=None, follow_redirects=False):
        assert method == "GET"
        assert url == "https://plant-backend.example/v1/ping"
        assert headers["Authorization"] == "Bearer backend-id-token"
        assert headers["X-Original-Authorization"] == f"Bearer {user_token}"
        assert headers["X-Gateway"] == "plant-gateway"
        req = httpx.Request(method, url)
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/plain"}, request=req)

    monkeypatch.setattr(gateway_main.http_client, "request", fake_request)

    with TestClient(gateway_main.app) as client:
        res = client.get("/v1/ping", headers={"Authorization": f"Bearer {user_token}"})

    assert res.status_code == 200
    assert res.text == "ok"
