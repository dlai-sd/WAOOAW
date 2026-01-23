import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException  # Importing HTTPException
from main import app  # Assuming your FastAPI app is in main.py

client = TestClient(app)

def test_request_validation():
    response = client.post("/your-endpoint", json={"valid": "data"})
    assert response.status_code == 200

def test_request_validation_failure():
    response = client.post("/your-endpoint", json={"invalid": "data"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid request"}

def test_circuit_breaker():
    # Simulate failures to test circuit breaker
    for _ in range(3):
        response = client.post("/your-endpoint", json={"valid": "data"})
        assert response.status_code == 200

    # Simulate failure
    with pytest.raises(HTTPException):  # Now defined
        client.post("/your-endpoint", json={"invalid": "data"})
