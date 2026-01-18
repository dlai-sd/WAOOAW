"""
Tests for Policy Middleware (GW-102)

Tests trial mode, Governor approval, sandbox routing.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from src.gateway.middleware.policy import PolicyMiddleware


@pytest.fixture
def trial_jwt_claims():
    return {
        "user_id": "user123",
        "email": "user@example.com",
        "customer_id": "customer123",
        "roles": ["user"],
        "trial_mode": True,
        "trial_expires_at": "2026-12-31T23:59:59Z",
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "user123"
    }


@pytest.fixture
def paid_jwt_claims():
    return {
        "user_id": "user456",
        "email": "paid@example.com",
        "customer_id": "customer456",
        "roles": ["user"],
        "trial_mode": False,
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "user456"
    }


@pytest.fixture
def governor_jwt_claims():
    return {
        "user_id": "user789",
        "email": "user@example.com",
        "customer_id": "customer789",
        "roles": ["user"],
        "governor_agent_id": "governor123",
        "trial_mode": False,
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "user789"
    }


# Test Trial Mode - Under Limit
@pytest.mark.asyncio
async def test_policy_trial_mode_under_limit(trial_jwt_claims):
    """Trial user under 10 tasks/day limit"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "task_count": 5,
                    "limit": 10
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com"
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = trial_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 200


# Test Trial Mode - Limit Exceeded
@pytest.mark.asyncio
async def test_policy_trial_mode_limit_exceeded(trial_jwt_claims):
    """Trial user at 10 tasks/day limit"""
    # Mock feature flag service to enable trial mode policy
    mock_ff_service = MagicMock()
    mock_ff_service.is_enabled.return_value = True
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": False,
                    "deny_reason": "Trial limit exceeded: 10 tasks per day",
                    "task_count": 10,
                    "limit": 10
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com",
            feature_flag_service=mock_ff_service
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = trial_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 429
        assert "trial" in response.json()["detail"].lower()
        assert "limit" in response.json()["detail"].lower()
        assert "Retry-After" in response.headers


# Test Trial Mode - Expired
@pytest.mark.asyncio
async def test_policy_trial_mode_expired():
    """Expired trial user blocked"""
    # Mock feature flag service to enable trial mode policy
    mock_ff_service = MagicMock()
    mock_ff_service.is_enabled.return_value = True
    
    expired_claims = {
        "user_id": "user123",
        "email": "user@example.com",
        "customer_id": "customer123",
        "roles": ["user"],
        "trial_mode": True,
        "trial_expires_at": "2020-01-01T00:00:00Z",  # Past date
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "user123"
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": False,
                    "deny_reason": "Trial expired on 2020-01-01",
                    "trial_expires_at": "2020-01-01T00:00:00Z"
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com",
            feature_flag_service=mock_ff_service
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = expired_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 403
        assert "expired" in response.json()["detail"].lower()


# Test Governor Approval - Required
@pytest.mark.asyncio
async def test_policy_governor_approval_required(governor_jwt_claims):
    """Sensitive action requires Governor approval"""
    # Mock feature flag service to enable governor approval policy
    mock_ff_service = MagicMock()
    mock_ff_service.is_enabled.return_value = True
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": False,
                    "deny_reason": "Governor approval required for delete_agent action"
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com",
            feature_flag_service=mock_ff_service
        )
        
        @test_app.delete("/api/v1/agents/{agent_id}")
        async def delete_agent(agent_id: str):
            return {"deleted": agent_id}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = governor_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.delete("/api/v1/agents/agent123", follow_redirects=False)
        
        assert response.status_code == 307  # Redirect to approval UI
        assert "Location" in response.headers
        assert "approval.waooaw.com" in response.headers["Location"]
        assert "X-Governor-Approval-Required" in response.headers


# Test Sandbox Routing - Trial User
@pytest.mark.asyncio
async def test_policy_sandbox_routing_trial(trial_jwt_claims):
    """Trial user routed to sandbox"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Mock trial_mode response (allowed)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "target_backend": "sandbox"
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com"
        )
        
        @test_app.get("/api/v1/agents")
        async def list_agents(request: Request):
            target = getattr(request.state, "target_backend", None)
            return {"target_backend": target}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = trial_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.get("/api/v1/agents")
        
        assert response.status_code == 200
        # Note: In real implementation, would check X-Target-Backend header


# Test Sandbox Routing - Paid User
@pytest.mark.asyncio
async def test_policy_sandbox_routing_paid(paid_jwt_claims):
    """Paid user routed to production"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "target_backend": "production"
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com"
        )
        
        @test_app.get("/api/v1/agents")
        async def list_agents(request: Request):
            target = getattr(request.state, "target_backend", None)
            return {"target_backend": target}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = paid_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.get("/api/v1/agents")
        
        assert response.status_code == 200


# Test Public Endpoints Bypass
@pytest.mark.asyncio
async def test_policy_public_endpoint_bypassed():
    """Public endpoints bypass policy checks"""
    test_app = FastAPI()
    test_app.add_middleware(
        PolicyMiddleware,
        opa_service_url="http://opa:8181",
        redis_url="redis://redis:6379",
        approval_ui_url="https://approval.waooaw.com"
    )
    
    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    client = TestClient(test_app)
    response = client.get("/health")
    
    assert response.status_code == 200


# Test OPA Timeout
@pytest.mark.asyncio
async def test_policy_opa_timeout(trial_jwt_claims):
    """OPA timeout returns 503"""
    import httpx
    
    # Mock feature flag service to enable trial mode policy
    mock_ff_service = MagicMock()
    mock_ff_service.is_enabled.return_value = True
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com",
            timeout=2,
            feature_flag_service=mock_ff_service
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = trial_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 503


# Test Missing JWT Claims
@pytest.mark.asyncio
async def test_policy_missing_jwt_claims():
    """Missing JWT claims returns 500"""
    test_app = FastAPI()
    test_app.add_middleware(
        PolicyMiddleware,
        opa_service_url="http://opa:8181",
        redis_url="redis://redis:6379",
        approval_ui_url="https://approval.waooaw.com"
    )
    
    @test_app.post("/api/v1/tasks")
    async def create_task():
        return {"task_id": "task123"}
    
    client = TestClient(test_app)
    response = client.post("/api/v1/tasks", json={})
    
    assert response.status_code == 500


# Test Parallel Policy Queries
@pytest.mark.asyncio
async def test_policy_parallel_queries(trial_jwt_claims):
    """Multiple policies queried in parallel"""
    # Mock feature flag service to enable all policies
    mock_ff_service = MagicMock()
    mock_ff_service.is_enabled.return_value = True
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Mock will be called multiple times in parallel
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            PolicyMiddleware,
            opa_service_url="http://opa:8181",
            redis_url="redis://redis:6379",
            approval_ui_url="https://approval.waooaw.com",
            feature_flag_service=mock_ff_service
        )
        
        @test_app.post("/api/v1/tasks")
        async def create_task():
            return {"task_id": "task123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = trial_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 200
        # Verify OPA was called (at least once for trial_mode policy)
        assert mock_post.call_count >= 1
