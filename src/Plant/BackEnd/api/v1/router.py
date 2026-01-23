"""
API v1 router - mount all endpoints
"""

from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html

from api.v1 import genesis, agents, audit
from api import trials


api_v1_router = APIRouter(prefix="/api/v1")
api_v2_router = APIRouter(prefix="/api/v2")

# Mount all routers for v1
api_v1_router.include_router(genesis.router)
api_v1_router.include_router(agents.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(trials.router)

# Mount all routers for v2
api_v2_router.include_router(genesis.router)
api_v2_router.include_router(agents.router)
api_v2_router.include_router(audit.router)
api_v2_router.include_router(trials.router)

# Swagger UI route
@api_v1_router.get("/docs", include_in_schema=False)
async def swagger_ui():
    return get_swagger_ui_html(openapi_url=api_v1_router.openapi_url, title="WAOOAW API Docs")
