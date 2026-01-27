"""
Tests for Auth Middleware (GW-100)

This module contains tests for the AuthMiddleware to ensure proper JWT validation
and authorization handling.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from src.gateway.middleware.auth import AuthMiddleware, JWTClaims, validate_jwt

# Test FastAPI app
app = FastAPI()
app.add_middleware(AuthMiddleware)

@app.get("/api/v1/protected")
async def protected():
    return {"message": "Protected route"}

@pytest.fixture
def client():
    return TestClient(app)

def test_protected_route_without_token(client):
    """Test accessing protected route without token returns 401."""
    response = client.get("/api/v1/protected")
    assert response.status_code == 401
    assert response.json()["type"] == "https://waooaw.com/errors/unauthorized"

def test_protected_route_with_invalid_token(client):
    """Test accessing protected route with invalid token returns 401."""
    response = client.get("/api/v1/protected", headers={"Authorization": "Bearer invalid.token"})
    assert response.status_code == 401
    assert response.json()["type"] == "https://waooaw.com/errors/invalid-token"

def test_protected_route_with_valid_token(client):
    """Test accessing protected route with valid token returns 200."""
    # Create a valid JWT token for testing
    token = create_test_jwt(user_id="user-123", email="test@waooaw.com", roles=["user"])
    response = client.get("/api/v1/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Protected route"

def create_test_jwt(user_id, email, roles):
    """Helper function to create a test JWT token."""
    claims = {
        "user_id": user_id,
        "email": email,
        "roles": roles,
        "iat": 1705485600,
        "exp": 1705489200,
        "iss": "waooaw.com",
        "sub": user_id,
    }
    return validate_jwt(claims)
