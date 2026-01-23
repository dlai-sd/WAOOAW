"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient
from .main import app  # Assuming your FastAPI app is in main.py

client = TestClient(app)

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
def test_token_endpoint():
    """Test token generation endpoint"""
    response = client.post("/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.unit
@pytest.mark.auth
def test_invalid_token():
    """Test invalid token handling"""
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
