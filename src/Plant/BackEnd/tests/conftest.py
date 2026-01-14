"""
Test fixtures and configuration for Plant backend tests
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from core.database import Base
from core.config import settings
from main import app


# Test database URL (use in-memory or testcontainers)
TEST_DATABASE_URL = "postgresql://test_user:test_password@localhost:5432/plant_test"


@pytest.fixture(scope="session")
def db_engine():
    """
    Create test database engine (session-scoped).
    """
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create database session for each test (function-scoped).
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def test_client():
    """
    Create FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture
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
