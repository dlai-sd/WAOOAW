import time
from fastapi import HTTPException

class CircuitBreaker:
    def __init__(self, max_failures: int = 3, reset_timeout: int = 10):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        if self.failure_count >= self.max_failures:
            if time.time() - self.last_failure_time < self.reset_timeout:
                raise HTTPException(status_code=503, detail="Service unavailable")
            else:
                self.reset()

        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            raise

    def reset(self):
        self.failure_count = 0
        self.last_failure_time = None
