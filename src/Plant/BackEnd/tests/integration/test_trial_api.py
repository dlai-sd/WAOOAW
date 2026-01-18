"""
Integration Tests for Trial API Endpoints
Tests end-to-end trial flow with database (MVP-001)
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from uuid import uuid4

from main import app
from models.trial import TrialStatus


@pytest.mark.integration
@pytest.mark.asyncio
class TestTrialAPIIntegration:
    """Integration tests for Trial API endpoints"""

    @pytest.fixture
    async def async_client(self):
        """Create async HTTP client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def sample_agent_id(self):
        """Provide a sample agent ID for testing"""
        # In real integration tests, this should be an actual agent from DB
        return str(uuid4())

    async def test_create_trial_success(
        self, async_client, sample_agent_id
    ):
        """Test creating a trial successfully"""
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": "integration.test@example.com",
            "customer_name": "Integration Test User",
            "customer_company": "Test Corp",
            "customer_phone": "+1234567890",
        }

        response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["customer_email"] == trial_data["customer_email"]
        assert data["status"] == "active"
        assert "id" in data
        assert "start_date" in data
        assert "end_date" in data
        assert data["days_remaining"] <= 7

    async def test_create_trial_invalid_email(
        self, async_client, sample_agent_id
    ):
        """Test creating trial with invalid email"""
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": "invalid-email",
            "customer_name": "Test User",
        }

        response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )

        assert response.status_code == 422
        data = response.json()
        assert "email" in str(data).lower()

    async def test_list_trials_empty(self, async_client):
        """Test listing trials when none exist"""
        response = await async_client.get("/api/v1/trials")

        assert response.status_code == 200
        data = response.json()
        assert "trials" in data
        assert "total" in data
        assert isinstance(data["trials"], list)

    async def test_list_trials_with_pagination(self, async_client):
        """Test listing trials with pagination"""
        response = await async_client.get(
            "/api/v1/trials?skip=0&limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5

    async def test_list_trials_filter_by_email(
        self, async_client, sample_agent_id
    ):
        """Test filtering trials by customer email"""
        # Create a trial first
        email = f"filter.test.{uuid4()}@example.com"
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": email,
            "customer_name": "Filter Test User",
        }
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        assert create_response.status_code == 201

        # Filter by email
        response = await async_client.get(
            f"/api/v1/trials?customer_email={email}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(
            t["customer_email"] == email for t in data["trials"]
        )

    async def test_list_trials_filter_by_status(self, async_client):
        """Test filtering trials by status"""
        response = await async_client.get(
            "/api/v1/trials?status=active"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(
            t["status"] == "active" for t in data["trials"]
        )

    async def test_get_trial_by_id(
        self, async_client, sample_agent_id
    ):
        """Test getting a specific trial by ID"""
        # Create a trial
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": f"get.test.{uuid4()}@example.com",
            "customer_name": "Get Test User",
        }
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        trial_id = create_response.json()["id"]

        # Get trial by ID
        response = await async_client.get(f"/api/v1/trials/{trial_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == trial_id
        assert data["customer_email"] == trial_data["customer_email"]

    async def test_get_trial_not_found(self, async_client):
        """Test getting a non-existent trial"""
        fake_id = str(uuid4())
        response = await async_client.get(f"/api/v1/trials/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_update_trial_status(
        self, async_client, sample_agent_id
    ):
        """Test updating trial status"""
        # Create a trial
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": f"update.test.{uuid4()}@example.com",
            "customer_name": "Update Test User",
        }
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        trial_id = create_response.json()["id"]

        # Update status
        update_data = {"status": "converted"}
        response = await async_client.patch(
            f"/api/v1/trials/{trial_id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "converted"

    async def test_update_trial_invalid_status(
        self, async_client, sample_agent_id
    ):
        """Test updating trial with invalid status"""
        # Create a trial
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": f"invalid.update.{uuid4()}@example.com",
            "customer_name": "Invalid Update Test",
        }
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        trial_id = create_response.json()["id"]

        # Try invalid status
        update_data = {"status": "invalid_status"}
        response = await async_client.patch(
            f"/api/v1/trials/{trial_id}", json=update_data
        )

        assert response.status_code == 422

    async def test_cancel_trial(
        self, async_client, sample_agent_id
    ):
        """Test cancelling a trial"""
        # Create a trial
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": f"cancel.test.{uuid4()}@example.com",
            "customer_name": "Cancel Test User",
        }
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        trial_id = create_response.json()["id"]

        # Cancel trial
        response = await async_client.delete(
            f"/api/v1/trials/{trial_id}"
        )

        assert response.status_code == 204

        # Verify cancellation
        get_response = await async_client.get(
            f"/api/v1/trials/{trial_id}"
        )
        assert get_response.json()["status"] == "cancelled"

    async def test_get_trial_deliverables_empty(
        self, async_client, sample_agent_id
    ):
        """Test getting deliverables for trial with none"""
        # Create a trial
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": f"deliverable.test.{uuid4()}@example.com",
            "customer_name": "Deliverable Test User",
        }
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        trial_id = create_response.json()["id"]

        # Get deliverables
        response = await async_client.get(
            f"/api/v1/trials/{trial_id}/deliverables"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_trial_lifecycle(
        self, async_client, sample_agent_id
    ):
        """Test complete trial lifecycle: create → active → converted"""
        # 1. Create trial
        trial_data = {
            "agent_id": sample_agent_id,
            "customer_email": f"lifecycle.test.{uuid4()}@example.com",
            "customer_name": "Lifecycle Test User",
            "customer_company": "Test Corp",
        }
        create_response = await async_client.post(
            "/api/v1/trials", json=trial_data
        )
        assert create_response.status_code == 201
        trial_id = create_response.json()["id"]
        assert create_response.json()["status"] == "active"

        # 2. Get trial details
        get_response = await async_client.get(
            f"/api/v1/trials/{trial_id}"
        )
        assert get_response.status_code == 200
        assert get_response.json()["customer_company"] == "Test Corp"

        # 3. Convert trial
        update_response = await async_client.patch(
            f"/api/v1/trials/{trial_id}",
            json={"status": "converted"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "converted"

        # 4. Verify final state
        final_response = await async_client.get(
            f"/api/v1/trials/{trial_id}"
        )
        assert final_response.json()["status"] == "converted"
