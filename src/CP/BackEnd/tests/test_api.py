import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/api/token", json={"email": "test@example.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post("/api/token", json={"email": "wrong@example.com", "password": "wrongpassword"})
    assert response.status_code == 401

def test_auth_examples():
    response = client.get("/api/auth/examples")
    assert response.status_code == 200
    assert "python" in response.json()
    assert "javascript" in response.json()
    assert "java" in response.json()
