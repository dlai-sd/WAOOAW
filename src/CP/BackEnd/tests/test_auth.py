"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient
from ..main import app

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
def test_create_access_token():
    response = client.post("/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user():
    token = "valid_token_here"  # Replace with a valid token for testing
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
