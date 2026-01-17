"""
Tests for Error Handling Middleware (GW-105)

Tests RFC 7807 format, error type mapping, correlation IDs.
"""

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from middleware.error_handler import setup_error_handlers, create_problem_details


# Test RFC 7807 Format
def test_create_problem_details():
    """create_problem_details helper generates RFC 7807 format"""
    problem = create_problem_details(
        error_type="budget-exceeded",
        status=402,
        detail="Platform budget exceeded",
        instance="/api/v1/agents",
        platform_budget={"limit": 100, "spent": 105}
    )
    
    assert problem["type"] == "https://waooaw.com/errors/budget-exceeded"
    assert problem["title"] == "Budget Exceeded"
    assert problem["status"] == 402
    assert problem["detail"] == "Platform budget exceeded"
    assert problem["instance"] == "/api/v1/agents"
    assert problem["platform_budget"]["limit"] == 100


# Test HTTPException (401)
def test_error_handler_http_exception_401():
    """HTTPException 401 converted to RFC 7807"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.get("/api/v1/protected")
    async def protected():
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/protected")
    
    assert response.status_code == 401
    assert response.json()["type"] == "https://waooaw.com/errors/unauthorized"
    assert response.json()["title"] == "Unauthorized"
    assert response.json()["status"] == 401
    assert "missing" in response.json()["detail"].lower()
    assert response.json()["instance"] == "/api/v1/protected"
    assert response.headers["Content-Type"] == "application/problem+json"


# Test HTTPException (403)
def test_error_handler_http_exception_403():
    """HTTPException 403 converted to permission-denied"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.delete("/api/v1/agents/123")
    async def delete_agent():
        raise HTTPException(status_code=403, detail="Permission denied: requires delete:agents permission")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.delete("/api/v1/agents/123")
    
    assert response.status_code == 403
    assert response.json()["type"] == "https://waooaw.com/errors/permission-denied"
    assert response.json()["title"] == "Forbidden"
    assert "permission" in response.json()["detail"].lower()


# Test HTTPException (402)
def test_error_handler_http_exception_402():
    """HTTPException 402 converted to budget-exceeded"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.post("/api/v1/tasks")
    async def create_task():
        raise HTTPException(status_code=402, detail="Budget limit exceeded")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/v1/tasks", json={})
    
    assert response.status_code == 402
    assert response.json()["type"] == "https://waooaw.com/errors/budget-exceeded"
    assert response.json()["title"] == "Payment Required"


# Test HTTPException (429)
def test_error_handler_http_exception_429():
    """HTTPException 429 converted to trial-limit-exceeded"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.post("/api/v1/tasks")
    async def create_task():
        raise HTTPException(status_code=429, detail="Trial limit exceeded: 10 tasks per day")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/v1/tasks", json={})
    
    assert response.status_code == 429
    assert response.json()["type"] == "https://waooaw.com/errors/trial-limit-exceeded"
    assert "trial" in response.json()["detail"].lower()
    assert "limit" in response.json()["detail"].lower()


# Test HTTPException (404)
def test_error_handler_http_exception_404():
    """HTTPException 404 converted to not-found"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.get("/api/v1/agents/nonexistent")
    async def get_agent():
        raise HTTPException(status_code=404, detail="Agent not found")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/agents/nonexistent")
    
    assert response.status_code == 404
    assert response.json()["type"] == "https://waooaw.com/errors/not-found"
    assert response.json()["title"] == "Not Found"


# Test HTTPException (503)
def test_error_handler_http_exception_503():
    """HTTPException 503 converted to service-unavailable"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.get("/api/v1/agents")
    async def list_agents():
        raise HTTPException(status_code=503, detail="OPA service unavailable")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 503
    assert response.json()["type"] == "https://waooaw.com/errors/service-unavailable"
    assert "unavailable" in response.json()["detail"].lower()


# Test Unexpected Exception (500)
def test_error_handler_unexpected_exception():
    """Unexpected exception converted to internal-server-error"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.get("/api/v1/agents")
    async def list_agents():
        raise ValueError("Unexpected error")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 500
    assert response.json()["type"] == "https://waooaw.com/errors/internal-server-error"
    assert response.json()["title"] == "Internal Server Error"
    assert response.json()["status"] == 500
    # In production, generic message (not "Unexpected error")
    assert "error occurred" in response.json()["detail"].lower()


# Test Development Mode (Stack Traces)
def test_error_handler_development_mode():
    """Development mode includes stack traces"""
    app = FastAPI()
    setup_error_handlers(app, environment="development")
    
    @app.get("/api/v1/agents")
    async def list_agents():
        raise ValueError("Test error")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 500
    assert "trace" in response.json()  # Stack trace included
    assert "exception_type" in response.json()
    assert response.json()["exception_type"] == "ValueError"
    assert response.json()["detail"] == "Test error"  # Actual error shown in dev


# Test Correlation ID
def test_error_handler_correlation_id():
    """Error response includes correlation_id if present"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.get("/api/v1/agents")
    async def list_agents(request: Request):
        request.state.correlation_id = "corr-123-456"
        raise HTTPException(status_code=404, detail="Not found")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 404
    assert response.json()["correlation_id"] == "corr-123-456"


# Test Error Type Inference (Keyword-based)
def test_error_handler_infer_trial_expired():
    """Infer trial-expired from detail message"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.post("/api/v1/tasks")
    async def create_task():
        raise HTTPException(status_code=403, detail="Your trial has expired")
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/v1/tasks", json={})
    
    assert response.status_code == 403
    assert response.json()["type"] == "https://waooaw.com/errors/trial-expired"


def test_error_handler_infer_approval_required():
    """Infer approval-required from detail message"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.delete("/api/v1/agents/123")
    async def delete_agent():
        raise HTTPException(status_code=307, detail="Governor approval required for this action")
    
    client = TestClient(app, follow_redirects=False)
    response = client.delete("/api/v1/agents/123")
    
    assert response.status_code == 307
    assert response.json()["type"] == "https://waooaw.com/errors/approval-required"


# Test Successful Request (No Error)
def test_error_handler_successful_request():
    """Successful requests pass through unchanged"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.get("/api/v1/agents")
    async def list_agents():
        return {"agents": []}
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 200
    assert response.json() == {"agents": []}


# Test Public Endpoint Success
def test_error_handler_public_endpoint():
    """Public endpoints work normally"""
    app = FastAPI()
    setup_error_handlers(app, environment="production")
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
