import json

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from middleware.request_pipeline import CircuitBreaker, CircuitBreakerConfig, RequestPipelineMiddleware


class _DummyHttpClient:
    def __init__(self, *, spec: dict, upstream_status: int = 200):
        self._spec = spec
        self._upstream_status = upstream_status
        self.get_calls = 0
        self.request_calls = 0

    async def get(self, url, headers=None):
        self.get_calls += 1
        return httpx.Response(200, json=self._spec, headers={"content-type": "application/json"})

    async def request(self, method, url, headers, content, follow_redirects):
        self.request_calls += 1
        body = {"ok": True}
        return httpx.Response(self._upstream_status, json=body, headers={"content-type": "application/json"})


def _spec_for_widget_post() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/api/v1/widgets": {
                "post": {
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {"name": {"type": "string"}},
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }


@pytest.mark.unit
def test_request_pipeline_mints_correlation_id_and_surfaces_header():
    dummy = _DummyHttpClient(spec=_spec_for_widget_post())

    app = FastAPI()
    app.add_middleware(
        RequestPipelineMiddleware,
        http_client_getter=lambda: dummy,
        backend_url_getter=lambda: "http://upstream",
        validate_openapi=False,
    )

    @app.get("/api/v1/agents")
    async def agents(request: Request):
        return JSONResponse({"ok": True})

    client = TestClient(app)
    res = client.get("/api/v1/agents")

    assert res.status_code == 200
    assert res.headers.get("X-Correlation-ID")


@pytest.mark.unit
def test_request_pipeline_openapi_validation_rejects_invalid_body_and_allows_valid():
    dummy = _DummyHttpClient(spec=_spec_for_widget_post())

    app = FastAPI()
    app.add_middleware(
        RequestPipelineMiddleware,
        http_client_getter=lambda: dummy,
        backend_url_getter=lambda: "http://upstream",
        validate_openapi=True,
        spec_cache_ttl_seconds=60,
    )

    @app.post("/api/v1/widgets")
    async def widgets(request: Request):
        payload = await request.json()
        return JSONResponse({"echo": payload})

    client = TestClient(app)

    bad = client.post("/api/v1/widgets", json={})
    assert bad.status_code == 422
    assert bad.json()["detail"].lower().find("openapi") >= 0

    good = client.post("/api/v1/widgets", json={"name": "w"})
    assert good.status_code == 200
    assert good.json()["echo"]["name"] == "w"


@pytest.mark.unit
def test_request_pipeline_circuit_breaker_opens_after_three_failures():
    dummy = _DummyHttpClient(spec=_spec_for_widget_post())
    breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3, window_seconds=10))

    app = FastAPI()
    app.add_middleware(
        RequestPipelineMiddleware,
        http_client_getter=lambda: dummy,
        backend_url_getter=lambda: "http://upstream",
        validate_openapi=False,
        circuit_breaker=breaker,
    )

    calls = {"n": 0}

    @app.get("/api/v1/fails")
    async def fails(request: Request):
        calls["n"] += 1
        return JSONResponse({"error": "upstream"}, status_code=503)

    client = TestClient(app)

    for _ in range(3):
        r = client.get("/api/v1/fails")
        assert r.status_code == 503

    # Now breaker should be open and the endpoint should not be called again.
    before = calls["n"]
    r4 = client.get("/api/v1/fails")
    assert r4.status_code == 503
    assert r4.json()["detail"].lower().find("circuit") >= 0
    assert calls["n"] == before
