"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient
from src.CP.BackEnd.api.auth import router
from src.CP.BackEnd.core.security import hash_password, validate_token

client = TestClient(router)

@pytest.mark.unit
@pytest.mark.auth
def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user_unauthorized():
    """Test getting current user without auth"""
    response = client.get("/api/auth/me")
    assert response.status_code in [401, 403]  # Either is acceptable for unauthorized

@pytest.mark.unit
@pytest.mark.auth
def test_google_login_endpoint_exists():
    """Test that Google login endpoint exists."""
    response = client.get("/api/auth/google/login", follow_redirects=False)
    assert response.status_code != 404

@pytest.mark.unit
@pytest.mark.auth
def test_login():
    """Test login endpoint returns valid JWT"""
    response = client.post("/api/auth/token", data={"username": "test_user", "password": "test_password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.unit
@pytest.mark.auth
def test_token_validation():
    """Test token validation"""
    token_response = client.post("/api/auth/token", data={"username": "test_user", "password": "test_password"})
    token = token_response.json()["access_token"]
    payload = validate_token(token)
    assert "user_id" in payload
    assert "tenant_id" in payload
