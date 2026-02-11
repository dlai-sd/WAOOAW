# Phase 1 Database Changes Tracking

**Purpose**: Single source of truth for all DDL (schema) and data changes made during the Agent Phase 1 DB iteration.

**Last Updated**: 2026-02-11

---

## Summary

| Date | Story ID | Change Type | Description | Revision |
|---|---|---|---|---|
| 2026-02-11 | AGP1-DB-0.1 | Fix | Fixed migration 009_customer_unique_phone downgrade to use if_exists | 009_customer_unique_phone |
| 2026-02-11 | AGP1-DB-0.2 | Test | Added migration test coverage for 006-009; updated conftest to apply all migrations | N/A |
| 2026-02-11 | AGP1-DB-0.3 | Doc | Documented DB connectivity patterns (TCP vs Unix socket); verified health check | N/A |
| 2026-02-11 | AGP1-DB-1.1 | Migration | Created agent_type_definitions table with JSONB payload for AgentTypeDefinition storage | 010_agent_type_definitions |
| 2026-02-11 | AGP1-DB-1.2 | Code | Implemented repository, service, and DB-backed API for AgentTypeDefinition with fallback to in-memory | N/A |
| 2026-02-11 | AGP1-DB-1.3 | Seed | Seeded Marketing and Trading agent type definitions into DB for dev/test environments | N/A |
| 2026-02-11 | AGP1-DB-2.1 & 2.2 | Migration | Created hired_agents and goal_instances tables with JSONB config/settings for hired agent state | 011_hired_agents_and_goals |

---

## Migration Changes (DDL)

_Record all Alembic migrations below, newest first._

### Migration Fix: 009_customer_unique_phone - AGP1-DB-0.1
**Date**: 2026-02-11
**Story**: AGP1-DB-0.1 - Audit Alembic heads and resolve conflicts
**Alembic Revision**: `009_customer_unique_phone`

**Issue Fixed**: Downgrade function was failing when index didn't exist (DB was stamped but migrations never ran)

**Change**:
- Added `if_exists=True` to `op.drop_index()` call in downgrade function
- Makes downgrade idempotent

**Rollback Command**:
```bash
# Revert to previous migration version if needed
alembic downgrade -1
```

**Current State**: All migrations (001-009) now upgrade/downgrade cleanly. DB stamped at current revision.

---

### Test Coverage Update - AGP1-DB-0.2
**Date**: 2026-02-11
**Story**: AGP1-DB-0.2 - Add migration test coverage for AgentPhase1 tables

**Tests Added**:
- `test_migration_006_trial_tables_exist` - Validates trials and trial_deliverables tables
- `test_migration_007_gateway_audit_logs_table_exists` - Validates gateway_audit_logs table
- `test_migration_008_customer_entity_table_exists` - Validates customer_entity table
- `test_migration_009_customer_phone_unique_constraint` - Validates unique constraint on phone
- `test_migration_009_customer_phone_index_exists` - Validates index on phone column

**Configuration Change**:
- Updated `tests/conftest.py` to apply migrations to `head` instead of stopping at `006_trial_tables`
- Ensures all new migrations are tested

**Test Results**: All 18 migration tests pass

---

### DB Connectivity Documentation - AGP1-DB-0.3
**Date**: 2026-02-11
**Story**: AGP1-DB-0.3 - Document Codespaces vs GCP DB URLs and verify connectivity

**Documentation Created**:
- Created comprehensive [DB_CONNECTIVITY_GUIDE.md](./DB_CONNECTIVITY_GUIDE.md)
- Documents DATABASE_URL patterns for all environments:
  - Codespaces/Docker: TCP connection `postgresql+asyncpg://user:pass@postgres:5432/dbname`
  - GCP Cloud SQL: Unix socket `postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/...`

**Key Differences**:
- **Codespaces**: Uses Docker Compose service name `postgres` on port `5432`
- **GCP**: Uses Cloud SQL Proxy unix socket path `/cloudsql/PROJECT:REGION:INSTANCE`
- **Driver**: Both use `asyncpg` via SQLAlchemy async

**Connectivity Verification**:
```bash
# Tested health check in running Plant backend container
docker compose -f docker-compose.local.yml exec -T plant-backend \
  python -c "from core.database import _connector; import asyncio; print('DB Health:', asyncio.run(_connector.health_check()))"

# Result: DB Health: True ✓
```

