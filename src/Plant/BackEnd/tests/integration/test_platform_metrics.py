"""Tests for platform posting metrics and usage events.

Tests:
- Event logging and data capture
- Metrics collection and aggregation
- Success/failure tracking
- Timing and duration measurement
- Context manager usage
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from integrations.social.metrics import (
    PlatformMetricsCollector,
    PlatformPostEvent,
    PostingStatus,
    TimedPlatformCall,
    get_metrics_collector,
    log_platform_post_event,
)
from integrations.social.base import SocialPlatformError


class TestPlatformPostEvent:
    """Test PlatformPostEvent dataclass."""
    
    def test_create_success_event(self):
        """Create event for successful post."""
        event = PlatformPostEvent(
            correlation_id="test-123",
            customer_id="CUST-456",
            agent_id="AGENT-789",
            platform="youtube",
            status="success",
            timestamp="2026-02-11T12:00:00Z",
            duration_ms=1234,
            post_id="post_123",
            post_url="https://youtube.com/post/post_123",
        )
        
        assert event.event_type == "platform_post"
        assert event.platform == "youtube"
        assert event.status == "success"
        assert event.post_id == "post_123"
        assert event.error_code is None
    
    def test_create_failure_event(self):
        """Create event for failed post."""
        event = PlatformPostEvent(
            correlation_id="test-456",
            customer_id="CUST-789",
            agent_id="AGENT-012",
            platform="instagram",
            status="failed",
            timestamp="2026-02-11T12:00:00Z",
            duration_ms=567,
            error_code="AUTH_FAILED",
            error_message="Invalid credentials",
            is_transient=False,
            retry_count=0,
            max_retries=5,
        )
        
        assert event.status == "failed"
        assert event.error_code == "AUTH_FAILED"
        assert event.is_transient is False
        assert event.post_id is None
    
    def test_to_dict_removes_none_values(self):
        """to_dict() removes None values."""
        event = PlatformPostEvent(
            correlation_id="test-789",
            customer_id="CUST-012",
            agent_id="AGENT-345",
            platform="facebook",
            status="success",
            timestamp="2026-02-11T12:00:00Z",
            duration_ms=890,
            post_id="fb_post_123",
        )
        
        data = event.to_dict()
        # Should not have None values
        assert "error_code" not in data
        assert "error_message" not in data
        # Should have non-None values
        assert data["post_id"] == "fb_post_123"
        assert data["platform"] == "facebook"


class TestPlatformMetricsCollector:
    """Test PlatformMetricsCollector."""
    
    @pytest.fixture
    def collector(self):
        """Create metrics collector for testing."""
        return PlatformMetricsCollector(enable_remote_logging=False)
    
    @pytest.mark.asyncio
    async def test_log_successful_post(self, collector, caplog):
        """Log successful post attempt."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.INFO, logger="integrations.social.metrics")
        
        await collector.log_post_attempt(
            customer_id="CUST-123",
            agent_id="AGENT-456",
            platform="youtube",
            status=PostingStatus.SUCCESS,
            duration_ms=1000,
            post_id="post_123",
            post_url="https://youtube.com/post/post_123",
            correlation_id="test-success",
        )
        
        # Check metrics
        summary = collector.get_metrics_summary()
        assert summary["youtube"]["total_posts"] == 1
        assert summary["youtube"]["successful_posts"] == 1
        assert summary["youtube"]["failed_posts"] == 0
        assert summary["youtube"]["success_rate_pct"] == 100.0
        assert summary["youtube"]["avg_duration_ms"] == 1000.0
        
        # Check logging
        assert "test-success" in caplog.text
        assert "platform=youtube" in caplog.text
        assert "status=success" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_failed_post(self, collector, caplog):
        """Log failed post attempt."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.ERROR, logger="integrations.social.metrics")
        
        await collector.log_post_attempt(
            customer_id="CUST-789",
            agent_id="AGENT-012",
            platform="instagram",
            status=PostingStatus.FAILED,
            duration_ms=500,
            error_code="RATE_LIMIT",
            error_message="Too many requests",
            is_transient=True,
            retry_count=5,  # All retries exhausted
            max_retries=5,
            correlation_id="test-failure",
        )
        
        # Check metrics
        summary = collector.get_metrics_summary()
        assert summary["instagram"]["total_posts"] == 1
        assert summary["instagram"]["successful_posts"] == 0
        assert summary["instagram"]["failed_posts"] == 1
        assert summary["instagram"]["success_rate_pct"] == 0.0
        
        # Check logging
        assert "test-failure" in caplog.text
        assert "platform=instagram" in caplog.text
        assert "status=failed" in caplog.text
        assert "error=RATE_LIMIT" in caplog.text
        assert "retry=5/5" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_retrying_post(self, collector, caplog):
        """Log retrying post attempt."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.WARNING, logger="integrations.social.metrics")
        await collector.log_post_attempt(
            customer_id="CUST-345",
            agent_id="AGENT-678",
            platform="facebook",
            status=PostingStatus.RETRYING,
            duration_ms=750,
            error_code="SERVER_ERROR",
            error_message="Service unavailable",
            is_transient=True,
            retry_count=2,
            max_retries=5,
            correlation_id="test-retry",
        )
        
        # Retrying attempts don't count as failures yet
        summary = collector.get_metrics_summary()
        assert summary["facebook"]["total_posts"] == 1
        assert summary["facebook"]["failed_posts"] == 0
        
        # Check logging
        assert "test-retry" in caplog.text
        assert "status=retrying" in caplog.text
        assert "retry=2/5" in caplog.text
    
    @pytest.mark.asyncio
    async def test_multiple_platforms(self, collector):
        """Track metrics for multiple platforms."""
        # YouTube success
        await collector.log_post_attempt(
            customer_id="CUST-1",
            agent_id="AGENT-1",
            platform="youtube",
            status=PostingStatus.SUCCESS,
            duration_ms=1000,
            post_id="yt_1",
        )
        
        # Instagram success
        await collector.log_post_attempt(
            customer_id="CUST-1",
            agent_id="AGENT-1",
            platform="instagram",
            status=PostingStatus.SUCCESS,
            duration_ms=1500,
            post_id="ig_1",
        )
        
        # Instagram failure
        await collector.log_post_attempt(
            customer_id="CUST-1",
            agent_id="AGENT-1",
            platform="instagram",
            status=PostingStatus.FAILED,
            duration_ms=500,
            error_code="ERROR",
            retry_count=5,
            max_retries=5,
        )
        
        # Check metrics
        summary = collector.get_metrics_summary()
        
        assert summary["youtube"]["total_posts"] == 1
        assert summary["youtube"]["successful_posts"] == 1
        assert summary["youtube"]["success_rate_pct"] == 100.0
        
        assert summary["instagram"]["total_posts"] == 2
        assert summary["instagram"]["successful_posts"] == 1
        assert summary["instagram"]["failed_posts"] == 1
        assert summary["instagram"]["success_rate_pct"] == 50.0
        assert summary["instagram"]["avg_duration_ms"] == 1000.0  # (1500 + 500) / 2
    
    def test_reset_metrics(self, collector):
        """Reset metrics clears all counters."""
        # Add some data
        collector._post_count["youtube"] = 10
        collector._success_count["youtube"] = 8
        collector._failure_count["youtube"] = 2
        
        # Reset
        collector.reset_metrics()
        
        # Should be empty
        summary = collector.get_metrics_summary()
        assert len(summary) == 0
    
    @pytest.mark.asyncio
    async def test_remote_logging_disabled(self, collector):
        """Remote logging disabled does not send to backend."""
        collector._enable_remote_logging = False
        
        with patch.object(collector, "_send_to_backend") as mock_send:
            await collector.log_post_attempt(
                customer_id="CUST-1",
                agent_id="AGENT-1",
                platform="youtube",
                status=PostingStatus.SUCCESS,
                duration_ms=1000,
            )
            
            # Should not call backend
            mock_send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remote_logging_enabled(self, caplog):
        """Remote logging enabled sends to backend."""
        collector = PlatformMetricsCollector(enable_remote_logging=True)
        
        with patch.object(collector, "_send_to_backend", new_callable=AsyncMock) as mock_send:
            await collector.log_post_attempt(
                customer_id="CUST-1",
                agent_id="AGENT-1",
                platform="youtube",
                status=PostingStatus.SUCCESS,
                duration_ms=1000,
            )
            
            # Should call backend
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remote_logging_failure_handled_gracefully(self, collector, caplog):
        """Backend logging failure does not crash."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.WARNING, logger="integrations.social.metrics")
        collector._enable_remote_logging = True
        
        with patch.object(
            collector,
            "_send_to_backend",
            new_callable=AsyncMock,
            side_effect=Exception("Backend unavailable"),
        ):
            # Should not raise exception
            await collector.log_post_attempt(
                customer_id="CUST-1",
                agent_id="AGENT-1",
                platform="youtube",
                status=PostingStatus.SUCCESS,
                duration_ms=1000,
            )
            
            # Should log warning
            assert "Failed to send usage event to backend" in caplog.text


class TestTimedPlatformCall:
    """Test TimedPlatformCall context manager."""
    
    @pytest.mark.asyncio
    async def test_successful_call(self, caplog):
        """Successful call logs success event."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.INFO, logger="integrations.social.metrics")
        
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        async with TimedPlatformCall(
            customer_id="CUST-123",
            agent_id="AGENT-456",
            platform="youtube",
            correlation_id="test-timed-success",
        ) as timer:
            # Simulate successful API call
            timer.set_success(
                post_id="post_123",
                post_url="https://youtube.com/post/post_123",
            )
        
        # Check metrics
        summary = collector.get_metrics_summary()
        assert summary["youtube"]["successful_posts"] == 1
        assert summary["youtube"]["failed_posts"] == 0
        
        # Check logging
        assert "test-timed-success" in caplog.text
        assert "status=success" in caplog.text
    
    @pytest.mark.asyncio
    async def test_failed_call(self, caplog):
        """Failed call logs failure event."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.ERROR, logger="integrations.social.metrics")
        
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        async with TimedPlatformCall(
            customer_id="CUST-789",
            agent_id="AGENT-012",
            platform="instagram",
            correlation_id="test-timed-failure",
        ) as timer:
            # Simulate failed API call
            timer.set_failure(
                error_code="AUTH_FAILED",
                error_message="Invalid token",
                is_transient=False,
                retry_count=5,  # All retries exhausted
                max_retries=5,
            )
        
        # Check metrics
        summary = collector.get_metrics_summary()
        assert summary["instagram"]["successful_posts"] == 0
        assert summary["instagram"]["failed_posts"] == 1
        
        # Check logging
        assert "test-timed-failure" in caplog.text
        assert "status=failed" in caplog.text
        assert "error=AUTH_FAILED" in caplog.text
    
    @pytest.mark.asyncio
    async def test_retrying_call(self, caplog):
        """Retrying call logs retry event."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.WARNING, logger="integrations.social.metrics")
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        async with TimedPlatformCall(
            customer_id="CUST-345",
            agent_id="AGENT-678",
            platform="facebook",
            correlation_id="test-timed-retry",
        ) as timer:
            # Simulate retrying API call
            timer.set_retrying(
                error_code="RATE_LIMIT",
                error_message="Too many requests",
                retry_count=2,
                max_retries=5,
            )
        
        # Check logging
        assert "test-timed-retry" in caplog.text
        assert "status=retrying" in caplog.text
        assert "retry=2/5" in caplog.text
    
    @pytest.mark.asyncio
    async def test_exception_auto_failure(self, caplog):
        """Unhandled exception auto-marks as failure."""
        import logging
        caplog.set_level(logging.INFO)
        caplog.set_level(logging.ERROR, logger="integrations.social.metrics")
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        try:
            async with TimedPlatformCall(
                customer_id="CUST-999",
                agent_id="AGENT-888",
                platform="linkedin",
                correlation_id="test-exception",
            ) as timer:
                # Raise exception without setting status
                raise ValueError("Something went wrong")
        except ValueError:
            pass
        
        # Should log as failure
        assert "test-exception" in caplog.text
        assert "status=failed" in caplog.text
    
    @pytest.mark.asyncio
    async def test_timing_accuracy(self):
        """Context manager accurately measures duration."""
        import asyncio
        
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        async with TimedPlatformCall(
            customer_id="CUST-1",
            agent_id="AGENT-1",
            platform="youtube",
        ) as timer:
            # Simulate 100ms delay
            await asyncio.sleep(0.1)
            timer.set_success(post_id="test")
        
        # Check duration is approximately 100ms (with some tolerance)
        summary = collector.get_metrics_summary()
        avg_duration = summary["youtube"]["avg_duration_ms"]
        assert 90 <= avg_duration <= 150  # Allow 50ms tolerance


