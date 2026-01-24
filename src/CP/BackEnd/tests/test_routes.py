"""
Tests for auth routes
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.CP.BackEnd.api.v1.router import api_v1_router

@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(api_v1_router)
    yield TestClient(app)

pytestmark = pytest.mark.unit

def test_refresh_token_with_invalid_token(client: TestClient):
    """Test refresh endpoint with invalid token"""
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401

def test_swagger_ui(client: TestClient):
    """Test Swagger UI is accessible"""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text
