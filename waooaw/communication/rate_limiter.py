"""
Rate Limiting for Inter-Agent Communication

Provides token bucket and sliding window rate limiting to prevent agent abuse
and ensure fair resource allocation across the agent ecosystem.

Features:
- Token bucket algorithm for rate limiting
- Sliding window counter for burst detection
- Per-agent quota enforcement
- Configurable limits (messages per second/minute/hour)
- Integration with MessageBus
- Rate limit exceeded errors with retry-after
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional

from waooaw.common.logging_framework import StructuredLogger


class RateLimitWindow(Enum):
    """Time window for rate limiting."""
    
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an agent."""
    
    agent_id: str
    max_requests: int
    window: RateLimitWindow
    burst_size: Optional[int] = None  # Max burst above rate limit


@dataclass
class RateLimitStatus:
    """Current rate limit status."""
    
    agent_id: str
    requests_made: int
    requests_remaining: int
    window_start: datetime
    window_end: datetime
    retry_after: Optional[float] = None  # Seconds until limit resets


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, status: RateLimitStatus):
        self.status = status
        message = (
            f"Rate limit exceeded for agent {status.agent_id}: "
            f"{status.requests_made} requests made, "
            f"{status.requests_remaining} remaining. "
            f"Retry after {status.retry_after:.1f}s"
        )
        super().__init__(message)


