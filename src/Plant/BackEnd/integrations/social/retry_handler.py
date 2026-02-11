"""Unified retry logic and circuit breaker for social platform integrations.

Provides:
- Exponential backoff retry with configurable limits
- Circuit breaker pattern to prevent cascading failures
- Error classification (transient vs permanent)
- Retry-After header respect
- Comprehensive logging with correlation IDs
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type

from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Open after N consecutive failures
    recovery_timeout: int = 60  # Seconds to wait before trying again
    success_threshold: int = 2  # Successes needed to close from half-open


@dataclass
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.
    
    Pattern:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing recovery, allow limited requests
    
    Transitions:
    - CLOSED → OPEN: After failure_threshold consecutive failures
    - OPEN → HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN → CLOSED: After success_threshold consecutive successes
    - HALF_OPEN → OPEN: On any failure
    """
    
    platform: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    # State tracking
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    
    def record_success(self) -> None:
        """Record successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"Circuit breaker for {self.platform}: success in HALF_OPEN "
                f"({self.success_count}/{self.config.success_threshold})"
            )
            
            if self.success_count >= self.config.success_threshold:
                self._close()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record failed call."""
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            logger.warning(
                f"Circuit breaker for {self.platform}: failure "
                f"({self.failure_count}/{self.config.failure_threshold})"
            )
            
            if self.failure_count >= self.config.failure_threshold:
                self._open()
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning(f"Circuit breaker for {self.platform}: failure in HALF_OPEN, reopening")
            self._open()
    
    def can_attempt(self) -> bool:
        """Check if request can be attempted."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if self.opened_at and datetime.utcnow() - self.opened_at >= timedelta(
                seconds=self.config.recovery_timeout
            ):
                self._transition_to_half_open()
                return True
            return False
        
        # HALF_OPEN: allow attempt
        return True
    
    def _open(self) -> None:
        """Transition to OPEN state."""
        self.state = CircuitBreakerState.OPEN
        self.opened_at = datetime.utcnow()
        logger.error(
            f"Circuit breaker for {self.platform} OPENED after "
            f"{self.failure_count} consecutive failures"
        )
    
    def _close(self) -> None:
        """Transition to CLOSED state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        logger.info(f"Circuit breaker for {self.platform} CLOSED (recovered)")
    
    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0
        logger.info(
            f"Circuit breaker for {self.platform} transitioned to HALF_OPEN "
            f"(testing recovery after {self.config.recovery_timeout}s)"
        )


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, platform: str, retry_after: int):
        self.platform = platform
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker for {platform} is OPEN. Retry after {retry_after}s"
        )


# Global circuit breakers per platform
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(platform: str) -> CircuitBreaker:
    """Get or create circuit breaker for platform."""
    if platform not in _circuit_breakers:
        _circuit_breakers[platform] = CircuitBreaker(platform=platform)
    return _circuit_breakers[platform]


class TransientError(Exception):
    """Base class for transient errors that should trigger retry."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        self.message = message
        self.retry_after = retry_after  # Seconds to wait before retry (from Retry-After header)
        super().__init__(message)


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 5  # Max retry attempts
    min_wait: int = 1  # Min wait between retries (seconds)
    max_wait: int = 16  # Max wait between retries (seconds)
    multiplier: int = 2  # Exponential multiplier
    
    # Exponential backoff: 1s, 2s, 4s, 8s, 16s


def should_retry(exception: Exception) -> bool:
    """Determine if exception should trigger retry."""
    return isinstance(exception, TransientError)


@asynccontextmanager
async def with_circuit_breaker(platform: str):
    """Context manager for circuit breaker pattern.
    
    Usage:
        async with with_circuit_breaker("youtube"):
            result = await make_api_call()
    """
    breaker = get_circuit_breaker(platform)
    
    if not breaker.can_attempt():
        retry_after = breaker.config.recovery_timeout
        if breaker.opened_at:
            elapsed = (datetime.utcnow() - breaker.opened_at).total_seconds()
            retry_after = max(0, int(breaker.config.recovery_timeout - elapsed))
        
        raise CircuitBreakerOpen(platform, retry_after)
    
    try:
        yield breaker
        breaker.record_success()
    except Exception as e:
        breaker.record_failure()
        raise


async def retry_with_backoff(
    func: Callable,
    *args: Any,
    platform: str,
    config: Optional[RetryConfig] = None,
    correlation_id: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Execute function with exponential backoff retry and circuit breaker.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for func
        platform: Platform name (for circuit breaker)
        config: Retry configuration (default: 5 attempts, 1-16s exponential)
        correlation_id: Optional correlation ID for logging
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func
        
    Raises:
        CircuitBreakerOpen: If circuit breaker is open
        RetryError: If all retry attempts exhausted
    """
    if config is None:
        config = RetryConfig()
    
    log_prefix = f"[{correlation_id}] " if correlation_id else ""
    
    async with with_circuit_breaker(platform) as breaker:
        attempt = 0
        
        async for attempt_state in AsyncRetrying(
            stop=stop_after_attempt(config.max_attempts),
            wait=wait_exponential(
                multiplier=config.multiplier,
                min=config.min_wait,
                max=config.max_wait,
            ),
            retry=retry_if_exception_type(TransientError),
            reraise=True,
        ):
            with attempt_state:
                attempt = attempt_state.attempt_number
                
                try:
                    logger.info(
                        f"{log_prefix}Attempting {platform} API call "
                        f"(attempt {attempt}/{config.max_attempts})"
                    )
                    
                    result = await func(*args, **kwargs)
                    
                    logger.info(
                        f"{log_prefix}{platform} API call succeeded "
                        f"(attempt {attempt})"
                    )
                    
                    return result
                    
                except TransientError as e:
                    logger.warning(
                        f"{log_prefix}{platform} API call failed with transient error "
                        f"(attempt {attempt}/{config.max_attempts}): {e.message}"
                    )
                    
                    # Respect Retry-After header if provided
                    if e.retry_after:
                        wait_time = e.retry_after
                        logger.info(
                            f"{log_prefix}Respecting Retry-After: waiting {wait_time}s"
                        )
                        time.sleep(wait_time)
                    
                    raise  # Let tenacity handle retry
                
                except Exception as e:
                    # Permanent error - don't retry
                    logger.error(
                        f"{log_prefix}{platform} API call failed with permanent error: {e}",
                        exc_info=True,
                    )
                    raise


