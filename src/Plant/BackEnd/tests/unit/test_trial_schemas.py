"""
Unit Tests for Trial Pydantic Schemas
Tests validation and serialization (MVP-001)
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timedelta
from uuid import uuid4

from schemas.trial import (
    TrialCreate,
    TrialUpdate,
    TrialResponse,
    TrialDeliverableCreate,
    TrialDeliverableResponse,
    TrialListResponse,
)
from models.trial import TrialStatus


@pytest.mark.unit
class TestTrialCreateSchema:
    """Unit tests for TrialCreate schema"""

    def test_valid_trial_create(self):
        """Test valid trial creation request"""
        data = {
            "agent_id": str(uuid4()),
            "customer_email": "test@example.com",
            "customer_name": "John Doe",
            "customer_company": "Acme Corp",
            "customer_phone": "+1234567890",
        }

        trial = TrialCreate(**data)
        assert trial.customer_email == "test@example.com"
        assert trial.customer_name == "John Doe"

    def test_trial_create_invalid_email(self):
        """Test trial creation with invalid email"""
        data = {
            "agent_id": str(uuid4()),
            "customer_email": "invalid-email",
            "customer_name": "John Doe",
        }

        with pytest.raises(ValidationError) as exc_info:
            TrialCreate(**data)

        errors = exc_info.value.errors()
        assert any("email" in str(e).lower() for e in errors)

    def test_trial_create_missing_required_fields(self):
        """Test trial creation with missing required fields"""
        with pytest.raises(ValidationError):
            TrialCreate(customer_email="test@example.com")

    def test_trial_create_optional_fields(self):
        """Test trial creation with optional fields omitted"""
        data = {
            "agent_id": str(uuid4()),
            "customer_email": "test@example.com",
            "customer_name": "John Doe",
        }

        trial = TrialCreate(**data)
        assert trial.customer_company is None
        assert trial.customer_phone is None

    def test_trial_create_email_validation(self):
        """Test email validation in trial creation"""
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "user+tag@example.com",
        ]

        for email in valid_emails:
            data = {
                "agent_id": str(uuid4()),
                "customer_email": email,
                "customer_name": "Test User",
            }
            trial = TrialCreate(**data)
            assert trial.customer_email == email


@pytest.mark.unit
class TestTrialUpdateSchema:
    """Unit tests for TrialUpdate schema"""

    def test_valid_trial_update(self):
        """Test valid trial update request"""
        data = {"status": "converted"}
        update = TrialUpdate(**data)
        assert update.status == TrialStatus.CONVERTED

    def test_trial_update_invalid_status(self):
        """Test trial update with invalid status"""
        with pytest.raises(ValidationError):
            TrialUpdate(status="invalid_status")

    def test_trial_update_all_statuses(self):
        """Test trial update with all valid statuses"""
        statuses = ["active", "converted", "cancelled", "expired"]

        for status in statuses:
            update = TrialUpdate(status=status)
            assert update.status == status


@pytest.mark.unit
class TestTrialResponseSchema:
    """Unit tests for TrialResponse schema"""

    def test_trial_response_serialization(self):
        """Test trial response serialization"""
        data = {
            "id": str(uuid4()),
            "agent_id": str(uuid4()),
            "customer_email": "test@example.com",
            "customer_name": "John Doe",
            "customer_company": "Acme Corp",
            "customer_phone": "+1234567890",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "active",
            "days_remaining": 7,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = TrialResponse(**data)
        assert response.customer_email == "test@example.com"
        assert response.status == TrialStatus.ACTIVE
        assert response.days_remaining == 7

    def test_trial_response_with_deliverables(self):
        """Test trial response with deliverables"""
        data = {
            "id": str(uuid4()),
            "agent_id": str(uuid4()),
            "customer_email": "test@example.com",
            "customer_name": "John Doe",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "active",
            "days_remaining": 7,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "deliverables": [],
        }

        response = TrialResponse(**data)
        assert isinstance(response.deliverables, list)


@pytest.mark.unit
class TestTrialListResponseSchema:
    """Unit tests for TrialListResponse schema"""

    def test_trial_list_response(self):
        """Test trial list response"""
        trials = [
            {
                "id": str(uuid4()),
                "agent_id": str(uuid4()),
                "customer_email": f"user{i}@example.com",
                "customer_name": f"User {i}",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "status": "active",
                "days_remaining": 7,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            for i in range(3)
        ]

        response = TrialListResponse(
            trials=trials, total=3, skip=0, limit=10
        )

        assert len(response.trials) == 3
        assert response.total == 3
        assert response.skip == 0
        assert response.limit == 10

    def test_trial_list_pagination(self):
        """Test trial list with pagination"""
        response = TrialListResponse(
            trials=[], total=100, skip=20, limit=10
        )

        assert response.total == 100
        assert response.skip == 20
        assert response.limit == 10


@pytest.mark.unit
class TestTrialDeliverableSchemas:
    """Unit tests for TrialDeliverable schemas"""

    def test_deliverable_create(self):
        """Test deliverable creation request"""
        data = {
            "file_name": "report.pdf",
            "file_url": "https://storage.example.com/report.pdf",
            "file_type": "application/pdf",
            "file_size": 1024000,
            "description": "Marketing report",
        }

        deliverable = TrialDeliverableCreate(**data)
        assert deliverable.file_name == "report.pdf"
        assert deliverable.file_size == 1024000

    def test_deliverable_response(self):
        """Test deliverable response serialization"""
        data = {
            "id": str(uuid4()),
            "trial_id": str(uuid4()),
            "file_name": "data.csv",
            "file_url": "https://example.com/data.csv",
            "file_type": "text/csv",
            "file_size": 5000,
            "created_at": datetime.utcnow().isoformat(),
        }

        response = TrialDeliverableResponse(**data)
        assert response.file_name == "data.csv"
        assert response.file_type == "text/csv"
