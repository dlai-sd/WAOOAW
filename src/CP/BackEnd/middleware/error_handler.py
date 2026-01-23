import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4
from ..core.security import standardize_error_handling

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid4())
        logger.info(f"Request {request.method} {request.url} Correlation-ID: {correlation_id}")
        try:
            response = await call_next(request)
            return response
        except HTTPException as http_exc:
            logger.error(f"HTTP error occurred: {http_exc.detail} Correlation-ID: {correlation_id}")
            return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})
        except Exception as e:
            logger.error(f"Error occurred: {e} Correlation-ID: {correlation_id}")
            standardized_error = standardize_error_handling(e)
            return JSONResponse(status_code=standardized_error["status_code"], content=standardized_error)

def add_error_handling(app):
    app.add_middleware(ErrorHandlerMiddleware)
