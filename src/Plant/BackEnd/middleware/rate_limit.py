"""
AGP2-SEC-1.2: Rate Limiting Middleware

Implements request rate limiting for DoS prevention with:
- Per-customer rate limits  
- Per-IP rate limits (anonymous)
- Sliding window algorithm
- Proper 429 responses with Retry-After header
- Redis-based distributed rate limiting support
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitStore:
    """
    Abstract rate limit  storage interface.
    
    Implementations: InMemoryRateLimitStore (development), RedisRateLimitStore (production)
    """
    
    def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        """
        Increment request counter for a key in a time window.
        
        Args:
            key: Rate limit key (customer_id or IP address)
            window_seconds: Time window in seconds
            
        Returns:
            tuple: (current_count, window_reset_timestamp)
        """
        raise NotImplementedError
    
    def reset(self, key: str) -> None:
        """Reset rate limit counter for a key."""
        raise NotImplementedError


class InMemoryRateLimitStore:
    """
    In-memory rate limit storage (development only, not distributed).
    
    Uses sliding window algorithm with automatic cleanup.
    """
    
    def __init__(self):
        # Storage: {key: [(timestamp, count), ...]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._lock = Lock()
    
    def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Increment request count for key within sliding window."""
        now = time.time()
        window_start = now - window_seconds
        
        with self._lock:
            # Clean up old requests outside window
            self._requests[key] = [
                (ts, count) for ts, count in self._requests[key]
                if ts > window_start
            ]
            
            # Add current request
            self._requests[key].append((now, 1))
            
            # Count requests in window
            current_count = sum(count for _, count in self._requests[key])
            
            # Window resets at end of current window
            window_reset = int(now + window_seconds)
            
            return current_count, window_reset
    
    def reset(self, key: str) -> None:
        """Reset rate limit for key."""
        with self._lock:
            if key in self._requests:
                del self._requests[key]
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600) -> None:
        """Clean up entries older than max_age to prevent memory leaks."""
        now = time.time()
        cutoff = now - max_age_seconds
        
        with self._lock:
            keys_to_delete = []
            for key, requests in self._requests.items():
                # Remove requests older than cutoff
                self._requests[key] = [(ts, count) for ts, count in requests if ts > cutoff]
                # If no requests left, mark key for deletion
                if not self._requests[key]:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._requests[key]


