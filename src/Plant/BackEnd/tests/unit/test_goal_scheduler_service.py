"""Tests for goal scheduler service with error handling and retry logic."""

import asyncio
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from services.goal_scheduler_service import (
    ErrorType,
    GoalExecutionError,
    GoalRunStatus,
    GoalSchedulerService,
    PermanentError,
    TransientError,
)


# Test fixture for scheduled time
@pytest.fixture
def scheduled_time():
    """Provide a consistent scheduled time for tests."""
    return datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)


class TestGoalSchedulerService:
    """Test cases for goal scheduler basic functionality."""
    
    def test_scheduler_initialization(self):
        """Test scheduler initializes with correct defaults."""
        scheduler = GoalSchedulerService()
        
        assert scheduler.max_retries == 5
        assert scheduler.initial_backoff_seconds == 60
        assert scheduler.backoff_multiplier == 2.0
    
    def test_scheduler_custom_config(self):
        """Test scheduler accepts custom configuration."""
        scheduler = GoalSchedulerService(
            max_retries=3,
            initial_backoff_seconds=30,
            backoff_multiplier=1.5,
        )
        
        assert scheduler.max_retries == 3
        assert scheduler.initial_backoff_seconds == 30
        assert scheduler.backoff_multiplier == 1.5
    
    def test_calculate_backoff(self):
        """Test exponential backoff calculation."""
        scheduler = GoalSchedulerService(
            initial_backoff_seconds=60,
            backoff_multiplier=2.0,
        )
        
        # Backoff schedule: 60s, 120s, 240s, 480s, 960s
        assert scheduler._calculate_backoff(1) == 60  # 60 * 2^0
        assert scheduler._calculate_backoff(2) == 120  # 60 * 2^1
        assert scheduler._calculate_backoff(3) == 240  # 60 * 2^2
        assert scheduler._calculate_backoff(4) == 480  # 60 * 2^3
        assert scheduler._calculate_backoff(5) == 960  # 60 * 2^4


class TestGoalExecutionSuccess:
    """Test cases for successful goal execution."""
    
    @pytest.mark.asyncio
    async def test_successful_execution_first_attempt(self, scheduled_time):
        """Test successful goal execution on first attempt."""
        scheduler = GoalSchedulerService()
        
        # Mock successful execution
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = "deliverable-123"
            
            result = await scheduler.run_goal_with_retry("goal-456", scheduled_time)
            
            assert result.status == GoalRunStatus.COMPLETED
            assert result.goal_instance_id == "goal-456"
            assert result.deliverable_id == "deliverable-123"
            assert result.attempts == 1
            assert result.error_message is None
            assert result.total_duration_ms is not None
            mock_execute.assert_called_once_with("goal-456", None)
    
    @pytest.mark.asyncio
    async def test_successful_execution_with_correlation_id(self, scheduled_time):
        """Test successful execution includes correlation ID in logs."""
        scheduler = GoalSchedulerService()
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = "deliverable-789"
            
            result = await scheduler.run_goal_with_retry(
                "goal-123", scheduled_time, correlation_id="test-corr-456"
            )
            
            assert result.status == GoalRunStatus.COMPLETED
            assert result.deliverable_id == "deliverable-789"
            mock_execute.assert_called_once_with("goal-123", "test-corr-456")


class TestTransientErrorRetry:
    """Test cases for transient error retry logic."""
    
    @pytest.mark.asyncio
    async def test_transient_error_retries_with_backoff(self, scheduled_time):
        """Test transient errors retry with exponential backoff."""
        scheduler = GoalSchedulerService(
            max_retries=3,
            initial_backoff_seconds=1,  # Short for testing
        )
        
        # Mock: fail twice with transient, then succeed
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = [
                TransientError("Network timeout"),
                TransientError("Connection refused"),
                "deliverable-success",
            ]
            
            result = await scheduler.run_goal_with_retry("goal-retry", scheduled_time)
            
            assert result.status == GoalRunStatus.COMPLETED
            assert result.deliverable_id == "deliverable-success"
            assert result.attempts == 3
            assert mock_execute.call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self, scheduled_time):
        """Test goal fails after max retries exhausted."""
        scheduler = GoalSchedulerService(
            max_retries=2,
            initial_backoff_seconds=0.1,  # Very short for testing
        )
        
        # Mock: always fail with transient error
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = TransientError("Always fails")
            
            result = await scheduler.run_goal_with_retry("goal-fail", scheduled_time)
            
            assert result.status == GoalRunStatus.FAILED
            assert result.error_type == ErrorType.TRANSIENT
            assert "Max retries exhausted" in result.error_message
            assert result.attempts == 2
            assert mock_execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_backoff_delays_applied(self, scheduled_time):
        """Test that backoff delays are calculated and sleep is called."""
        scheduler = GoalSchedulerService(
            max_retries=3,
            initial_backoff_seconds=0.1,
            backoff_multiplier=2.0,
        )
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_execute.side_effect = [
                TransientError("Fail 1"),
                TransientError("Fail 2"),
                "success",
            ]
            
            await scheduler.run_goal_with_retry("goal-timing", scheduled_time)
            
            # Should have called sleep twice with backoff values (0.1s, 0.2s)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(0.1)  # First backoff
            mock_sleep.assert_any_call(0.2)  # Second backoff