**Files Updated**:
- Created `src/Plant/Docs/DB_CONNECTIVITY_GUIDE.md` (comprehensive environment guide)
- No changes to .env templates (already correctly configured)

**Validation**:
- ✓ DB health check passes in Codespaces
- ✓ All .env templates have correct DATABASE_URL patterns
- ✓ Connection pool settings documented for dev/prod

---

### Migration: 010_agent_type_definitions - AGP1-DB-1.1
**Date**: 2026-02-11
**Story**: AGP1-DB-1.1 - Create DB model + migration for AgentTypeDefinition  
**Alembic Revision**: `ce2ce3126c3b` (renamed to `010_agent_type_definitions`)

**Tables Created**:
- `agent_type_definitions`: Versioned storage for agent type schemas + goal templates
  - Columns:
    - `id` (varchar, PK): Unique identifier (typically `{agent_type_id}@{version}`)
    - `agent_type_id` (varchar, NOT NULL, indexed): Agent type ID (e.g., "marketing.healthcare.v1")
    - `version` (varchar, NOT NULL): Semantic version (e.g., "1.0.0")
    - `payload` (jsonb, NOT NULL): Full JSON structure with config_schema, goal_templates, enforcement_defaults
    - `created_at` (timestamptz, NOT NULL): Creation timestamp
    - `updated_at` (timestamptz, NOT NULL): Last update timestamp
  - Indexes:
    - `pk_agent_type_definitions` (PRIMARY KEY on id)
    - `ix_agent_type_definitions_agent_type_id` (on agent_type_id)
  - Constraints:
    - `uq_agent_type_id_version` (UNIQUE on agent_type_id, version)

**Migration Command**:
```bash
docker compose -f docker-compose.local.yml exec -T plant-backend alembic upgrade head
```

**Rollback Command**:
```bash
docker compose -f docker-compose.local.yml exec -T plant-backend alembic downgrade -1
```

**Model File**: `src/Plant/BackEnd/models/agent_type.py`

**Test Coverage**:
- `test_migration_010_agent_type_definitions_table_exists` - Validates table exists
- `test_migration_010_agent_type_definitions_columns` - Validates all columns including JSONB payload
- `test_migration_010_agent_type_id_version_unique_constraint` - Validates unique constraint
- `test_migration_010_agent_type_id_index_exists` - Validates index on agent_type_id

**Test Results**: All 4 migration 010 tests pass ✓

**Verification**:
```bash
# Verified table structure
docker compose -f docker-compose.local.yml exec -T postgres psql -U waooaw -d waooaw_db -c "\d agent_type_definitions"

# Tested downgrade/upgrade cycle
docker compose -f docker-compose.local.yml exec -T plant-backend alembic downgrade -1
docker compose -f docker-compose.local.yml exec -T plant-backend alembic upgrade head
```

**Current State**: Table created successfully, migration is reversible, tests pass

---

### Migration: 011_hired_agents_and_goals - AGP1-DB-2.1 & 2.2
**Date**: 2026-02-11
**Stories**: AGP1-DB-2.1 (HiredAgentModel), AGP1-DB-2.2 (GoalInstanceModel)
**Alembic Revision**: `bb0ee0250f8a` (renamed to `011_hired_agents_and_goals`)

**Tables Created**:

1. `hired_agents`: Storage for hired agent instances (replaces hired_agents_simple.py in-memory)
   - Columns:
     - `hired_instance_id` (varchar, PK): Unique identifier for hired agent
     - `subscription_id` (varchar, NOT NULL, UNIQUE indexed): Links to billing subscription
     - `agent_id` (varchar, NOT NULL, indexed): Agent type ID
     - `customer_id` (varchar, NOT NULL, indexed): Customer who hired agent
     - `config` (jsonb, NOT NULL): Merged configuration (defaults + overrides)
     - `settings` (jsonb): Additional runtime settings
     - `configured` (boolean, default false): Whether initial configuration complete
     - `goals_completed` (boolean, default false): Whether goal setup complete
     - `active` (boolean, default true, indexed): Whether agent active
     - `trial_start` (timestamptz): Trial period start timestamp
     - `trial_end` (timestamptz): Trial period end timestamp
     - `trial_status` (varchar, indexed): Current trial status enum
     - `created_at` (timestamptz, NOT NULL): Creation timestamp
     - `updated_at` (timestamptz, NOT NULL): Last update timestamp
   - Indexes:
     - `pk_hired_agents` (PRIMARY KEY on hired_instance_id)
     - `uq_hired_agents_subscription_id` (UNIQUE on subscription_id)  
     - `ix_hired_agents_agent_id` (on agent_id)
     - `ix_hired_agents_customer_id` (on customer_id)
     - `ix_hired_agents_trial_status` (on trial_status)
     - `ix_hired_agents_active` (on active)

