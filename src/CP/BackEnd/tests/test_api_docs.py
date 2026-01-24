import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_swagger_ui():
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text

def test_openapi_json():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
