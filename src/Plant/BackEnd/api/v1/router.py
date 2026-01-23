"""
API v1 router - mount all endpoints
"""

from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.models import OpenAPI
from api.v1 import genesis, agents, audit
from api import trials

api_v1_router = APIRouter(prefix="/api/v1")

# Mount all routers
api_v1_router.include_router(genesis.router)
api_v1_router.include_router(agents.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(trials.router)

@api_v1_router.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url=api_v1_router.openapi_url, title="WAOOAW API Docs")
