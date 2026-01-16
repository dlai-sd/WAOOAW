"""
Load Tests for Trial API Endpoints
Tests performance and concurrency (MVP-001)
"""

import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime

from main import app


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestTrialAPILoad:
    """Load tests for Trial API endpoints"""

    @pytest.fixture
    async def async_client(self):
        """Create async HTTP client"""
        async with AsyncClient(
            app=app, base_url="http://test", timeout=30.0
        ) as client:
            yield client

    async def test_create_trial_concurrent_requests(
        self, async_client
    ):
        """Test creating trials concurrently"""
        agent_id = str(uuid4())
        num_requests = 50

        async def create_trial(index):
            trial_data = {
                "agent_id": agent_id,
                "customer_email": f"load.test.{index}.{uuid4()}@example.com",
                "customer_name": f"Load Test User {index}",
            }
            start_time = datetime.utcnow()
            response = await async_client.post(
                "/api/v1/trials", json=trial_data
            )
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            return response.status_code, duration

        # Execute concurrent requests
        tasks = [create_trial(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

        # Validate results
        status_codes = [r[0] for r in results]
        durations = [r[1] for r in results]

        success_count = sum(1 for code in status_codes if code == 201)
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        print(f"\n--- Load Test Results ---")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {success_count}")
        print(f"Average Duration: {avg_duration:.3f}s")
        print(f"Max Duration: {max_duration:.3f}s")

        # Assertions
        assert success_count >= num_requests * 0.95  # 95% success rate
        assert avg_duration < 2.0  # Average under 2 seconds
        assert max_duration < 5.0  # No single request over 5 seconds

    async def test_list_trials_concurrent_reads(self, async_client):
        """Test reading trials concurrently"""
        num_requests = 100

        async def list_trials(index):
            start_time = datetime.utcnow()
            response = await async_client.get(
                "/api/v1/trials?skip=0&limit=10"
            )
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            return response.status_code, duration

        tasks = [list_trials(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

        status_codes = [r[0] for r in results]
        durations = [r[1] for r in results]

        success_count = sum(1 for code in status_codes if code == 200)
        avg_duration = sum(durations) / len(durations)

        print(f"\n--- Concurrent Read Test ---")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {success_count}")
        print(f"Average Duration: {avg_duration:.3f}s")

        assert success_count == num_requests  # 100% success for reads
        assert avg_duration < 1.0  # Fast reads

    async def test_trial_api_response_times(self, async_client):
        """Test Trial API response time SLA"""
        agent_id = str(uuid4())

        # Test create trial response time
        trial_data = {
            "agent_id": agent_id,
            "customer_email": f"sla.test.{uuid4()}@example.com",
            "customer_name": "SLA Test User",
        }

        start = datetime.utcnow()
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        create_duration = (datetime.utcnow() - start).total_seconds()

        assert create_response.status_code == 201
        assert create_duration < 2.0  # Create under 2s

        trial_id = create_response.json()["id"]

        # Test get trial response time
        start = datetime.utcnow()
        get_response = await async_client.get(
            f"/api/v1/trials/{trial_id}"
        )
        get_duration = (datetime.utcnow() - start).total_seconds()

        assert get_response.status_code == 200
        assert get_duration < 0.5  # Get under 500ms

        # Test list trials response time
        start = datetime.utcnow()
        list_response = await async_client.get("/api/v1/trials")
        list_duration = (datetime.utcnow() - start).total_seconds()

        assert list_response.status_code == 200
        assert list_duration < 1.0  # List under 1s

        print(f"\n--- Response Time SLA ---")
        print(f"Create Trial: {create_duration:.3f}s (SLA: < 2.0s)")
        print(f"Get Trial: {get_duration:.3f}s (SLA: < 0.5s)")
        print(f"List Trials: {list_duration:.3f}s (SLA: < 1.0s)")

    async def test_trial_status_updates_concurrent(
        self, async_client
    ):
        """Test concurrent trial status updates"""
        agent_id = str(uuid4())
        num_trials = 20

        # Create trials
        trial_ids = []
        for i in range(num_trials):
            trial_data = {
                "agent_id": agent_id,
                "customer_email": f"concurrent.{i}.{uuid4()}@example.com",
                "customer_name": f"Concurrent User {i}",
            }
            response = await async_client.post(
                "/api/v1/trials", json=trial_data
            )
            trial_ids.append(response.json()["id"])

        # Update statuses concurrently
        async def update_status(trial_id):
            start_time = datetime.utcnow()
            response = await async_client.patch(
                f"/api/v1/trials/{trial_id}",
                json={"status": "converted"},
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            return response.status_code, duration

        tasks = [update_status(tid) for tid in trial_ids]
        results = await asyncio.gather(*tasks)

        status_codes = [r[0] for r in results]
        durations = [r[1] for r in results]

        success_count = sum(1 for code in status_codes if code == 200)
        avg_duration = sum(durations) / len(durations)

        print(f"\n--- Concurrent Update Test ---")
        print(f"Total Updates: {num_trials}")
        print(f"Successful: {success_count}")
        print(f"Average Duration: {avg_duration:.3f}s")

        assert success_count == num_trials
        assert avg_duration < 1.0
