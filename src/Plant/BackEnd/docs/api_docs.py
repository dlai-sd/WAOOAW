"""
API Documentation Management
"""

from fastapi import APIRouter
from fastapi.openapi.utils import get_openapi

api_docs_router = APIRouter()

@api_docs_router.get("/openapi.json", include_in_schema=False)
async def openapi_spec():
    """
    Generate OpenAPI spec for the API.
    """
    return get_openapi(
        title="WAOOAW Plant Phase API",
        version="0.1.0",
        routes=api_docs_router.routes,
    )
