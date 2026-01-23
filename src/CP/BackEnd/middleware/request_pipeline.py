import json
import logging
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from openapi_schema_validator import OAS30Validator
from circuitbreaker import CircuitBreaker

logger = logging.getLogger(__name__)

class RequestPipelineMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, schema):
        super().__init__(app)
        self.schema = schema
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10)

    async def dispatch(self, request: Request, call_next):
        # Validate request against OpenAPI schema
        try:
            body = await request.json()
            OAS30Validator(self.schema).validate(body)
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            raise HTTPException(status_code=400, detail="Invalid request")

        # Automatic tenant isolation injection
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            logger.error("Missing tenant ID")
            raise HTTPException(status_code=403, detail="Tenant ID required")

        # Log request with correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", "unknown")
        logger.info(f"Request received: {request.method} {request.url} - Correlation ID: {correlation_id}")

        # Use circuit breaker for Plant API calls
        with self.circuit_breaker:
            response = await call_next(request)

        return response
