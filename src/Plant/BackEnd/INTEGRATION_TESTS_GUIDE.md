# Integration Tests Guide - WAOOAW Plant Phase 0

## Overview

This document describes how to run the comprehensive integration test suite for WAOOAW Plant backend. The suite contains **70+ async integration tests** across 7 test files validating all critical database layers.

**Test Files Created:**
- `test_database_connection.py` - 12 tests for async engine, extensions, pooling
- `test_alembic_migrations.py` - 11 tests for migration validation
- `test_rls_policies.py` - 11 tests for row-level security & constraints
- `test_pgvector_functionality.py` - 9 tests for vector operations
- `test_audit_trail.py` - 10 tests for audit logging & immutability
- `test_connector_pooling.py` - 11 tests for connection pooling
- `test_transactions.py` - 10 tests for transaction consistency

**Total: 74 async integration tests**

---

## Quick Start

### Prerequisites

```bash
# Required packages (already in requirements.txt)
- pytest==7.4.4
- pytest-asyncio==0.23.3
- pytest-cov==4.1.0
- testcontainers==3.7.1
- SQLAlchemy==2.0.25
- asyncpg  # Async PostgreSQL driver
```

### Running Tests Locally

```bash
# 1. Navigate to backend directory
cd /workspaces/WAOOAW/src/Plant/BackEnd

# 2. Ensure virtual environment is active
source /workspaces/WAOOAW/.venv/bin/activate

# 3. Run all integration tests
pytest tests/integration/ -v --cov=core,models,validators --cov-report=html

# 4. View coverage report
open htmlcov/index.html
```

### Running Specific Test Files

```bash
# Database connection tests only
pytest tests/integration/test_database_connection.py -v

# Migration validation only
pytest tests/integration/test_alembic_migrations.py -v

# Security tests (RLS + Audit)
pytest tests/integration/test_rls_policies.py tests/integration/test_audit_trail.py -v

# Performance tests (pooling + transactions)
pytest tests/integration/test_connector_pooling.py tests/integration/test_transactions.py -v
```

### Running with Coverage

```bash
# Full coverage report with 90% failure threshold
pytest tests/integration/ \
  --cov=core \
  --cov=models \
  --cov=validators \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=90 \
  -v

# View HTML coverage report
open htmlcov/index.html

# Or terminal summary
pytest tests/integration/ --cov=core --cov-report=term-missing
```

---

## Test Architecture

### Fixtures (conftest.py)

**Session-Scoped (Reused Across All Tests):**
```python
event_loop()           # Async event loop for pytest-asyncio
postgres_container     # testcontainers PostgreSQL 15
test_db_url()         # Async connection URL (asyncpg driver)
async_engine()        # SQLAlchemy async engine with all tables created
```

**Function-Scoped (Fresh for Each Test):**
```python
async_session         # Fresh AsyncSession with auto-rollback
create_test_skill()   # Factory: creates test Skill entities
create_test_industry() # Factory: creates test Industry entities
create_test_job_role() # Factory: creates test JobRole entities
create_test_agent()   # Factory: creates test Agent entities
```

### Database Setup

Tests use **testcontainers** which automatically:
1. Starts a PostgreSQL 15 container
2. Creates all tables via SQLAlchemy ORM (Base.metadata.create_all)
3. Loads extensions (pgvector, uuid-ossp)
4. Cleans up after test session ends

**No external database needed** - all tests are isolated in ephemeral containers.

---

## Test Coverage Breakdown

### Layer 1: Database Connection (test_database_connection.py - 12 tests)

Validates async connector initialization and pooling:

```python
✅ test_async_engine_created()
✅ test_pgvector_extension_loaded()
✅ test_uuid_ossp_extension_loaded()
✅ test_base_entity_table_created()
✅ test_async_session_lifecycle()
✅ test_database_connection_timeout()
✅ test_schema_validation()
✅ test_database_insert_and_retrieve()
✅ test_connection_pool_properties()
✅ test_multiple_concurrent_connections()
✅ test_transaction_rollback()
✅ test_async_context_manager()
```

**Coverage Target:** `core/database.py`, `core/connector.py` (100%)

### Layer 2: Alembic Migrations (test_alembic_migrations.py - 11 tests)

Validates all database migrations execute correctly:

