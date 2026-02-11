# Phase 1 Database Changes Tracking

**Purpose**: Single source of truth for all DDL (schema) and data changes made during the Agent Phase 1 DB iteration.

**Last Updated**: 2026-02-11

---

## Summary

| Date | Story ID | Change Type | Description | Revision |
|---|---|---|---|---|
| 2026-02-11 | AGP1-DB-0.1 | Fix | Fixed migration 009_customer_unique_phone downgrade to use if_exists | 009_customer_unique_phone |
| 2026-02-11 | AGP1-DB-0.2 | Test | Added migration test coverage for 006-009; updated conftest to apply all migrations | N/A |

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
