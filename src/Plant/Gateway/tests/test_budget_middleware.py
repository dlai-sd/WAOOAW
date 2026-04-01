from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from middleware.budget import BudgetGuardMiddleware


def test_budget_middleware_uses_background_enqueue():
    jwt_claims = {
        "user_id": "user123",
        "email": "user@example.com",
        "customer_id": "customer123",
        "agent_id": "agent123",
        "roles": ["user"],
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "agent123",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, patch(
        "middleware.budget.redis_runtime.enqueue_budget_update",
        new_callable=AsyncMock,
    ) as mock_enqueue:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "alert_level": "normal",
                    "platform_utilization_percent": 45.0,
                    "agent_utilization_percent": 30.0,
                }
            },
        )

        app = FastAPI()
        app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
        )

        @app.get("/api/v1/tasks")
        async def tasks():
            return {"ok": True}

        async def inject_jwt(request: Request, call_next):
            request.state.jwt = jwt_claims
            return await call_next(request)

        app.middleware("http")(inject_jwt)

        response = TestClient(app).get("/api/v1/tasks")

    assert response.status_code == 200
    mock_enqueue.assert_awaited_once()
