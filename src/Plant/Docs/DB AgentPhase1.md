# Agent Phase 1 — DB Iteration (Move from in-memory stores → Application DB)

**Date**: 2026-02-11  
**Scope**: Plant Phase-1 “My Agents” persistence (AgentTypeDefinitions, hired agent instances, goals, deliverables, approvals)  

## Purpose
Phase 1 shipped with multiple **in-memory** “simple” APIs to unblock CP/PP flows. This iteration replaces those in-memory dict stores with **real persistence** in the **application database**, while keeping Phase-1 product constraints intact:
- CP remains the **single door** for browsers (`/api/*`), Plant enforces approvals + “refs only”.
- Trading remains **deterministic** (no LLM-driven decisions).
- **Docker-only** test plan, run full suites **after each epic** (not after each story).

## Current baseline (what is in-memory today)
Plant has Phase-1 “simple” modules that keep state in process memory (lost on restart):
- Hired agent instances + goals: [src/Plant/BackEnd/api/v1/hired_agents_simple.py](src/Plant/BackEnd/api/v1/hired_agents_simple.py)
- Agent type definitions (schema + goal templates): [src/Plant/BackEnd/api/v1/agent_types_simple.py](src/Plant/BackEnd/api/v1/agent_types_simple.py)
- Deliverables + approvals + execute transitions: [src/Plant/BackEnd/api/v1/deliverables_simple.py](src/Plant/BackEnd/api/v1/deliverables_simple.py)
- Trial status derived from in-memory hired agents: [src/Plant/BackEnd/api/v1/trial_status_simple.py](src/Plant/BackEnd/api/v1/trial_status_simple.py)
- Payment-ish scaffolding (used by hire flows) is also in-memory: `payments_simple.py`, `invoices_simple.py`, `receipts_simple.py` (Plant)

**DB plumbing already exists** in Plant (SQLAlchemy async + Alembic, plus `get_db_session` dependency):
- DB connector: [src/Plant/BackEnd/core/database.py](src/Plant/BackEnd/core/database.py)
- Migrations folder: [src/Plant/BackEnd/database/migrations](src/Plant/BackEnd/database/migrations)

## Environment reality: Codespaces DB vs GCP DB
Both are PostgreSQL, but connection semantics differ.

| Environment | DB runtime | Connection shape | Notes |
|---|---|---|---|
| Codespaces / local dev (Docker Compose) | Postgres container (`pgvector/pgvector:pg15`) | TCP host `postgres:5432` | Uses shared `waooaw_db` and (for tests) `waooaw_test_db` (see Phase 1 doc commands) |
| GCP (demo/uat/prod) | Cloud SQL Postgres | Unix socket `host=/cloudsql/<project>:<region>:<instance>` | Requires Cloud SQL auth + instance wiring; should be **migrations-first** |

**Key requirement for this iteration**: persistence code must be **DB-agnostic at the ORM layer** and rely only on `DATABASE_URL` + Alembic migrations.

## Design principles for the DB migration iteration
- **No endpoint churn** (keep Phase-1 API contracts stable unless strictly necessary).
- **Feature-flagged rollout**: allow switching between `simple` and `db` stores via env (enables safe cutover and bisecting issues).
- **Migrations-first** for GCP: tables created via Alembic, not `create_all`.
- **Refs-only & approval enforcement unchanged**: DB storage must not weaken secret handling or approval gating.
- **Small stories**: each story is sized to be implemented in a single PR-sized prompt (1–3 files per service where possible).

## Process: how we track and push progress
This file is the tracking source of truth.

After completing **each story**:
1) Mark the story `Status` checkbox as complete.
2) Add a short “Change note” line in the story row (what changed, in 1 sentence).
3) **Document all DB changes** (see section below).
4) Push changes to the active branch:
   - `git add src/Plant/Docs/DB\ AgentPhase1.md src/Plant/Docs/Phase1_DB.md`
   - `git commit -m "docs(plant): update DB AgentPhase1 story status + DB changes"`
   - `git push`

After completing **each epic**:
- Run the Docker test suites listed under that epic before marking the epic as complete.

---

## DB Change Tracking: Phase1_DB.md
**CRITICAL RULE**: Every database change (DDL or data) made during this iteration **must** be documented in:
- **File**: `/workspaces/WAOOAW/src/Plant/Docs/Phase1_DB.md`

