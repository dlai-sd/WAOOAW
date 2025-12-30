"""
Tests for WowTrialManager - Trial Lifecycle Management Agent

Story 1.1.1: Trial Provisioning Engine (5 points)
Story 1.1.2: Usage Tracking System (5 points)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from waooaw.agents.wowtrialmanager import (
    WowTrialManager,
    TrialProvisioningEngine,
    TrialUsageTracker,
    Trial,
    TrialStatus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = Mock()
    db.trials = AsyncMock()
    db.customers = AsyncMock()
    db.trial_deliverables = AsyncMock()
    return db


@pytest.fixture
def mock_agent_factory():
    """Mock WowAgentFactory"""
    factory = AsyncMock()
    factory.create_instance = AsyncMock(return_value={
        "agent_id": str(uuid4()),
        "name": "Marketing Content Agent",
        "status": "active"
    })
    return factory


@pytest.fixture
def mock_notification_service():
    """Mock notification service"""
    service = AsyncMock()
    service.send_email = AsyncMock()
    return service


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service"""
    service = AsyncMock()
    service.log_event = AsyncMock()
    return service


@pytest.fixture
def mock_payment_service():
    """Mock payment service"""
    service = AsyncMock()
    return service


@pytest.fixture
def provisioning_engine(mock_db, mock_agent_factory, mock_notification_service):
    """TrialProvisioningEngine instance"""
    return TrialProvisioningEngine(
        db=mock_db,
        agent_factory=mock_agent_factory,
        notification_service=mock_notification_service
    )


@pytest.fixture
def usage_tracker(mock_db, mock_analytics_service):
    """TrialUsageTracker instance"""
    return TrialUsageTracker(
        db=mock_db,
        analytics_service=mock_analytics_service
    )


@pytest.fixture
def trial_manager(
    mock_db,
    mock_agent_factory,
    mock_notification_service,
    mock_analytics_service,
    mock_payment_service
):
    """WowTrialManager instance"""
    return WowTrialManager(
        db_connection=mock_db,
        agent_factory=mock_agent_factory,
        notification_service=mock_notification_service,
        analytics_service=mock_analytics_service,
        payment_service=mock_payment_service
    )


@pytest.fixture
def sample_customer():
    """Sample customer data"""
    return {
        "customer_id": str(uuid4()),
        "email": "customer@example.com",
        "name": "John Doe"
    }


@pytest.fixture
def sample_trial():
    """Sample trial object"""
    customer_id = str(uuid4())
    return Trial(
        trial_id=str(uuid4()),
        customer_id=customer_id,
        agent_type="marketing-content",
        status=TrialStatus.ACTIVE,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=7),
        days_remaining=7
    )


