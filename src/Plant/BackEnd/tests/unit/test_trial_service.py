"""
Unit Tests for Trial Service
Tests business logic for trial operations (MVP-001)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from services.trial_service import TrialService
from models.trial import Trial, TrialStatus, TrialDeliverable
from schemas.trial import TrialCreate, TrialUpdate


@pytest.mark.unit
@pytest.mark.asyncio
class TestTrialService:
    """Unit tests for TrialService"""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def trial_service(self, mock_db_session):
        """Create TrialService instance with mock session"""
        return TrialService(mock_db_session)

    async def test_create_trial(self, trial_service, mock_db_session):
        """Test creating a trial"""
        agent_id = uuid4()
        trial_data = TrialCreate(
            agent_id=agent_id,
            customer_email="test@example.com",
            customer_name="John Doe",
            customer_company="Acme Corp",
        )

        # Mock database operations
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        trial = await trial_service.create_trial(trial_data)

        assert trial.customer_email == "test@example.com"
        assert trial.status == TrialStatus.ACTIVE
        assert trial.agent_id == agent_id
        # Trial should be 7 days
        duration = (trial.end_date - trial.start_date).days
        assert duration == 7

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_awaited_once()

    async def test_list_trials_no_filters(self, trial_service, mock_db_session):
        """Test listing trials without filters"""
        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        trials = await trial_service.list_trials()

        assert isinstance(trials, list)
        mock_db_session.execute.assert_awaited_once()

    async def test_list_trials_with_email_filter(
        self, trial_service, mock_db_session
    ):
        """Test listing trials filtered by customer email"""
        email = "customer@example.com"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        trials = await trial_service.list_trials(customer_email=email)

        assert isinstance(trials, list)
        mock_db_session.execute.assert_awaited_once()

    async def test_list_trials_with_status_filter(
        self, trial_service, mock_db_session
    ):
        """Test listing trials filtered by status"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        trials = await trial_service.list_trials(status=TrialStatus.ACTIVE)

        assert isinstance(trials, list)
        mock_db_session.execute.assert_awaited_once()

    async def test_update_trial_status_valid_transition(
        self, trial_service, mock_db_session
    ):
        """Test updating trial status with valid transition"""
        trial_id = uuid4()
        
        # Mock existing trial
        existing_trial = Trial(
            id=trial_id,
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_trial
        mock_db_session.execute.return_value = mock_result

        update_data = TrialUpdate(status=TrialStatus.CONVERTED)
        updated_trial = await trial_service.update_trial_status(
            trial_id, update_data
        )

        assert updated_trial.status == TrialStatus.CONVERTED
        mock_db_session.commit.assert_awaited_once()

    async def test_update_trial_status_invalid_transition(
        self, trial_service, mock_db_session
    ):
        """Test updating trial status with invalid transition"""
        trial_id = uuid4()
        
        # Mock cancelled trial (cannot be converted)
        existing_trial = Trial(
            id=trial_id,
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.CANCELLED,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_trial
        mock_db_session.execute.return_value = mock_result

        update_data = TrialUpdate(status=TrialStatus.CONVERTED)
        
        with pytest.raises(ValueError, match="Invalid status transition"):
            await trial_service.update_trial_status(trial_id, update_data)

    async def test_cancel_trial(self, trial_service, mock_db_session):
        """Test cancelling a trial"""
        trial_id = uuid4()
        
        existing_trial = Trial(
            id=trial_id,
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_trial
        mock_db_session.execute.return_value = mock_result

        cancelled_trial = await trial_service.cancel_trial(trial_id)

        assert cancelled_trial.status == TrialStatus.CANCELLED
        mock_db_session.commit.assert_awaited_once()

    async def test_convert_trial(self, trial_service, mock_db_session):
        """Test converting a trial"""
        trial_id = uuid4()
        
        existing_trial = Trial(
            id=trial_id,
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_trial
        mock_db_session.execute.return_value = mock_result

        converted_trial = await trial_service.convert_trial(trial_id)

        assert converted_trial.status == TrialStatus.CONVERTED
        mock_db_session.commit.assert_awaited_once()

    async def test_check_and_expire_trials(
        self, trial_service, mock_db_session
    ):
        """Test checking and expiring old trials"""
        # Mock expired trial
        expired_trial = Trial(
            id=uuid4(),
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow() - timedelta(days=10),
            end_date=datetime.utcnow() - timedelta(days=3),
            status=TrialStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expired_trial]
        mock_db_session.execute.return_value = mock_result

        expired_count = await trial_service.check_and_expire_trials()

        assert expired_count == 1
        assert expired_trial.status == TrialStatus.EXPIRED
        mock_db_session.commit.assert_awaited_once()

    async def test_add_deliverable(self, trial_service, mock_db_session):
        """Test adding a deliverable to a trial"""
        trial_id = uuid4()
        
        existing_trial = Trial(
            id=trial_id,
            agent_id=uuid4(),
            customer_email="test@example.com",
            customer_name="Test User",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status=TrialStatus.ACTIVE,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_trial
        mock_db_session.execute.return_value = mock_result
        mock_db_session.add = MagicMock()

        deliverable = await trial_service.add_deliverable(
            trial_id=trial_id,
            file_name="report.pdf",
            file_url="https://example.com/report.pdf",
            file_type="application/pdf",
            file_size=1024000,
            description="Test report",
        )

        assert deliverable.file_name == "report.pdf"
        assert deliverable.trial_id == trial_id
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_awaited_once()
