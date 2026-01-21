"""
Pytest Configuration and Shared Fixtures

This file provides common test fixtures for all test types:
- Unit tests (mocked dependencies)
- Integration tests (real database/Redis)
- E2E tests (full stack)
"""

import os
import pytest
from typing import Generator
from pathlib import Path

# Determine test mode from environment
TEST_MODE = os.getenv("TEST_MODE", "unit")  # unit, integration, e2e


@pytest.fixture(scope="session")
def test_mode() -> str:
    """Get current test mode."""
    return TEST_MODE


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Database URL for tests.
    
    For unit tests: Returns None (use mocks)
    For integration/e2e: Returns test database URL
    """
    if TEST_MODE == "unit":
        return None
    
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://waooaw_test:waooaw_test_password@localhost:5433/waooaw_test_db"
    )


@pytest.fixture(scope="session")
def test_redis_url() -> str:
    """
    Redis URL for tests.
    
    For unit tests: Returns None (use mocks)
    For integration/e2e: Returns test Redis URL
    """
    if TEST_MODE == "unit":
        return None
    
    return os.getenv(
        "TEST_REDIS_URL",
        "redis://localhost:6380/0"
    )


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables for unit tests."""
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@mock:5432/mock")
    monkeypatch.setenv("REDIS_URL", "redis://mock:6379/0")
    monkeypatch.setenv("JWT_SECRET", "test-secret-key")
    return monkeypatch


# Add markers for different test types
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, mocked dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (real database/Redis)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full stack)"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take more than 5 seconds"
    )