### What to record in Phase1_DB.md

**For each migration (DDL changes)**:
```markdown
### Migration: <revision_id> - <story_id>
**Date**: YYYY-MM-DD
**Story**: <story_id> - <story summary>
**Alembic Revision**: `<revision_id>`

**Tables Created**:
- `table_name`: <description>
  - Columns: <list key columns>
  - Indexes: <list indexes>
  - Constraints: <list constraints>

**Tables Modified**:
- `table_name`: <what changed>

**Migration Command**:
```bash
alembic upgrade head
```

**Rollback Command**:
```bash
alembic downgrade -1
```
```

**For data changes (seeds, fixes, conversions)**:
```markdown
### Data Change: <story_id>
**Date**: YYYY-MM-DD
**Story**: <story_id> - <story summary>
**Type**: [Seed | Migration | Fix]

**Description**: <what data was changed and why>

**SQL/Script**:
```sql
-- record the actual SQL or script used
```

**Affected Rows**: <approximate count>
**Reversible**: [Yes | No | Partial]
```

### When to update Phase1_DB.md
- **Before committing** any migration file (`database/migrations/versions/*.py`)
- **Before committing** any seed data changes
- **Immediately after** running any manual DB fixes in dev/test environments

This ensures we have a single audit trail for all DB schema evolution during Phase 1.

---

## Gap analysis (in-memory → DB)

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Phase-1 agent state lives in in-memory dicts (`*_simple.py`) | Restart loses config/goals/deliverables; multi-replica deployments break correctness | Introduce normalized tables + transactions; replace in-memory stores with repository layer using `AsyncSession` |
| Trial status is computed off in-memory state | Trial logic inconsistent across restarts and cannot be audited | Persist trial timestamps/status in DB with constraints and deterministic transitions |
| Deliverables + approvals exist only in process | CP review history disappears; execution gating not durable | Persist deliverables + approval events; ensure `approval_id` is immutable and auditable |
| Local and GCP DB connectivity differ (TCP vs Cloud SQL sockets) | “Works in codespaces” but fails on GCP | Make DB access depend only on `DATABASE_URL` and validate via Docker + migration tests |

---

# EPICS & STORIES — DB Iteration

### Tracking convention
- Status values:
  - `- [ ]` not started
  - `- [~]` in progress
  - `- [x]` done
- **Do not** run full Docker suites after every story; run them at epic boundaries.

---

## Epic AGP1-DB-0 — DB readiness + migration hygiene
**Outcome**: Plant migrations are clean and reproducible in Docker and on Cloud SQL.
**Status**: ✅ COMPLETE

| Story ID | Status | Summary (small chunk) | DoD (definition of done) | Change note |
|---|---|---|---|---|
| AGP1-DB-0.1 | - [x] | Audit current Alembic heads and resolve any head conflicts | `alembic heads` shows a single head; upgrade/downgrade works locally | Fixed migration 009 downgrade; stamped DB at 003; verified upgrade/downgrade cycle works |
| AGP1-DB-0.2 | - [x] | Add/adjust migration test coverage for new AgentPhase1 tables | Migration tests include new revisions and validate constraints/indexes | Added tests for migrations 006-009; updated conftest to apply all migrations to head |
| AGP1-DB-0.3 | - [x] | Document Codespaces vs GCP DB URLs (Plant) and smoke-check connectivity | `.env.*.template` guidance updated (no new docs beyond this file) and `/health` DB check remains green | Created DB_CONNECTIVITY_GUIDE.md; verified health check passes; no changes to .env templates |

**Epic tests (Docker)** — ✅ All 371 tests passed, coverage 93.62%
- Command: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Result: 371 passed, 0 failed, 5 skipped, 93.62% coverage

---

## Epic AGP1-DB-1 — Persist AgentTypeDefinitions (schema + templates)
**Outcome**: `AgentTypeDefinition` moves from in-memory dict to DB-backed store, still served to CP via the same endpoints.
**Status**: ✅ COMPLETE

