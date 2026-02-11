"""
API v1 router - mount all endpoints
"""

from fastapi import APIRouter

from api.v1 import genesis, agents, audit, agent_mold, reference_agents, db_updates, usage_events, marketing_drafts, customers, auth, payments_simple, hired_agents_simple, invoices_simple, receipts_simple, trial_status_simple, notifications, agent_types_simple, agent_types_db, deliverables_simple
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
api_v1_router.include_router(customers.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(db_updates.router)
api_v1_router.include_router(payments_simple.router)
api_v1_router.include_router(hired_agents_simple.router)
api_v1_router.include_router(deliverables_simple.hired_agents_router)
api_v1_router.include_router(agent_types_simple.router)
api_v1_router.include_router(agent_types_db.router)  # DB-backed agent types (AGP1-DB-1.2)
api_v1_router.include_router(deliverables_simple.deliverables_router)
api_v1_router.include_router(deliverables_simple.scheduler_router)
api_v1_router.include_router(invoices_simple.router)
api_v1_router.include_router(receipts_simple.router)
api_v1_router.include_router(trial_status_simple.router)
api_v1_router.include_router(notifications.router)

