"""Basic health check tests for V2 backend"""
import pytest
from fastapi.testclient import TestClient


def test_import_app():
    """Test that the app can be imported without errors"""
    from app.main import app
    assert app is not None
    assert app.title == "WAOOAW API v2"


def test_root_endpoint():
    """Test the root endpoint returns successfully"""
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data or "service" in data


def test_health_endpoint():
    """Test the health check endpoint"""
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_agents_endpoint():
    """Test agents listing endpoint"""
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/agents")
    
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
