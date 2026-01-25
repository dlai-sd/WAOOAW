"""
Tests for auth routes
"""

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


pytestmark = pytest.mark.unit


def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_google_login_redirects_with_state(client: TestClient):
    """Test Google login endpoint creates redirect URL with state"""
    response = client.get("/api/auth/google/login?source=cp", follow_redirects=False)
    
    assert response.status_code == 307  # RedirectResponse
    assert "google" in response.headers["location"]
    assert "client_id=" in response.headers["location"]
    assert "state=" in response.headers["location"]
    assert "redirect_uri=" in response.headers["location"]


def test_google_callback_with_error(client: TestClient):
    """Test Google callback handles OAuth errors"""
    response = client.get(
        "/api/auth/google/callback?error=access_denied&code=&state=",
        follow_redirects=False
    )
    
    assert response.status_code in (302, 307)  # RedirectResponse
    assert "error=access_denied" in response.headers["location"]


def test_google_callback_missing_params(client: TestClient):
    """Test Google callback validates required params"""
    response = client.get(
        "/api/auth/google/callback?code=&state=",
        follow_redirects=False
    )
    
    # FastAPI may return 422 for missing required params
    assert response.status_code in (302, 307, 422)
    if response.status_code != 422:
        assert "error=missing_params" in response.headers["location"]


def test_google_callback_invalid_state(client: TestClient):
    """Test Google callback rejects invalid state token"""
    response = client.get(
        "/api/auth/google/callback?code=test123&state=invalid_state&error=",
        follow_redirects=False
    )
    
    assert response.status_code in (302, 307)  # RedirectResponse
    assert "error=invalid_state" in response.headers["location"]


@patch("api.auth.google_oauth.get_user_from_google")
def test_google_callback_success_flow(mock_get_user, client: TestClient):
    """Test complete Google OAuth callback flow"""
    # First get state from login
    login_response = client.get("/api/auth/google/login?source=cp", follow_redirects=False)
    state = None
    for param in login_response.headers["location"].split("?")[1].split("&"):
        if param.startswith("state="):
            state = param.split("=")[1]
            break
    
    assert state is not None
    
    # Mock Google user info response
    mock_get_user.return_value = {
        "id": "google_123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg"
    }
    
    # Complete callback
    callback_response = client.get(
        f"/api/auth/google/callback?code=test_code&state={state}&error=",
        follow_redirects=False
    )
    
    assert callback_response.status_code in (302, 307)  # RedirectResponse
    location = callback_response.headers["location"]
    assert "access_token=" in location
    assert "refresh_token=" in location
    mock_get_user.assert_called_once()


@patch("api.auth.google_oauth.get_user_from_google")
def test_google_callback_auth_failure(mock_get_user, client: TestClient):
    """Test Google callback handles authentication failures"""
    # Get state from login
    login_response = client.get("/api/auth/google/login?source=pp", follow_redirects=False)
    state = None
    for param in login_response.headers["location"].split("?")[1].split("&"):
        if param.startswith("state="):
            state = param.split("=")[1]
            break
    
    # Mock exception during auth
    mock_get_user.side_effect = Exception("Auth failed")
    
    # Complete callback
    callback_response = client.get(
        f"/api/auth/google/callback?code=test_code&state={state}&error=",
        follow_redirects=False
    )
    
    assert callback_response.status_code in (302, 307)  # RedirectResponse
    assert "error=auth_failed" in callback_response.headers["location"]
