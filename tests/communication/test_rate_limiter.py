"""
Tests for Rate Limiting - Token Bucket & Sliding Window

Tests cover:
- Token bucket algorithm
- Sliding window counter
- Per-agent rate limiting
- Rate limit exceeded errors
- Burst handling
- Multiple time windows
"""

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio

from waooaw.communication.rate_limiter import (
    RateLimiter,
    TokenBucket,
    SlidingWindowCounter,
    RateLimitConfig,
    RateLimitWindow,
    RateLimitExceeded,
)


# Token Bucket Tests

@pytest.mark.asyncio
async def test_token_bucket_consume():
    """Test consuming tokens from bucket."""
    bucket = TokenBucket(capacity=10, refill_rate=1.0)  # 1 token/second
    
    # Should consume successfully
    assert await bucket.consume(5) is True
    
    # Check remaining tokens
    tokens = await bucket.get_tokens()
    assert 4.5 <= tokens <= 5.5  # ~5 tokens (allow small refill)


@pytest.mark.asyncio
async def test_token_bucket_refill():
    """Test token bucket refilling over time."""
    bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/second
    
    # Consume all tokens
    assert await bucket.consume(10) is True
    assert await bucket.get_tokens() < 1.0
    
    # Wait for refill
    await asyncio.sleep(0.5)  # 0.5s * 10 tokens/s = 5 tokens
    
    tokens = await bucket.get_tokens()
    assert 4.0 <= tokens <= 6.0  # ~5 tokens (timing variance)


@pytest.mark.asyncio
async def test_token_bucket_overflow():
    """Test bucket doesn't exceed capacity."""
    bucket = TokenBucket(capacity=5, refill_rate=10.0)
    
    # Wait for potential overflow
    await asyncio.sleep(1.0)  # Would refill 10 tokens
    
    # Should cap at capacity
    tokens = await bucket.get_tokens()
    assert tokens <= 5.0


@pytest.mark.asyncio
async def test_token_bucket_insufficient():
    """Test consuming more tokens than available."""
    bucket = TokenBucket(capacity=10, refill_rate=1.0, initial_tokens=3)
    
    # Try to consume more than available
    assert await bucket.consume(5) is False
    
    # Tokens unchanged
    assert await bucket.get_tokens() >= 3.0


@pytest.mark.asyncio
async def test_token_bucket_wait():
    """Test waiting for tokens."""
    bucket = TokenBucket(capacity=5, refill_rate=10.0, initial_tokens=0)
    
    # Wait for tokens (should succeed quickly at 10/s)
    success = await bucket.wait_for_tokens(3, timeout=1.0)
    assert success is True


# Sliding Window Tests

@pytest.mark.asyncio
async def test_sliding_window_allow():
    """Test sliding window allows requests under limit."""
    window = SlidingWindowCounter(max_requests=5, window_seconds=1.0)
    
    # Should allow up to max_requests
    for i in range(5):
        allowed, retry_after = await window.allow_request()
        assert allowed is True
        assert retry_after is None


@pytest.mark.asyncio
async def test_sliding_window_exceed():
    """Test sliding window blocks when limit exceeded."""
    window = SlidingWindowCounter(max_requests=3, window_seconds=1.0)
    
    # Use up quota
    for i in range(3):
        allowed, _ = await window.allow_request()
        assert allowed is True
    
    # Next request should fail
    allowed, retry_after = await window.allow_request()
    assert allowed is False
    assert retry_after is not None
    assert retry_after > 0


@pytest.mark.asyncio
async def test_sliding_window_expiry():
    """Test sliding window resets after time expires."""
    window = SlidingWindowCounter(max_requests=2, window_seconds=0.5)
    
    # Use up quota
    await window.allow_request()
    await window.allow_request()
    
    # Should be blocked
    allowed, _ = await window.allow_request()
    assert allowed is False
    
    # Wait for window to expire
    await asyncio.sleep(0.6)
    
    # Should allow again
    allowed, _ = await window.allow_request()
    assert allowed is True


@pytest.mark.asyncio
async def test_sliding_window_count():
    """Test getting request count."""
    window = SlidingWindowCounter(max_requests=5, window_seconds=1.0)
    
    # Make 3 requests
    for i in range(3):
        await window.allow_request()
    
    # Check count
    count = await window.get_count()
    assert count == 3


@pytest.mark.asyncio
async def test_sliding_window_reset():
    """Test resetting window."""
    window = SlidingWindowCounter(max_requests=2, window_seconds=1.0)
    
    # Use up quota
    await window.allow_request()
    await window.allow_request()
    
    # Reset
    await window.reset()
    
    # Should allow again
    allowed, _ = await window.allow_request()
    assert allowed is True


# RateLimiter Tests

@pytest_asyncio.fixture
async def rate_limiter():
    """Create rate limiter with default config."""
    config = RateLimitConfig(
        agent_id="default",
        max_requests=10,
        window=RateLimitWindow.MINUTE,
    )
    return RateLimiter(default_config=config)


@pytest.mark.asyncio
async def test_rate_limiter_check_limit(rate_limiter):
    """Test checking rate limit."""
    status = await rate_limiter.check_limit("test-agent")
    
    assert status.agent_id == "test-agent"
    assert status.requests_made == 1  # First request
    assert status.requests_remaining > 0