class TokenBucket:
    """
    Token bucket rate limiter.
    
    Allows bursts up to bucket capacity while maintaining average rate.
    Tokens refill at constant rate.
    """
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,  # Tokens per second
        initial_tokens: Optional[int] = None,
    ):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens in bucket (burst size)
            refill_rate: Tokens added per second
            initial_tokens: Starting tokens (defaults to capacity)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        async with self._lock:
            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_refill
            refill_tokens = elapsed * self.refill_rate
            
            self.tokens = min(self.capacity, self.tokens + refill_tokens)
            self.last_refill = now
            
            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def get_tokens(self) -> float:
        """Get current token count."""
        async with self._lock:
            # Refill first
            now = time.time()
            elapsed = now - self.last_refill
            refill_tokens = elapsed * self.refill_rate
            
            self.tokens = min(self.capacity, self.tokens + refill_tokens)
            self.last_refill = now
            
            return self.tokens
    
    async def wait_for_tokens(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait until tokens available.
        
        Args:
            tokens: Number of tokens needed
            timeout: Max seconds to wait (None = wait forever)
            
        Returns:
            True if tokens acquired, False if timeout
        """
        start = time.time()
        
        while True:
            if await self.consume(tokens):
                return True
            
            # Check timeout
            if timeout and (time.time() - start) >= timeout:
                return False
            
            # Calculate wait time until next token
            wait_time = 1.0 / self.refill_rate
            await asyncio.sleep(min(wait_time, 0.1))  # Poll every 100ms


class SlidingWindowCounter:
    """
    Sliding window rate limiter.
    
    Tracks requests in a sliding time window. More accurate than fixed windows
    but requires more memory (stores timestamp per request).
    """
    
    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize sliding window counter.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Size of sliding window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: list[float] = []  # Timestamps of requests
        self._lock = asyncio.Lock()
    
    async def allow_request(self) -> tuple[bool, Optional[float]]:
        """
        Check if request allowed.
        
        Returns:
            (allowed, retry_after) tuple
            - allowed: True if request permitted
            - retry_after: Seconds until limit resets (if not allowed)
        """
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old requests outside window
            self.requests = [ts for ts in self.requests if ts > cutoff]
            
            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True, None
            
            # Calculate retry_after (time until oldest request expires)
            oldest_request = min(self.requests)
            retry_after = oldest_request + self.window_seconds - now
            
            return False, max(0, retry_after)
    
    async def get_count(self) -> int:
        """Get current request count in window."""
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old requests
            self.requests = [ts for ts in self.requests if ts > cutoff]
            
            return len(self.requests)
    
    async def reset(self):
        """Reset counter (clear all requests)."""
        async with self._lock:
            self.requests.clear()


class RateLimiter:
    """
    Multi-agent rate limiter with configurable limits.
    
    Combines token bucket (for smooth rate) with sliding window (for accuracy).
    Supports per-agent quotas and different time windows.
    """
    
    def __init__(
        self,
        default_config: RateLimitConfig,
        redis_url: Optional[str] = None,
    ):
        """
        Initialize rate limiter.
        
        Args:
            default_config: Default rate limit for all agents
            redis_url: Redis URL for distributed rate limiting (optional)
        """
        self.default_config = default_config
        self.redis_url = redis_url
        
        # Per-agent limiters
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.configs: Dict[str, RateLimitConfig] = {}
        
        # Logging
        self.logger = StructuredLogger(
            name="rate-limiter",
            level="INFO",
        )
    
    def set_agent_limit(self, config: RateLimitConfig):
        """Set custom rate limit for specific agent."""
        self.configs[config.agent_id] = config
        
        # Create limiters
        window_seconds = self._window_to_seconds(config.window)
        
        # Token bucket: capacity = burst_size or max_requests
        capacity = config.burst_size or config.max_requests
        refill_rate = config.max_requests / window_seconds
        
        self.token_buckets[config.agent_id] = TokenBucket(
            capacity=capacity,
            refill_rate=refill_rate,
        )
        
        self.sliding_windows[config.agent_id] = SlidingWindowCounter(
            max_requests=config.max_requests,
            window_seconds=window_seconds,
        )
        
        self.logger.info(
            "rate_limit_configured",
            agent_id=config.agent_id,
            max_requests=config.max_requests,
            window=config.window.value,
            burst_size=capacity,
        )
    
    async def check_limit(self, agent_id: str) -> RateLimitStatus:
        """
        Check rate limit status for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current rate limit status
            
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        # Get or create limiter
        if agent_id not in self.configs:
            self.set_agent_limit(
                RateLimitConfig(
                    agent_id=agent_id,
                    max_requests=self.default_config.max_requests,
                    window=self.default_config.window,
                    burst_size=self.default_config.burst_size,
                )
            )
        
        config = self.configs[agent_id]
        token_bucket = self.token_buckets[agent_id]
        sliding_window = self.sliding_windows[agent_id]
        
        # Check sliding window first (authoritative)
        allowed, retry_after = await sliding_window.allow_request()
        
        if not allowed:
            # Get status for error
            requests_made = await sliding_window.get_count()
            window_seconds = self._window_to_seconds(config.window)
            now = datetime.utcnow()
            
            status = RateLimitStatus(
                agent_id=agent_id,
                requests_made=requests_made,
                requests_remaining=0,
                window_start=now - timedelta(seconds=window_seconds),
                window_end=now,
                retry_after=retry_after,
            )
            
            self.logger.warning(
                "rate_limit_exceeded",
                agent_id=agent_id,
                requests_made=requests_made,
                retry_after=retry_after,
            )
            
            raise RateLimitExceeded(status)
        
        # Also consume token from bucket (smooth rate)
        token_consumed = await token_bucket.consume(1)
        
        # Get current status
        requests_made = await sliding_window.get_count()
        remaining_tokens = await token_bucket.get_tokens()
        window_seconds = self._window_to_seconds(config.window)
        now = datetime.utcnow()
        
        status = RateLimitStatus(
            agent_id=agent_id,
            requests_made=requests_made,
            requests_remaining=int(remaining_tokens),
            window_start=now - timedelta(seconds=window_seconds),
            window_end=now,
        )
        
        return status
    
    async def reset_limit(self, agent_id: str):
        """Reset rate limit for agent."""
        if agent_id in self.sliding_windows:
            await self.sliding_windows[agent_id].reset()
        
        if agent_id in self.token_buckets:
            bucket = self.token_buckets[agent_id]
            async with bucket._lock:
                bucket.tokens = bucket.capacity
                bucket.last_refill = time.time()
        
        self.logger.info("rate_limit_reset", agent_id=agent_id)
    
    async def get_status(self, agent_id: str) -> Optional[RateLimitStatus]:
        """Get current rate limit status without consuming quota."""
        if agent_id not in self.configs:
            return None
        
        config = self.configs[agent_id]
        sliding_window = self.sliding_windows[agent_id]
        token_bucket = self.token_buckets[agent_id]
        
        requests_made = await sliding_window.get_count()
        remaining_tokens = await token_bucket.get_tokens()
        window_seconds = self._window_to_seconds(config.window)
        now = datetime.utcnow()
        
        return RateLimitStatus(
            agent_id=agent_id,
            requests_made=requests_made,
            requests_remaining=int(remaining_tokens),
            window_start=now - timedelta(seconds=window_seconds),
            window_end=now,
        )
    
    def _window_to_seconds(self, window: RateLimitWindow) -> float:
        """Convert window enum to seconds."""
        if window == RateLimitWindow.SECOND:
            return 1.0
        elif window == RateLimitWindow.MINUTE:
            return 60.0
        elif window == RateLimitWindow.HOUR:
            return 3600.0
        elif window == RateLimitWindow.DAY:
            return 86400.0
        else:
            return 60.0  # Default to minute
