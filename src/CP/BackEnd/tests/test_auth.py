"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient
from src.CP.BackEnd.core.security import hash_password, get_current_user
from src.CP.BackEnd.api.auth import router

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/api/auth")
    yield TestClient(app)

@pytest.mark.unit
@pytest.mark.auth
def test_health_endpoint(client):
    response = client.get("/api/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user_unauthorized(client):
    response = client.get("/api/auth/v1/me")
    assert response.status_code in [401, 403]

@pytest.mark.unit
@pytest.mark.auth
def test_google_login_endpoint_exists(client):
    response = client.get("/api/auth/google/login", follow_redirects=False)
    assert response.status_code != 404

@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user_with_token(client):
    response = client.get("/api/auth/v1/me", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    assert response.json() == {"user_id": "user_id"}

@pytest.mark.unit
@pytest.mark.auth
def test_login_with_valid_credentials(client):
    response = client.post("/api/auth/v1/token", data={"username": "test@example.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.unit
@pytest.mark.auth
def test_login_with_invalid_credentials(client):
    response = client.post("/api/auth/v1/token", data={"username": "test@example.com", "password": "wrongpassword"})
    assert response.status_code == 401

@pytest.mark.unit
@pytest.mark.auth
def test_get_current_user_v2(client):
    response = client.get("/api/auth/v2/me", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    assert response.json() == {"user_id": "user_id"}