# ============================================================================
# STORY 1.1.1: TRIAL PROVISIONING ENGINE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestTrialProvisioning:
    """Test trial provisioning functionality"""
    
    async def test_provision_trial_success(
        self,
        provisioning_engine,
        mock_db,
        mock_agent_factory,
        mock_notification_service,
        sample_customer
    ):
        """Test successful trial provisioning"""
        # Setup mocks
        mock_db.customers.find_one = AsyncMock(return_value={
            "customer_id": sample_customer["customer_id"]
        })
        mock_db.trials.find_one = AsyncMock(return_value=None)  # No existing trial
        mock_db.trials.insert = AsyncMock()
        mock_db.trials.update = AsyncMock()
        
        # Provision trial
        trial = await provisioning_engine.provision_trial(
            customer_id=sample_customer["customer_id"],
            agent_type="marketing-content",
            customer_email=sample_customer["email"],
            customer_name=sample_customer["name"]
        )
        
        # Assertions
        assert trial.customer_id == sample_customer["customer_id"]
        assert trial.agent_type == "marketing-content"
        assert trial.status == TrialStatus.ACTIVE
        assert trial.days_remaining == 7
        assert trial.agent_id is not None
        
        # Verify database calls
        assert mock_db.trials.insert.called
        assert mock_db.trials.update.called
        
        # Verify agent was created
        mock_agent_factory.create_instance.assert_called_once()
        
        # Verify welcome email was triggered (async)
        # Note: Email is fire-and-forget, so we can't assert it was called
    
    async def test_provision_trial_performance(
        self,
        provisioning_engine,
        mock_db,
        sample_customer
    ):
        """Test trial provisioning completes in <5 seconds"""
        # Setup mocks
        mock_db.customers.find_one = AsyncMock(return_value={
            "customer_id": sample_customer["customer_id"]
        })
        mock_db.trials.find_one = AsyncMock(return_value=None)
        mock_db.trials.insert = AsyncMock()
        mock_db.trials.update = AsyncMock()
        
        # Measure time
        start_time = datetime.now()
        
        trial = await provisioning_engine.provision_trial(
            customer_id=sample_customer["customer_id"],
            agent_type="marketing-content",
            customer_email=sample_customer["email"],
            customer_name=sample_customer["name"]
        )
        
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        
        # Assert <5 second requirement
        assert elapsed_seconds < 5.0, f"Provisioning took {elapsed_seconds}s (requirement: <5s)"
        assert trial.status == TrialStatus.ACTIVE
    
    async def test_provision_trial_duplicate_active(
        self,
        provisioning_engine,
        mock_db,
        sample_customer
    ):
        """Test that duplicate active trial is rejected"""
        # Setup: customer already has active trial
        mock_db.customers.find_one = AsyncMock(return_value={
            "customer_id": sample_customer["customer_id"]
        })
        mock_db.trials.find_one = AsyncMock(return_value={
            "trial_id": str(uuid4()),
            "customer_id": sample_customer["customer_id"],
            "agent_type": "marketing-content",
            "status": TrialStatus.ACTIVE
        })
        
        # Attempt to provision duplicate trial
        with pytest.raises(ValueError, match="already has active trial"):
            await provisioning_engine.provision_trial(
                customer_id=sample_customer["customer_id"],
                agent_type="marketing-content",
                customer_email=sample_customer["email"],
                customer_name=sample_customer["name"]
            )
    
    async def test_provision_trial_invalid_agent_type(
        self,
        provisioning_engine,
        mock_db,
        sample_customer
    ):
        """Test that invalid agent type is rejected"""
        # Setup
        mock_db.customers.find_one = AsyncMock(return_value={
            "customer_id": sample_customer["customer_id"]
        })
        mock_db.trials.find_one = AsyncMock(return_value=None)
        
        # Attempt with invalid agent type
        with pytest.raises(ValueError, match="Invalid agent type"):
            await provisioning_engine.provision_trial(
                customer_id=sample_customer["customer_id"],
                agent_type="invalid-type",
                customer_email=sample_customer["email"],
                customer_name=sample_customer["name"]
            )
    
    async def test_provision_trial_customer_not_found(
        self,
        provisioning_engine,
        mock_db,
        sample_customer
    ):
        """Test that missing customer is rejected"""
        # Setup: customer doesn't exist
        mock_db.customers.find_one = AsyncMock(return_value=None)
        
        # Attempt to provision trial
        with pytest.raises(ValueError, match="Customer not found"):
            await provisioning_engine.provision_trial(
                customer_id=sample_customer["customer_id"],
                agent_type="marketing-content",
                customer_email=sample_customer["email"],
                customer_name=sample_customer["name"]
            )
    
    async def test_trial_to_dict(self, sample_trial):
        """Test Trial.to_dict() serialization"""
        trial_dict = sample_trial.to_dict()
        
        assert trial_dict["trial_id"] == sample_trial.trial_id
        assert trial_dict["customer_id"] == sample_trial.customer_id
        assert trial_dict["agent_type"] == sample_trial.agent_type
        assert trial_dict["status"] == sample_trial.status
        assert trial_dict["days_remaining"] == 7
        assert isinstance(trial_dict["start_date"], str)
        assert isinstance(trial_dict["end_date"], str)


# ============================================================================
# STORY 1.1.2: USAGE TRACKING TESTS
# ============================================================================

