# This file contains the new error handling logic.
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any


def setup_error_handlers(
    app: FastAPI,
    environment: str = "production",
    include_trace: bool = False
):
    """
    Register exception handlers for RFC 7807 error formatting.
    
    Args:
        app: FastAPI application
        environment: "production" or "development"
        include_trace: Include stack traces in responses (auto-enabled in development)
    """
    include_trace_flag = include_trace or (environment.lower() == "development")
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTPException and format as RFC 7807."""
        return _format_http_exception(exc, request, include_trace_flag)
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTPException and format as RFC 7807."""
        return _format_http_exception(exc, request, include_trace_flag)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions and format as RFC 7807."""
        return _format_unexpected_error(exc, request, include_trace_flag)


def _format_http_exception(exc: HTTPException, request: Request, include_trace: bool = False) -> JSONResponse:
    """
    Format HTTPException as RFC 7807 Problem Details.
    """
    status_code = exc.status_code
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    
    # Determine error type from status code or detail
    error_type = _infer_error_type(status_code, detail)
    
    # Build RFC 7807 response
    problem_details = {
        "type": f"https://waooaw.com/errors/{error_type}",
        "title": _get_title_for_status(status_code),
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path)
    }
    
    # Add correlation_id if present
    correlation_id = getattr(request.state, "correlation_id", None)
    if correlation_id:
        problem_details["correlation_id"] = correlation_id
    
    # Add extra fields from exception headers
    if hasattr(exc, "headers") and exc.headers:
        for key, value in exc.headers.items():
            if key.startswith("X-"):
                problem_details[key.lower().replace("x-", "")] = value
    
    # Add stack trace in development
    if include_trace:
        problem_details["trace"] = traceback.format_exc()
    
    logger.warning(
        f"HTTPException: status={status_code}, type={error_type}, "
        f"detail={detail}, path={request.url.path}"
    )
    
    # Build headers
    headers = {}
    if hasattr(exc, "headers") and exc.headers:
        headers.update(exc.headers)
    headers["Content-Type"] = "application/problem+json"
    
    return JSONResponse(
        status_code=status_code,
        content=problem_details,
        headers=headers
    )


def _format_unexpected_error(exc: Exception, request: Request, include_trace: bool = False) -> JSONResponse:
    """
    Format unexpected exception as RFC 7807 Problem Details.
    """
    error_type = "internal-server-error"
    status_code = 500
    
    # Get correlation_id for tracing
    correlation_id = getattr(request.state, "correlation_id", None)
    
    # Build RFC 7807 response
    problem_details = {
        "type": f"https://waooaw.com/errors/{error_type}",
        "title": "Internal Server Error",
        "status": status_code,
        "detail": str(exc) if include_trace else "An unexpected error occurred",
        "instance": str(request.url.path)
    }
    
    if correlation_id:
        problem_details["correlation_id"] = correlation_id
    
    # Add stack trace in development
    if include_trace:
        problem_details["trace"] = traceback.format_exc()
        problem_details["exception_type"] = type(exc).__name__
    
    logger.error(
        f"Unexpected error: type={type(exc).__name__}, "
        f"detail={str(exc)}, path={request.url.path}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status_code,
        content=problem_details,
        headers={"Content-Type": "application/problem+json"}
    )


def _infer_error_type(status_code: int, detail: str) -> str:
    """
    Infer error type from status code and detail message.
    """
    detail_lower = detail.lower()
    
    # Check detail for keywords
    if "unauthorized" in detail_lower or "auth" in detail_lower:
        return "unauthorized"
    if "expired" in detail_lower and "trial" in detail_lower:
        return "trial-expired"
    if "limit" in detail_lower and "trial" in detail_lower:
        return "trial-limit-exceeded"
    if "approval" in detail_lower or "governor" in detail_lower:
        return "approval-required"
    if "budget" in detail_lower:
        return "budget-exceeded"
    if "permission" in detail_lower or "forbidden" in detail_lower:
        return "permission-denied"
    if "not found" in detail_lower:
        return "not-found"
    if "timeout" in detail_lower:
        return "gateway-timeout"
    if "unavailable" in detail_lower:
        return "service-unavailable"
    
    # Fallback to status code mapping
    status_to_type = {
        401: "unauthorized",
        403: "permission-denied",
        404: "not-found",
        402: "budget-exceeded",
        429: "trial-limit-exceeded",
        503: "service-unavailable",
        504: "gateway-timeout",
        500: "internal-server-error"
    }
    
    return status_to_type.get(status_code, "internal-server-error")


def _get_title_for_status(status_code: int) -> str:
    """
    Get human-readable title for HTTP status code.
    """
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }
    
    return titles.get(status_code, "Error")


def create_problem_details(error_type: str, status: int, detail: str, instance: str, **extra_fields) -> Dict[str, Any]:
    """
    Helper function to create RFC 7807 Problem Details dict.
    
    Usage:
    raise HTTPException(
        status_code=402,
        detail=json.dumps(create_problem_details(
            error_type="budget-exceeded",
            status=402,
            detail="Platform budget exceeded",
            instance="/api/v1/agents",
            platform_budget={"limit": 100, "spent": 105}
        ))
    )
    """
    problem = {
        "type": f"https://waooaw.com/errors/{error_type}",
        "title": _get_title_for_error_type(error_type),
        "status": status,
        "detail": detail,
        "instance": instance
    }
    
    # Add extra fields
    problem.update(extra_fields)
    
    return problem


def _get_title_for_error_type(error_type: str) -> str:
    """Get title for error type."""
    titles = {
        "unauthorized": "Unauthorized",
        "invalid-token-format": "Invalid Token Format",
        "token-expired": "Token Expired",
        "invalid-token": "Invalid Token",
        "permission-denied": "Permission Denied",
        "trial-expired": "Trial Expired",
        "trial-limit-exceeded": "Trial Limit Exceeded",
        "approval-required": "Approval Required",
        "budget-exceeded": "Budget Exceeded",
        "not-found": "Not Found",
        "validation-error": "Validation Error",
        "conflict": "Conflict",
        "service-unavailable": "Service Unavailable",
        "gateway-timeout": "Gateway Timeout",
        "internal-server-error": "Internal Server Error"
    }
    
    return titles.get(error_type, "Error")


# Backwards compatibility: Keep ErrorHandlingMiddleware class but mark deprecated
# Removed deprecated ErrorHandlingMiddleware class
"""
Error Handling - GW-105