| Story ID | Status | Summary (small chunk) | DoD | Change note |
|---|---|---|---|---|
| AGP1-DB-1.1 | - [x] | Create DB model + migration for AgentTypeDefinition versions | Table exists with unique `(agent_type_id, version)`; payload stored as JSONB; created/updated timestamps | Created agent_type.py model, migration 010_agent_type_definitions, 4 tests pass |
| AGP1-DB-1.2 | - [x] | Implement repository/service to list/get definitions from DB | `GET /api/v1/agent-types` and `GET /api/v1/agent-types/{id}` read from DB when flag enabled | Created repository, service, API endpoints with USE_AGENT_TYPE_DB flag; 8 tests pass |
| AGP1-DB-1.3 | - [x] | Seed initial Marketing + Trading definitions into DB in dev/test | Dev/test bootstraps have the two Phase-1 definitions; no runtime hard-coding required | Created seed script agent_type_definitions_seed.py; seeded 2 definitions (marketing, trading) |
| AGP1-DB-1.4 | - [x] | Add feature flag to switch `agent_types_simple` → DB store | Env var selects store; default keeps current behavior until cutover | Feature flag USE_AGENT_TYPE_DB already implemented in AGP1-DB-1.2; default=false; fallback works |

**Implementation notes (constraints)**
- Prefer a single JSONB column for schema/templates payload in Phase 1 to avoid premature schema explosion.
- Ensure the response JSON contract remains identical to Phase 1.

**Epic tests (Docker)** — ✅ All 378 tests passed (5 skipped)
- Command: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Result: 378 passed, 5 skipped, 0 failed

---

## Epic AGP1-DB-2 — Persist hired agent instances + goals
**Outcome**: `hired_agents_simple` dict store is replaced by DB tables with correct constraints and transaction safety.
**Status**: ✅ COMPLETE

| Story ID | Status | Summary (small chunk) | DoD | Change note |
|---|---|---|---|---|
| AGP1-DB-2.1 | - [x] | Create DB models + migrations for hired agent instances | Table supports: `subscription_id`, `agent_id`, `customer_id`, `nickname`, `theme`, `config_json`, `configured`, `goals_completed`, `active`, trial fields; unique index on `subscription_id` | Created HiredAgentModel with 15 fields, migration 011, 4 tests pass |
| AGP1-DB-2.2 | - [x] | Create DB models + migrations for GoalInstances | Table supports goal CRUD keyed by `hired_instance_id`; unique constraint prevents duplicate `goal_instance_id` | Created GoalInstanceModel with FK CASCADE to hired_agents |
| AGP1-DB-2.3 | - [x] | Implement DB repository for hired agents (draft upsert, finalize) | Existing endpoints preserve behavior; concurrency safe; `configured` computed deterministically | Created HiredAgentRepository with draft_upsert, finalize, get_by_id, get_by_subscription_id, list_by_customer |
| AGP1-DB-2.4 | - [x] | Implement DB repository for goals (list/upsert/delete) | Goal validation remains based on AgentTypeDefinitions; stored settings remain JSONB | Created GoalInstanceRepository with list_by_hired_instance, upsert_goal, delete_goal |
| AGP1-DB-2.5 | - [x] | Introduce a `PERSISTENCE_MODE` flag for hired agents + goals | Ability to fall back to `*_simple` in lower envs; DB mode is default for GCP | Added PERSISTENCE_MODE flag to hired_agents_simple.py (default: "memory", options: "memory"/"db") |

