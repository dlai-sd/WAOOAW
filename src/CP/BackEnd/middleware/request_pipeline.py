from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, ValidationError
import jsonschema
from jsonschema import validate
import json  # Importing json
from .config import settings  # Importing settings

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter("request_count", "Total request count", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("request_latency_seconds", "Request latency", ["method", "endpoint"])

class RequestPipelineMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.circuit_breaker = CircuitBreaker()

    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        logger.info(f"Request {correlation_id}: {request.method} {request.url}")

        # Validate request against OpenAPI schema
        try:
            request_body = await request.json()
            self.validate_request(request_body)
        except (ValidationError, jsonschema.exceptions.ValidationError) as e:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail="Invalid request")

        start_time = time.time()
        response: Response = await call_next(request)
        duration = time.time() - start_time

        # Update Prometheus metrics
        REQUEST_COUNT.labels(method=request.method, endpoint=str(request.url)).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=str(request.url)).observe(duration)

        logger.info(f"Response {correlation_id}: {response.status_code} in {duration:.3f}s")
        response.headers["X-Correlation-ID"] = correlation_id

        return response

    def validate_request(self, request_body: dict):
        # Load OpenAPI schema and validate
        schema = self.load_openapi_schema()
        validate(instance=request_body, schema=schema)

    def load_openapi_schema(self):
        # Load the OpenAPI schema from the specified path
        with open(settings.OPENAPI_SCHEMA_PATH) as schema_file:
            return json.load(schema_file)

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_time=10):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        if self.is_open():
            raise HTTPException(status_code=503, detail="Service Unavailable")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                logger.error("Circuit breaker opened due to failures")
                raise HTTPException(status_code=503, detail="Service Unavailable")
            raise e

    def is_open(self):
        if self.failure_count >= self.failure_threshold:
            if time.time() - self.last_failure_time < self.recovery_time:
                return True
            self.reset()
        return False

    def reset(self):
        self.failure_count = 0
        self.last_failure_time = None
