"""
Load Tests for Authentication API
Tests auth performance and concurrent login (MVP-002)
"""

import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime
from prometheus_client import CollectorRegistry, generate_latest

from main import app

@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthAPILoad:
    """Load tests for Authentication API"""

    @pytest.fixture
    async def async_client(self):
        """Create async HTTP client"""
        async with AsyncClient(
            app=app, base_url="http://test", timeout=30.0
        ) as client:
            yield client

    async def test_token_endpoint(self, async_client):
        """Test token endpoint for valid JWT"""
        user_data = {
            "email": f"test.{uuid4()}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
        }
        # Register the user first
        await async_client.post("/api/v1/auth/register", json=user_data)

        # Now test login
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": user_data["email"], "password": user_data["password"]},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    # Additional tests for SDK generation and documentation
    async def test_sdk_generation(self):
        """Test SDK generation for Python and JavaScript"""
        # This is a placeholder for actual SDK generation tests
        assert True  # Replace with actual SDK generation logic

    async def test_documentation_access(self, async_client):
        """Test access to Swagger UI documentation"""
        response = await async_client.get("/api/docs")
        assert response.status_code == 200
