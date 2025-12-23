"""
Health Check and Basic API Tests

Tests for core API endpoints to verify the service is operational.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test that health endpoint returns 200 and correct status"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "waooaw-backend"


def test_root_endpoint():
    """Test that root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "WAOOAW Platform API" in data["name"]
    assert data["version"] == "1.0.0"
    assert data["tagline"] == "Agents Earn Your Business"
    assert data["status"] == "operational"
    assert data["docs"] == "/api/docs"


def test_api_agents_endpoint():
    """Test that agents endpoint returns list of agents"""
    response = client.get("/api/agents")
    assert response.status_code == 200

    data = response.json()
    assert "agents" in data
    assert "total" in data
    assert isinstance(data["agents"], list)
    assert data["total"] == 19

    # Verify at least one agent is returned
    assert len(data["agents"]) > 0

    # Verify agent structure
    if data["agents"]:
        agent = data["agents"][0]
        assert "id" in agent
        assert "name" in agent
        assert "category" in agent
        assert "status" in agent
        assert "rating" in agent
        assert "trial_price" in agent
