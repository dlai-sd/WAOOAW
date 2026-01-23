"""
API v1 router - mount all endpoints
"""

from fastapi import APIRouter
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from api.v1 import genesis, agents, audit
from api import trials


api_v1_router = APIRouter(prefix="/api/v1")

# Mount all routers
api_v1_router.include_router(genesis.router)
api_v1_router.include_router(agents.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(trials.router)

# Prometheus metrics endpoint
@api_v1_router.get("/metrics")
async def metrics():
    return Instrumentator().expose()