class TestGlobalMetricsCollector:
    """Test global metrics collector singleton."""
    
    def test_get_metrics_collector_singleton(self):
        """get_metrics_collector() returns same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        assert collector1 is collector2
    
    @pytest.mark.asyncio
    async def test_log_platform_post_event_convenience(self):
        """log_platform_post_event() convenience function works."""
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        await log_platform_post_event(
            customer_id="CUST-1",
            agent_id="AGENT-1",
            platform="youtube",
            status=PostingStatus.SUCCESS,
            duration_ms=1000,
            post_id="test_123",
        )
        
        # Check metrics
        summary = collector.get_metrics_summary()
        assert summary["youtube"]["total_posts"] == 1
        assert summary["youtube"]["successful_posts"] == 1


class TestContentTracking:
    """Test content type and length tracking."""
    
    @pytest.mark.asyncio
    async def test_track_text_content(self):
        """Track text content type and length."""
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        text = "This is a test post"
        
        async with TimedPlatformCall(
            customer_id="CUST-1",
            agent_id="AGENT-1",
            platform="youtube",
            content_type="text",
            content_length=len(text),
        ) as timer:
            timer.set_success(post_id="test")
        
        # Metrics logged (verified by no errors)
        assert True
    
    @pytest.mark.asyncio
    async def test_track_video_content(self):
        """Track video content type and length."""
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        async with TimedPlatformCall(
            customer_id="CUST-1",
            agent_id="AGENT-1",
            platform="youtube",
            content_type="video",
            content_length=1048576,  # 1MB in bytes
        ) as timer:
            timer.set_success(post_id="short_123")
        
        # Metrics logged (verified by no errors)
        assert True