def create_retry_decorator(
    platform: str,
    config: Optional[RetryConfig] = None,
) -> Callable:
    """Create retry decorator for a specific platform.
    
    Usage:
        @create_retry_decorator("youtube")
        async def post_text(self, text: str) -> Result:
            # Make API call
            pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            correlation_id = kwargs.pop("correlation_id", None)
            return await retry_with_backoff(
                func,
                *args,
                platform=platform,
                config=config,
                correlation_id=correlation_id,
                **kwargs,
            )
        return wrapper
    
    return decorator


# Platform-specific transient error classes
class YouTubeTransientError(TransientError):
    """YouTube-specific transient error."""
    pass


class InstagramTransientError(TransientError):
    """Instagram-specific transient error."""
    pass


class FacebookTransientError(TransientError):
    """Facebook-specific transient error."""
    pass


class LinkedInTransientError(TransientError):
    """LinkedIn-specific transient error."""
    pass


class WhatsAppTransientError(TransientError):
    """WhatsApp-specific transient error."""
    pass


def classify_http_error(
    platform: str,
    status_code: int,
    error_body: Dict[str, Any],
    retry_after_header: Optional[str] = None,
) -> Exception:
    """Classify HTTP error as transient or permanent.
    
    Args:
        platform: Platform name
        status_code: HTTP status code
        error_body: Error response body
        retry_after_header: Value of Retry-After header
        
    Returns:
        TransientError for retryable errors
        SocialPlatformError for permanent errors
    """
    from integrations.social.base import SocialPlatformError
    
    # Parse retry_after header
    retry_after = None
    if retry_after_header:
        try:
            retry_after = int(retry_after_header)
        except ValueError:
            # Could be HTTP date format, default to 60s
            retry_after = 60
    
    # Transient errors (should retry)
    if status_code == 429:  # Rate limit
        return TransientError(
            f"{platform} rate limit exceeded",
            retry_after=retry_after or 60,
        )
    
    if status_code == 503:  # Service unavailable
        return TransientError(
            f"{platform} service unavailable",
            retry_after=retry_after or 30,
        )
    
    if status_code >= 500:  # Server errors
        return TransientError(
            f"{platform} server error ({status_code})",
            retry_after=retry_after or 5,
        )
    
    # Check for quota errors (platform-specific)
    error_reason = str(error_body.get("error", {}).get("reason", "")).lower()
    if "quota" in error_reason or status_code == 403 and "quota" in str(error_body).lower():
        return TransientError(
            f"{platform} quota exceeded",
            retry_after=86400,  # 24 hours for quota reset
        )
    
    # Permanent errors (don't retry)
    error_message = error_body.get("error", {}).get("message", "Unknown error")
    
    if status_code == 401:
        return SocialPlatformError(
            message=f"{platform} authentication failed: {error_message}",
            platform=platform,
            error_code="AUTH_FAILED",
            is_transient=False,
        )
    
    if status_code == 400:
        return SocialPlatformError(
            message=f"{platform} bad request: {error_message}",
            platform=platform,
            error_code="BAD_REQUEST",
            is_transient=False,
        )
    
    if status_code == 403:
        return SocialPlatformError(
            message=f"{platform} forbidden: {error_message}",
            platform=platform,
            error_code="FORBIDDEN",
            is_transient=False,
        )
    
    if status_code == 404:
        return SocialPlatformError(
            message=f"{platform} not found: {error_message}",
            platform=platform,
            error_code="NOT_FOUND",
            is_transient=False,
        )
    
    # Unknown error - treat as permanent
    return SocialPlatformError(
        message=f"{platform} error ({status_code}): {error_message}",
        platform=platform,
        error_code="UNKNOWN_ERROR",
        is_transient=False,
    )
