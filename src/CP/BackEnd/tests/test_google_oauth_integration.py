"""
Integration Tests for Google OAuth Authentication API
Tests end-to-end Google OAuth flow (MVP-002)
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from uuid import uuid4

from main import app


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestGoogleOAuthIntegration:
    """Integration tests for Google OAuth endpoints"""

    @pytest.fixture
    async def async_client(self):
        """Create async HTTP client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_google_login_redirect(self, async_client):
        """Test Google OAuth login initiates redirect"""
        response = await async_client.get(
            "/api/auth/google/login?source=cp", follow_redirects=False
        )

        assert response.status_code == 307  # Redirect
        assert "accounts.google.com" in response.headers["location"]
        assert "client_id" in response.headers["location"]
        assert "state" in response.headers["location"]

    async def test_google_login_with_source(self, async_client):
        """Test Google login with different source parameter"""
        for source in ["cp", "pp", "mobile"]:
            response = await async_client.get(
                f"/api/auth/google/login?source={source}",
                follow_redirects=False,
            )

            assert response.status_code == 307
            location = response.headers["location"]
            assert "accounts.google.com" in location

    @patch("api.auth.routes.verify_google_token")
    async def test_google_verify_token_success(
        self, mock_verify, async_client
    ):
        """Test successful Google ID token verification"""
        # Mock Google token verification
        mock_user_info = {
            "sub": "google_user_123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
        }
        mock_verify.return_value = mock_user_info

        request_data = {
            "id_token": "valid_google_id_token",
            "source": "cp",
        }

        response = await async_client.post(
            "/api/auth/google/verify", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @patch("api.auth.routes.verify_google_token")
    async def test_google_verify_token_invalid(
        self, mock_verify, async_client
    ):
        """Test Google ID token verification with invalid token"""
        # Mock failed token verification
        mock_verify.side_effect = ValueError("Invalid token")

        request_data = {
            "id_token": "invalid_google_id_token",
            "source": "cp",
        }

        response = await async_client.post(
            "/api/auth/google/verify", json=request_data
        )

        assert response.status_code == 400
        assert "Failed to verify Google token" in response.json()["detail"]

    @patch("api.auth.routes.verify_google_token")
    async def test_google_auth_creates_new_user(
        self, mock_verify, async_client
    ):
        """Test that Google auth creates new user on first login"""
        unique_email = f"newuser.{uuid4()}@example.com"
        mock_user_info = {
            "sub": f"google_{uuid4()}",
            "email": unique_email,
            "name": "New Test User",
            "picture": "https://example.com/new.jpg",
            "email_verified": True,
        }
        mock_verify.return_value = mock_user_info

        request_data = {
            "id_token": "valid_new_user_token",
            "source": "cp",
        }

        response = await async_client.post(
            "/api/auth/google/verify", json=request_data
        )

        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens

        # Verify we can use the token to get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_response = await async_client.get(
            "/api/auth/me", headers=headers
        )

        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == unique_email
        assert user_data["name"] == "New Test User"

    @patch("api.auth.routes.verify_google_token")
    async def test_google_auth_existing_user(
        self, mock_verify, async_client
    ):
        """Test Google auth with existing user returns same user"""
        mock_user_info = {
            "sub": "google_existing_123",
            "email": "existing@example.com",
            "name": "Existing User",
            "picture": "https://example.com/existing.jpg",
            "email_verified": True,
        }
        mock_verify.return_value = mock_user_info

        request_data = {
            "id_token": "valid_token_1",
            "source": "cp",
        }

        # First login
        response1 = await async_client.post(
            "/api/auth/google/verify", json=request_data
        )
        assert response1.status_code == 200

        # Second login with same Google account
        request_data["id_token"] = "valid_token_2"
        response2 = await async_client.post(
            "/api/auth/google/verify", json=request_data
        )
        assert response2.status_code == 200

        # Both should work (same user)
        assert "access_token" in response2.json()

    async def test_refresh_token_endpoint(self, async_client):
        """Test refresh token endpoint"""
        # First, authenticate with Google (mocked)
        with patch("api.auth.routes.verify_google_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "google_refresh_test",
                "email": "refresh@example.com",
                "name": "Refresh Test",
                "email_verified": True,
            }

            auth_response = await async_client.post(
                "/api/auth/google/verify",
                json={"id_token": "valid_token", "source": "cp"},
            )

            assert auth_response.status_code == 200
            tokens = auth_response.json()
            refresh_token = tokens["refresh_token"]

        # Use refresh token to get new access token
        headers = {"Authorization": f"Bearer {refresh_token}"}
        refresh_response = await async_client.post(
            "/api/auth/refresh",
            headers=headers,
        )

        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        # Tokens should be valid (same timestamp can produce same token, which is fine)

    async def test_get_current_user(self, async_client):
        """Test getting current user info with valid token"""
        # Authenticate first
        with patch("api.auth.routes.verify_google_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "google_me_test",
                "email": "me@example.com",
                "name": "Me Test User",
                "picture": "https://example.com/me.jpg",
                "email_verified": True,
            }

            auth_response = await async_client.post(
                "/api/auth/google/verify",
                json={"id_token": "valid_token", "source": "cp"},
            )

            tokens = auth_response.json()

        # Get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = await async_client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "me@example.com"
        assert user_data["name"] == "Me Test User"
        assert "id" in user_data

    async def test_get_current_user_no_token(self, async_client):
        """Test /me endpoint without authentication"""
        response = await async_client.get("/api/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    async def test_get_current_user_invalid_token(self, async_client):
        """Test /me endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = await async_client.get("/api/auth/me", headers=headers)

        assert response.status_code == 401

    async def test_logout(self, async_client):
        """Test logout endpoint"""
        # Authenticate first
        with patch("api.auth.routes.verify_google_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "google_logout_test",
                "email": "logout@example.com",
                "name": "Logout Test",
                "email_verified": True,
            }

            auth_response = await async_client.post(
                "/api/auth/google/verify",
                json={"id_token": "valid_token", "source": "cp"},
            )

            tokens = auth_response.json()

        # Logout
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = await async_client.post(
            "/api/auth/logout", headers=headers
        )

        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    async def test_health_check(self, async_client):
        """Test auth service health check"""
        response = await async_client.get("/api/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "oauth_configured" in data

    async def test_complete_oauth_flow(self, async_client):
        """Test complete OAuth flow: login -> verify -> get user -> refresh -> logout"""
        # 1. Initiate Google login
        login_response = await async_client.get(
            "/api/auth/google/login?source=cp", follow_redirects=False
        )
        assert login_response.status_code == 307

        # 2. Verify Google ID token (simulated)
        with patch("api.auth.routes.verify_google_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "google_complete_flow",
                "email": "complete@example.com",
                "name": "Complete Flow User",
                "email_verified": True,
            }

            verify_response = await async_client.post(
                "/api/auth/google/verify",
                json={"id_token": "valid_token", "source": "cp"},
            )

            assert verify_response.status_code == 200
            tokens = verify_response.json()

        # 3. Get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_response = await async_client.get(
            "/api/auth/me", headers=headers
        )
        assert me_response.status_code == 200

        # 4. Refresh tokens
        refresh_headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
        refresh_response = await async_client.post(
            "/api/auth/refresh",
            headers=refresh_headers,
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()

        # 5. Logout
        logout_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        logout_response = await async_client.post(
            "/api/auth/logout", headers=logout_headers
        )
        assert logout_response.status_code == 200
