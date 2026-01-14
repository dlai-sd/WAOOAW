"""
Test fixtures and configuration for Plant backend tests
Async-first fixtures using pytest-asyncio and testcontainers
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from testcontainers.postgres import PostgresContainer
import uuid
from datetime import datetime

from core.database import Base, get_connector, DatabaseConnector
from models.skill import Skill
from models.job_role import JobRole
from models.team import Team
from models.agent import Agent
from models.industry import Industry


# ========== SESSION & EVENT LOOP ==========
@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests (session-scoped).
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ========== TESTCONTAINERS DATABASE ==========
@pytest.fixture(scope="session")
def postgres_container():
    """
    Start PostgreSQL testcontainer for all tests.
    Auto-stops after session completes.
    """
    container = PostgresContainer("postgres:15-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def test_db_url(postgres_container):
    """
    Get connection URL from testcontainer.
    Convert to async URL (asyncpg driver).
    """
    url = postgres_container.get_connection_url()
    # Convert to async format
    async_url = url.replace("postgresql://", "postgresql+asyncpg://")
    return async_url


@pytest.fixture(scope="session")
async def async_engine(test_db_url):
    """
    Create async SQLAlchemy engine for tests.
    """
    engine = create_async_engine(
        test_db_url,
        echo=False,
        connect_args={"connect_timeout": 10},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session for each test.
    Auto-rolls back after test completes.
    """
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ========== SEED DATA FACTORIES ==========
@pytest.fixture
async def create_test_skill(async_session: AsyncSession):
    """Factory for creating test Skill entities."""
    async def _create_skill(
        name: str = "Python",
        category: str = "technical",
        embedding: list = None
    ) -> Skill:
        if embedding is None:
            embedding = [0.1] * 384  # MiniLM-384 dimension
        
        skill = Skill(
            id=uuid.uuid4(),
            entity_type="Skill",
            name=name,
            category=category,
            embedding_384=embedding,
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(skill)
        await async_session.commit()
        return skill
    
    return _create_skill


@pytest.fixture
async def create_test_industry(async_session: AsyncSession):
    """Factory for creating test Industry entities."""
    async def _create_industry(
        name: str = "Marketing",
        description: str = "Marketing industry"
    ) -> Industry:
        industry = Industry(
            id=uuid.uuid4(),
            entity_type="Industry",
            name=name,
            description=description,
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(industry)
        await async_session.commit()
        return industry
    
    return _create_industry


@pytest.fixture
async def create_test_job_role(async_session: AsyncSession, create_test_skill):
    """Factory for creating test JobRole entities."""
    async def _create_job_role(
        name: str = "Senior Developer",
        skills: list = None
    ) -> JobRole:
        if skills is None:
            skill = await create_test_skill(name="Python")
            skills = [str(skill.id)]
        
        job_role = JobRole(
            id=uuid.uuid4(),
            entity_type="JobRole",
            name=name,
            skills=skills,
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(job_role)
        await async_session.commit()
        return job_role
    
    return _create_job_role


@pytest.fixture
async def create_test_agent(async_session: AsyncSession, create_test_skill, create_test_industry, create_test_job_role):
    """Factory for creating test Agent entities."""
    async def _create_agent(
        name: str = "TestAgent",
        industry_id: str = None
    ) -> Agent:
        if industry_id is None:
            industry = await create_test_industry()
            industry_id = str(industry.id)
        
        job_role = await create_test_job_role()
        
        agent = Agent(
            id=uuid.uuid4(),
            entity_type="Agent",
            name=name,
            industry_id=industry_id,
            job_role_id=str(job_role.id),
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(agent)
        await async_session.commit()
        return agent
    
    return _create_agent


@pytest.fixture
async def test_db_cleanup(async_session: AsyncSession):
    """
    Cleanup fixture - called after each test to ensure isolation.
    """
    yield
    # Rollback any uncommitted transactions
    await async_session.rollback()
def genesis_skill_data():
    """
    Sample skill data for testing.
    """
    return {
        "name": "Test Skill",
        "description": "A test skill for unit testing",
        "category": "technical",
        "governance_agent_id": "genesis",
    }


@pytest.fixture
def genesis_job_role_data():
    """
    Sample job role data for testing.
    """
    return {
        "name": "Test Job Role",
        "description": "A test job role",
        "required_skills": [],
        "seniority_level": "mid",
        "governance_agent_id": "genesis",
    }


@pytest.fixture
def rsa_keypair():
    """
    Generate RSA keypair for cryptography tests.
    """
    from security.cryptography import generate_rsa_keypair
    return generate_rsa_keypair()
