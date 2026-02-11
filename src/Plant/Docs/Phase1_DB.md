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
