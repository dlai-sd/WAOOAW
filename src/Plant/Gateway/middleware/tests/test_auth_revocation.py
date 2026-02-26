"""Unit tests for E2-S2 — Gateway access-token revocation check (jti Redis list).

TC-E2-S2-1  Valid non-revoked JWT → passes through (Redis returns 0)
TC-E2-S2-2  JWT with revoked jti in Redis → 401 TOKEN_REVOKED
TC-E2-S2-4  Token expired naturally → 401 (not TOKEN_REVOKED)
TC-E2-S2-5  Redis failure → fail open (request passes)

NOTE: Keys and env vars (JWT_ALGORITHM=RS256, JWT_PUBLIC_KEY) are configured
by conftest.pytest_configure *before* this module is imported.
"""

from __future__ import annotations

import os
import pytest
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from middleware.auth import AuthMiddleware

_ISSUER = "waooaw.com"


def _get_private_key() -> str:
    """Get RSA private key set by conftest._ensure_test_env()."""
    return os.environ["TEST_JWT_PRIVATE_KEY"]
_USER_ID = "user-it1-test"
_CUSTOMER_ID = "cust-it1-test"


def _make_jwt(
    exp_delta: timedelta = timedelta(hours=1),
    jti: str = "test-jti-001",
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": _USER_ID,
        "user_id": _USER_ID,
        "customer_id": _CUSTOMER_ID,
        "email": "test@waooaw.com",
        "roles": ["user"],
        "iss": _ISSUER,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
        "jti": jti,
    }
    return pyjwt.encode(payload, _get_private_key(), algorithm="RS256")


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/api/v1/protected")
    async def protected(request: Request):
        return JSONResponse({"ok": True, "user_id": request.state.user_id})

    return app


# ---------------------------------------------------------------------------
# TC-E2-S2-1: valid (non-revoked) JWT passes through
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2_s2_valid_jwt_passes(monkeypatch):
    """Non-revoked JWT should pass through — Redis returns 0 for EXISTS."""
    app = _make_app()
    token = _make_jwt(jti="clean-jti")

    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("middleware.auth._get_gateway_redis", lambda: mock_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 200
    mock_redis.exists.assert_awaited_once_with("revoked_access:clean-jti")


# ---------------------------------------------------------------------------
# TC-E2-S2-2: revoked jti → 401 TOKEN_REVOKED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2_s2_revoked_jti_blocked(monkeypatch):
    """JWT whose jti has been added to revocation list → 401 TOKEN_REVOKED."""
    app = _make_app()
    token = _make_jwt(jti="revoked-jti-001")

    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)  # 1 = key exists = revoked
    monkeypatch.setattr("middleware.auth._get_gateway_redis", lambda: mock_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 401
    body = r.json()
    assert body.get("detail") == "TOKEN_REVOKED"


# ---------------------------------------------------------------------------
# TC-E2-S2-4: expired token → 401, not TOKEN_REVOKED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2_s2_expired_token_distinct_from_revoked(monkeypatch):
    """An expired token should give 401 but NOT the TOKEN_REVOKED code."""
    app = _make_app()
    token = _make_jwt(exp_delta=timedelta(seconds=-60), jti="expired-jti")

    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("middleware.auth._get_gateway_redis", lambda: mock_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 401
    body = r.json()
    # Must NOT report TOKEN_REVOKED — token expired legitimately
    assert body.get("detail") != "TOKEN_REVOKED"


# ---------------------------------------------------------------------------
# TC-E2-S2: Redis failure is non-fatal (fail open)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2_s2_redis_failure_is_non_fatal(monkeypatch):
    """If Redis is unavailable, request should still pass through (fail open)."""
    app = _make_app()
    token = _make_jwt(jti="redis-fail-jti")

    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(side_effect=ConnectionError("Redis down"))
    monkeypatch.setattr("middleware.auth._get_gateway_redis", lambda: mock_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Should succeed — Redis check is non-fatal by design
    assert r.status_code == 200
