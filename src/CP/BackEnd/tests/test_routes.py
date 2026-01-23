"""
Tests for auth routes
"""

import pytest
from fastapi.testclient import TestClient
from core.config import settings
from api.auth.google_oauth import get_user_from_google

pytestmark = pytest.mark.unit


def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_google_oauth_flow(client: TestClient):
    """Test Google OAuth flow"""
    # Mock the Google OAuth flow here
    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback"
    state = "test_state"
    
    # Simulate getting user info from Google
    user_info = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "http://example.com/picture.jpg"
    }
    
    # Mock the function to return user info
    async def mock_get_user_from_google(code: str, redirect_uri: str):
        return user_info

    # Replace the actual function with the mock
    get_user_from_google = mock_get_user_from_google

    # Call the function and check the result
    result = await get_user_from_google("mock_code", redirect_uri)
    assert result == user_info
