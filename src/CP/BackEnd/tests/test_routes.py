"""
Tests for auth routes
"""

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry, generate_latest

from main import app  # Assuming your FastAPI app is in main.py

pytestmark = pytest.mark.unit


def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401

def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "api_requests_total" in response.text
    assert "api_request_latency_seconds" in response.text
