"""
Test Suite for Agent API Endpoints
Tests the simple in-memory implementation
"""

import pytest
from uuid import UUID
import json
import httpx

# Note: Run from /src/Plant/BackEnd directory
# pytest tests/test_agents_api.py -v


def test_import_api():
    """Test that API module imports correctly"""
    try:
        from api.v1.agents_simple import router
        assert router is not None
        print("✅ API router imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import API router: {e}")


@pytest.fixture
async def client():
    """Create FastAPI async test client"""
    from fastapi import FastAPI
    from api.v1.agents_simple import router as agents_router
    
    app = FastAPI()
    app.include_router(agents_router)

    # NOTE: Starlette's TestClient has had compatibility breaks across httpx
    # versions (e.g., httpx dropped the `app=` kwarg). Use ASGITransport
    # directly for a stable in-process client.
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.mark.asyncio
class TestAgentEndpoints:
    """Test suite for Agent API endpoints"""
    
    async def test_create_agent(self, client):
        """Test creating a new agent"""
        response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "Sarah Marketing Expert",
                "specialization": "healthcare",
                "industry": "marketing",
                "hourly_rate": 85.0,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sarah Marketing Expert"
        assert data["specialization"] == "healthcare"
        assert data["industry"] == "marketing"
        assert data["hourly_rate"] == 85.0
        assert data["status"] == "available"
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_multiple_agents(self, client):
        """Test creating multiple agents"""
        agent_data = [
            {
                "name": "Agent 1",
                "specialization": "marketing",
                "industry": "marketing",
                "hourly_rate": 80.0,
            },
            {
                "name": "Agent 2",
                "specialization": "sales",
                "industry": "sales",
                "hourly_rate": 90.0,
            },
            {
                "name": "Agent 3",
                "specialization": "teaching",
                "industry": "education",
                "hourly_rate": 75.0,
            },
        ]
        
        agent_ids = []
        for data in agent_data:
            response = await client.post("/api/v1/agents/", json=data)
            assert response.status_code == 201
            agent_ids.append(response.json()["id"])
        
        assert len(agent_ids) == 3
    
    async def test_list_agents(self, client):
        """Test listing agents"""
        # Create agents
        for i in range(3):
            await client.post(
                "/api/v1/agents/",
                json={
                    "name": f"Agent {i}",
                    "specialization": "test",
                    "industry": "marketing",
                    "hourly_rate": 80.0 + i * 5,
                },
            )
        
        # List agents
        response = await client.get("/api/v1/agents/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    async def test_list_agents_with_filter(self, client):
        """Test listing agents with filters"""
        # Create agents in different industries
        await client.post(
            "/api/v1/agents/",
            json={
                "name": "Marketing Agent",
                "specialization": "social",
                "industry": "marketing",
                "hourly_rate": 85.0,
            },
        )
        await client.post(
            "/api/v1/agents/",
            json={
                "name": "Sales Agent",
                "specialization": "b2b",
                "industry": "sales",
                "hourly_rate": 95.0,
            },
        )
        
        # Filter by industry
        response = await client.get("/api/v1/agents/?industry=marketing")
        assert response.status_code == 200
        data = response.json()
        assert all(a["industry"] == "marketing" for a in data)
    
    async def test_get_agent(self, client):
        """Test getting a specific agent"""
        # Create agent
        create_response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "Test Agent",
                "specialization": "test",
                "industry": "marketing",
                "hourly_rate": 80.0,
            },
        )
        agent_id = create_response.json()["id"]
        
        # Get agent
        response = await client.get(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
        assert data["name"] == "Test Agent"
    
    async def test_get_nonexistent_agent(self, client):
        """Test getting non-existent agent returns 404"""
        from uuid import uuid4
        fake_id = uuid4()
        
        response = await client.get(f"/api/v1/agents/{fake_id}")
        assert response.status_code == 404
    
    async def test_update_agent(self, client):
        """Test updating an agent"""
        # Create agent
        create_response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "Original Name",
                "specialization": "test",
                "industry": "marketing",
                "hourly_rate": 80.0,
            },
        )
        agent_id = create_response.json()["id"]
        
        # Update agent
        response = await client.put(
            f"/api/v1/agents/{agent_id}",
            json={
                "name": "Updated Name",
                "hourly_rate": 95.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["hourly_rate"] == 95.0
    
    async def test_update_agent_status(self, client):
        """Test updating agent status"""
        # Create agent
        create_response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "Test Agent",
                "specialization": "test",
                "industry": "marketing",
                "hourly_rate": 80.0,
            },
        )
        agent_id = create_response.json()["id"]
        
        # Update status
        response = await client.put(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": "working"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "working"
    
    async def test_delete_agent(self, client):
        """Test deleting an agent"""
        # Create agent
        create_response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "Test Agent",
                "specialization": "test",
                "industry": "marketing",
                "hourly_rate": 80.0,
            },
        )
        agent_id = create_response.json()["id"]
        
        # Delete agent
        response = await client.delete(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 204
        
        # Verify deleted
        response = await client.get(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 404
    
    async def test_search_available_agents(self, client):
        """Test searching for available agents"""
        # Create agents
        await client.post(
            "/api/v1/agents/",
            json={
                "name": "Sarah Healthcare",
                "specialization": "healthcare",
                "industry": "marketing",
                "hourly_rate": 85.0,
            },
        )
        await client.post(
            "/api/v1/agents/",
            json={
                "name": "Mike Sales",
                "specialization": "b2b",
                "industry": "sales",
                "hourly_rate": 95.0,
            },
        )
        
        # Search for Sarah
        response = await client.get("/api/v1/agents/available/search?query=Sarah")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("Sarah" in a["name"] for a in data)
    
    async def test_get_agent_metrics(self, client):
        """Test getting agent metrics"""
        # Create agent
        create_response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "Test Agent",
                "specialization": "test",
                "industry": "marketing",
                "hourly_rate": 80.0,
            },
        )
        agent_id = create_response.json()["id"]
        
        # Get metrics
        response = await client.get(f"/api/v1/agents/{agent_id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "avg_rating" in data
        assert "retention_rate" in data


@pytest.mark.asyncio
class TestValidation:
    """Test request validation"""
    
    async def test_invalid_name_empty(self, client):
        """Test creating agent with empty name fails"""
        response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "",
                "specialization": "test",
                "industry": "marketing",
                "hourly_rate": 80.0,
            },
        )
        assert response.status_code == 422  # Validation error
    
    async def test_invalid_hourly_rate_negative(self, client):
        """Test creating agent with negative rate fails"""
        response = await client.post(
            "/api/v1/agents/",
            json={
                "name": "Test",
                "specialization": "test",
                "industry": "marketing",
                "hourly_rate": -50.0,
            },
        )
        assert response.status_code == 422
    
    async def test_invalid_limit_exceeds_max(self, client):
        """Test pagination limit validation"""
        response = await client.get("/api/v1/agents/?limit=1000")
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
