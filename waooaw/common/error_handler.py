"""
WAOOAW Common Components: Error Handler

Provides retry with exponential backoff, circuit breaker, DLQ, and graceful degradation.

Usage:
    # Basic usage (default: 3 retries, exponential backoff):
    handler = ErrorHandler()
    result = handler.execute(risky_operation)
    
    # With fallback:
    result = handler.execute(
        operation=llm_call,
        fallback=rule_based_decision,
        on_error=log_error
    )
    
    # Advanced configuration:
    handler = ErrorHandler(
        retry_policy=RetryPolicy(max_attempts=3, base_delay=1.0),
        circuit_breaker=CircuitBreaker(failure_threshold=5, timeout=60)
    )

Vision Compliance:
    ✅ Zero Risk: Circuit breaker prevents cascading failures
    ✅ Cost Optimization: Graceful degradation to cheaper alternatives
    ✅ Simplicity: Sensible defaults, optional advanced features
"""

import time
import logging
from typing import Any, Callable, Optional, List, Type
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryPolicy:
    """
    Retry policy configuration.
    
    Attributes:
        max_attempts: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        backoff_multiplier: Exponential backoff multiplier (default: 2.0)
        retryable_exceptions: List of exception types to retry (default: all)
    """
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_exceptions: Optional[List[Type[Exception]]] = None
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay)
    
    def is_retryable(self, exception: Exception) -> bool:
        """
        Check if exception is retryable.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if should retry
        """
        if self.retryable_exceptions is None:
            return True  # Retry all exceptions by default
        
        return any(isinstance(exception, exc_type) 
                  for exc_type in self.retryable_exceptions)


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing if service recovered
    
    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        
        if breaker.allow_request():
            try:
                result = risky_operation()
                breaker.record_success()
            except Exception as e:
                breaker.record_failure()
                raise
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_requests: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            timeout: Seconds to wait before half-open
            half_open_requests: Test requests in half-open state
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_attempts = 0
    
    def allow_request(self) -> bool:
        """
        Check if request should be allowed.
        
        Returns:
            True if request should proceed
        """
        if self._state == CircuitState.CLOSED:
            return True
        
        if self._state == CircuitState.OPEN:
            # Check if timeout elapsed
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    logger.info("Circuit breaker moving to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_attempts = 0
                    return True
            return False
        
        if self._state == CircuitState.HALF_OPEN:
            # Allow limited requests to test
            if self._half_open_attempts < self.half_open_requests:
                self._half_open_attempts += 1
                return True
            return False
        
        return False
    
    def record_success(self):
        """Record successful operation."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker closing after successful test")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_attempts = 0
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self):
        """Record failed operation."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker opening after half-open failure")
            self._state = CircuitState.OPEN
            self._half_open_attempts = 0
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker opening after {self._failure_count} failures"
                )
                self._state = CircuitState.OPEN
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    def reset(self):
        """Reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_attempts = 0


class DLQHandler:
    """
    Dead Letter Queue handler for failed tasks.
    
    Example:
        dlq = DLQHandler(queue_name="failed_llm_calls")
        
        try:
            result = operation()
        except Exception as e:
            dlq.send(task_data, error=str(e))
    """
    
    def __init__(
        self,
        queue_name: str = "dead_letter_queue",
        max_retries_before_dlq: int = 3
    ):
        """
        Initialize DLQ handler.
        
        Args:
            queue_name: Name of dead letter queue
            max_retries_before_dlq: Retries before sending to DLQ
        """
        self.queue_name = queue_name
        self.max_retries_before_dlq = max_retries_before_dlq
        self._messages: List[dict] = []
    
    def send(self, task_data: Any, error: str, attempt: int = 0):
        """
        Send failed task to DLQ.
        
        Args:
            task_data: Task data that failed
            error: Error message
            attempt: Number of attempts made
        """
        message = {
            'task_data': task_data,
            'error': error,
            'attempt': attempt,
            'timestamp': datetime.now().isoformat(),
            'queue': self.queue_name
        }
        
        self._messages.append(message)
        
        logger.error(
            f"Task sent to DLQ '{self.queue_name}': {error} "
            f"(attempt {attempt}/{self.max_retries_before_dlq})"
        )
    
    def get_messages(self) -> List[dict]:
        """Get all DLQ messages."""
        return self._messages.copy()
    
    def clear(self):
        """Clear all DLQ messages."""
        self._messages.clear()


class ErrorHandler:
    """
    Comprehensive error handler with retry, circuit breaker, and DLQ.
    
    Features:
    - Exponential backoff retry
    - Circuit breaker pattern
    - Dead letter queue for permanent failures
    - Graceful fallback functions
    - Detailed error logging
    
    Example:
        handler = ErrorHandler(
            retry_policy=RetryPolicy(max_attempts=3),
            circuit_breaker=CircuitBreaker(failure_threshold=5)
        )
        
        result = handler.execute(
            operation=lambda: risky_api_call(),
            fallback=lambda: safe_default_value(),
            on_error=lambda e: log_to_monitoring(e)
        )
    """
    
    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        dlq_handler: Optional[DLQHandler] = None
    ):
        """
        Initialize error handler.
        
        Args:
            retry_policy: Retry configuration (default: 3 attempts)
            circuit_breaker: Circuit breaker (default: 5 failures, 60s timeout)
            dlq_handler: DLQ handler (default: basic DLQ)
        """
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.dlq_handler = dlq_handler or DLQHandler()
    
    def execute(
        self,
        operation: Callable[[], Any],
        fallback: Optional[Callable[[], Any]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        task_data: Optional[Any] = None
    ) -> Any:
        """
        Execute operation with full error handling.
        
        Flow:
        1. Check circuit breaker
        2. Try operation with retries
        3. On failure, call fallback if provided
        4. Send to DLQ if all retries exhausted
        5. Call on_error callback
        
        Args:
            operation: Function to execute
            fallback: Fallback function if operation fails
            on_error: Error callback function
            task_data: Task data for DLQ (optional)
            
        Returns:
            Result from operation or fallback
            
        Raises:
            Exception: If operation fails and no fallback provided
        """
        # Check circuit breaker
        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker OPEN, rejecting request")
            if fallback:
                return fallback()
            raise RuntimeError("Circuit breaker is OPEN")
        
        last_exception = None
        
        # Retry loop
        for attempt in range(self.retry_policy.max_attempts):
            try:
                result = operation()
                
                # Success!
                self.circuit_breaker.record_success()
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if retryable
                if not self.retry_policy.is_retryable(e):
                    logger.error(f"Non-retryable error: {e}")
                    break
                
                # Log attempt
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/"
                    f"{self.retry_policy.max_attempts}): {e}"
                )
                
                # Calculate backoff delay
                if attempt < self.retry_policy.max_attempts - 1:
                    delay = self.retry_policy.calculate_delay(attempt)
                    logger.debug(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        
        # All retries exhausted
        self.circuit_breaker.record_failure()
        
        # Send to DLQ
        if task_data:
            self.dlq_handler.send(
                task_data=task_data,
                error=str(last_exception),
                attempt=self.retry_policy.max_attempts
            )
        
        # Call error callback
        if on_error and last_exception:
            try:
                on_error(last_exception)
            except Exception as callback_error:
                logger.error(f"Error callback failed: {callback_error}")
        
        # Try fallback
        if fallback:
            logger.info("Executing fallback function")
            try:
                return fallback()
            except Exception as fallback_error:
                logger.error(f"Fallback failed: {fallback_error}")
                raise fallback_error
        
        # No fallback, raise original exception
        if last_exception:
            raise last_exception
        
        raise RuntimeError("Operation failed with no exception captured")
    
    def get_stats(self) -> dict:
        """
        Get error handler statistics.
        
        Returns:
            Dict with circuit breaker state, DLQ size, etc.
        """
        return {
            'circuit_breaker': {
                'state': self.circuit_breaker.state.value,
                'failure_count': self.circuit_breaker._failure_count
            },
            'dlq': {
                'message_count': len(self.dlq_handler.get_messages()),
                'queue_name': self.dlq_handler.queue_name
            },
            'retry_policy': {
                'max_attempts': self.retry_policy.max_attempts,
                'base_delay': self.retry_policy.base_delay
            }
        }


# Convenience functions

def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for simple retry logic.
    
    Example:
        @retry(max_attempts=3, base_delay=1.0)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            policy = RetryPolicy(
                max_attempts=max_attempts,
                base_delay=base_delay,
                retryable_exceptions=retryable_exceptions
            )
            handler = ErrorHandler(retry_policy=policy)
            return handler.execute(lambda: func(*args, **kwargs))
        return wrapper
    return decorator
