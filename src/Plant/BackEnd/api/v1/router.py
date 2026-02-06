"""
API v1 router - mount all endpoints
"""

from fastapi import APIRouter

from api.v1 import genesis, agents, audit, agent_mold, reference_agents, db_updates, usage_events, marketing_drafts
from api import trials


api_v1_router = APIRouter(prefix="/api/v1")

# Mount all routers
api_v1_router.include_router(genesis.router)
api_v1_router.include_router(agents.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(agent_mold.router)
api_v1_router.include_router(reference_agents.router)
api_v1_router.include_router(usage_events.router)
api_v1_router.include_router(marketing_drafts.router)
api_v1_router.include_router(trials.router)
api_v1_router.include_router(db_updates.router)