class TestPermanentErrorHandling:
    """Test cases for permanent error handling."""
    
    @pytest.mark.asyncio
    async def test_permanent_error_fails_immediately(self, scheduled_time):
        """Test permanent errors fail fast without retry."""
        scheduler = GoalSchedulerService(max_retries=5)
        
        # Mock: permanent error on first attempt
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = PermanentError("Invalid configuration")
            
            result = await scheduler.run_goal_with_retry("goal-perm-fail", scheduled_time)
            
            assert result.status == GoalRunStatus.FAILED
            assert result.error_type == ErrorType.PERMANENT
            assert result.error_message == "Invalid configuration"
            assert result.attempts == 1
            mock_execute.assert_called_once()  # No retries
    
    @pytest.mark.asyncio
    async def test_permanent_error_types(self, scheduled_time):
        """Test various permanent error scenarios."""
        scheduler = GoalSchedulerService()
        
        permanent_errors = [
            PermanentError("Credentials not found"),
            PermanentError("Authentication failed"),
            PermanentError("Goal configuration invalid"),
        ]
        
        for error in permanent_errors:
            with patch.object(
                scheduler, "_execute_goal", new_callable=AsyncMock
            ) as mock_execute:
                mock_execute.side_effect = error
                
                result = await scheduler.run_goal_with_retry("goal-test", scheduled_time)
                
                assert result.status == GoalRunStatus.FAILED
                assert result.error_type == ErrorType.PERMANENT
                assert result.attempts == 1


class TestErrorClassification:
    """Test cases for error classification logic."""
    
    def test_classify_transient_errors(self):
        """Test transient error classification."""
        scheduler = GoalSchedulerService()
        
        transient_errors = [
            Exception("Connection timeout"),
            Exception("Network error"),
            Exception("Rate limit exceeded"),
            Exception("Service unavailable"),
            Exception("Database deadlock"),
            TimeoutError("Request timeout"),
        ]
        
        for error in transient_errors:
            assert scheduler.classify_error(error) == ErrorType.TRANSIENT
    
    def test_classify_permanent_errors(self):
        """Test permanent error classification."""
        scheduler = GoalSchedulerService()
        
        permanent_errors = [
            Exception("Not found"),
            Exception("Invalid request"),
            Exception("Unauthorized"),
            Exception("Forbidden"),
            Exception("Credential error"),
            Exception("Authentication failed"),
            Exception("Permission denied"),
            Exception("Bad request"),
        ]
        
        for error in permanent_errors:
            assert scheduler.classify_error(error) == ErrorType.PERMANENT
    
    def test_classify_ambiguous_errors_as_transient(self):
        """Test that ambiguous errors default to transient."""
        scheduler = GoalSchedulerService()
        
        # Unknown errors should be transient (allow retry for safety)
        ambiguous_errors = [
            Exception("Something went wrong"),
            Exception("Unknown error"),
            ValueError("Unexpected value"),
        ]
        
        for error in ambiguous_errors:
            assert scheduler.classify_error(error) == ErrorType.TRANSIENT
    
    def test_classify_already_classified_errors(self):
        """Test classification respects pre-classified errors."""
        scheduler = GoalSchedulerService()
        
        transient = TransientError("Already transient")
        permanent = PermanentError("Already permanent")
        
        assert scheduler.classify_error(transient) == ErrorType.TRANSIENT
        assert scheduler.classify_error(permanent) == ErrorType.PERMANENT


