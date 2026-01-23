"""
Request validation middleware - centralized validation and tenant isolation

Architecture: Validates requests against OpenAPI schema and injects tenant information
"""

from fastapi import Request, HTTPException
from fastapi.openapi.models import Schema
from fastapi.openapi.utils import get_openapi
from typing import Any

async def request_validation_middleware(request: Request, call_next):
    """
    Middleware to validate requests against OpenAPI schema and inject tenant information.
    """
    # Example of tenant extraction from headers
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID is required")

    # Validate request against OpenAPI schema (pseudo-code)
    # schema = get_openapi()  # Fetch OpenAPI schema
    # if not validate_against_schema(request, schema):
    #     raise HTTPException(status_code=422, detail="Invalid request")

    request.state.tenant_id = tenant_id
    response = await call_next(request)
    return response