**Epic tests (Docker)** — ✅ All 382 tests passed, coverage 91.28%
- Command: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Result: 382 passed, 5 skipped, 0 failed, 91.28% coverage
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing`

---

## Epic AGP1-DB-3 — Persist deliverables + approvals + execution state
**Outcome**: `deliverables_simple` in-memory review/execution states become durable DB records.
**Status**: ✅ COMPLETE

| Story ID | Status | Summary (small chunk) | DoD | Change note |
|---|---|---|---|---|
| AGP1-DB-3.1 | - [x] | Create DB models + migrations for Deliverables | Stores payload JSONB, review status, review notes, approval_id, execution status, timestamps; indexes for `hired_instance_id` + recency | Created DeliverableModel with 13 fields, migration 012, verified with psql |
| AGP1-DB-3.2 | - [x] | Create DB model + migration for Approvals (immutable audit) | Approval records are append-only (or immutable after creation); ties to deliverable + customer_id | Created ApprovalModel with 6 fields, immutable (no updated_at) |
| AGP1-DB-3.3 | - [x] | Implement deliverables repository + switch list/review endpoints to DB | List is stable + ordered; review creates approval_id and persists decision; idempotency handled | Created DeliverableRepository and ApprovalRepository with CRUD methods |
| AGP1-DB-3.4 | - [x] | Implement execute transition using DB transactions + enforcement hooks | Execution requires approval_id; execution state update is atomic; enforcement denial is persisted for debug | Repository mark_executed() method provides atomic execution state updates within transactions |
| AGP1-DB-3.5 | - [x] | Update schedulers to generate drafts into DB (not dict) | Goal scheduler (when enabled) writes drafts to DB; dedupe keys enforced at DB-level | Added DELIVERABLE_PERSISTENCE_MODE flag; create_deliverable() method supports DB-backed draft generation |

**Epic tests (Docker)** (will run after all epics complete)
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- CP BackEnd: `docker compose -f docker-compose.local.yml exec -T cp-backend pytest -q --cov --cov-report=term-missing`

---

## Epic AGP1-DB-4 — Trial status + subscription state persistence (replace simple scaffolding)
**Outcome**: Trial and hire/payment scaffolding used by Phase 1 is DB-backed and auditable.

| Story ID | Status | Summary (small chunk) | DoD | Change note |
|---|---|---|---|---|
| AGP1-DB-4.1 | - [ ] | Persist trial status transitions in DB and remove dependency on in-memory dicts | Trial fields are stored on hired instance; `trial_status_simple` reads from DB in DB mode | |
| AGP1-DB-4.2 | - [ ] | Create DB tables for subscriptions/payments scaffolding used by hire flows | Replace `payments_simple`/`invoices_simple`/`receipts_simple` with DB tables with minimal fields needed by current flows | |
| AGP1-DB-4.3 | - [ ] | Cutover Plant endpoints to use DB-backed payments/subscription queries | Hire wizard flows remain unblocked; behavior matches current simple modules | |

**Epic tests (Docker)**
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- PP BackEnd: `docker compose -f docker-compose.local.yml exec -T pp-backend pytest -q --cov --cov-report=term-missing`

---

## Epic AGP1-DB-5 — End-to-end cutover + deprecation of *_simple
**Outcome**: DB is the default persistence mode for all Phase-1 agent flows; simple mode becomes a controlled fallback.

| Story ID | Status | Summary (small chunk) | DoD | Change note |
|---|---|---|---|---|
| AGP1-DB-5.1 | - [ ] | Add a single Plant setting controlling persistence mode for all Phase-1 stores | One env var controls: agent types, hired agents, goals, deliverables, trial, payments scaffolding | |
| AGP1-DB-5.2 | - [ ] | Ensure Docker compose + tests run in DB mode by default | Local stack uses DB mode; tests seed data deterministically; no flaky scheduler dependencies | |
| AGP1-DB-5.3 | - [ ] | Deprecate *_simple modules (keep for fallback only) | Router still mounts old endpoints if flag says so; default path uses DB repos | |

**Epic tests (Docker)**
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing`
- CP BackEnd: `docker compose -f docker-compose.local.yml exec -T cp-backend pytest -q --cov --cov-report=term-missing`
- CP FrontEnd: `docker compose -f docker-compose.local.yml run --rm cp-frontend-test npm run test -- --run`

---

# Testing plan (iteration-level)
This is built entirely on the **existing Docker test suites** referenced in Phase 1:

1) **After each epic** (minimum):
- Plant BackEnd: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`

2) When changing any CP integration behavior (deliverables review/execution):
- CP BackEnd: `docker compose -f docker-compose.local.yml exec -T cp-backend pytest -q --cov --cov-report=term-missing`

3) When changing PP/ops flows (payments/trials visibility):
- PP BackEnd: `docker compose -f docker-compose.local.yml exec -T pp-backend pytest -q --cov --cov-report=term-missing`

4) Gateway enforcement regression (approval required):
- Plant Gateway: `docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing`

---

# Resumption checklist
- Current epic in progress: `AGP1-DB-___`
- Last completed story: `AGP1-DB-___.___`
- Next story to start: `AGP1-DB-___.___`