class TestConsecutiveFailureTracking:
    """Test cases for consecutive failure tracking and alerting."""
    
    @pytest.mark.asyncio
    async def test_consecutive_failures_tracked(self, scheduled_time):
        """Test that consecutive failures are tracked per goal."""
        scheduler = GoalSchedulerService(max_retries=1, initial_backoff_seconds=0.01)
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = PermanentError("Always fails")
            
            # First failure
            await scheduler.run_goal_with_retry("goal-fail-tracking", scheduled_time)
            assert scheduler._consecutive_failures["goal-fail-tracking"] == 1
            
            # Second failure
            await scheduler.run_goal_with_retry("goal-fail-tracking", scheduled_time)
            assert scheduler._consecutive_failures["goal-fail-tracking"] == 2
            
            # Third failure
            await scheduler.run_goal_with_retry("goal-fail-tracking", scheduled_time)
            assert scheduler._consecutive_failures["goal-fail-tracking"] == 3
    
    @pytest.mark.asyncio
    async def test_consecutive_failures_reset_on_success(self, scheduled_time):
        """Test that consecutive failure counter resets on success."""
        scheduler = GoalSchedulerService()
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            # Fail once
            mock_execute.side_effect = [PermanentError("Fail once")]
            await scheduler.run_goal_with_retry("goal-reset", scheduled_time)
            assert scheduler._consecutive_failures["goal-reset"] == 1
            
            # Then succeed
            mock_execute.side_effect = ["deliverable-success"]
            await scheduler.run_goal_with_retry("goal-reset", scheduled_time)
            assert "goal-reset" not in scheduler._consecutive_failures
    
    @pytest.mark.asyncio
    async def test_alert_on_three_consecutive_failures(self, scheduled_time, caplog):
        """Test that alert is logged after 3 consecutive failures."""
        scheduler = GoalSchedulerService(max_retries=1, initial_backoff_seconds=0.01)
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = PermanentError("Always fails")
            
            with caplog.at_level(logging.ERROR):
                # First two failures - no alert
                await scheduler.run_goal_with_retry("goal-alert", scheduled_time)
                await scheduler.run_goal_with_retry("goal-alert", scheduled_time)
                assert "ALERT" not in caplog.text
                
                # Third failure - alert triggered
                caplog.clear()
                await scheduler.run_goal_with_retry("goal-alert", scheduled_time)
                assert "ALERT" in caplog.text
                assert "3 consecutive failures" in caplog.text
                assert "goal-alert" in caplog.text


class TestUnclassifiedErrorHandling:
    """Test cases for handling unclassified exceptions."""
    
    @pytest.mark.asyncio
    async def test_unclassified_error_retries_as_transient(self, scheduled_time):
        """Test that unclassified errors are retried as transient."""
        scheduler = GoalSchedulerService(
            max_retries=2,
            initial_backoff_seconds=0.01,
        )
        
        # Mock: unclassified exception, then success
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = [
                ValueError("Some unexpected error"),
                "deliverable-success",
            ]
            
            result = await scheduler.run_goal_with_retry("goal-unclass", scheduled_time)
            
            assert result.status == GoalRunStatus.COMPLETED
            assert result.attempts == 2
    
    @pytest.mark.asyncio
    async def test_unclassified_error_logs_stack_trace(self, scheduled_time, caplog):
        """Test that unclassified errors log full stack trace."""
        scheduler = GoalSchedulerService(max_retries=1, initial_backoff_seconds=0.01)
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = RuntimeError("Unexpected runtime error")
            
            with caplog.at_level(logging.WARNING):
                await scheduler.run_goal_with_retry("goal-trace", scheduled_time)
                
                # Should log with exc_info=True (stack trace)
                assert "unclassified error" in caplog.text
                assert "Unexpected runtime error" in caplog.text


class TestLoggingAndObservability:
    """Test cases for comprehensive logging."""
    
    @pytest.mark.asyncio
    async def test_success_logged_with_details(self, scheduled_time, caplog):
        """Test successful execution is logged with full details."""
        scheduler = GoalSchedulerService()
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = "deliverable-log-test"
            
            with caplog.at_level(logging.INFO):
                result = await scheduler.run_goal_with_retry(
                    "goal-log", scheduled_time, correlation_id="corr-123"
                )
                
                # Should log start and success
                assert "Starting goal execution" in caplog.text
                assert "Goal execution succeeded" in caplog.text
                assert "goal-log" in caplog.text
                assert "deliverable-log-test" in caplog.text
                assert "corr-123" in caplog.text
                assert f"duration_ms={result.total_duration_ms}" in caplog.text
    
    @pytest.mark.asyncio
    async def test_failure_logged_with_details(self, scheduled_time, caplog):
        """Test failed execution is logged with error details."""
        scheduler = GoalSchedulerService(max_retries=1, initial_backoff_seconds=0.01)
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = PermanentError("Test failure")
            
            with caplog.at_level(logging.ERROR):
                await scheduler.run_goal_with_retry(
                    "goal-fail-log", scheduled_time, correlation_id="corr-fail-456"
                )
                
                assert "Goal execution failed (permanent error)" in caplog.text
                assert "goal-fail-log" in caplog.text
                assert "Test failure" in caplog.text
                assert "corr-fail-456" in caplog.text
    
    @pytest.mark.asyncio
    async def test_retry_logged_with_backoff(self, scheduled_time, caplog):
        """Test retries are logged with backoff information."""
        scheduler = GoalSchedulerService(
            max_retries=2,
            initial_backoff_seconds=1,
        )
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.side_effect = [
                TransientError("Retry test"),
                "success",
            ]
            
            with caplog.at_level(logging.INFO):
                await scheduler.run_goal_with_retry("goal-retry-log", scheduled_time)
                
                assert "Goal execution failed (transient error)" in caplog.text
                assert "Retrying goal after 1.0s backoff" in caplog.text
                assert "attempt=2/2" in caplog.text