@pytest.mark.asyncio
async def test_rate_limiter_exceed(rate_limiter):
    """Test rate limit exceeded error."""
    # Set low limit
    rate_limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="limited-agent",
            max_requests=2,
            window=RateLimitWindow.SECOND,
        )
    )
    
    # Use up quota
    await rate_limiter.check_limit("limited-agent")
    await rate_limiter.check_limit("limited-agent")
    
    # Should raise exception
    with pytest.raises(RateLimitExceeded) as exc_info:
        await rate_limiter.check_limit("limited-agent")
    
    assert exc_info.value.status.agent_id == "limited-agent"
    assert exc_info.value.status.retry_after is not None


@pytest.mark.asyncio
async def test_rate_limiter_per_agent():
    """Test per-agent rate limits."""
    default_config = RateLimitConfig(
        agent_id="default",
        max_requests=10,
        window=RateLimitWindow.MINUTE,
    )
    limiter = RateLimiter(default_config=default_config)
    
    # Set different limits for two agents
    limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="agent-a",
            max_requests=5,
            window=RateLimitWindow.SECOND,
        )
    )
    limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="agent-b",
            max_requests=3,
            window=RateLimitWindow.SECOND,
        )
    )
    
    # Agent A should allow 5
    for i in range(5):
        await limiter.check_limit("agent-a")
    
    # Agent B should allow 3
    for i in range(3):
        await limiter.check_limit("agent-b")
    
    # Both should be blocked now
    with pytest.raises(RateLimitExceeded):
        await limiter.check_limit("agent-a")
    
    with pytest.raises(RateLimitExceeded):
        await limiter.check_limit("agent-b")


@pytest.mark.asyncio
async def test_rate_limiter_burst():
    """Test burst handling with token bucket."""
    config = RateLimitConfig(
        agent_id="bursty-agent",
        max_requests=10,  # 10 per second (not minute)
        window=RateLimitWindow.SECOND,
        burst_size=20,  # Allow bursts up to 20
    )
    limiter = RateLimiter(default_config=config)
    limiter.set_agent_limit(config)
    
    # Should handle burst of 10 within the second limit
    # (burst_size only affects token bucket smoothing, not sliding window)
    for i in range(10):
        status = await limiter.check_limit("bursty-agent")
        assert status.requests_remaining >= 0


@pytest.mark.asyncio
async def test_rate_limiter_reset(rate_limiter):
    """Test resetting rate limit."""
    # Set low limit
    rate_limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="reset-agent",
            max_requests=1,
            window=RateLimitWindow.SECOND,
        )
    )
    
    # Use up quota
    await rate_limiter.check_limit("reset-agent")
    
    # Should be blocked
    with pytest.raises(RateLimitExceeded):
        await rate_limiter.check_limit("reset-agent")
    
    # Reset
    await rate_limiter.reset_limit("reset-agent")
    
    # Should allow again
    status = await rate_limiter.check_limit("reset-agent")
    assert status.requests_made == 1


@pytest.mark.asyncio
async def test_rate_limiter_get_status(rate_limiter):
    """Test getting status without consuming quota."""
    rate_limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="status-agent",
            max_requests=5,
            window=RateLimitWindow.SECOND,
        )
    )
    
    # Make some requests
    await rate_limiter.check_limit("status-agent")
    await rate_limiter.check_limit("status-agent")
    
    # Get status (shouldn't consume quota)
    status = await rate_limiter.get_status("status-agent")
    
    assert status is not None
    assert status.agent_id == "status-agent"
    assert status.requests_made == 2
    
    # Get status again (should still show 2)
    status2 = await rate_limiter.get_status("status-agent")
    assert status2.requests_made == 2


@pytest.mark.asyncio
async def test_rate_limiter_multiple_windows():
    """Test different time windows."""
    limiter = RateLimiter(
        default_config=RateLimitConfig(
            agent_id="default",
            max_requests=100,
            window=RateLimitWindow.HOUR,
        )
    )
    
    # Per-second limit
    limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="per-second",
            max_requests=2,
            window=RateLimitWindow.SECOND,
        )
    )
    
    # Per-minute limit
    limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="per-minute",
            max_requests=60,
            window=RateLimitWindow.MINUTE,
        )
    )
    
    # Test per-second (2 allowed)
    await limiter.check_limit("per-second")
    await limiter.check_limit("per-second")
    
    with pytest.raises(RateLimitExceeded):
        await limiter.check_limit("per-second")
    
    # Test per-minute (should allow many quickly)
    for i in range(10):
        await limiter.check_limit("per-minute")


@pytest.mark.asyncio
async def test_rate_limit_status_fields():
    """Test all fields in RateLimitStatus."""
    config = RateLimitConfig(
        agent_id="test-agent",
        max_requests=5,
        window=RateLimitWindow.SECOND,
    )
    limiter = RateLimiter(default_config=config)
    limiter.set_agent_limit(config)
    
    # Make request
    status = await limiter.check_limit("test-agent")
    
    # Check all fields
    assert status.agent_id == "test-agent"
    assert isinstance(status.requests_made, int)
    assert isinstance(status.requests_remaining, int)
    assert isinstance(status.window_start, datetime)
    assert isinstance(status.window_end, datetime)
    assert status.retry_after is None  # Not exceeded yet
    
    # Exceed limit
    for i in range(10):
        try:
            await limiter.check_limit("test-agent")
        except RateLimitExceeded as e:
            # Check retry_after is set
            assert e.status.retry_after is not None
            assert e.status.retry_after > 0
            break
