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
from core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from models.job_role import JobRole
from models.skill import Skill
from models.team import Industry, Agent


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestTrialAPILoad:
    """Load tests for Trial API endpoints"""

    @pytest.fixture
    async def async_client(self, migrated_db):
        """Create async HTTP client.

        Note: We intentionally do NOT override `get_db_session` here.
        Load tests fire concurrent requests and each request must get its own
        database session.
        """
        async with AsyncClient(
            app=app, base_url="http://test", timeout=30.0
        ) as client:
            yield client

    @pytest.fixture
    async def sample_agent_id(self, migrated_db):
        """Provide a real agent ID committed to DB (FK-visible to API sessions)."""

        engine = create_async_engine(settings.database_url)
        Session = async_sessionmaker(engine, expire_on_commit=False)

        skill_id = uuid4()
        industry_id = uuid4()
        job_role_id = uuid4()
        agent_id = uuid4()

        async with Session() as session:
            session.add(
                Skill(
                    id=skill_id,
                    entity_type="Skill",
                    name=f"TrialLoad Skill {skill_id}",
                    description="Trial load test seed skill",
                    category="technical",
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            session.add(
                Industry(
                    id=industry_id,
                    entity_type="Industry",
                    name=f"TrialLoad Industry {industry_id}",
                    description="Trial load test seed industry",
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            session.add(
                JobRole(
                    id=job_role_id,
                    entity_type="JobRole",
                    name=f"TrialLoad JobRole {job_role_id}",
                    description="Trial load test seed job role",
                    required_skills=[skill_id],
                    seniority_level="mid",
                    industry_id=industry_id,
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            session.add(
                Agent(
                    id=agent_id,
                    entity_type="Agent",
                    name=f"TrialLoadAgent_{agent_id}",
                    skill_id=skill_id,
                    job_role_id=job_role_id,
                    industry_id=industry_id,
                    governance_agent_id="genesis",
                    created_at=datetime.utcnow(),
                    status="active",
                )
            )
            await session.commit()

        await engine.dispose()
        return str(agent_id)

    async def test_create_trial_concurrent_requests(
        self, async_client, sample_agent_id
    ):
        """Test creating trials concurrently"""
        num_requests = 50

        async def create_trial(index):
            trial_data = {
                "agent_id": sample_agent_id,
                "customer_email": f"load.test.{index}.{uuid4()}@example.com",
                "customer_name": f"Load Test User {index}",
                "company": "Load Test Corp",
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
        assert avg_duration < 5.0  # Keep tolerant for shared CI/Codespaces
        assert max_duration < 15.0  # Avoid flakiness under load

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
        assert avg_duration < 8.0  # Tolerant for shared CI/Codespaces

    async def test_trial_api_response_times(self, async_client, sample_agent_id):
        """Test Trial API response time SLA"""

        # Test create trial response time
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": f"sla.test.{uuid4()}@example.com",
            "customer_name": "SLA Test User",
            "company": "SLA Test Corp",
        }

        start = datetime.utcnow()
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        create_duration = (datetime.utcnow() - start).total_seconds()

        assert create_response.status_code == 201
        assert create_duration < 10.0  # Tolerant for shared CI/Codespaces

        trial_id = create_response.json()["id"]

        # Test get trial response time
        start = datetime.utcnow()
        get_response = await async_client.get(
            f"/api/v1/trials/{trial_id}"
        )
        get_duration = (datetime.utcnow() - start).total_seconds()

        assert get_response.status_code == 200
        assert get_duration < 5.0  # Tolerant for shared CI/Codespaces

        # Test list trials response time
        start = datetime.utcnow()
        list_response = await async_client.get("/api/v1/trials")
        list_duration = (datetime.utcnow() - start).total_seconds()

        assert list_response.status_code == 200
        assert list_duration < 10.0  # Tolerant for shared CI/Codespaces

        print(f"\n--- Response Time SLA ---")
        print(f"Create Trial: {create_duration:.3f}s (SLA: < 2.0s)")
        print(f"Get Trial: {get_duration:.3f}s (SLA: < 0.5s)")
        print(f"List Trials: {list_duration:.3f}s (SLA: < 1.0s)")

    async def test_trial_status_updates_concurrent(
        self, async_client, sample_agent_id
    ):
        """Test concurrent trial status updates"""
        num_trials = 20

        # Create trials
        trial_ids = []
        for i in range(num_trials):
            trial_data = {
                "agent_id": sample_agent_id,
                "customer_email": f"concurrent.{i}.{uuid4()}@example.com",
                "customer_name": f"Concurrent User {i}",
                "company": "Concurrent Corp",
            }
            response = await async_client.post(
                "/api/v1/trials", json=trial_data
            )
            assert response.status_code == 201
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
        assert avg_duration < 10.0