2. `goal_instances`: Storage for each goal activated on a hired agent
   - Columns:
     - `goal_instance_id` (varchar, PK): Unique identifier for goal
     - `hired_instance_id` (varchar, NOT NULL, FK to hired_agents): Parent hired agent
     - `goal_template_id` (varchar, NOT NULL): Reference to goal template
     - `frequency` (varchar, NOT NULL): Execution frequency (daily, weekly, monthly)
     - `settings` (jsonb): Goal-specific settings (overrides + runtime config)
     - `created_at` (timestamptz, NOT NULL): Creation timestamp
     - `updated_at` (timestamptz, NOT NULL): Last update timestamp
   - Indexes:
     - `pk_goal_instances` (PRIMARY KEY on goal_instance_id)
     - `ix_goal_instances_hired_instance_id` (on hired_instance_id)
   - Constraints:
     - `fk_goal_instances_hired_instance_id` (FOREIGN KEY to hired_agents.hired_instance_id with CASCADE delete)

**Migration Command**:
```bash
docker compose -f docker-compose.local.yml exec -T plant-backend alembic upgrade head
```

**Rollback Command**:
```bash
docker compose -f docker-compose.local.yml exec -T plant-backend alembic downgrade -1
```

**Model Files**: 
- `src/Plant/BackEnd/models/hired_agent.py` (HiredAgentModel, GoalInstanceModel with SQLAlchemy ORM relationship)

**Test Coverage**:
- `test_migration_011_hired_agents_table_exists` - Validates hired_agents table exists
- `test_migration_011_goal_instances_table_exists` - Validates goal_instances table exists
- `test_migration_011_hired_agents_subscription_id_unique` - Validates UNIQUE constraint on subscription_id
- `test_migration_011_goal_instances_foreign_key` - Validates FK constraint with CASCADE delete

**Test Results**: All 4 migration 011 tests pass ✓

**Verification**:
```bash
# Verified table structure
docker compose -f docker-compose.local.yml exec -T postgres psql -U waooaw -d waooaw_db -c "\d hired_agents"
docker compose -f docker-compose.local.yml exec -T postgres psql -U waooaw -d waooaw_db -c "\d goal_instances"

# Tested downgrade/upgrade cycle
docker compose -f docker-compose.local.yml exec -T plant-backend alembic downgrade -1
docker compose -f docker-compose.local.yml exec -T plant-backend alembic upgrade head
```

**Current State**: Tables created with relationships, migration is reversible, CASCADE behavior verified, tests pass

---

### Code Changes: Repository, Service, API - AGP1-DB-1.2
**Date**: 2026-02-11
**Story**: AGP1-DB-1.2 - Implement repository/service to list/get definitions from DB

**Files Created**:
- `src/Plant/BackEnd/repositories/agent_type_repository.py` - CRUD operations for agent_type_definitions
- `src/Plant/BackEnd/services/agent_type_service.py` - Business logic, converts DB ↔ Pydantic models
- `src/Plant/BackEnd/api/v1/agent_types_db.py` - DB-backed endpoints with feature flag
- `src/Plant/BackEnd/tests/unit/test_agent_types_db_api.py` - 8 tests for repository, service, API

**Files Modified**:
- `src/Plant/BackEnd/api/v1/router.py` - Added agent_types_db router

**API Endpoints** (prefix: `/api/v1/agent-types-db`):
- `GET /` - List all agent type definitions (latest versions)
- `GET /{agent_type_id}` - Get specific agent type definition
- `POST /` - Create new agent type definition (requires USE_AGENT_TYPE_DB=true)
- `PUT /{agent_type_id}` - Update existing agent type definition (requires USE_AGENT_TYPE_DB=true)

