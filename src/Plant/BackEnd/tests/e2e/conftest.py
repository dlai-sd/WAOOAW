"""Fixtures for end-to-end tests.

Provides database sessions, test data setup, and cleanup for E2E tests.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from core.database import Base


@pytest.fixture(scope="function")
def db_session():
    """Create a database session for each E2E test with transaction rollback.
    
    Uses PostgreSQL test database with transaction-based isolation.
    Changes are rolled back after each test for clean state.
    """
    # Use test PostgreSQL database via Docker network (container name)
    test_db_url = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql+psycopg2://waooaw_test:waooaw_test_password@waooaw-postgres-test:5432/waooaw_test_db",
    )
    
    # Create engine and connection
    engine = create_engine(test_db_url)
    connection = engine.connect()
    
    # Begin a transaction
    transaction = connection.begin()
    
    # Create session bound to the connection
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Roll back the transaction (discards all changes)
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture(scope="function")
def test_customer_data():
    """Provide test customer data for E2E tests."""
    return {
        "customer_id": "customer_e2e_test",
        "email": "e2e.test@example.com",
        "name": "E2E Test Customer",
        "subscription_tier": "trial",
    }


@pytest.fixture(scope="function")
def test_marketing_config():
    """Provide test marketing agent configuration."""
    return {
        "nickname": "E2E Marketing Agent",
        "timezone": "America/New_York",
        "brand_name": "E2E Test Brand",
        "platforms": {
            "instagram": {
                "enabled": True,
                "account_id": "test_instagram_account",
                "access_token": "test_instagram_token_secure",
            },
            "facebook": {
                "enabled": True,
                "page_id": "test_facebook_page",
                "access_token": "test_facebook_token_secure",
            },
        },
    }


@pytest.fixture(scope="function")
def test_trading_config():
    """Provide test trading agent configuration."""
    return {
        "nickname": "E2E Trading Agent",
        "timezone": "America/New_York",
        "allowed_coins": ["BTC", "ETH"],
        "max_units_per_order": 0.01,
        "delta_exchange_credentials": {
            "api_key": "test_delta_api_key",
            "api_secret": "test_delta_api_secret",
        },
    }