```python
✅ test_migration_001_base_entity_table_exists()
✅ test_migration_002_skill_entity_table_exists()
✅ test_skill_entity_has_embedding_column()
✅ test_migration_creates_indexes()
✅ test_base_entity_primary_key_exists()
✅ test_skill_entity_inherits_from_base_entity()
✅ test_migration_creates_foreign_keys()
✅ test_migration_adds_columns_idempotently()
✅ test_all_entity_tables_created()
✅ test_migrations_maintain_data_integrity()
✅ test_migration_null_constraints()
```

**Coverage Target:** `database/migrations/`, `models/` (100%)

### Layer 3: Row-Level Security (test_rls_policies.py - 11 tests)

Validates constraint enforcement and data isolation:

```python
✅ test_rls_policies_enabled_on_base_entity()
✅ test_insert_valid_skill()
✅ test_append_only_enforcement()
✅ test_skill_entity_insert_allowed()
✅ test_non_null_constraints_enforced()
✅ test_unique_constraint_on_external_id()
✅ test_primary_key_enforcement()
✅ test_foreign_key_constraint()
✅ test_check_constraint_status()
✅ test_insert_skill_with_valid_data()
✅ test_constraint_violation_handling()
```

**Coverage Target:** `models/` constraints, `security/rls.py` (100%)

### Layer 4: pgvector Operations (test_pgvector_functionality.py - 9 tests)

Validates vector storage and similarity search:

```python
✅ test_pgvector_extension_available()
✅ test_skill_embedding_column_exists()
✅ test_vector_insert_and_retrieve()
✅ test_vector_distance_calculation()
✅ test_vector_index_creation()
✅ test_vector_null_handling()
✅ test_multiple_vectors_stored()
✅ test_vector_type_compatibility()
✅ test_embedding_dimension_compatibility()
```

**Coverage Target:** `ml/embeddings.py`, `models/skill.py` (95%+)

### Layer 5: Audit Trail (test_audit_trail.py - 10 tests)

Validates immutability enforcement and audit logging:

```python
✅ test_audit_table_exists()
✅ test_skill_insert_creates_audit_record()
✅ test_timestamp_immutability()
✅ test_entity_version_tracking()
✅ test_hash_chain_computation()
✅ test_append_only_pattern_enforcement()
✅ test_created_at_indexed_for_audit()
✅ test_audit_log_retention()
✅ test_tamper_detection_via_hash_verification()
✅ test_sequential_audit_entries()
```

**Coverage Target:** `security/audit.py`, `models/base.py` (90%+)

### Layer 6: Connection Pooling (test_connector_pooling.py - 11 tests)

Validates pool configuration and concurrent connection handling:

```python
✅ test_pool_size_configuration()
✅ test_max_overflow_configuration()
✅ test_concurrent_connection_acquisition()
✅ test_connection_reuse()
✅ test_connection_timeout_handling()
✅ test_pool_exhaustion_handling()
✅ test_connection_cleanup_after_error()
✅ test_session_lifecycle_connection_release()
✅ test_nested_transaction_connection_reuse()
✅ test_pool_monitoring_metrics()
✅ test_readonly_vs_readwrite_pooling()
```

**Coverage Target:** `core/database.py` pooling logic (95%+)

### Layer 7: Transaction Consistency (test_transactions.py - 10 tests)

Validates ACID properties and isolation:

```python
✅ test_transaction_commit_atomicity()
✅ test_transaction_rollback_on_constraint_violation()
✅ test_transaction_isolation_level()
✅ test_dirty_read_prevention()
✅ test_repeatable_read_consistency()
✅ test_phantom_read_handling()
✅ test_serialization_consistency()
✅ test_concurrent_transaction_non_interference()
✅ test_transaction_deadlock_prevention()
✅ test_transaction_savepoint_support()
```

**Coverage Target:** `core/database.py` transaction logic (95%+)

---

## Expected Results

### Success Criteria

```
✅ All 74 tests passing
✅ Coverage ≥90% for:
   - core/database.py
   - core/connector.py
   - models/ (all entity models)
   - validators/
✅ No connection errors
✅ No transaction rollbacks on valid operations
✅ All migrations validated (001-005)
✅ All constraints enforced
✅ Vector operations working
```

### Test Execution Output

