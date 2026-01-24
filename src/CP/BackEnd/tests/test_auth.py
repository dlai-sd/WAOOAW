import pytest
from fastapi.testclient import TestClient
from src.CP.BackEnd.main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post("/token", data={"username": "wronguser", "password": "wrongpassword"})
    assert response.status_code == 401
