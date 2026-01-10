"""
Integration tests for complete auth flow
"""
import pytest


@pytest.mark.integration
def test_api_health_check(client):
    """Test main API health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.integration
def test_auth_health_check(client):
    """Test auth API health check"""
    response = client.get("/api/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@pytest.mark.integration
def test_api_docs_available(client):
    """Test that API docs are available"""
    response = client.get("/docs")
    assert response.status_code == 200
