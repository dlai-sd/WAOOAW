"""
Error handler middleware - centralized exception handling

Architecture: Converts all exceptions to JSON responses with error codes
Reference: PLANT_BLUEPRINT Section 13.10 (Middleware layer)
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import uuid

from core.exceptions import (
    PlantException,
    ConstitutionalAlignmentError,
    HashChainBrokenError,
    AmendmentSignatureError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)
from core.logging import get_logger
from core.metrics import record_request

logger = get_logger(__name__)

async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware.
    
    Catches all exceptions and returns standardized JSON response.
    """
    correlation_id = str(uuid.uuid4())
    request_start_time = datetime.utcnow()

    try:
        response = await call_next(request)
        return response
        
    except Exception as exc:
        duration = (datetime.utcnow() - request_start_time).total_seconds()
        record_request(duration, False)
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra={"correlation_id": correlation_id})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
                "correlation_id": correlation_id,
            }
        )
