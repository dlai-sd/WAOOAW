import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from ..core.security import standardize_error_handling  # Importing the function

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
        except HTTPException as http_exc:
            logger.error(f"HTTP error occurred: {http_exc.detail}")
            return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            standardized_error = standardize_error_handling(e)
            return JSONResponse(status_code=standardized_error["status_code"], content=standardized_error)

def add_error_handling(app):
    app.add_middleware(ErrorHandlerMiddleware)
