"""
Tests for RBAC Middleware (GW-101)

Tests 7-role hierarchy, OPA integration, permission checks, deny reasons.
"""

import pytest
import json
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from src.gateway.middleware.rbac import RBACMiddleware, UserInfo


# Test FastAPI app
app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/v1/agents")
async def list_agents(request: Request):
    user_info = request.state.user_info
    return {
        "agents": [],
        "user_id": user_info.user_id,
        "roles": user_info.roles
    }


@app.post("/api/v1/agents")
async def create_agent(request: Request):
    user_info = request.state.user_info
    return {
        "agent_id": "agent123",
        "created_by": user_info.user_id
    }


@app.delete("/api/v1/agents/{agent_id}")
async def delete_agent(agent_id: str, request: Request):
    user_info = request.state.user_info
    return {
        "deleted": agent_id,
        "deleted_by": user_info.user_id
    }


# Test fixtures
@pytest.fixture
def mock_jwt_claims():
    return {
        "user_id": "user123",
        "email": "user@example.com",
        "customer_id": "customer123",
        "roles": ["developer"],
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "user123"
    }


@pytest.fixture
def admin_jwt_claims():
    return {
        "user_id": "admin123",
        "email": "admin@example.com",
        "customer_id": "customer123",
        "roles": ["admin"],
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "admin123"
    }


@pytest.fixture
def viewer_jwt_claims():
    return {
        "user_id": "viewer123",
        "email": "viewer@example.com",
        "customer_id": "customer123",
        "roles": ["viewer"],
        "iat": 1234567890,
        "exp": 9999999999,
        "iss": "waooaw.com",
        "sub": "viewer123"
    }


# Test UserInfo class
def test_user_info_creation():
    user_info = UserInfo(
        user_id="user123",
        email="user@example.com",
        roles=["developer"],
        role_level=3,
        is_admin=False,
        permissions=["read:agents", "create:agents"]
    )
    
    assert user_info.user_id == "user123"
    assert user_info.email == "user@example.com"
    assert user_info.roles == ["developer"]
    assert user_info.role_level == 3
    assert user_info.is_admin is False
    assert user_info.permissions == ["read:agents", "create:agents"]


def test_user_info_has_permission():
    user_info = UserInfo(
        user_id="user123",
        email="user@example.com",
        roles=["developer"],
        role_level=3,
        is_admin=False,
        permissions=["read:agents", "create:agents", "update:agents"]
    )
    
    assert user_info.has_permission("read:agents") is True
    assert user_info.has_permission("create:agents") is True
    assert user_info.has_permission("delete:agents") is False


def test_user_info_to_dict():
    user_info = UserInfo(
        user_id="user123",
        email="user@example.com",
        roles=["developer"],
        role_level=3,
        is_admin=False,
        permissions=["read:agents"]
    )
    
    data = user_info.to_dict()
    assert data["user_id"] == "user123"
    assert data["email"] == "user@example.com"
    assert data["roles"] == ["developer"]
    assert data["role_level"] == 3


# Test RBAC Middleware - Admin Role
@pytest.mark.asyncio
async def test_rbac_admin_read_allowed(admin_jwt_claims):
    """Admin can read agents"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "user_info": {
                        "user_id": "admin123",
                        "email": "admin@example.com",
                        "roles": ["admin"],
                        "role_level": 1,
                        "is_admin": True,
                        "permissions": ["read:agents", "create:agents", "update:agents", "delete:agents"]
                    }
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.get("/api/v1/agents")
        async def list_agents(request: Request):
            user_info = request.state.user_info
            return {"user_id": user_info.user_id, "is_admin": user_info.is_admin}
        
        # Mock JWT in request state
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = admin_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.get("/api/v1/agents")
        
        assert response.status_code == 200
        assert response.json()["is_admin"] is True


@pytest.mark.asyncio
async def test_rbac_admin_delete_allowed(admin_jwt_claims):
    """Admin can delete agents"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "user_info": {
                        "user_id": "admin123",
                        "email": "admin@example.com",
                        "roles": ["admin"],
                        "role_level": 1,
                        "is_admin": True,
                        "permissions": ["delete:agents"]
                    }
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.delete("/api/v1/agents/{agent_id}")
        async def delete_agent(agent_id: str, request: Request):
            return {"deleted": agent_id}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = admin_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.delete("/api/v1/agents/agent123")
        
        assert response.status_code == 200


