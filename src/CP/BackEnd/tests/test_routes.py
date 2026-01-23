"""
Tests for auth routes
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from api.auth.google_oauth import get_user_from_google, verify_google_token
from api.auth.user_store import get_user_store
from core.security import standardize_error_handling


pytestmark = pytest.mark.unit


def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_get_user_from_google(client: TestClient):
    """Test getting user info from Google"""
    # Mock the function call to simulate Google response
    # This should be replaced with actual test logic
    pass


def test_verify_google_token(client: TestClient):
    """Test verifying Google ID token"""
    # Mock the function call to simulate Google response
    # This should be replaced with actual test logic
    pass


def test_standardize_error_handling():
    """Test standardize error handling"""
    with pytest.raises(HTTPException):
        raise HTTPException(status_code=400, detail="Bad Request")

    response = standardize_error_handling(HTTPException(status_code=400, detail="Bad Request"))
    assert response["status_code"] == 400
    assert response["detail"] == "Bad Request"

    response = standardize_error_handling(Exception("Some error"))
    assert response["status_code"] == 500
    assert response["detail"] == "Internal Server Error"
