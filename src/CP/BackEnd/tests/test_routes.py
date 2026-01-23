"""
Tests for auth routes
"""

import pytest
from fastapi.testclient import TestClient
from httpx import HTTPStatusError


pytestmark = pytest.mark.unit


def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_register_user_with_existing_email(client: TestClient):
    """Test registration with an existing email"""
    email = "existing@example.com"
    password = "Password123!"
    full_name = "Existing User"

    # Register the user first
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name}
    )
    assert response.status_code == 201

    # Attempt to register again
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name}
    )
    
    assert response.status_code == 400  # Expecting a bad request
    assert response.json() == {
        "type": "https://example.com/probs/duplicate-email",
        "title": "Duplicate Email",
        "status": 400,
        "detail": f"User with email {email} already exists"
    }


def test_login_with_invalid_credentials(client: TestClient):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "invalid@example.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401  # Unauthorized
    assert response.json() == {
        "type": "https://example.com/probs/invalid-credentials",
        "title": "Invalid Credentials",
        "status": 401,
        "detail": "Invalid email or password"
    }
