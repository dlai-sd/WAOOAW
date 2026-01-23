import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime
from main import app
from fastapi import HTTPException  # Importing HTTPException
from src.CP.BackEnd.middleware.circuit_breaker import CircuitBreaker  # Importing CircuitBreaker

@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthAPILoad:
    @pytest.fixture
    async def async_client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_concurrent_user_registrations(self, async_client):
        num_users = 30
        async def register_user(index):
            user_data = {
                "email": f"load.{index}.{uuid4()}@example.com",
                "password": f"LoadPass{index}123!",
                "full_name": f"Load Test User {index}",
            }
            response = await async_client.post("/api/v1/auth/register", json=user_data)
            return response.status_code

        tasks = [register_user(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for code in results if code == 201)
        assert success_count == num_users

    async def test_circuit_breaker(self, async_client):
        # Simulate Plant API down scenario
        async def simulate_failure():
            raise Exception("Simulated failure")

        circuit_breaker = CircuitBreaker(max_failures=3, reset_timeout=10)

        for _ in range(3):
            with pytest.raises(HTTPException):
                circuit_breaker.call(simulate_failure)

        with pytest.raises(HTTPException):
            circuit_breaker.call(simulate_failure)

