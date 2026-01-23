import pytest
from fastapi.testclient import TestClient
from src.CP.BackEnd.api.auth import app  # Assuming the FastAPI app is in auth.py
from src.CP.BackEnd.core.security import create_access_token
import jwt  # Importing the jwt module

client = TestClient(app)

def test_token_endpoint():
    response = client.post("/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()

def test_token_includes_claims():
    token = create_access_token({"user_id": "testuser", "tenant_id": "testtenant"})
    payload = jwt.decode(token, "dev-secret-change-in-production", algorithms=["HS256"])
    assert payload["user_id"] == "testuser"
    assert payload["tenant_id"] == "testtenant"

def test_rate_limiting():
    for _ in range(100):
        response = client.post("/token", data={"username": "testuser", "password": "testpass"})
        assert response.status_code == 200
    response = client.post("/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 429  # Too Many Requests
