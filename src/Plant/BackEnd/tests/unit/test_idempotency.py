"""Unit tests for IdempotencyMiddleware — Iteration 3 E2-S1 + E2-S2.

Covers:
  TC-E2-S1-1  POST without Idempotency-Key header → proceeds normally (no caching)
  TC-E2-S1-2  POST with new key → 201, response cached in Redis
  TC-E2-S1-3  POST with same key + same body → cached 201 returned, no second endpoint call
  TC-E2-S1-4  POST with same key + different body → 422 IDEMPOTENCY_KEY_CONFLICT
  TC-E2-S2-1  Redis unavailable → endpoint proceeds normally (graceful degradation)
  TC-E2-S2-2  Non-guarded path → idempotency NOT applied
  TC-E2-S2-3  GET request to guarded path → idempotency NOT applied
"""

from __future__ import annotations

import json
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from services.idempotency import IdempotencyMiddleware


# ---------------------------------------------------------------------------
# Minimal test app
# ---------------------------------------------------------------------------

def _make_app() -> FastAPI:
    """Build a small FastAPI test app that wraps IdempotencyMiddleware."""
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    call_counter: dict[str, int] = {"n": 0}

    @app.post("/api/v1/customers")
    async def create_customer(req: Request):
        call_counter["n"] += 1
        body = await req.json()
        return JSONResponse({"id": "cust-123", "echo": body}, status_code=201)

    @app.post("/api/v1/audit/events")
    async def create_audit_event(req: Request):
        body = await req.json()
        return JSONResponse({"recorded": True, "echo": body}, status_code=201)

    @app.get("/api/v1/customers")
    async def list_customers():
        return JSONResponse({"items": []}, status_code=200)

    @app.post("/api/v1/other-endpoint")
    async def other_endpoint(req: Request):
        return JSONResponse({"ok": True}, status_code=200)

    # Attach counter so tests can inspect it
    app.state.call_counter = call_counter
    return app


def _redis_mock(cached_raw: bytes | None = None, set_ok: bool = True) -> AsyncMock:
    """Return a mock Redis client."""
    r = AsyncMock()
    r.get = AsyncMock(return_value=cached_raw)
    r.set = AsyncMock(return_value=set_ok)
    return r


# ---------------------------------------------------------------------------
# TC-E2-S1-1: No Idempotency-Key → passes through unchanged
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_idempotency_key_passes_through():
    """TC-E2-S1-1: Without the header the middleware is transparent."""
    app = _make_app()
    with patch("services.idempotency.get_async_redis", return_value=_redis_mock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/customers", json={"email": "a@test.com"})

    assert resp.status_code == 201
    assert resp.json()["id"] == "cust-123"
    # Redis should NOT have been called when no key given
    # (no mock interaction needed — just asserting response)


# ---------------------------------------------------------------------------
# TC-E2-S1-2: First request with new key → endpoint called, response cached
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_request_with_new_key_is_cached():
    """TC-E2-S1-2: New idempotency key proceeds normally and caches 201."""
    r = _redis_mock(cached_raw=None)
    app = _make_app()

    with patch("services.idempotency.get_async_redis", return_value=r):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/customers",
                json={"email": "b@test.com"},
                headers={"Idempotency-Key": "key-111"},
            )

    assert resp.status_code == 201
    assert resp.json()["id"] == "cust-123"
    # Redis.set should have been called once to cache the result
    r.set.assert_awaited_once()
    call_args = r.set.call_args
    redis_key = call_args[0][0]
    assert "key-111" in redis_key
    assert call_args.kwargs["ex"] == 86400
    assert call_args.kwargs["nx"] is True


# ---------------------------------------------------------------------------
# TC-E2-S1-3: Repeated request same key + same body → cached response
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repeated_request_returns_cached_response():
    """TC-E2-S1-3: Same key + same body → returns cached response, endpoint not called again."""
    import hashlib

    body = {"email": "c@test.com"}
    body_bytes = json.dumps(body).encode()
    body_hash = hashlib.sha256(body_bytes).hexdigest()

    cached_value = json.dumps({
        "status_code": 201,
        "body": {"id": "cust-456", "echo": body},
        "body_hash": body_hash,
    }).encode()

    r = _redis_mock(cached_raw=cached_value)
    app = _make_app()

    with patch("services.idempotency.get_async_redis", return_value=r):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/customers",
                content=body_bytes,
                headers={
                    "Idempotency-Key": "key-222",
                    "Content-Type": "application/json",
                },
            )

    assert resp.status_code == 201
    assert resp.headers.get("x-idempotency-replayed") == "true"
    # Endpoint was not invoked again (counter should be 0 because middleware returned early)
    assert app.state.call_counter["n"] == 0
    # Redis.set should NOT be called
    r.set.assert_not_awaited()


