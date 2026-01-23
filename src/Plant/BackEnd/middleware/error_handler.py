"""
Error handler middleware - centralized exception handling

Architecture: Converts all exceptions to JSON responses with error codes
Reference: PLANT_BLUEPRINT Section 13.10 (Middleware layer)
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from core.exceptions import (
    PlantException,
    ConstitutionalAlignmentError,
    HashChainBrokenError,
    AmendmentSignatureError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Circuit breaker variables
circuit_breaker_failure_count = 0
circuit_breaker_last_failure_time = None

async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware.
    
    Catches all exceptions and returns standardized JSON response:
    {
        "detail": "Error message",
        "error_code": "EXCEPTION_NAME",
        "timestamp": "2026-01-14T12:00:00Z",
        "path": "/api/v1/genesis/skills"
    }
    """
    global circuit_breaker_failure_count, circuit_breaker_last_failure_time

    # Request logging with correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    logger.info(f"Request received: {request.method} {request.url} Correlation ID: {correlation_id}")

    try:
        response = await call_next(request)
        return response
        
    except ConstitutionalAlignmentError as exc:
        logger.error(f"Constitutional alignment error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": str(exc),
                "error_code": "CONSTITUTIONAL_ALIGNMENT_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
    
    except HashChainBrokenError as exc:
        logger.error(f"Hash chain broken: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": str(exc),
                "error_code": "HASH_CHAIN_BROKEN",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
    
    except AmendmentSignatureError as exc:
        logger.error(f"Amendment signature error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": str(exc),
                "error_code": "AMENDMENT_SIGNATURE_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
    
    except EntityNotFoundError as exc:
        logger.warning(f"Entity not found: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(exc),
                "error_code": "ENTITY_NOT_FOUND",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
    
    except DuplicateEntityError as exc:
        logger.warning(f"Duplicate entity: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "error_code": "DUPLICATE_ENTITY",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
    
    except ValidationError as exc:
        logger.warning(f"Validation error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": str(exc),
                "error_code": "VALIDATION_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
    
    except PlantException as exc:
        logger.error(f"Plant exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
                "error_code": exc.__class__.__name__.upper(),
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
    
    except Exception as exc:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        )
