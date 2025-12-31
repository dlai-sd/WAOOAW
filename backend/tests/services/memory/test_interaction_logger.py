"""
Unit tests for Interaction Logger.

Tests cover:
- Logging interactions
- Retrieving history
- Analytics queries
- Failure pattern detection
- GDPR cleanup
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.memory.interaction_logger import InteractionLogger
from app.models.interaction_log import InteractionLog as InteractionLogModel


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def sample_log():
    """Sample interaction log."""
    return InteractionLogModel(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        agent_id="agent_marketing_001",
        task_type="social_post",
        task_input="Create Instagram post",
        agent_output="Here's your post...",
        rating=5,
        duration_ms=1200,
        success=True,
        metadata={}
    )


class TestInteractionLogger:
    """Test suite for InteractionLogger."""
    
    @pytest.mark.asyncio
    async def test_log_interaction(self, mock_db_session):
        """Test logging interaction."""
        logger = InteractionLogger(mock_db_session)
        
        customer_id = str(uuid.uuid4())
        
        log = await logger.log_interaction(
            customer_id=customer_id,
            agent_id="agent_001",
            task_type="email_campaign",
            task_input="Create welcome email",
            agent_output="Subject: Welcome!...",
            rating=5,
            duration_ms=1500,
            success=True
        )
        
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called
    
    @pytest.mark.asyncio
    async def test_get_history(self, mock_db_session, sample_log):
        """Test retrieving interaction history."""
        logger = InteractionLogger(mock_db_session)
        customer_id = str(sample_log.customer_id)
        
        # Mock database return
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_log, sample_log]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result
        
        history = await logger.get_history(customer_id, limit=10)
        
        assert len(history) == 2
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_history_with_filters(self, mock_db_session, sample_log):
        """Test history with task_type filter."""
        logger = InteractionLogger(mock_db_session)
        customer_id = str(sample_log.customer_id)
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_log]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result
        
        history = await logger.get_history(
            customer_id,
            task_type="social_post",
            success_only=True
        )
        
        assert len(history) == 1
    
    @pytest.mark.asyncio
    async def test_get_analytics(self, mock_db_session):
        """Test analytics summary."""
        logger = InteractionLogger(mock_db_session)
        customer_id = str(uuid.uuid4())
        
        # Mock aggregation result
        mock_row = MagicMock()
        mock_row.total = 100
        mock_row.successful = 85
        mock_row.avg_rating = 4.5
        mock_row.avg_duration = 1200.5
        
        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_db_session.execute.return_value = mock_result
        
        analytics = await logger.get_analytics(customer_id=customer_id, days=30)
        
        assert analytics["total_interactions"] == 100
        assert analytics["successful_interactions"] == 85
        assert analytics["failed_interactions"] == 15
        assert analytics["success_rate"] == 85.0
        assert analytics["avg_rating"] == 4.5
    
    @pytest.mark.asyncio
    async def test_get_analytics_no_data(self, mock_db_session):
        """Test analytics with no data."""
        logger = InteractionLogger(mock_db_session)
        
        mock_row = MagicMock()
        mock_row.total = None
        mock_row.successful = None
        mock_row.avg_rating = None
        mock_row.avg_duration = None
        
        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_db_session.execute.return_value = mock_result
        
        analytics = await logger.get_analytics(days=7)
        
        assert analytics["total_interactions"] == 0
        assert analytics["success_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_detect_failure_patterns(self, mock_db_session):
        """Test failure pattern detection."""
        logger = InteractionLogger(mock_db_session)
        
        # Mock pattern results
        mock_row1 = MagicMock()
        mock_row1.task_type = "complex_report"
        mock_row1.agent_id = "agent_analytics_001"
        mock_row1.total = 10
        mock_row1.failures = 6  # 60% failure rate
        
        mock_row2 = MagicMock()
        mock_row2.task_type = "social_post"
        mock_row2.agent_id = "agent_marketing_002"
        mock_row2.total = 20
        mock_row2.failures = 4  # 20% failure rate
        
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row1, mock_row2]
        mock_db_session.execute.return_value = mock_result
        
        patterns = await logger.detect_failure_patterns(days=7, min_failures=3)
        
        assert len(patterns) == 2
        # Should be sorted by failure_rate descending
        assert patterns[0]["failure_rate"] == 60.0
        assert patterns[0]["task_type"] == "complex_report"
        assert "CRITICAL" in patterns[0]["recommendation"]
        
        assert patterns[1]["failure_rate"] == 20.0
    
    @pytest.mark.asyncio
    async def test_get_trending_tasks(self, mock_db_session):
        """Test trending task types."""
        logger = InteractionLogger(mock_db_session)
        
        # Mock trending results
        mock_row1 = MagicMock()
        mock_row1.task_type = "email_campaign"
        mock_row1.count = 50
        mock_row1.success_rate = 0.9
        
        mock_row2 = MagicMock()
        mock_row2.task_type = "social_post"
        mock_row2.count = 35
        mock_row2.success_rate = 0.85
        
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row1, mock_row2]
        mock_db_session.execute.return_value = mock_result
        
        trending = await logger.get_trending_tasks(days=7, limit=10)
        
        assert len(trending) == 2
        assert trending[0]["task_type"] == "email_campaign"
        assert trending[0]["count"] == 50
        assert trending[0]["success_rate"] == 90.0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, mock_db_session):
        """Test GDPR cleanup of old logs."""
        logger = InteractionLogger(mock_db_session)
        
        # Mock deletion result
        mock_result = MagicMock()
        mock_result.rowcount = 250  # 250 logs deleted
        mock_db_session.execute.return_value = mock_result
        
        deleted_count = await logger.cleanup_old_logs()
        
        assert deleted_count == 250
        assert mock_db_session.commit.called
    
    def test_generate_failure_recommendation_critical(self, mock_db_session):
        """Test recommendation for critical failure rate."""
        logger = InteractionLogger(mock_db_session)
        
        recommendation = logger._generate_failure_recommendation(
            "complex_task",
            "agent_001",
            60.0
        )
        
        assert "CRITICAL" in recommendation
        assert "urgently" in recommendation.lower()
    
    def test_generate_failure_recommendation_warning(self, mock_db_session):
        """Test recommendation for warning level failure rate."""
        logger = InteractionLogger(mock_db_session)
        
        recommendation = logger._generate_failure_recommendation(
            "medium_task",
            "agent_002",
            35.0
        )
        
        assert "WARNING" in recommendation
    
    def test_generate_failure_recommendation_monitor(self, mock_db_session):
        """Test recommendation for monitor level failure rate."""
        logger = InteractionLogger(mock_db_session)
        
        recommendation = logger._generate_failure_recommendation(
            "simple_task",
            "agent_003",
            15.0
        )
        
        assert "Monitor" in recommendation


class TestInteractionLogModel:
    """Test InteractionLog model."""
    
    def test_log_model_creation(self, sample_log):
        """Test creating InteractionLog model."""
        assert sample_log.task_type == "social_post"
        assert sample_log.success is True
        assert sample_log.rating == 5
    
    def test_log_model_repr(self, sample_log):
        """Test log string representation."""
        repr_str = repr(sample_log)
        
        assert "InteractionLog" in repr_str
        assert sample_log.agent_id in repr_str


# Integration test markers
@pytest.mark.integration
class TestInteractionLoggerIntegration:
    """
    Integration tests requiring real database.
    Run with: pytest -m integration
    """
    
    @pytest.mark.asyncio
    async def test_real_database_analytics(self):
        """Test actual database analytics queries."""
        pytest.skip("Integration test - requires PostgreSQL")