```bash
$ pytest tests/integration/ -v
collected 74 items

tests/integration/test_database_connection.py::test_async_engine_created PASSED
tests/integration/test_database_connection.py::test_pgvector_extension_loaded PASSED
tests/integration/test_database_connection.py::test_uuid_ossp_extension_loaded PASSED
...
tests/integration/test_transactions.py::test_transaction_deadlock_prevention PASSED

================= 74 passed in 45.3s =================

Coverage Report:
core/database.py     95%
core/connector.py    92%
models/skill.py      98%
models/agent.py      91%
models/job_role.py   89%
validators/          87%

================== SUCCESS ✅ ===================
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pytest'"

**Solution:** Activate virtual environment and reinstall dependencies
```bash
source /workspaces/WAOOAW/.venv/bin/activate
pip install -r requirements.txt
```

### Issue: "ConnectionRefusedError: Cannot connect to database"

**Solution:** testcontainers will start PostgreSQL automatically. Ensure:
- Docker is running (if using Docker)
- PostgreSQL 15 image available
- Or ensure testcontainers can download it

```bash
# Manual start if needed
docker run -d -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:15-alpine
```

### Issue: "TimeoutError: Database container failed to start"

**Solution:** testcontainers needs more time or Docker resources
```bash
# Increase timeout in conftest.py:
engine = create_async_engine(
    test_db_url,
    connect_args={"connect_timeout": 30}  # Increase from 10
)
```

### Issue: "pgvector extension not available"

**Solution:** Ensure PostgreSQL image includes pgvector
```bash
# testcontainers uses postgres:15-alpine which may need pgvector installed
# Alternative: Use custom docker image with pgvector pre-installed
```

### Issue: "AssertionError: Expected ≥90% coverage, got XX%"

**Solution:** Review uncovered code and add tests:
```bash
# Generate detailed coverage report
pytest tests/integration/ --cov=core --cov=models --cov-report=html

# Open htmlcov/index.html to see uncovered lines
open htmlcov/index.html

# Add tests for uncovered branches
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r src/Plant/BackEnd/requirements.txt

      - name: Run integration tests
        run: |
          cd src/Plant/BackEnd
          pytest tests/integration/ \
            --cov=core,models,validators \
            --cov-fail-under=90 \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Performance Baseline

### Expected Test Execution Times

```
test_database_connection.py       ~8s   (12 tests, serial)
test_alembic_migrations.py        ~15s  (11 tests, migration heavy)
test_rls_policies.py              ~6s   (11 tests, constraint checks)
test_pgvector_functionality.py    ~4s   (9 tests, vector ops)
test_audit_trail.py               ~5s   (10 tests, audit ops)
test_connector_pooling.py          ~12s  (11 tests, concurrency)
test_transactions.py               ~10s  (10 tests, ACID)

Total: ~60s for all 74 tests (serial execution)
       ~20-30s with parallel execution (pytest-xdist)
```

### Resource Requirements

```
Memory:   512 MB (testcontainers + Python + PostgreSQL)
Disk:     1 GB (test database ephemeral storage)
CPU:      2 cores (concurrent connection tests)
Network:  Docker registry access (image download)
```

---

## Next Steps

Once all 74 tests pass with ≥90% coverage:

1. **Phase 2 Genesis Webhook** (Sprint 2)
   - Implement event stream processor
   - Add webhook event handlers
   - Integrate with audit trail

2. **Phase 3 Temporal Workflows** (Sprint 3)
   - Workflow definitions and lifecycle
   - Worker process management
   - Workflow state machine

3. **GCP Infrastructure & CI/CD** (Final)
   - Cloud Run deployment
   - Cloud SQL proxy
   - GitHub Actions pipeline

---

## Quick Reference

### Run All Tests
```bash
pytest tests/integration/ -v
```

### Run with Coverage
```bash
pytest tests/integration/ --cov=core,models --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/integration/test_database_connection.py -v
```

### Run Single Test
```bash
pytest tests/integration/test_database_connection.py::test_async_engine_created -v
```

### Run with Markers
```bash
# Assuming markers defined in pytest.ini
pytest tests/integration/ -m "not slow" -v
```

### Generate Report
```bash
pytest tests/integration/ --html=report.html --self-contained-html
```

---

**Last Updated:** 2024-01-14  
**Total Tests:** 74 async integration tests  
**Coverage Target:** ≥90%  
**Test Framework:** pytest + pytest-asyncio + testcontainers
