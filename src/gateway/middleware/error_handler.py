# This file is deprecated. Use error_handler_new.py instead.

from .error_handler_new import setup_error_handlers
from typing import Dict, Any


def _infer_error_type(status_code: int, detail: str) -> str:
    """Infer error type from status code and detail message."""
    detail_lower = detail.lower()
    
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
    
    status_to_type = {
        401: "unauthorized", 403: "permission-denied", 404: "not-found",
        402: "budget-exceeded", 429: "trial-limit-exceeded",
        503: "service-unavailable", 504: "gateway-timeout", 500: "internal-server-error"
    }
    
    return status_to_type.get(status_code, "internal-server-error")


def _get_title_for_status(status_code: int) -> str:
    """Get human-readable title for HTTP status code."""
    titles = {
        400: "Bad Request", 401: "Unauthorized", 402: "Payment Required",
        403: "Forbidden", 404: "Not Found", 409: "Conflict",
        429: "Too Many Requests", 500: "Internal Server Error",
        502: "Bad Gateway", 503: "Service Unavailable", 504: "Gateway Timeout"
    }
    return titles.get(status_code, "Error")


def create_problem_details(error_type: str, status: int, detail: str, instance: str, **extra_fields) -> Dict[str, Any]:
    """Helper function to create RFC 7807 Problem Details dict."""
    problem = {
        "type": f"https://waooaw.com/errors/{error_type}",
        "title": _get_title_for_error_type(error_type),
        "status": status,
        "detail": detail,
        "instance": instance
    }
    problem.update(extra_fields)
    return problem


def _get_title_for_error_type(error_type: str) -> str:
    """Get title for error type."""
    titles = {
        "unauthorized": "Unauthorized", "invalid-token-format": "Invalid Token Format",
        "token-expired": "Token Expired", "invalid-token": "Invalid Token",
        "permission-denied": "Permission Denied", "trial-expired": "Trial Expired",
        "trial-limit-exceeded": "Trial Limit Exceeded", "approval-required": "Approval Required",
        "budget-exceeded": "Budget Exceeded", "not-found": "Not Found",
        "validation-error": "Validation Error", "conflict": "Conflict",
        "service-unavailable": "Service Unavailable", "gateway-timeout": "Gateway Timeout",
        "internal-server-error": "Internal Server Error"
    }
    return titles.get(error_type, "Error")


# Backwards compatibility
# Removed deprecated ErrorHandlingMiddleware class
