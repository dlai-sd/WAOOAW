# Plant Docs — Single Source of Truth (Living)

This folder is intentionally kept **small**: the source of truth is implemented code, and this README is the only “context index” we keep updating as features land.

Terminology: **PP = Platform Portal**, **CP = Customer Portal**.

## Keep-docs (do not delete)

These three documents define the product intent and must remain available:

- [OperationsAndMaintenanceEpics.md](OperationsAndMaintenanceEpics.md) — Phase 3 ops epics (observability/DR/scaling/onboarding automation)
- [Digital Marketing WaooaW Agent.md](Digital%20Marketing%20WaooaW%20Agent.md) — marketing agent scope, safety rules, and workflow
- [Share Trading WaooaW Agent.md](Share%20Trading%20WaooaW%20Agent.md) — trading agent scope, safety rules, and workflow

## Living implementation plans

- [Skills_Implementation.md](Skills_Implementation.md) — skills catalog → certification → composition → customer config → enforcement → outcomes (living)

Everything else in this folder is considered **transient** and should be deleted once the corresponding functionality is implemented and referenced here.

## Non‑negotiable invariants (do not break)

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Browsers bypass Plant/Gateway | Side effects could occur without policy enforcement | **Single door**: CP FrontEnd calls CP BackEnd `/api/*` only; CP BackEnd proxies as needed |
| Secrets leak to browser or Plant APIs | Credential compromise and compliance risk | Store secrets **encrypted at rest** in CP/Platform Portal (PP); Plant receives **refs only** and resolves server-side |
| External actions not approval-gated | Autopost/autotrade without consent | Enforce `approval_id` for `publish/post/send/place_order/close_position` via Plant enforcement hooks |
| Trading uses non-deterministic decisions (Phase 1) | Safety/compliance risk | Trading runs must remain **deterministic** in Phase 1; no LLM-based trade decisions |
| Trial/budget enforcement is bypassable | Cost risk and unfair usage | Route LLM/tool calls through a non-bypassable enforcement plane (hooks + usage events) |

## Where the truth lives (code anchors)

### Agent manufacturing + enforcement (Plant)

- AgentSpec + mold entrypoints: [src/Plant/BackEnd/agent_mold/spec.py](../BackEnd/agent_mold/spec.py)
- Dimension registry/materialization: [src/Plant/BackEnd/agent_mold/registry.py](../BackEnd/agent_mold/registry.py)
- Hook bus + approval enforcement: [src/Plant/BackEnd/agent_mold/hooks.py](../BackEnd/agent_mold/hooks.py)
- Enforcement API (skills execution): [src/Plant/BackEnd/api/v1/agent_mold.py](../BackEnd/api/v1/agent_mold.py)
- Reference agents registry: [src/Plant/BackEnd/agent_mold/reference_agents.py](../BackEnd/agent_mold/reference_agents.py)
- Reference agents API: [src/Plant/BackEnd/api/v1/reference_agents.py](../BackEnd/api/v1/reference_agents.py)

### Marketing skill pipeline (Plant)

- Playbook loader: [src/Plant/BackEnd/agent_mold/skills/loader.py](../BackEnd/agent_mold/skills/loader.py)
- Deterministic executor: [src/Plant/BackEnd/agent_mold/skills/executor.py](../BackEnd/agent_mold/skills/executor.py)
- Platform adapters: [src/Plant/BackEnd/agent_mold/skills/adapters.py](../BackEnd/agent_mold/skills/adapters.py)

### Audit + usage signals (Plant)

- Usage events: [src/Plant/BackEnd/services/usage_events.py](../BackEnd/services/usage_events.py)
- Policy denial audit: [src/Plant/BackEnd/services/policy_denial_audit.py](../BackEnd/services/policy_denial_audit.py)

### Observability (Plant)

- Prometheus metrics + /metrics + /health: [src/Plant/BackEnd/core/metrics.py](../BackEnd/core/metrics.py)
- Structured logging + request middleware + trace context: [src/Plant/BackEnd/core/observability.py](../BackEnd/core/observability.py)
- Wiring: [src/Plant/BackEnd/main.py](../BackEnd/main.py)

### Persistence + DB migrations (Plant)

- DB connector (SQLAlchemy async): [src/Plant/BackEnd/core/database.py](../BackEnd/core/database.py)
- Alembic migrations: [src/Plant/BackEnd/database/migrations/](../BackEnd/database/migrations/)

## Local run & tests (Docker-only)

WAOOAW is a **Docker-first** repo. The “no Docker” workflow is deprecated.

### Start the stack

```bash
docker compose -f docker-compose.local.yml up -d --build
```

### Run tests (examples)

```bash
# Plant BackEnd
docker compose -f docker-compose.local.yml exec -T \
	-e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db \
	plant-backend pytest -q

# Plant Gateway
docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing
```

## DB connectivity (mental model)

| Environment | Connection | Pattern |
|---|---|---|
| Codespaces / Docker Compose | TCP | `postgresql+asyncpg://user:pass@postgres:5432/dbname` |
| GCP Cloud SQL (demo/uat/prod) | Unix socket | `postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE` |

If DB connectivity is failing, start with the health endpoint and DB connector in the Plant backend.

## How to keep this README small (editing rules)

When you implement something that used to live in a transient doc:

1. Add (or update) a **single bullet** here that links to the implemented code anchor(s).
2. Delete the transient doc.
3. Do **not** paste long runbooks here — keep procedural depth in code-level tests and services.
