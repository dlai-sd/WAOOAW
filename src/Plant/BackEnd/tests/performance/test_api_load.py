"""
Load Tests: API Endpoint Performance

Tests API endpoint performance and throughput using pytest-benchmark.
Simulates concurrent requests and measures response times.
"""

import asyncio
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.config import settings
from models.job_role import JobRole
from models.skill import Skill
from models.team import Industry


def test_list_agents_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark GET /agents endpoint performance."""
    
    def get_agents():
        response = test_client.get("/api/v1/agents")
        return response.status_code
    
    result = benchmark.pedantic(get_agents, iterations=50, rounds=5)
    assert result == 200


def test_create_agent_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark POST /agents endpoint performance."""

    async def seed_dependencies() -> tuple[str, str, str]:
        engine = create_async_engine(settings.database_url)
        Session = async_sessionmaker(engine, expire_on_commit=False)

        skill_id = uuid4()
        industry_id = uuid4()
        job_role_id = uuid4()

        async with Session() as session:
            session.add(
                Skill(
                    id=skill_id,
                    entity_type="Skill",
                    name=f"LoadTest Skill {skill_id}",
                    description="Load test seed skill",
                    category="technical",
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            session.add(
                Industry(
                    id=industry_id,
                    entity_type="Industry",
                    name=f"LoadTest Industry {industry_id}",
                    description="Load test seed industry",
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            session.add(
                JobRole(
                    id=job_role_id,
                    entity_type="JobRole",
                    name=f"LoadTest JobRole {job_role_id}",
                    description="Load test seed job role",
                    required_skills=[skill_id],
                    seniority_level="mid",
                    industry_id=industry_id,
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            await session.commit()

        await engine.dispose()
        return str(skill_id), str(job_role_id), str(industry_id)

    skill_id, job_role_id, industry_id = asyncio.run(seed_dependencies())
    
    def create_agent():
        agent_data = {
            "name": f"LoadTestAgent_{uuid4()}",
            "skill_id": skill_id,
            "job_role_id": job_role_id,
            "industry_id": industry_id,
            "governance_agent_id": "genesis",
        }
        response = test_client.post("/api/v1/agents", json=agent_data)
        return response.status_code
    
    result = benchmark.pedantic(create_agent, iterations=20, rounds=3)
    assert result in [200, 201]


def test_filter_agents_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark GET /agents with filters performance."""

    async def seed_industry() -> str:
        engine = create_async_engine(settings.database_url)
        Session = async_sessionmaker(engine, expire_on_commit=False)

        industry_id = uuid4()
        async with Session() as session:
            session.add(
                Industry(
                    id=industry_id,
                    entity_type="Industry",
                    name=f"LoadTest Filter Industry {industry_id}",
                    description="Load test seed industry",
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            await session.commit()

        await engine.dispose()
        return str(industry_id)

    industry_id = asyncio.run(seed_industry())
    
    def filter_agents():
        response = test_client.get(
            f"/api/v1/agents?industry_id={industry_id}&limit=10"
        )
        return response.status_code
    
    result = benchmark.pedantic(filter_agents, iterations=30, rounds=4)
    assert result == 200


def test_health_check_endpoint_load(test_client: TestClient, benchmark):
    """Benchmark GET /health endpoint (should be very fast)."""
    
    def health_check():
        response = test_client.get("/health")
        return response.status_code
    
    result = benchmark.pedantic(health_check, iterations=100, rounds=10)
    assert result == 200
