import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, max_failures: int, reset_timeout: int):
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
            logger.error(f"Circuit breaker triggered: {e}")
            raise

    def reset(self):
        self.failure_count = 0
        self.last_failure_time = None

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

def add_error_handling(app):
    app.add_middleware(ErrorHandlerMiddleware)

