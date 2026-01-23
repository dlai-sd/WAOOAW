from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import APIKey
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

class RequestValidator:
    def __init__(self, schema):
        self.schema = schema

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable]):
        # Validate request against OpenAPI schema
        try:
            body = await request.json()
            self.schema.validate(body)
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            raise HTTPException(status_code=400, detail="Invalid request")

        response = await call_next(request)
        return response

def add_request_validation(app):
    app.middleware("http")(RequestValidator)

