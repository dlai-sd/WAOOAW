"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..auth.jwt_auth import create_access_token, verify_token

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
    """Test that Google login endpoint exists.

    This endpoint redirects to Google OAuth, so we MUST disable redirects here.
    Otherwise the test becomes dependent on external network availability.
    """
    response = client.get("/api/auth/google/login", follow_redirects=False)

    # Should redirect (3xx) or otherwise respond (but not 404)
    assert response.status_code != 404


def test_create_access_token():
    token = create_access_token({"user_id": "test_user"})
    assert token is not None

def test_verify_token():
    token = create_access_token({"user_id": "test_user"})
    payload = verify_token(token)
    assert payload["user_id"] == "test_user"