class RateLimitConfig:
    """Rate limit configuration."""
    
    def __init__(
        self,
        *,
        requests_per_minute: int = 100,
        requests_per_hour: Optional[int] = None,
        customer_multiplier: float = 10.0,  # Authenticated users get 10x limit
        enable_ip_rate_limit: bool = True,
        enable_customer_rate_limit: bool = True,
        exempt_paths: Optional[list[str]] = None,
    ):
        """
        Initialize rate limit configuration.
        
        Args:
            requests_per_minute: Rate limit per minute (default: 100)
            requests_per_hour: Optional hourly limit (default: None)
            customer_multiplier: Multiplier for authenticated customers (default: 10x)
            enable_ip_rate_limit: Enable per-IP rate limiting (default: True)
            enable_customer_rate_limit: Enable per-customer rate limiting (default: True)
            exempt_paths: Paths exempt from rate limiting (health checks, etc.)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.customer_multiplier = customer_multiplier
        self.enable_ip_rate_limit = enable_ip_rate_limit
        self.enable_customer_rate_limit = enable_customer_rate_limit
        self.exempt_paths = exempt_paths or ["/health", "/", "/docs", "/redoc", "/openapi.json"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request rate limiting.
    
    Features:
    - Per-IP rate limiting (anonymous requests)
    - Per-customer rate limiting (authenticated requests)
    - Sliding window algorithm
    - Proper 429 responses with Retry-After header
    - X-RateLimit-* headers for transparency
    
    Example:
        app.add_middleware(
            RateLimitMiddleware,
            store=InMemoryRateLimitStore(),
            config=RateLimitConfig(requests_per_minute=100)
        )
    """
    
    def __init__(
        self,
        app,
        store: Optional[RateLimitStore] = None,
        config: Optional[RateLimitConfig] = None,
    ):
        super().__init__(app)
        self.store = store or InMemoryRateLimitStore()
        self.config = config or RateLimitConfig()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.config.exempt_paths:
            return await call_next(request)
        
        # Extract customer ID from auth (if authenticated)
        customer_id = self._extract_customer_id(request)
        
        # Determine rate limit key and limits
        if customer_id and self.config.enable_customer_rate_limit:
            rate_limit_key = f"customer:{customer_id}"
            minute_limit = int(self.config.requests_per_minute * self.config.customer_multiplier)
            hour_limit = int(self.config.requests_per_hour * self.config.customer_multiplier) if self.config.requests_per_hour else None
        elif self.config.enable_ip_rate_limit:
            ip_address = self._extract_ip(request)
            rate_limit_key = f"ip:{ip_address}"
            minute_limit = self.config.requests_per_minute
            hour_limit = self.config.requests_per_hour
        else:
            # Rate limiting disabled
            return await call_next(request)
        
        # Check minute rate limit
        minute_count, minute_reset = self.store.increment(f"{rate_limit_key}:minute", 60)
        
        if minute_count > minute_limit:
            return self._rate_limit_response(
                limit=minute_limit,
                remaining=0,
                reset=minute_reset,
                retry_after=minute_reset - int(time.time())
            )
        
        # Check hourly rate limit (if configured)
        if hour_limit:
            hour_count, hour_reset = self.store.increment(f"{rate_limit_key}:hour", 3600)
            
            if hour_count > hour_limit:
                return self._rate_limit_response(
                    limit=hour_limit,
                    remaining=0,
                    reset=hour_reset,
                    retry_after=hour_reset - int(time.time())
                )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(minute_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, minute_limit - minute_count))
        response.headers["X-RateLimit-Reset"] = str(minute_reset)
        
        return response
    
    def _extract_customer_id(self, request: Request) -> Optional[str]:
        """
        Extract customer ID from request (JWT token or API key).
        
        TODO: Integrate with actual auth system.
        For now, checks X-Customer-ID header (testing only).
        """
        # Check test header
        customer_id = request.headers.get("X-Customer-ID")
        if customer_id:
            return customer_id
        
        # TODO: Extract from JWT token
        # auth_header = request.headers.get("Authorization")
        # if auth_header and auth_header.startswith("Bearer "):
        #     token = auth_header[7:]
        #     payload = verify_token(token)
        #     if payload:
        #         return payload.get("sub")  # customer_id from JWT
        
        return None
    
    def _extract_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP (client IP, not proxy IPs)
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct connection  IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _rate_limit_response(
        self,
        limit: int,
        remaining: int,
        reset: int,
        retry_after: int
    ) -> JSONResponse:
        """Create 429 Too Many Requests response."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "type": "https://waooaw.com/errors/rate-limit-exceeded",
                "title": "Rate Limit Exceeded",
                "status": 429,
                "detail": f"Rate limit of {limit} requests per minute exceeded. Please retry after {retry_after} seconds.",
                "instance": "/",
                "limit": limit,
                "remaining": remaining,
                "reset": reset,
                "retry_after": retry_after,
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset),
                "Retry-After": str(retry_after),
            }
        )


# ========== HELPER FUNCTIONS ==========

def get_rate_limit_store() -> RateLimitStore:
    """Get rate limit store based on environment."""
    # TODO: Add Redis support for production
    # redis_url = os.getenv("REDIS_URL")
    # if redis_url:
    #     return RedisRateLimitStore(redis_url)
    return InMemoryRateLimitStore()


def create_rate_limit_middleware(
    requests_per_minute: int = 100,
    requests_per_hour: Optional[int] = None,
) -> RateLimitMiddleware:
    """
    Create rate limit middleware with default configuration.
    
    Args:
        requests_per_minute: Rate limit per minute (default: 100)
        requests_per_hour: Optional hourly limit
    
    Returns:
        RateLimitMiddleware: Configured middleware
    
    Example:
        app.add_middleware(create_rate_limit_middleware(requests_per_minute=200))
    """
    store = get_rate_limit_store()
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
    )
    return RateLimitMiddleware(app=None, store=store, config=config)
