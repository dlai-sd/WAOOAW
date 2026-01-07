"""
Pytest Configuration and Fixtures

Provides shared fixtures and configuration for the test suite.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://waooaw_test:test_password@localhost:5432/waooaw_test_db",
)


@pytest.fixture(scope="session")
def db_engine():
    """
    Create a database engine for the test session.

    This fixture is scoped to the session, meaning the engine
    is created once and shared across all tests.
    """
    engine = create_engine(DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a database session for each test function.

    This fixture provides a clean database session for each test,
    with automatic rollback after the test completes to ensure
    test isolation.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
