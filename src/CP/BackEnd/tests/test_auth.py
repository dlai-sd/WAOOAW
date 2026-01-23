"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient
from .main import app  # Assuming your FastAPI app is in main.py

client = TestClient(app)

@pytest.mark.unit
@pytest.mark.auth
def test_health_endpoint():
    response = client.get("/api/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user_unauthorized():
    response = client.get("/api/auth/me")
    assert response.status_code in [401, 403]

@pytest.mark.unit
@pytest.mark.auth
def test_google_login_endpoint_exists():
    response = client.get("/api/auth/google/login", follow_redirects=False)
    assert response.status_code != 404

@pytest.mark.unit
@pytest.mark.auth
def test_login_success():
    response = client.post("/api/auth/token", json={"email": "test@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600

@pytest.mark.unit
@pytest.mark.auth
def test_login_failure():
    response = client.post("/api/auth/token", json={"email": "wrong@example.com", "password": "wrong"})
    assert response.status_code == 401
