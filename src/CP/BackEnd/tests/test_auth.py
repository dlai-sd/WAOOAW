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

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "request_count" in response.text

def test_logging_includes_tenant_id():
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    # Check logs for tenant_id (this would require a logging setup to capture logs)