# Test RBAC Middleware - Developer Role
@pytest.mark.asyncio
async def test_rbac_developer_read_allowed(mock_jwt_claims):
    """Developer can read agents"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "user_info": {
                        "user_id": "user123",
                        "email": "user@example.com",
                        "roles": ["developer"],
                        "role_level": 3,
                        "is_admin": False,
                        "permissions": ["read:agents", "create:agents"]
                    }
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.get("/api/v1/agents")
        async def list_agents(request: Request):
            user_info = request.state.user_info
            return {"role_level": user_info.role_level}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.get("/api/v1/agents")
        
        assert response.status_code == 200
        assert response.json()["role_level"] == 3


@pytest.mark.asyncio
async def test_rbac_developer_create_allowed(mock_jwt_claims):
    """Developer can create agents"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "user_info": {
                        "user_id": "user123",
                        "email": "user@example.com",
                        "roles": ["developer"],
                        "role_level": 3,
                        "is_admin": False,
                        "permissions": ["create:agents"]
                    }
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.post("/api/v1/agents")
        async def create_agent(request: Request):
            return {"agent_id": "agent123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/agents", json={})
        
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_rbac_developer_delete_denied(mock_jwt_claims):
    """Developer cannot delete agents"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": False,
                    "deny_reason": "Insufficient permissions: requires delete:agents permission"
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.delete("/api/v1/agents/{agent_id}")
        async def delete_agent(agent_id: str):
            return {"deleted": agent_id}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.delete("/api/v1/agents/agent123")
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()


# Test RBAC Middleware - Viewer Role
@pytest.mark.asyncio
async def test_rbac_viewer_read_allowed(viewer_jwt_claims):
    """Viewer can read agents"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "user_info": {
                        "user_id": "viewer123",
                        "email": "viewer@example.com",
                        "roles": ["viewer"],
                        "role_level": 7,
                        "is_admin": False,
                        "permissions": ["read:agents"]
                    }
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.get("/api/v1/agents")
        async def list_agents(request: Request):
            user_info = request.state.user_info
            return {"role_level": user_info.role_level}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = viewer_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.get("/api/v1/agents")
        
        assert response.status_code == 200
        assert response.json()["role_level"] == 7


@pytest.mark.asyncio
async def test_rbac_viewer_create_denied(viewer_jwt_claims):
    """Viewer cannot create agents"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": False,
                    "deny_reason": "Insufficient permissions: viewer role cannot create agents"
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.post("/api/v1/agents")
        async def create_agent():
            return {"agent_id": "agent123"}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = viewer_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.post("/api/v1/agents", json={})
        
        assert response.status_code == 403
        assert "viewer" in response.json()["detail"].lower()


# Test Public Endpoints
@pytest.mark.asyncio
async def test_rbac_public_endpoint_bypassed():
    """Public endpoints bypass RBAC"""
    test_app = FastAPI()
    test_app.add_middleware(
        RBACMiddleware,
        opa_service_url="http://opa:8181",
        gateway_type="PP"
    )
    
    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    client = TestClient(test_app)
    response = client.get("/health")
    
    assert response.status_code == 200


# Test CP Gateway Bypass
@pytest.mark.asyncio
async def test_rbac_cp_gateway_bypassed(mock_jwt_claims):
    """RBAC skipped on CP Gateway"""
    test_app = FastAPI()
    test_app.add_middleware(
        RBACMiddleware,
        opa_service_url="http://opa:8181",
        gateway_type="CP"  # CP Gateway
    )
    
    @test_app.get("/api/v1/agents")
    async def list_agents():
        return {"agents": []}
    
    async def mock_middleware(request: Request, call_next):
        request.state.jwt = mock_jwt_claims
        return await call_next(request)
    
    test_app.middleware("http")(mock_middleware)
    
    client = TestClient(test_app)
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 200


# Test OPA Timeout
@pytest.mark.asyncio
async def test_rbac_opa_timeout(mock_jwt_claims):
    """OPA timeout returns 503"""
    import httpx
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP",
            timeout=2
        )
        
        @test_app.get("/api/v1/agents")
        async def list_agents():
            return {"agents": []}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.get("/api/v1/agents")
        
        assert response.status_code == 503
        assert "timeout" in response.json()["detail"].lower()


# Test Missing JWT Claims
@pytest.mark.asyncio
async def test_rbac_missing_jwt_claims():
    """Missing JWT claims returns 500"""
    test_app = FastAPI()
    test_app.add_middleware(
        RBACMiddleware,
        opa_service_url="http://opa:8181",
        gateway_type="PP"
    )
    
    @test_app.get("/api/v1/agents")
    async def list_agents():
        return {"agents": []}
    
    client = TestClient(test_app)
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 500
    assert "jwt claims" in response.json()["detail"].lower()


# Test Response Headers
@pytest.mark.asyncio
async def test_rbac_response_headers(mock_jwt_claims):
    """RBAC adds headers to response"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "result": {
                    "allow": True,
                    "user_info": {
                        "user_id": "user123",
                        "email": "user@example.com",
                        "roles": ["developer"],
                        "role_level": 3,
                        "is_admin": False,
                        "permissions": ["read:agents"]
                    }
                }
            }
        )
        
        test_app = FastAPI()
        test_app.add_middleware(
            RBACMiddleware,
            opa_service_url="http://opa:8181",
            gateway_type="PP"
        )
        
        @test_app.get("/api/v1/agents")
        async def list_agents():
            return {"agents": []}
        
        async def mock_middleware(request: Request, call_next):
            request.state.jwt = mock_jwt_claims
            return await call_next(request)
        
        test_app.middleware("http")(mock_middleware)
        
        client = TestClient(test_app)
        response = client.get("/api/v1/agents")
        
        assert response.status_code == 200
        assert "X-RBAC-User-ID" in response.headers
        assert "X-RBAC-Roles" in response.headers
        assert "X-RBAC-Role-Level" in response.headers
        assert response.headers["X-RBAC-User-ID"] == "user123"
        assert response.headers["X-RBAC-Roles"] == "developer"
        assert response.headers["X-RBAC-Role-Level"] == "3"
