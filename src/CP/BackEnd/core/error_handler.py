from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    tenant_id = request.state.tenant_id if hasattr(request.state, 'tenant_id') else "unknown"
    user_id = request.state.user_id if hasattr(request.state, 'user_id') else "unknown"
    endpoint = request.url.path
    duration = request.state.duration if hasattr(request.state, 'duration') else 0

    logger.error(f"Error occurred: tenant_id={tenant_id}, user_id={user_id}, endpoint={endpoint}, duration={duration}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "https://httpstatuses.com/" + str(exc.status_code),
            "title": "Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": endpoint
        },
    )

async def general_exception_handler(request: Request, exc: Exception):
    tenant_id = request.state.tenant_id if hasattr(request.state, 'tenant_id') else "unknown"
    user_id = request.state.user_id if hasattr(request.state, 'user_id') else "unknown"
    endpoint = request.url.path
    duration = request.state.duration if hasattr(request.state, 'duration') else 0

    logger.error(f"Internal server error: tenant_id={tenant_id}, user_id={user_id}, endpoint={endpoint}, duration={duration}")
    
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://httpstatuses.com/500",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
            "instance": endpoint
        },
    )
