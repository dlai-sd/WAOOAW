"""
Correlation ID middleware - adds X-Request-ID to all requests

Architecture: UUID-based request tracing across services
Reference: PLANT_BLUEPRINT Section 13.10 (Middleware layer)
"""

from fastapi import Request
import uuid


async def correlation_id_middleware(request: Request, call_next):
    """
    Add correlation ID to request state and response headers.
    
    - Checks for existing X-Request-ID header (from upstream)
    - Generates new UUID if not present
    - Adds to request.state for access in handlers
    - Adds to response headers for client tracing
    """
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Request-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    
    # Store in request state
    request.state.correlation_id = correlation_id
    
    # Process request
    response = await call_next(request)
    
    # Add to response headers
    response.headers["X-Request-ID"] = correlation_id
    
    return response