**Feature Flag**:
- `USE_AGENT_TYPE_DB` (env var, default: `false`)
- When `false`: falls back to in-memory implementation from `agent_types_simple.py`
- When `true`: uses DB-backed implementation via repository + service

**Repository Methods** (`AgentTypeDefinitionRepository`):
- `get_by_id(agent_type_id)` - Get latest version by agent_type_id
- `get_by_id_and_version(agent_type_id, version)` - Get specific version
- `list_all()` - List latest version of each agent type
- `create(agent_type_id, version, payload)` - Insert new definition
- `update(agent_type_id, version, payload)` - Update existing definition

**Service Methods** (`AgentTypeDefinitionService`):
- `get_definition(agent_type_id)` - Returns Pydantic model
- `list_definitions()` - Returns list of Pydantic models
- `create_definition(definition)` - Create from Pydantic model
- `update_definition(definition)` - Update from Pydantic model
- `_to_pydantic(db_model)` - Converts DB model → Pydantic

**Test Coverage**: 8 tests pass
- `test_agent_type_repository_create` - DB create operation
- `test_agent_type_repository_get_by_id` - DB retrieval
- `test_agent_type_repository_list_all` - List with deduplication
- `test_agent_type_service_create_and_get` - Service layer integration
- `test_agent_type_service_list_definitions` - Service list operation
- `test_agent_type_api_list_fallback_to_in_memory` - Fallback behavior
- `test_agent_type_api_get_by_id_fallback` - Fallback for get
- `test_agent_type_api_create_requires_feature_flag` - Feature flag enforcement

**Validation**:
```bash
docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest tests/unit/test_agent_types_db_api.py -v
# Result: 8 passed ✓
```

**Next Steps**: AGP1-DB-1.3 will seed Marketing + Trading definitions into DB

---
# Data Seed: Marketing + Trading Agent Types - AGP1-DB-1.3
**Date**: 2026-02-11
**Story**: AGP1-DB-1.3 - Seed initial Marketing + Trading definitions into DB in dev/test
**Type**: Seed

**Description**: Created seed script to populate agent_type_definitions table with Phase-1 definitions

**Files Created**:
- `src/Plant/BackEnd/database/seeds/agent_type_definitions_seed.py` - Main seed script
- `src/Plant/BackEnd/database/seeds/test_agent_type_seed.py` - Verification script

**Seeds Inserted**:
1. `marketing.healthcare.v1@1.0.0`
   - Config schema: 11 fields (nickname, theme, primary_language, timezone, brand_name, etc.)
   - Goal templates: 3 (weekly multichannel batch, daily micro-post, monthly campaign pack)
   - Enforcement: approval_required=true, deterministic=false

2. `trading.delta_futures.v1@1.0.0`
   - Config schema: 8 fields (nickname, theme, timezone, exchange_provider, credential_ref, etc.)
   - Goal templates: 3 (trade intent draft, close position reminder, guardrail report)
   - Enforcement: approval_required=true, deterministic=true

**Seed Command**:
```bash
docker compose -f docker-compose.local.yml exec -T plant-backend python database/seeds/agent_type_definitions_seed.py
```

**Verification**:
```bash
# Check DB records
docker compose -f docker-compose.local.yml exec -T postgres psql -U waooaw -d waooaw_db -c "SELECT id, agent_type_id, version FROM agent_type_definitions;"

# Result: 2 rows
# - marketing.healthcare.v1@1.0.0
# - trading.delta_futures.v1@1.0.0
```

**Idempotency**: Seed script checks for existing definitions before inserting, safe to re-run

**Rollback**: Delete inserted rows if needed:
```sql
DELETE FROM agent_type_definitions WHERE agent_type_id IN ('marketing.healthcare.v1', 'trading.delta_futures.v1');
```

---

##
## Data Changes (Seeds, Migrations, Fixes)

_Record all data modifications below, newest first._

---

## Rollback Instructions

_If a full rollback of Phase 1 DB changes is needed:_

```bash
# Determine the revision before Phase 1 DB iteration started
alembic history

# Downgrade to that revision
alembic downgrade <revision_before_phase1>

# Verify current state
alembic current
```

---

## Notes
- All migrations must be tested in Docker before merging
- GCP deployments require migration dry-run approval
- Never commit migrations without updating this file
