"""
Retry Policies

Configurable retry mechanisms with exponential backoff for handling
transient failures in task execution.
"""

import asyncio
import random
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Any

from waooaw.common.logging_framework import StructuredLogger


class RetryStrategy(Enum):
    """Retry strategy types"""

    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear increase in delay
    RANDOM = "random"  # Random delay within range


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts exceeded"""

    def __init__(self, attempts: int, last_error: Optional[Exception] = None):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Max retries ({attempts}) exceeded. Last error: {last_error}"
        )


@dataclass
class RetryConfig:
    """
    Configuration for retry policy
    
    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries)
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential backoff (default 2)
        jitter: Add random jitter to prevent thundering herd (0.0-1.0)
        retry_on: Exception types to retry on (None = all exceptions)
    """

    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.1
    retry_on: Optional[tuple] = None  # Exception types to retry

    def __post_init__(self):
        """Validate configuration"""
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.exponential_base < 1:
            raise ValueError("exponential_base must be >= 1")
        if not 0 <= self.jitter <= 1:
            raise ValueError("jitter must be between 0 and 1")


@dataclass
class RetryContext:
    """
    Context information for retry attempt
    
    Tracks retry state and history for a specific operation.
    """

    attempt: int = 0
    total_delay: float = 0.0
    errors: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def record_error(self, error: Exception, delay: float):
        """Record error and delay for this attempt"""
        self.errors.append(error)
        self.total_delay += delay


class RetryPolicy:
    """
    Retry policy with configurable strategies
    
    Implements various retry strategies including exponential backoff,
    linear backoff, and fixed delays with jitter.
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry policy
        
        Args:
            config: Retry configuration (uses defaults if None)
        """
        self.config = config or RetryConfig()
        self._logger = StructuredLogger(name="retry-policy", level="INFO")

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given retry attempt
        
        Args:
            attempt: Current retry attempt (0-indexed)
            
        Returns:
            Delay in seconds before next retry
        """
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay

        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (
                self.config.exponential_base ** attempt
            )

        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)

        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.config.base_delay, self.config.max_delay)

        else:
            delay = self.config.base_delay

        # Cap at max delay
        delay = min(delay, self.config.max_delay)

        # Add jitter
        if self.config.jitter > 0:
            jitter_amount = delay * self.config.jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)  # Ensure non-negative

        return delay

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried
        
        Args:
            error: Exception that occurred
            attempt: Current attempt number (1-indexed)
            
        Returns:
            True if should retry, False otherwise
        """
        # Check max retries
        if attempt > self.config.max_retries:
            return False

        # Check exception type filter
        if self.config.retry_on is not None:
            if not isinstance(error, self.config.retry_on):
                return False

        return True

    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry policy
        
        Args:
            func: Async callable to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from successful execution
            
        Raises:
            MaxRetriesExceededError: If all retries exhausted
        """
        context = RetryContext()

        for attempt in range(self.config.max_retries + 1):
            context.attempt = attempt

            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success!
                if attempt > 0:
                    self._logger.info(
                        "retry_succeeded",
                        extra={
                            "attempt": attempt,
                            "total_delay": context.total_delay,
                        },
                    )

                return result

            except Exception as error:
                # Check if should retry
                if not self.should_retry(error, attempt):
                    self._logger.error(
                        "retry_failed_not_retryable",
                        extra={
                            "attempt": attempt,
                            "error": str(error),
                            "error_type": type(error).__name__,
                        },
                    )
                    raise

                # Calculate delay
                delay = self.calculate_delay(attempt)
                context.record_error(error, delay)

                # Last attempt?
                if attempt >= self.config.max_retries:
                    self._logger.error(
                        "retry_exhausted",
                        extra={
                            "max_retries": self.config.max_retries,
                            "total_delay": context.total_delay,
                            "last_error": str(error),
                        },
                    )
                    raise MaxRetriesExceededError(
                        attempts=attempt + 1, last_error=error
                    )

                # Wait before retry
                self._logger.warning(
                    "retrying_after_failure",
                    extra={
                        "attempt": attempt,
                        "delay": delay,
                        "error": str(error),
                        "error_type": type(error).__name__,
                    },
                )

                await asyncio.sleep(delay)

        # Should never reach here
        raise MaxRetriesExceededError(attempts=context.attempt + 1)

    async def execute_with_context(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> tuple[Any, RetryContext]:
        """
        Execute function with retry policy and return context
        
        Args:
            func: Async callable to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Tuple of (result, retry_context)
            
        Raises:
            MaxRetriesExceededError: If all retries exhausted
        """
        context = RetryContext()

        for attempt in range(self.config.max_retries + 1):
            context.attempt = attempt

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                return result, context

            except Exception as error:
                if not self.should_retry(error, attempt):
                    raise

                delay = self.calculate_delay(attempt)
                context.record_error(error, delay)

                if attempt >= self.config.max_retries:
                    raise MaxRetriesExceededError(
                        attempts=attempt + 1, last_error=error
                    )

                await asyncio.sleep(delay)

        raise MaxRetriesExceededError(attempts=context.attempt + 1)


# Predefined retry policies for common scenarios
RETRY_POLICY_AGGRESSIVE = RetryConfig(
    max_retries=5,
    strategy=RetryStrategy.EXPONENTIAL,
    base_delay=0.5,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=0.1,
)

RETRY_POLICY_STANDARD = RetryConfig(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=0.1,
)

RETRY_POLICY_CONSERVATIVE = RetryConfig(
    max_retries=2,
    strategy=RetryStrategy.LINEAR,
    base_delay=2.0,
    max_delay=10.0,
    jitter=0.05,
)

RETRY_POLICY_QUICK = RetryConfig(
    max_retries=3,
    strategy=RetryStrategy.FIXED,
    base_delay=0.5,
    max_delay=0.5,
    jitter=0.0,
)
