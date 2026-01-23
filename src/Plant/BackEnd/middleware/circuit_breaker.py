"""
Circuit breaker middleware - prevents excessive calls to the Plant API

Architecture: Implements a circuit breaker pattern to handle failures gracefully
"""

import time
from fastapi import Request, HTTPException

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time: int = 10):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        if self.is_open():
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")

        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.last_failure_time = time.time()
            raise

    def is_open(self):
        if self.failure_count >= self.failure_threshold:
            if time.time() - self.last_failure_time < self.recovery_time:
                return True
        return False

async def circuit_breaker_middleware(request: Request, call_next):
    """
    Middleware to implement circuit breaker for Plant API calls.
    """
    circuit_breaker = CircuitBreaker()

    response = await circuit_breaker.call(call_next, request)
    return response
