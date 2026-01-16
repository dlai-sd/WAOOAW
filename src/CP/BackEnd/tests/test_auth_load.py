"""
Load Tests for Authentication API
Tests auth performance and concurrent login (MVP-002)
"""

import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime

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

    async def test_concurrent_user_registrations(self, async_client):
        """Test concurrent user registrations"""
        num_users = 30

        async def register_user(index):
            user_data = {
                "email": f"load.{index}.{uuid4()}@example.com",
                "password": f"LoadPass{index}123!",
                "full_name": f"Load Test User {index}",
            }
            start_time = datetime.utcnow()
            response = await async_client.post(
                "/api/v1/auth/register", json=user_data
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            return response.status_code, duration

        tasks = [register_user(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)

        status_codes = [r[0] for r in results]
        durations = [r[1] for r in results]

        success_count = sum(1 for code in status_codes if code == 201)
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        print(f"\n--- Concurrent Registration Test ---")
        print(f"Total Registrations: {num_users}")
        print(f"Successful: {success_count}")
        print(f"Average Duration: {avg_duration:.3f}s")
        print(f"Max Duration: {max_duration:.3f}s")

        assert success_count == num_users
        assert avg_duration < 3.0  # Average under 3s (bcrypt is slow)
        assert max_duration < 10.0

    async def test_concurrent_logins(self, async_client):
        """Test concurrent login requests"""
        # Register users first
        num_users = 50
        users = []

        for i in range(num_users):
            email = f"login.load.{i}.{uuid4()}@example.com"
            password = f"Pass{i}123!"
            register_data = {
                "email": email,
                "password": password,
                "full_name": f"User {i}",
            }
            response = await async_client.post(
                "/api/v1/auth/register", json=register_data
            )
            assert response.status_code == 201
            users.append({"email": email, "password": password})

        # Concurrent logins
        async def login_user(user):
            start_time = datetime.utcnow()
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": user["email"],
                    "password": user["password"],
                },
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            return response.status_code, duration

        tasks = [login_user(user) for user in users]
        results = await asyncio.gather(*tasks)

        status_codes = [r[0] for r in results]
        durations = [r[1] for r in results]

        success_count = sum(1 for code in status_codes if code == 200)
        avg_duration = sum(durations) / len(durations)

        print(f"\n--- Concurrent Login Test ---")
        print(f"Total Logins: {num_users}")
        print(f"Successful: {success_count}")
        print(f"Average Duration: {avg_duration:.3f}s")

        assert success_count == num_users
        assert avg_duration < 2.0

    async def test_auth_api_response_times(self, async_client):
        """Test authentication API response time SLA"""
        unique_email = f"sla.{uuid4()}@example.com"
        password = "SLAPass123!"

        # Test registration response time
        start = datetime.utcnow()
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "SLA Test User",
            },
        )
        register_duration = (datetime.utcnow() - start).total_seconds()

        assert register_response.status_code == 201
        assert register_duration < 5.0  # Register under 5s (bcrypt)

        # Test login response time
        start = datetime.utcnow()
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password},
        )
        login_duration = (datetime.utcnow() - start).total_seconds()

        assert login_response.status_code == 200
        assert login_duration < 3.0  # Login under 3s

        # Test get user response time
        access_token = login_response.json()["access_token"]
        start = datetime.utcnow()
        get_user_response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        get_user_duration = (datetime.utcnow() - start).total_seconds()

        assert get_user_response.status_code == 200
        assert get_user_duration < 0.5  # Get user under 500ms

        print(f"\n--- Auth API Response Time SLA ---")
        print(f"Register: {register_duration:.3f}s (SLA: < 5.0s)")
        print(f"Login: {login_duration:.3f}s (SLA: < 3.0s)")
        print(f"Get User: {get_user_duration:.3f}s (SLA: < 0.5s)")

    async def test_jwt_token_validation_load(self, async_client):
        """Test JWT token validation under load"""
        # Register and login a user
        email = f"jwt.load.{uuid4()}@example.com"
        password = "JWTLoad123!"
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "JWT Load User",
            },
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        access_token = login_response.json()["access_token"]

        # Concurrent token validations
        num_requests = 100

        async def validate_token():
            start_time = datetime.utcnow()
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            return response.status_code, duration

        tasks = [validate_token() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)

        status_codes = [r[0] for r in results]
        durations = [r[1] for r in results]

        success_count = sum(1 for code in status_codes if code == 200)
        avg_duration = sum(durations) / len(durations)

        print(f"\n--- JWT Validation Load Test ---")
        print(f"Total Validations: {num_requests}")
        print(f"Successful: {success_count}")
        print(f"Average Duration: {avg_duration:.3f}s")

        assert success_count == num_requests
        assert avg_duration < 0.5  # JWT validation should be fast

    async def test_password_hashing_performance(self, async_client):
        """Test password hashing performance (bcrypt)"""
        num_registrations = 10

        async def register_user(index):
            user_data = {
                "email": f"hash.perf.{index}.{uuid4()}@example.com",
                "password": f"ComplexPassword{index}!@#$%",
                "full_name": f"Hash Perf User {index}",
            }
            start_time = datetime.utcnow()
            response = await async_client.post(
                "/api/v1/auth/register", json=user_data
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            return duration

        tasks = [register_user(i) for i in range(num_registrations)]
        durations = await asyncio.gather(*tasks)

        avg_duration = sum(durations) / len(durations)

        print(f"\n--- Password Hashing Performance ---")
        print(f"Total Hashes: {num_registrations}")
        print(f"Average Duration: {avg_duration:.3f}s")

        # bcrypt is intentionally slow (security feature)
        assert avg_duration < 5.0
        assert avg_duration > 0.1  # Should take some time
