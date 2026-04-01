from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
import pytest

from middleware.auth import AuthMiddleware


@pytest.mark.asyncio
async def test_auth_middleware_uses_redis_runtime_helper(monkeypatch):
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/api/v1/protected")
    async def protected(request: Request):
        return JSONResponse({"ok": True, "user_id": request.state.user_id})

    class Claims:
        user_id = "user-1"
        email = "user@example.com"
        customer_id = "customer-1"
        roles = ["user"]
        trial_mode = False
        trial_expires_at = None
        sub = "user-1"
        jti = "jwt-1"
        token_version = None

        def to_dict(self):
            return {
                "user_id": self.user_id,
                "email": self.email,
                "customer_id": self.customer_id,
                "roles": self.roles,
                "trial_mode": self.trial_mode,
                "trial_expires_at": self.trial_expires_at,
                "sub": self.sub,
                "jti": self.jti,
                "token_version": self.token_version,
            }

    claims = Claims()

    monkeypatch.setattr("middleware.auth.validate_jwt", lambda token: claims)
    is_revoked = AsyncMock(return_value=False)
    monkeypatch.setattr("middleware.auth.redis_runtime.is_access_token_revoked", is_revoked)
    monkeypatch.setattr("middleware.auth.redis_runtime.get_token_version", AsyncMock(return_value=None))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/protected",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    is_revoked.assert_awaited_once_with("jwt-1")