RFC 7807 Problem Details wrapper for all gateway errors.
Converts exceptions to standardized error responses.

NOTE: This module provides EXCEPTION HANDLERS, not middleware.
FastAPI's exception handlers run before middleware, so we must
register these as exception handlers, not middleware.

Usage:
    from src.gateway.middleware.error_handler import setup_error_handlers
    setup_error_handlers(app, environment="production")
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, FastAPI
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# Error type to HTTP status code mapping
ERROR_TYPE_STATUS = {
    "unauthorized": 401,
    "invalid-token-format": 401,
    "token-expired": 401,
    "invalid-token": 401,
    "permission-denied": 403,
    "trial-expired": 403,
    "trial-limit-exceeded": 429,
    "approval-required": 307,
    "budget-exceeded": 402,
    "not-found": 404,
    "validation-error": 400,
    "conflict": 409,
    "service-unavailable": 503,
    "gateway-timeout": 504,
    "internal-server-error": 500
}


def setup_error_handlers(app: FastAPI, environment: str = "production", include_trace: bool = False):
    """
    Register exception handlers for RFC 7807 error formatting.
    
    Args:
        app: FastAPI application
        environment: "production" or "development"
        include_trace: Include stack traces in responses (auto-enabled in development)
    """
    include_trace_flag = include_trace or (environment.lower() == "development")
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTPException and format as RFC 7807."""
        return _format_http_exception(exc, request, include_trace_flag)
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTPException and format as RFC 7807."""
        return _format_http_exception(exc, request, include_trace_flag)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions and format as RFC 7807."""
        return _format_unexpected_error(exc, request, include_trace_flag)


def _format_http_exception(
    exc: HTTPException,
    request: Request,
    include_trace: bool = False
) -> JSONResponse:
    """
    Format HTTPException as RFC 7807 Problem Details.
    """
    status_code = exc.status_code
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    
    # Determine error type from status code or detail
    error_type = _infer_error_type(status_code, detail)
    
    # Build RFC 7807 response
    problem_details = {
        "type": f"https://waooaw.com/errors/{error_type}",
        "title": _get_title_for_status(status_code),
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path)
    }
    
    # Add correlation_id if present
    correlation_id = getattr(request.state, "correlation_id", None)
    if correlation_id:
        problem_details["correlation_id"] = correlation_id
    
    # Add extra fields from exception headers
    if hasattr(exc, "headers") and exc.headers:
        for key, value in exc.headers.items():
            if key.startswith("X-"):
                problem_details[key.lower().replace("x-", "")] = value
    
    # Add stack trace in development
    if include_trace:
        problem_details["trace"] = traceback.format_exc()
    
    logger.warning(
        f"HTTPException: status={status_code}, type={error_type}, "
        f"detail={detail}, path={request.url.path}"
    )
    
    # Build headers
    headers = {}
    if hasattr(exc, "headers") and exc.headers:
        headers.update(exc.headers)
    headers["Content-Type"] = "application/problem+json"
    
    return JSONResponse(
        status_code=status_code,
        content=problem_details,
        headers=headers
    )


def _format_unexpected_error(
    exc: Exception,
    request: Request,
    include_trace: bool = False
) -> JSONResponse:
    """
    Format unexpected exception as RFC 7807 Problem Details.
    """
    error_type = "internal-server-error"
    status_code = 500
    
    # Get correlation_id for tracing
    correlation_id = getattr(request.state, "correlation_id", None)
    
    # Build RFC 7807 response
    problem_details = {
        "type": f"https://waooaw.com/errors/{error_type}",
        "title": "Internal Server Error",
        "status": status_code,
        "detail": str(exc) if include_trace else "An unexpected error occurred",
        "instance": str(request.url.path)
    }
    
    if correlation_id:
        problem_details["correlation_id"] = correlation_id
    
    # Add stack trace in development
    if include_trace:
        problem_details["trace"] = traceback.format_exc()
        problem_details["exception_type"] = type(exc).__name__
    
    logger.error(
        f"Unexpected error: type={type(exc).__name__}, "
        f"detail={str(exc)}, path={request.url.path}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status_code,
        content=problem_details,
        headers={"Content-Type": "application/problem+json"}
    )


def _infer_error_type(status_code: int, detail: str) -> str:
    """
    Infer error type from status code and detail message.
    """
    detail_lower = detail.lower()
    
    # Check detail for keywords
    if "unauthorized" in detail_lower or "auth" in detail_lower:
        return "unauthorized"
    if "expired" in detail_lower and "trial" in detail_lower:
        return "trial-expired"
    if "limit" in detail_lower and "trial" in detail_lower:
        return "trial-limit-exceeded"
    if "approval" in detail_lower or "governor" in detail_lower:
        return "approval-required"
    if "budget" in detail_lower:
        return "budget-exceeded"
    if "permission" in detail_lower or "forbidden" in detail_lower:
        return "permission-denied"
    if "not found" in detail_lower:
        return "not-found"
    if "timeout" in detail_lower:
        return "gateway-timeout"
    if "unavailable" in detail_lower:
        return "service-unavailable"
    
    # Fallback to status code mapping
    status_to_type = {
        401: "unauthorized",
        403: "permission-denied",
        404: "not-found",
        402: "budget-exceeded",
        429: "trial-limit-exceeded",
        503: "service-unavailable",
        504: "gateway-timeout",
        500: "internal-server-error"
    }
    
    return status_to_type.get(status_code, "internal-server-error")


def _get_title_for_status(status_code: int) -> str:
    """
    Get human-readable title for HTTP status code.
    """
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }
    
    return titles.get(status_code, "Error")


def create_problem_details(
    error_type: str,
    status: int,
    detail: str,
    instance: str,
    **extra_fields
) -> Dict[str, Any]:
    """
    Helper function to create RFC 7807 Problem Details dict.
    
    Usage:
    raise HTTPException(
        status_code=402,
        detail=json.dumps(create_problem_details(
            error_type="budget-exceeded",
            status=402,
            detail="Platform budget exceeded",
            instance="/api/v1/agents",
            platform_budget={"limit": 100, "spent": 105}
        ))
    )
    """
    problem = {
        "type": f"https://waooaw.com/errors/{error_type}",
        "title": _get_title_for_error_type(error_type),
        "status": status,
        "detail": detail,
        "instance": instance
    }
    
    # Add extra fields
    problem.update(extra_fields)
    
    return problem


def _get_title_for_error_type(error_type: str) -> str:
    """Get title for error type."""
    titles = {
        "unauthorized": "Unauthorized",
        "invalid-token-format": "Invalid Token Format",
        "token-expired": "Token Expired",
        "invalid-token": "Invalid Token",
        "permission-denied": "Permission Denied",
        "trial-expired": "Trial Expired",
        "trial-limit-exceeded": "Trial Limit Exceeded",
        "approval-required": "Approval Required",
        "budget-exceeded": "Budget Exceeded",
        "not-found": "Not Found",
        "validation-error": "Validation Error",
        "conflict": "Conflict",
        "service-unavailable": "Service Unavailable",
        "gateway-timeout": "Gateway Timeout",
        "internal-server-error": "Internal Server Error"
    }
    
    return titles.get(error_type, "Error")


# Backwards compatibility: Keep ErrorHandlingMiddleware class but mark deprecated
class ErrorHandlingMiddleware:
    """
    DEPRECATED: Use setup_error_handlers() instead.
    
    This middleware class doesn't work correctly because FastAPI's
    default exception handler runs before middleware. Use exception
    handlers instead.
    """
    def __init__(self, app, **kwargs):
        logger.warning(
            "ErrorHandlingMiddleware is deprecated. Use setup_error_handlers() instead. "
            "Exception handlers run before middleware, so middleware-based error handling doesn't work."
        )
