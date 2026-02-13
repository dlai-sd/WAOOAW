"""Tests for unified retry logic and circuit breaker.

Tests:
- Exponential backoff retry
- Circuit breaker state transitions
- Transient vs permanent error classification
- Retry-After header respect
- Max retry limits
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.social.retry_handler import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitBreakerState,
    RetryConfig,
    TransientError,
    classify_http_error,
    get_circuit_breaker,
    retry_with_backoff,
    with_circuit_breaker,
)
from integrations.social.base import SocialPlatformError


class TestCircuitBreaker:
    """Test circuit breaker pattern."""
    
    def test_initial_state_closed(self):
        """Circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker(platform="test")
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.can_attempt() is True
    
    def test_opens_after_threshold_failures(self):
        """Circuit breaker opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(platform="test", config=config)
        
        # Record failures
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.CLOSED
        
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.CLOSED
        
        breaker.record_failure()  # Third failure should open
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.can_attempt() is False
    
    def test_transitions_to_half_open_after_timeout(self):
        """Circuit breaker transitions to HALF_OPEN after recovery timeout."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        breaker = CircuitBreaker(platform="test", config=config)
        
        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        import time
        time.sleep(1.1)
        
        # Should transition to HALF_OPEN
        assert breaker.can_attempt() is True
        # Calling can_attempt() transitions the state
        assert breaker.state == CircuitBreakerState.HALF_OPEN
    
    def test_closes_after_successes_in_half_open(self):
        """Circuit breaker closes after success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0,
            success_threshold=2,
        )
        breaker = CircuitBreaker(platform="test", config=config)
        
        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN
        
        # Transition to HALF_OPEN
        breaker._transition_to_half_open()
        assert breaker.state == CircuitBreakerState.HALF_OPEN
        
        # Record successes
        breaker.record_success()
        assert breaker.state == CircuitBreakerState.HALF_OPEN
        
        breaker.record_success()  # Second success should close
        assert breaker.state == CircuitBreakerState.CLOSED
    
    def test_reopens_on_failure_in_half_open(self):
        """Circuit breaker reopens on failure in HALF_OPEN state."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0)
        breaker = CircuitBreaker(platform="test", config=config)
        
        # Open and transition to HALF_OPEN
        breaker.record_failure()
        breaker.record_failure()
        breaker._transition_to_half_open()
        assert breaker.state == CircuitBreakerState.HALF_OPEN
        
        # Failure in HALF_OPEN should reopen
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN
    
    def test_success_resets_failure_count_in_closed(self):
        """Success in CLOSED state resets failure count."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(platform="test", config=config)
        
        # Record some failures
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2
        
        # Success should reset
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitBreakerState.CLOSED


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """Function succeeds on first attempt without retry."""
        call_count = 0
        
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await retry_with_backoff(
            successful_func,
            platform="test",
        )
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self):
        """Function retries on transient errors."""
        call_count = 0
        
        async def failing_then_succeeding_func():
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                raise TransientError("Temporary failure")
            
            return "success"
        
        config = RetryConfig(max_attempts=5)
        result = await retry_with_backoff(
            failing_then_succeeding_func,
            platform="test",
            config=config,
        )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_fails_after_max_attempts(self):
        """Function fails after max retry attempts."""
        call_count = 0
        
        async def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise TransientError("Always failing")
        
        config = RetryConfig(max_attempts=3)
        
        with pytest.raises(TransientError):
            await retry_with_backoff(
                always_failing_func,
                platform="test",
                config=config,
            )
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Function does not retry on permanent errors."""
        call_count = 0
        
        async def permanent_error_func():
            nonlocal call_count
            call_count += 1
            raise SocialPlatformError(
                message="Permanent error",
                platform="test",
                error_code="AUTH_FAILED",
                is_transient=False,
            )
        
        config = RetryConfig(max_attempts=5)
        
        with pytest.raises(SocialPlatformError):
            await retry_with_backoff(
                permanent_error_func,
                platform="test",
                config=config,
            )
        
        # Should fail immediately without retries
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Circuit breaker opens after consecutive failures."""
        call_count = 0
        
        async def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise TransientError("Always failing")
        
        # Reset circuit breaker
        breaker = get_circuit_breaker("test_cb_open")
        breaker.state = CircuitBreakerState.CLOSED
        breaker.failure_count = 0
        breaker.config = CircuitBreakerConfig(failure_threshold=2)
        
        config = RetryConfig(max_attempts=1)  # Don't retry
        
        # First call - fails
        with pytest.raises(TransientError):
            await retry_with_backoff(
                always_failing_func,
                platform="test_cb_open",
                config=config,
            )
        
        # Second call - fails, should open circuit
        with pytest.raises(TransientError):
            await retry_with_backoff(
                always_failing_func,
                platform="test_cb_open",
                config=config,
            )
        
        assert breaker.state == CircuitBreakerState.OPEN
        
        # Third call - should be rejected by circuit breaker
        with pytest.raises(CircuitBreakerOpen):
            await retry_with_backoff(
                always_failing_func,
                platform="test_cb_open",
                config=config,
            )


class TestErrorClassification:
    """Test HTTP error classification."""
    
    def test_classify_429_as_transient(self):
        """429 rate limit classified as transient."""
        error = classify_http_error(
            platform="test",
            status_code=429,
            error_body={"error": {"message": "Rate limit exceeded"}},
        )
        
        assert isinstance(error, TransientError)
        assert error.retry_after == 60
    
    def test_classify_503_as_transient(self):
        """503 service unavailable classified as transient."""
        error = classify_http_error(
            platform="test",
            status_code=503,
            error_body={"error": {"message": "Service unavailable"}},
        )
        
        assert isinstance(error, TransientError)
        assert error.retry_after == 30
    
    def test_classify_5xx_as_transient(self):
        """5xx server errors classified as transient."""
        error = classify_http_error(
            platform="test",
            status_code=500,
            error_body={"error": {"message": "Internal server error"}},
        )
        
        assert isinstance(error, TransientError)
        assert error.retry_after == 5
    
    def test_classify_quota_as_transient(self):
        """Quota exceeded errors classified as transient."""
        error = classify_http_error(
            platform="test",
            status_code=403,
            error_body={"error": {"reason": "quotaExceeded", "message": "Quota exceeded"}},
        )
        
        assert isinstance(error, TransientError)
        assert error.retry_after == 86400  # 24 hours
    
    def test_classify_401_as_permanent(self):
        """401 authentication errors classified as permanent."""
        error = classify_http_error(
            platform="test",
            status_code=401,
            error_body={"error": {"message": "Invalid credentials"}},
        )
        
        assert isinstance(error, SocialPlatformError)
        assert error.is_transient is False
        assert error.error_code == "AUTH_FAILED"
    
    def test_classify_400_as_permanent(self):
        """400 bad request classified as permanent."""
        error = classify_http_error(
            platform="test",
            status_code=400,
            error_body={"error": {"message": "Invalid request"}},
        )
        
        assert isinstance(error, SocialPlatformError)
        assert error.is_transient is False
        assert error.error_code == "BAD_REQUEST"
    
    def test_classify_404_as_permanent(self):
        """404 not found classified as permanent."""
        error = classify_http_error(
            platform="test",
            status_code=404,
            error_body={"error": {"message": "Resource not found"}},
        )
        
        assert isinstance(error, SocialPlatformError)
        assert error.is_transient is False
        assert error.error_code == "NOT_FOUND"
    
    def test_respects_retry_after_header(self):
        """Retry-After header value is respected."""
        error = classify_http_error(
            platform="test",
            status_code=429,
            error_body={"error": {"message": "Rate limit"}},
            retry_after_header="120",
        )
        
        assert isinstance(error, TransientError)
        assert error.retry_after == 120


class TestRetryAfterHeader:
    """Test Retry-After header handling."""
    
    @pytest.mark.asyncio
    async def test_respects_retry_after_from_exception(self):
        """Retry logic respects retry_after from TransientError."""
        call_count = 0
        start_time = None
        
        async def func_with_retry_after():
            nonlocal call_count, start_time
            call_count += 1
            
            if call_count == 1:
                start_time = datetime.utcnow()
                raise TransientError("Rate limited", retry_after=2)
            
            return "success"
        
        config = RetryConfig(max_attempts=3, min_wait=0, max_wait=0)
        
        with patch("time.sleep") as mock_sleep:
            result = await retry_with_backoff(
                func_with_retry_after,
                platform="test",
                config=config,
            )
            
            assert result == "success"
            assert call_count == 2
            # Should have slept for retry_after duration
            mock_sleep.assert_called_once_with(2)


class TestConcurrentCircuitBreakers:
    """Test circuit breakers for multiple platforms."""
    
    def test_independent_circuit_breakers(self):
        """Circuit breakers are independent per platform."""
        breaker_youtube = get_circuit_breaker("youtube")
        breaker_instagram = get_circuit_breaker("instagram")
        
        # Open YouTube circuit
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker_youtube.config = config
        breaker_youtube.record_failure()
        breaker_youtube.record_failure()
        
        assert breaker_youtube.state == CircuitBreakerState.OPEN
        assert breaker_instagram.state == CircuitBreakerState.CLOSED
        
        # Instagram should still work
        assert breaker_instagram.can_attempt() is True
        assert breaker_youtube.can_attempt() is False


class TestCorrelationIdLogging:
    """Test correlation ID logging."""
    
    @pytest.mark.asyncio
    async def test_correlation_id_in_logs(self, caplog):
        """Correlation ID appears in logs."""
        async def successful_func():
            return "success"
        
        with caplog.at_level("INFO"):
            await retry_with_backoff(
                successful_func,
                platform="test",
                correlation_id="test-correlation-123",
            )
        
        # Check logs contain correlation ID
        assert any("test-correlation-123" in record.message for record in caplog.records)
