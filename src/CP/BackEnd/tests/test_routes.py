"""
Tests for auth routes
"""

import pytest
from fastapi.testclient import TestClient
from src.CP.BackEnd.api.auth import app  # Assuming the FastAPI app is defined here
from unittest.mock import patch

pytestmark = pytest.mark.unit

client = TestClient(app)

def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401

def test_authenticate_user(client: TestClient):
    """Test user authentication"""
    response = client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "request_rate" in response.text
    assert "latency" in response.text
    assert "error_rate" in response.text
