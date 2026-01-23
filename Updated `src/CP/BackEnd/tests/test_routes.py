"""
Tests for auth routes
"""

import pytest
from fastapi.testclient import TestClient
from src.CP.BackEnd.core.security import hash_password

pytestmark = pytest.mark.unit

def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401

def test_hash_password():
    """Test password hashing"""
    password = "mysecretpassword"
    hashed = hash_password(password)
    assert hashed != password  # Ensure the password is hashed
