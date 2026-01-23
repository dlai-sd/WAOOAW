"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient
from src.CP.BackEnd.core.security import hash_password, get_current_user

@pytest.mark.unit
@pytest.mark.auth
def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user_unauthorized(client):
    """Test getting current user without auth"""
    response = client.get("/api/auth/me")
    
    assert response.status_code in [401, 403]  # Either is acceptable for unauthorized


@pytest.mark.unit
@pytest.mark.auth
def test_google_login_endpoint_exists(client):
    """Test that Google login endpoint exists.

    This endpoint redirects to Google OAuth, so we MUST disable redirects here.
    Otherwise the test becomes dependent on external network availability.
    """
    response = client.get("/api/auth/google/login", follow_redirects=False)

    # Should redirect (3xx) or otherwise respond (but not 404)
    assert response.status_code != 404


@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user_with_token(client):
    """Test getting current user with valid token"""
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    assert response.json() == {"user_id": "user_id"}
