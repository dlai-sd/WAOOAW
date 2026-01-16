"""
Unit Tests for Trial Models
Tests Trial and TrialDeliverable models (MVP-001)
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from models.trial import Trial, TrialStatus, TrialDeliverable


@pytest.mark.unit
class TestTrialModel:
    """Unit tests for Trial model"""

    def test_trial_creation(self):
        """Test creating a trial instance"""
        agent_id = uuid4()
        trial = Trial(
            id=uuid4(),
            agent_id=agent_id,
            customer_email="customer@example.com",
            customer_name="John Doe",
            customer_company="Acme Corp",
            customer_phone="+1234567890",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.ACTIVE,
        )

        assert trial.agent_id == agent_id
        assert trial.customer_email == "customer@example.com"
        assert trial.status == TrialStatus.ACTIVE

    def test_trial_days_remaining(self):
        """Test days_remaining property"""
        trial = Trial(
            id=uuid4(),
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow() - timedelta(days=3),
            end_date=datetime.utcnow() + timedelta(days=4),
            status=TrialStatus.ACTIVE,
        )

        days_remaining = trial.days_remaining
        assert 3 <= days_remaining <= 5  # Allow small time differences

    def test_trial_is_expired_false(self):
        """Test is_expired when trial is active"""
        trial = Trial(
            id=uuid4(),
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.ACTIVE,
        )

        assert trial.is_expired is False

    def test_trial_is_expired_true(self):
        """Test is_expired when trial has ended"""
        trial = Trial(
            id=uuid4(),
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow() - timedelta(days=10),
            end_date=datetime.utcnow() - timedelta(days=3),
            status=TrialStatus.EXPIRED,
        )

        assert trial.is_expired is True

    def test_trial_status_enum(self):
        """Test TrialStatus enum values"""
        assert TrialStatus.ACTIVE == "active"
        assert TrialStatus.CONVERTED == "converted"
        assert TrialStatus.CANCELLED == "cancelled"
        assert TrialStatus.EXPIRED == "expired"

    def test_trial_optional_fields(self):
        """Test trial with optional fields"""
        trial = Trial(
            id=uuid4(),
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.ACTIVE,
            customer_company=None,
            customer_phone=None,
        )

        assert trial.customer_company is None
        assert trial.customer_phone is None


@pytest.mark.unit
class TestTrialDeliverableModel:
    """Unit tests for TrialDeliverable model"""

    def test_deliverable_creation(self):
        """Test creating a deliverable instance"""
        trial_id = uuid4()
        deliverable = TrialDeliverable(
            id=uuid4(),
            trial_id=trial_id,
            file_name="report.pdf",
            file_url="https://storage.example.com/reports/report.pdf",
            file_type="application/pdf",
            file_size=1024000,
            description="Monthly marketing report",
            created_at=datetime.utcnow(),
        )

        assert deliverable.trial_id == trial_id
        assert deliverable.file_name == "report.pdf"
        assert deliverable.file_type == "application/pdf"
        assert deliverable.file_size == 1024000

    def test_deliverable_optional_description(self):
        """Test deliverable without description"""
        deliverable = TrialDeliverable(
            id=uuid4(),
            trial_id=uuid4(),
            file_name="data.csv",
            file_url="https://storage.example.com/data.csv",
            file_type="text/csv",
            file_size=5000,
            created_at=datetime.utcnow(),
        )

        assert deliverable.description is None

    def test_deliverable_timestamps(self):
        """Test deliverable timestamp handling"""
        now = datetime.utcnow()
        deliverable = TrialDeliverable(
            id=uuid4(),
            trial_id=uuid4(),
            file_name="file.txt",
            file_url="https://example.com/file.txt",
            file_type="text/plain",
            file_size=100,
            created_at=now,
        )

        assert isinstance(deliverable.created_at, datetime)
        assert (deliverable.created_at - now).total_seconds() < 1
