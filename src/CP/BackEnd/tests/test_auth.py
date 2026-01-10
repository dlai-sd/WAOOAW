"""
Unit tests for authentication routes
"""
import pytest


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
    """Test that Google login endpoint exists"""
    response = client.get("/api/auth/google/login")
    
    # Should redirect or return some response (not 404)
    assert response.status_code != 404