@pytest.mark.asyncio
class TestUsageTracking:
    """Test usage tracking functionality"""
    
    async def test_track_task_completed(
        self,
        usage_tracker,
        mock_db,
        mock_analytics_service,
        sample_trial
    ):
        """Test tracking a completed task"""
        # Setup
        mock_db.trials.find_one = AsyncMock(return_value=sample_trial.to_dict())
        mock_db.trials.update = AsyncMock()
        
        task = {
            "id": str(uuid4()),
            "deliverable_type": "blog_post",
            "output": "This is a sample blog post content...",
            "metadata": {"word_count": 500}
        }
        
        # Track task
        await usage_tracker.track_task_completed(sample_trial.trial_id, task)
        
        # Verify database update
        mock_db.trials.update.assert_called_once()
        update_call = mock_db.trials.update.call_args
        assert update_call[0][0] == {"trial_id": sample_trial.trial_id}
        assert update_call[0][1]["tasks_completed"] == 1
        assert len(update_call[0][1]["deliverables"]) == 1
        
        # Verify analytics event
        mock_analytics_service.log_event.assert_called_once_with(
            "trial_task_completed",
            {
                "trial_id": sample_trial.trial_id,
                "task_id": task["id"],
                "task_type": "blog_post",
                "tasks_total": 1
            }
        )
    
    async def test_track_multiple_tasks(
        self,
        usage_tracker,
        mock_db,
        sample_trial
    ):
        """Test tracking multiple tasks increments counter"""
        # Setup: trial with 2 existing tasks
        trial_dict = sample_trial.to_dict()
        trial_dict["tasks_completed"] = 2
        trial_dict["deliverables"] = [{"id": "1"}, {"id": "2"}]
        mock_db.trials.find_one = AsyncMock(return_value=trial_dict)
        mock_db.trials.update = AsyncMock()
        
        task = {
            "id": str(uuid4()),
            "deliverable_type": "social_post",
            "output": "Sample social media post"
        }
        
        # Track third task
        await usage_tracker.track_task_completed(sample_trial.trial_id, task)
        
        # Verify counter incremented to 3
        update_call = mock_db.trials.update.call_args
        assert update_call[0][1]["tasks_completed"] == 3
        assert len(update_call[0][1]["deliverables"]) == 3
    
    async def test_track_interaction(
        self,
        usage_tracker,
        mock_db,
        mock_analytics_service,
        sample_trial
    ):
        """Test tracking customer interaction"""
        # Setup
        trial_dict = sample_trial.to_dict()
        trial_dict["customer_interactions"] = 5
        trial_dict["satisfaction_score"] = 4.0
        mock_db.trials.find_one = AsyncMock(return_value=trial_dict)
        mock_db.trials.update = AsyncMock()
        
        # Track interaction
        await usage_tracker.track_interaction(
            trial_id=sample_trial.trial_id,
            interaction_type="feedback",
            duration_seconds=90,
            metadata={"rating": 5}
        )
        
        # Verify database update
        update_call = mock_db.trials.update.call_args
        assert update_call[0][1]["customer_interactions"] == 6
        assert update_call[0][1]["satisfaction_score"] > 4.0  # Increased
        
        # Verify analytics event
        mock_analytics_service.log_event.assert_called_once()
    
    async def test_track_interaction_improves_satisfaction(
        self,
        usage_tracker,
        mock_db,
        sample_trial
    ):
        """Test that positive feedback interaction improves satisfaction score"""
        # Setup
        trial_dict = sample_trial.to_dict()
        trial_dict["satisfaction_score"] = 4.0
        mock_db.trials.find_one = AsyncMock(return_value=trial_dict)
        mock_db.trials.update = AsyncMock()
        
        # Track positive feedback (>60s)
        await usage_tracker.track_interaction(
            trial_id=sample_trial.trial_id,
            interaction_type="feedback",
            duration_seconds=90
        )
        
        # Verify satisfaction improved
        update_call = mock_db.trials.update.call_args
        new_satisfaction = update_call[0][1]["satisfaction_score"]
        assert new_satisfaction > 4.0
        assert new_satisfaction <= 5.0  # Capped at max
    
    async def test_track_interaction_complaint_decreases_satisfaction(
        self,
        usage_tracker,
        mock_db,
        sample_trial
    ):
        """Test that complaint interaction decreases satisfaction score"""
        # Setup
        trial_dict = sample_trial.to_dict()
        trial_dict["satisfaction_score"] = 4.0
        mock_db.trials.find_one = AsyncMock(return_value=trial_dict)
        mock_db.trials.update = AsyncMock()
        
        # Track complaint
        await usage_tracker.track_interaction(
            trial_id=sample_trial.trial_id,
            interaction_type="complaint",
            duration_seconds=120
        )
        
        # Verify satisfaction decreased
        update_call = mock_db.trials.update.call_args
        new_satisfaction = update_call[0][1]["satisfaction_score"]
        assert new_satisfaction < 4.0
        assert new_satisfaction >= 1.0  # Floored at min
    
    async def test_get_usage_summary(
        self,
        usage_tracker,
        mock_db,
        sample_trial
    ):
        """Test getting usage summary for a trial"""
        # Setup
        trial_dict = sample_trial.to_dict()
        trial_dict["tasks_completed"] = 10
        trial_dict["deliverables"] = [{"id": f"{i}"} for i in range(10)]
        trial_dict["customer_interactions"] = 25
        trial_dict["satisfaction_score"] = 4.5
        trial_dict["days_remaining"] = 3
        mock_db.trials.find_one = AsyncMock(return_value=trial_dict)
        
        # Get summary
        summary = await usage_tracker.get_usage_summary(sample_trial.trial_id)
        
        # Verify summary
        assert summary["trial_id"] == sample_trial.trial_id
        assert summary["tasks_completed"] == 10
        assert summary["deliverables_count"] == 10
        assert summary["customer_interactions"] == 25
        assert summary["satisfaction_score"] == 4.5
        assert summary["days_remaining"] == 3
        assert summary["status"] == TrialStatus.ACTIVE
    
    async def test_track_task_trial_not_found(
        self,
        usage_tracker,
        mock_db
    ):
        """Test error handling when trial not found"""
        mock_db.trials.find_one = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Trial not found"):
            await usage_tracker.track_task_completed(
                str(uuid4()),
                {"id": str(uuid4()), "output": "test"}
            )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestWowTrialManagerIntegration:
    """Integration tests for WowTrialManager"""
    
    async def test_full_trial_lifecycle(
        self,
        trial_manager,
        mock_db,
        sample_customer
    ):
        """Test complete trial lifecycle from provisioning to usage tracking"""
        # Setup mocks
        mock_db.customers.find_one = AsyncMock(return_value={
            "customer_id": sample_customer["customer_id"]
        })
        mock_db.trials.find_one = AsyncMock(return_value=None)
        mock_db.trials.insert = AsyncMock()
        mock_db.trials.update = AsyncMock()
        
        # 1. Provision trial
        trial_dict = await trial_manager.provision_trial(
            customer_id=sample_customer["customer_id"],
            agent_type="marketing-content",
            customer_email=sample_customer["email"],
            customer_name=sample_customer["name"]
        )
        
        trial_id = trial_dict["trial_id"]
        assert trial_dict["status"] == TrialStatus.ACTIVE
        
        # 2. Track some tasks
        mock_db.trials.find_one = AsyncMock(return_value=trial_dict)
        
        await trial_manager.track_task(trial_id, {
            "id": str(uuid4()),
            "deliverable_type": "blog_post",
            "output": "Sample content"
        })
        
        # 3. Track interactions
        await trial_manager.track_interaction(
            trial_id=trial_id,
            interaction_type="feedback",
            duration_seconds=120
        )
        
        # 4. Get status
        trial_dict["tasks_completed"] = 1
        trial_dict["customer_interactions"] = 1
        mock_db.trials.find_one = AsyncMock(return_value=trial_dict)
        
        status = await trial_manager.get_trial_status(trial_id)
        assert status["tasks_completed"] == 1
        assert status["customer_interactions"] == 1
    
    async def test_list_trials_by_customer(
        self,
        trial_manager,
        mock_db,
        sample_customer
    ):
        """Test listing trials for a specific customer"""
        # Setup: customer has 3 trials
        trials = [
            {
                "trial_id": str(uuid4()),
                "customer_id": sample_customer["customer_id"],
                "agent_type": "marketing-content",
                "status": TrialStatus.ACTIVE
            },
            {
                "trial_id": str(uuid4()),
                "customer_id": sample_customer["customer_id"],
                "agent_type": "education-math",
                "status": TrialStatus.CONVERTED
            },
            {
                "trial_id": str(uuid4()),
                "customer_id": sample_customer["customer_id"],
                "agent_type": "sales-sdr",
                "status": TrialStatus.CANCELLED
            }
        ]
        mock_db.trials.find = AsyncMock(return_value=trials)
        
        # List trials
        result = await trial_manager.list_trials(
            customer_id=sample_customer["customer_id"]
        )
        
        assert len(result) == 3
        assert all(t["customer_id"] == sample_customer["customer_id"] for t in result)
    
    async def test_list_trials_by_status(
        self,
        trial_manager,
        mock_db
    ):
        """Test listing trials filtered by status"""
        # Setup: mix of trial statuses
        trials = [
            {
                "trial_id": str(uuid4()),
                "status": TrialStatus.ACTIVE
            },
            {
                "trial_id": str(uuid4()),
                "status": TrialStatus.ACTIVE
            }
        ]
        mock_db.trials.find = AsyncMock(return_value=trials)
        
        # List only active trials
        result = await trial_manager.list_trials(status=TrialStatus.ACTIVE)
        
        assert len(result) == 2
        assert all(t["status"] == TrialStatus.ACTIVE for t in result)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks for trial management"""
    
    async def test_provision_100_trials_under_5s_each(
        self,
        provisioning_engine,
        mock_db,
        mock_agent_factory
    ):
        """Test that each trial provisions in <5s even under load"""
        # Setup
        mock_db.customers.find_one = AsyncMock(return_value={"customer_id": str(uuid4())})
        mock_db.trials.find_one = AsyncMock(return_value=None)
        mock_db.trials.insert = AsyncMock()
        mock_db.trials.update = AsyncMock()
        
        # Provision 100 trials and track times
        times = []
        for i in range(100):
            start = datetime.now()
            
            await provisioning_engine.provision_trial(
                customer_id=str(uuid4()),
                agent_type="marketing-content",
                customer_email=f"customer{i}@example.com",
                customer_name=f"Customer {i}"
            )
            
            elapsed = (datetime.now() - start).total_seconds()
            times.append(elapsed)
        
        # All should be <5s
        assert all(t < 5.0 for t in times), f"Some trials exceeded 5s: {max(times)}s"
        
        # Average should be well under 5s
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0, f"Average time too high: {avg_time}s"
