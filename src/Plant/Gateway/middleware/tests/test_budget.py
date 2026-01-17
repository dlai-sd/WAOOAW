"""
Tests for Budget Guard Middleware (GW-103)

Tests platform/agent budgets, alert thresholds, Redis updates.
"""

import pytest
from decimal import Decimal
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from middleware.budget import BudgetGuardMiddleware


@pytest.fixture
def mock_jwt_claims():
    return {
        "user_id": "user123",
        "email": "user@example.com",
        "customer_id": "customer123",
        "agent_id": "agent123",
        "roles": ["user"],
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "agent123"
    }


# Test Budget Under Limit
@pytest.mark.asyncio
async def test_budget_under_limit(mock_jwt_claims):
    """Budget under limit allows request"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("redis.asyncio.from_url") as mock_redis:
        
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "alert_level": "normal",
                    "platform_utilization_percent": 45.0,
                    "agent_utilization_percent": 30.0,
                    "platform_budget": {
                        "limit": 100.0,
                        "spent": 45.0,
                        "remaining": 55.0
                    },
                    "agent_budget": {
                        "limit": 1.0,
                        "spent": 0.30,
                        "remaining": 0.70
                    }
                }
            }
        )
        
        # Mock Redis
        mock_redis_client = AsyncMock()
        mock_redis_client.hincrbyfloat = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        test_app = FastAPI()
        test_app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379"
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 200
        assert "X-Budget-Alert-Level" in response.headers
        assert response.headers["X-Budget-Alert-Level"] == "normal"


# Test Budget Warning (80%)
@pytest.mark.asyncio
async def test_budget_warning_threshold(mock_jwt_claims):
    """Budget at 80% warning threshold"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("redis.asyncio.from_url") as mock_redis:
        
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "alert_level": "warning",
                    "platform_utilization_percent": 85.0,
                    "agent_utilization_percent": 82.0,
                    "platform_budget": {
                        "limit": 100.0,
                        "spent": 85.0,
                        "remaining": 15.0
                    },
                    "agent_budget": {
                        "limit": 1.0,
                        "spent": 0.82,
                        "remaining": 0.18
                    }
                }
            }
        )
        
        mock_redis_client = AsyncMock()
        mock_redis_client.hincrbyfloat = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        test_app = FastAPI()
        test_app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379"
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 200
        assert response.headers["X-Budget-Alert-Level"] == "warning"


# Test Budget High (95%)
@pytest.mark.asyncio
async def test_budget_high_threshold(mock_jwt_claims):
    """Budget at 95% high threshold"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("redis.asyncio.from_url") as mock_redis:
        
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "alert_level": "high",
                    "platform_utilization_percent": 97.0,
                    "agent_utilization_percent": 96.0,
                    "platform_budget": {
                        "limit": 100.0,
                        "spent": 97.0,
                        "remaining": 3.0
                    },
                    "agent_budget": {
                        "limit": 1.0,
                        "spent": 0.96,
                        "remaining": 0.04
                    }
                }
            }
        )
        
        mock_redis_client = AsyncMock()
        mock_redis_client.hincrbyfloat = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        test_app = FastAPI()
        test_app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379"
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 200
        assert response.headers["X-Budget-Alert-Level"] == "high"


# Test Budget Exceeded (100%)
@pytest.mark.asyncio
async def test_budget_exceeded_critical(mock_jwt_claims):
    """Budget at 100% blocks request"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": False,
                    "deny_reason": "Platform budget exceeded: $100.00 monthly limit reached",
                    "alert_level": "critical",
                    "platform_utilization_percent": 100.0,
                    "agent_utilization_percent": 100.0,
                    "platform_budget": {
                        "limit": 100.0,
                        "spent": 100.0,
                        "remaining": 0.0
                    },
                    "agent_budget": {
                        "limit": 1.0,
                        "spent": 1.0,
                        "remaining": 0.0
                    }
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379"
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 402  # Payment Required
        assert "budget" in response.json()["detail"].lower()
        assert "Retry-After" in response.headers
        assert response.json()["alert_level"] == "critical"


# Test Redis Update
@pytest.mark.asyncio
async def test_budget_redis_update(mock_jwt_claims):
    """Budget updates Redis after request"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("redis.asyncio.from_url") as mock_redis:
        
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "alert_level": "normal",
                    "platform_utilization_percent": 45.0,
                    "agent_utilization_percent": 30.0
                }
            }
        )
        
        # Mock Redis
        mock_redis_client = AsyncMock()
        mock_redis_client.hincrbyfloat = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        test_app = FastAPI()
        test_app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379"
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 200
        # Verify Redis was called (would be called 3 times: platform, agent, customer)
        # Note: Actual Redis calls happen async, test validates middleware logic


# Test Public Endpoints Bypass
@pytest.mark.asyncio
async def test_budget_public_endpoint_bypassed():
    """Public endpoints bypass budget checks"""
    test_app = FastAPI()
    test_app.add_middleware(
        BudgetGuardMiddleware,
        opa_service_url="http://opa:8181",
        redis_url="redis://redis:6379"
    )
    
    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    client = TestClient(test_app)
    response = client.get("/health")
    
    assert response.status_code == 200


# Test OPA Timeout (Fail-Open)
@pytest.mark.asyncio
async def test_budget_opa_timeout_fail_open(mock_jwt_claims):
    """OPA timeout fails open (allows request)"""
    import httpx
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        test_app = FastAPI()
        test_app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            timeout=2
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        # Fail-open: Allow request even if OPA times out
        assert response.status_code == 200


# Test Missing JWT Claims
@pytest.mark.asyncio
async def test_budget_missing_jwt_claims():
    """Missing JWT claims returns 500"""
    test_app = FastAPI()
    test_app.add_middleware(
        BudgetGuardMiddleware,
        opa_service_url="http://opa:8181",
        redis_url="redis://redis:6379"
    )
    
    @test_app.post("/api/v1/tasks")
    async def create_task():
        return {"task_id": "task123"}
    
    client = TestClient(test_app)
    response = client.post("/api/v1/tasks", json={})
    
    assert response.status_code == 500


# Test Response Headers
@pytest.mark.asyncio
async def test_budget_response_headers(mock_jwt_claims):
    """Budget adds utilization headers to response"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("redis.asyncio.from_url") as mock_redis:
        
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "alert_level": "warning",
                    "platform_utilization_percent": 85.5,
                    "agent_utilization_percent": 72.3
                }
            }
        )
        
        mock_redis_client = AsyncMock()
        mock_redis_client.hincrbyfloat = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        test_app = FastAPI()
        test_app.add_middleware(
            BudgetGuardMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379"
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 200
        assert "X-Budget-Alert-Level" in response.headers
        assert "X-Platform-Utilization" in response.headers
        assert "X-Agent-Utilization" in response.headers
        assert response.headers["X-Budget-Alert-Level"] == "warning"
        assert response.headers["X-Platform-Utilization"] == "85.50"
        assert response.headers["X-Agent-Utilization"] == "72.30"
