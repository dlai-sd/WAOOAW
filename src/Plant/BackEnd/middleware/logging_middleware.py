"""
Logging middleware - structured logging for all requests/responses

Architecture: JSON logs with request_id, method, path, status, latency
Reference: PLANT_BLUEPRINT Section 13.10 (Middleware layer)
"""

from fastapi import Request
import time
import logging
import uuid


logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    """
    Log all requests/responses with structured data.
    
    Logs:
    - Request: method, path, query_params, headers
    - Response: status_code, latency_ms
    - Correlation ID for tracing
    """
    # Generate correlation ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timer
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request received",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    
    # Log response
    logger.info(
        "Response sent",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
        }
    )
    
    # Add correlation ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response