# ---------------------------------------------------------------------------
# TC-E2-S1-4: Same key + different body → 422 IDEMPOTENCY_KEY_CONFLICT
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_same_key_different_body_returns_conflict():
    """TC-E2-S1-4: Body hash mismatch → 422 IDEMPOTENCY_KEY_CONFLICT."""
    import hashlib

    original_body = {"email": "d@test.com"}
    original_body_bytes = json.dumps(original_body).encode()
    original_body_hash = hashlib.sha256(original_body_bytes).hexdigest()

    cached_value = json.dumps({
        "status_code": 201,
        "body": {"id": "cust-789"},
        "body_hash": original_body_hash,
    }).encode()

    r = _redis_mock(cached_raw=cached_value)
    app = _make_app()

    different_body = {"email": "DIFFERENT@test.com"}
    different_body_bytes = json.dumps(different_body).encode()

    with patch("services.idempotency.get_async_redis", return_value=r):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/customers",
                content=different_body_bytes,
                headers={
                    "Idempotency-Key": "key-333",
                    "Content-Type": "application/json",
                },
            )

    assert resp.status_code == 422
    assert resp.json()["detail"] == "IDEMPOTENCY_KEY_CONFLICT"


# ---------------------------------------------------------------------------
# TC-E2-S2-1: Redis unavailable → endpoint proceeds normally
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_redis_unavailable_proceeds_normally():
    """TC-E2-S2-1: Redis error → graceful degradation, endpoint still called."""
    r = AsyncMock()
    r.get = AsyncMock(side_effect=ConnectionError("Redis down"))
    app = _make_app()

    with patch("services.idempotency.get_async_redis", return_value=r):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/customers",
                json={"email": "e@test.com"},
                headers={"Idempotency-Key": "key-444"},
            )

    # Should still return 201 from the actual endpoint
    assert resp.status_code == 201
    assert resp.json()["id"] == "cust-123"


@pytest.mark.asyncio
async def test_redis_import_error_proceeds_normally():
    """TC-E2-S2-1 (import error variant): If get_async_redis raises, proceed normally."""
    app = _make_app()

    with patch(
        "services.idempotency.get_async_redis",
        side_effect=Exception("redis not configured"),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/customers",
                json={"email": "f@test.com"},
                headers={"Idempotency-Key": "key-555"},
            )

    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# TC-E2-S2-2: Non-guarded path → idempotency NOT applied
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_non_guarded_path_not_intercepted():
    """TC-E2-S2-2: Non-guarded POST endpoints are unaffected by middleware."""
    r = _redis_mock(cached_raw=None)
    app = _make_app()

    with patch("services.idempotency.get_async_redis", return_value=r):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/other-endpoint",
                json={"data": "test"},
                headers={"Idempotency-Key": "key-666"},
            )

    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    # Redis should NOT have been called
    r.get.assert_not_awaited()


# ---------------------------------------------------------------------------
# TC-E2-S2-3: GET request to guarded path → idempotency NOT applied
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_request_not_intercepted():
    """TC-E2-S2-3: Only POST requests to guarded paths get idempotency treatment."""
    r = _redis_mock(cached_raw=None)
    app = _make_app()

    with patch("services.idempotency.get_async_redis", return_value=r):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/v1/customers",
                headers={"Idempotency-Key": "key-777"},
            )

    assert resp.status_code == 200
    r.get.assert_not_awaited()


# ---------------------------------------------------------------------------
# Audit events endpoint also guarded
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_events_guarded():
    """Audit events endpoint is also covered by idempotency guard."""
    r = _redis_mock(cached_raw=None)
    app = _make_app()

    with patch("services.idempotency.get_async_redis", return_value=r):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/audit/events",
                json={"event_type": "login"},
                headers={"Idempotency-Key": "key-888"},
            )

    assert resp.status_code == 201
    r.set.assert_awaited_once()
    redis_key_arg = r.set.call_args[0][0]
    assert "/api/v1/audit/events" in redis_key_arg
    assert "key-888" in redis_key_arg
