"""
Load Tests: API Endpoint Performance

Tests API endpoint performance and throughput using pytest-benchmark.
Simulates concurrent requests and measures response times.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_list_agents_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark GET /agents endpoint performance."""
    
    def get_agents():
        response = test_client.get("/agents")
        return response.status_code
    
    result = benchmark.pedantic(get_agents, iterations=50, rounds=5)
    assert result == 200


@pytest.mark.asyncio
async def test_create_agent_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark POST /agents endpoint performance."""
    
    agent_data = {
        "name": "LoadTestAgent",
        "skill_id": "skill_123",
        "job_role_id": "role_456",
        "industry_id": "industry_789",
        "entity_type": "Agent",
        "governance_agent_id": "genesis",
        "version_hash": "load_v1",
    }
    
    def create_agent():
        response = test_client.post("/agents", json=agent_data)
        return response.status_code
    
    result = benchmark.pedantic(create_agent, iterations=20, rounds=3)
    assert result in [200, 201]


@pytest.mark.asyncio
async def test_filter_agents_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark GET /agents with filters performance."""
    
    def filter_agents():
        response = test_client.get("/agents?industry=healthcare&limit=10")
        return response.status_code
    
    result = benchmark.pedantic(filter_agents, iterations=30, rounds=4)
    assert result == 200


@pytest.mark.asyncio
async def test_health_check_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark GET /health endpoint (should be very fast)."""
    
    def health_check():
        response = test_client.get("/health")
        return response.status_code
    
    result = benchmark.pedantic(health_check, iterations=100, rounds=10)
    assert result == 200
