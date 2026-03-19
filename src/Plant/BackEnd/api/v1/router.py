"""
API v1 router - mount all endpoints
"""

from core.routing import waooaw_router  # P-3

from api.v1 import genesis, agents, agent_catalog, agent_authoring, audit, agent_mold, reference_agents, db_updates, usage_events, marketing_drafts, customers, customers_fcm, auth, payments_simple, hired_agents_simple, hired_agent_studio, digital_marketing_activation, invoices_simple, receipts_simple, trial_status_simple, notifications, agent_types_simple, agent_types_db, deliverables_simple, otp, feature_flags, agent_skills, platform_connections, performance_stats, campaigns, skill_configs, flow_runs, approvals
from api.v1.construct_diagnostics import router as construct_diagnostics_router, ops_router as construct_ops_router
from api import trials

api_v1_router = waooaw_router(prefix="/api/v1")

# Mount all routers
api_v1_router.include_router(genesis.router)
api_v1_router.include_router(agents.router)
api_v1_router.include_router(agent_catalog.router)
api_v1_router.include_router(agent_authoring.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(agent_mold.router)
api_v1_router.include_router(reference_agents.router)
api_v1_router.include_router(usage_events.router)
api_v1_router.include_router(marketing_drafts.router)
api_v1_router.include_router(trials.router)
api_v1_router.include_router(customers.router)
api_v1_router.include_router(customers_fcm.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(db_updates.router)
api_v1_router.include_router(payments_simple.router)
api_v1_router.include_router(hired_agents_simple.router)
api_v1_router.include_router(hired_agent_studio.router)
api_v1_router.include_router(digital_marketing_activation.router)
api_v1_router.include_router(digital_marketing_activation.theme_router)
api_v1_router.include_router(deliverables_simple.hired_agents_router)
api_v1_router.include_router(agent_types_simple.router)
api_v1_router.include_router(agent_types_db.router)  # DB-backed agent types (AGP1-DB-1.2)
api_v1_router.include_router(deliverables_simple.deliverables_router)
api_v1_router.include_router(deliverables_simple.scheduler_router)
api_v1_router.include_router(invoices_simple.router)
api_v1_router.include_router(receipts_simple.router)
api_v1_router.include_router(trial_status_simple.router)
api_v1_router.include_router(notifications.router)
api_v1_router.include_router(otp.router)
api_v1_router.include_router(feature_flags.router)  # E2-S1 (Iteration 7)
api_v1_router.include_router(agent_skills.router)               # PLANT-SKILLS-1 E1-S2
api_v1_router.include_router(agent_skills.skills_router)        # PLANT-SKILLS-1 E1-S2
api_v1_router.include_router(agent_skills.hired_agent_skills_router)  # PLANT-RUNTIME-1 It1 E1-S1
api_v1_router.include_router(platform_connections.router)       # PLANT-SKILLS-1 E4-S1
api_v1_router.include_router(platform_connections.customer_router)
api_v1_router.include_router(performance_stats.router)          # PLANT-SKILLS-1 E4-S2
api_v1_router.include_router(campaigns.router)                  # PLANT-CONTENT-1 Iteration 2
api_v1_router.include_router(construct_diagnostics_router)      # PLANT-MOULD-1 E4: per-construct health
api_v1_router.include_router(construct_ops_router)              # PLANT-MOULD-1 E4: ops DLQ console
api_v1_router.include_router(skill_configs.router)              # EXEC-ENGINE-001 E1-S3: skill config PATCH
api_v1_router.include_router(skill_configs.hired_agent_router)  # PLANT-RUNTIME-1 It1 E1-S2
api_v1_router.include_router(flow_runs.router)                  # EXEC-ENGINE-001 E6-S1: flow-runs endpoints
api_v1_router.include_router(flow_runs.skill_runs_router)       # PLANT-RUNTIME-1 It2 E3-S2
api_v1_router.include_router(flow_runs.component_runs_router)   # PLANT-RUNTIME-1 It2 E3-S1
api_v1_router.include_router(approvals.router)                  # EXEC-ENGINE-001 E8-S2: approve/reject gate

