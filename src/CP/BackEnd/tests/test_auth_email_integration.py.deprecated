"""
Integration Tests for Email/Password Authentication API
Tests end-to-end auth flow (MVP-002)
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from main import app


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthEmailAPIIntegration:
    """Integration tests for email/password auth endpoints"""

    @pytest.fixture
    async def async_client(self):
        """Create async HTTP client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_register_user_success(self, async_client):
        """Test successful user registration"""
        unique_email = f"test.{uuid4()}@example.com"
        user_data = {
            "email": unique_email,
            "password": "SecurePass123!",
            "full_name": "Test User",
        }

        response = await async_client.post(
            "/api/v1/auth/register", json=user_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == unique_email
        assert data["full_name"] == "Test User"
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose hash

    async def test_register_user_duplicate_email(self, async_client):
        """Test registering with existing email"""
        unique_email = f"duplicate.{uuid4()}@example.com"
        user_data = {
            "email": unique_email,
            "password": "SecurePass123!",
            "full_name": "First User",
        }

        # First registration
        response1 = await async_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert response1.status_code == 201

        # Duplicate registration
        response2 = await async_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already registered" in data["detail"].lower()

    async def test_register_user_invalid_email(self, async_client):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "full_name": "Test User",
        }

        response = await async_client.post(
            "/api/v1/auth/register", json=user_data
        )

        assert response.status_code == 422

    async def test_login_user_success(self, async_client):
        """Test successful login"""
        # Register user first
        unique_email = f"login.{uuid4()}@example.com"
        password = "LoginPass123!"
        register_data = {
            "email": unique_email,
            "password": password,
            "full_name": "Login Test User",
        }
        register_response = await async_client.post(
            "/api/v1/auth/register", json=register_data
        )
        assert register_response.status_code == 201

        # Login
        login_data = {
            "email": unique_email,
            "password": password,
        }
        response = await async_client.post(
            "/api/v1/auth/login", json=login_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    async def test_login_user_wrong_password(self, async_client):
        """Test login with incorrect password"""
        # Register user
        unique_email = f"wrongpass.{uuid4()}@example.com"
        register_data = {
            "email": unique_email,
            "password": "CorrectPass123!",
            "full_name": "Test User",
        }
        register_response = await async_client.post(
            "/api/v1/auth/register", json=register_data
        )
        assert register_response.status_code == 201

        # Login with wrong password
        login_data = {
            "email": unique_email,
            "password": "WrongPass456!",
        }
        response = await async_client.post(
            "/api/v1/auth/login", json=login_data
        )

        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    async def test_login_user_not_found(self, async_client):
        """Test login with non-existent user"""
        login_data = {
            "email": f"nonexistent.{uuid4()}@example.com",
            "password": "SomePass123!",
        }

        response = await async_client.post(
            "/api/v1/auth/login", json=login_data
        )

        assert response.status_code == 401

    async def test_get_current_user_success(self, async_client):
        """Test getting current user with valid token"""
        # Register and login
        unique_email = f"getme.{uuid4()}@example.com"
        password = "GetMePass123!"
        register_data = {
            "email": unique_email,
            "password": password,
            "full_name": "GetMe Test User",
        }
        register_response = await async_client.post(
            "/api/v1/auth/register", json=register_data
        )
        assert register_response.status_code == 201

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password},
        )
        access_token = login_response.json()["access_token"]

        # Get current user
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email
        assert data["full_name"] == "GetMe Test User"

    async def test_get_current_user_no_token(self, async_client):
        """Test getting current user without token"""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_get_current_user_invalid_token(self, async_client):
        """Test getting current user with invalid token"""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_123"},
        )

        assert response.status_code == 401

    async def test_logout(self, async_client):
        """Test logout endpoint"""
        response = await async_client.post("/api/v1/auth/logout")

        # Stateless JWT, so just returns 204
        assert response.status_code == 204

    async def test_auth_flow_complete(self, async_client):
        """Test complete authentication flow"""
        unique_email = f"flow.{uuid4()}@example.com"
        password = "FlowPass123!"

        # 1. Register
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "Flow Test User",
            },
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 3. Get user profile with token
        profile_response = await async_client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {tokens['access_token']}"
            },
        )
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["email"] == unique_email

        # 4. Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout"
        )
        assert logout_response.status_code == 204
