"""
Unit tests for OAuth2 authentication
"""
import pytest
from fastapi.testclient import TestClient
from .main import app  # Assuming your FastAPI app is in main.py
from .services.auth_service import AuthService
import jwt
from core.config import settings

client = TestClient(app)

def decode_jwt(token: str):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

@pytest.mark.unit
@pytest.mark.auth
def test_login_success():
    response = client.post("/api/v1/token", data={"username": "test@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600

@pytest.mark.unit
@pytest.mark.auth
def test_login_failure():
    response = client.post("/api/v1/token", data={"username": "wrong@example.com", "password": "wrong"})
    assert response.status_code == 401

@pytest.mark.unit
@pytest.mark.auth
def test_token_includes_claims():
    response = client.post("/api/v1/token", data={"username": "test@example.com", "password": "password"})
    data = response.json()
    token = data["access_token"]
    claims = decode_jwt(token)
    assert "user_id" in claims
    assert "tenant_id" in claims
