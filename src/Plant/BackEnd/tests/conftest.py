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
from core.metrics import start_metrics_server

# Start metrics server for testing
@pytest.fixture(scope="session", autouse=True)
def metrics_server():
    """Start the Prometheus metrics server."""
    start_metrics_server()

# ========== SESSION & EVENT LOOP ==========
# Use pytest-asyncio's default event loop management
# Don't override event_loop fixture to avoid deprecation warnings

# ========== DATABASE CONFIGURATION ==========
@pytest.fixture(scope="session")
def test_db_url():
    """
    Use local development database for integration tests.
    This avoids testcontainer driver compatibility issues.
    """
    import os
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev"
    )

@pytest.fixture(scope="session")
async def async_engine(test_db_url):
    """
    Create async SQLAlchemy engine for tests.
    Uses existing dev database - no table creation/deletion.
    """
    engine = create_async_engine(
        test_db_url,
        echo=False,
        connect_args={"timeout": 10},
    )
    
    yield engine
    
    await engine.dispose()

@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session for each test.
    Uses nested transaction (SAVEPOINT) for complete isolation.
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
        async with session.begin_nested():
            yield session
            await session.rollback()
        await session.close()

# Additional test fixtures for monitoring and observability
@pytest.fixture
async def create_test_metrics(async_session: AsyncSession):
    """Factory for creating test metrics data."""
    async def _create_metrics(
        request_rate: float = 0.0,
        latency: float = 0.0,
        error_rate: float = 0.0
    ):
        # Implement logic to create and store metrics data
        pass
    
    return _create_metrics
