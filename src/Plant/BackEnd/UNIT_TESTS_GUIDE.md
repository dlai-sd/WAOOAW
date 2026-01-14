# Unit Tests Guide - WAOOAW Plant Backend

**Document:** Unit Tests Execution & Coverage Guide  
**Date:** 2026-01-14  
**Framework:** pytest + pytest-cov  
**Coverage Target:** ≥90% (core, models, validators, security)  
**Status:** Ready for Execution  

---

## Overview

Unit tests validate individual components in isolation without external dependencies. The Plant backend uses pytest with markers for test categorization.

### Test Categories

| Category | Marker | Examples | Run Command |
|----------|--------|----------|------------|
| **Unit Tests** | `@pytest.mark.unit` | BaseEntity, crypto, validators | `pytest -m unit` |
| **Integration Tests** | `@pytest.mark.integration` | DB, API endpoints | `pytest -m integration` |
| **Performance Tests** | `@pytest.mark.performance` | Load, SLA validation | `pytest -m performance` |
| **Security Tests** | `@pytest.mark.security` | Cryptography, hash chains | `pytest -m security` |

---

## Quick Start

### Run All Unit Tests
```bash
cd /workspaces/WAOOAW/src/Plant/BackEnd

# Activate venv
source /workspaces/WAOOAW/.venv/bin/activate

# Run all unit tests
pytest tests/unit/ -v -m unit

# Run with coverage
pytest tests/unit/ -v -m unit --cov=core,models,validators,security --cov-report=html
```

### Run Specific Test File
```bash
# BaseEntity tests
pytest tests/unit/test_base_entity.py -v

# Cryptography tests
pytest tests/unit/test_cryptography.py -v

# Hash chain tests
pytest tests/unit/test_hash_chain.py -v

# Validator tests
pytest tests/unit/test_validators.py -v
```

### Run Single Test
```bash
pytest tests/unit/test_base_entity.py::test_base_entity_creation -v
```

---

## Unit Test Structure

### 1. BaseEntity Tests (test_base_entity.py)

**Purpose:** Validate 7-section BaseEntity pattern

**Test Coverage:**
```python
✓ test_base_entity_creation() 
  - Identity section (uuid, entity_type, external_id)
  - Lifecycle section (created_at, updated_at, status)
  - Default values correctly set

✓ test_base_entity_versioning()
  - version_hash generation (SHA-256)
  - amendment_history tracking
  - evolution_markers appended

✓ test_base_entity_constitutional_alignment()
  - l0_compliance_status set correctly
  - amendment_alignment validation
  - drift_detector initialized

✓ test_base_entity_audit_trail()
  - append_only marker set
  - hash_chain_sha256 initialized
  - tamper_proof flag set

✓ test_base_entity_relationships()
  - parent_id optional
  - child_ids array managed
  - governance_agent_id tracked

✓ test_base_entity_metadata()
  - tags array handling
  - custom_attributes JSON
  - governance_notes storage

✓ test_base_entity_evolution()
  - evolve() creates new version
  - amendment_history appended
  - timestamp updated
```

**Expected Coverage:** 95%+ for `models/base_entity.py`

### 2. Cryptography Tests (test_cryptography.py)

**Purpose:** Validate RSA-4096 and hashing operations

**Test Coverage:**
```python
✓ test_rsa_keypair_generation()
  - RSA-4096 key generation
  - Private/public key format
  - Key length validation

✓ test_rsa_signing()
  - Data signing with private key
  - RSA-SHA256 signature
  - Deterministic output

✓ test_rsa_verification()
  - Signature verification with public key
  - Valid signature passes
  - Invalid signature fails

✓ test_sha256_hashing()
  - SHA-256 computation
  - Hex digest format
  - Deterministic output

✓ test_hash_chain_creation()
  - Link creation (previous_hash + current_data)
  - SHA-256 hashing
  - Chain integrity

✓ test_key_storage()
  - Google Secret Manager integration
  - Key retrieval
  - Key expiration handling

✓ test_key_rotation()
  - Annual rotation scheduling
  - New key generation
  - Old key archival
```

**Expected Coverage:** 93%+ for `security/cryptography.py`

### 3. Hash Chain Tests (test_hash_chain.py)

**Purpose:** Validate immutable audit trail integrity

**Test Coverage:**
```python
✓ test_hash_chain_initialization()
  - Empty chain creation
  - First hash calculation
  - Chain state validation

✓ test_hash_link_append()
  - New link creation
  - Previous hash validation
  - Chain continuity

✓ test_chain_verification()
  - Full chain validation
  - Link sequence verification
  - Continuity confirmation

✓ test_tamper_detection()
  - Modified entry detection
  - Hash mismatch identification
  - Tampering report

✓ test_amendment_history_tracking()
  - Amendment recording
  - Timestamp preservation
  - Non-repudiation (RSA signature)

✓ test_hash_chain_persistence()
  - Chain storage in database
  - Retrieval integrity
  - No data loss
```

**Expected Coverage:** 96%+ for `security/hash_chain.py`

### 4. Validator Tests (test_validators.py)

**Purpose:** Validate L0/L1 constitutional checks

**Test Coverage:**
```python
✓ test_l0_compliance_validation()
  - L0 Rule 1: Identity uniqueness
  - L0 Rule 2: Immutable created_at
  - L0 Rule 3: Hash chain integrity
  - L0 Rule 4: Constitutional alignment
  - L0 Rule 5: Governance authority

✓ test_l1_entity_validation()
  - Entity-specific L1 rules
  - Skill validation
  - JobRole validation
  - Agent validation

✓ test_constitutional_alignment_check()
  - drift_detector flag
  - Amendment alignment verification
  - Non-repudiation (RSA signature)

✓ test_validator_error_handling()
  - ConstitutionalAlignmentError raised
  - Clear error messages
  - No silent failures

✓ test_custom_validator_rules()
  - Domain-specific validations
  - Business logic checks
  - Field dependency validation
```

**Expected Coverage:** 91%+ for `validators/`

---

## Test Execution Patterns

### Run by Test Category
```bash
# Only unit tests (fast, no dependencies)
pytest -m unit -v

# Only security tests (cryptography, hash chains)
pytest -m security -v

# Exclude slow tests
pytest -m "not slow" -v

# Multiple markers (unit AND security)
pytest -m "unit or security" -v
```

### Generate Coverage Report
```bash
# HTML coverage report
pytest tests/unit/ --cov=core,models,validators,security --cov-report=html

# Terminal coverage summary
pytest tests/unit/ --cov=core,models,validators,security --cov-report=term-missing

# Fail if coverage < 90%
pytest tests/unit/ --cov=core,models,validators,security --cov-fail-under=90
```

### Run with Different Verbosity
```bash
# Verbose (show each test)
pytest tests/unit/ -v

# Very verbose (show test details)
pytest tests/unit/ -vv

# Quiet (show only summary)
pytest tests/unit/ -q
```

---

## Expected Coverage Breakdown

### By Module

| Module | Target | Expected |
|--------|--------|----------|
| `core/config.py` | 90% | 94% |
| `core/database.py` | 90% | 92% |
| `core/exceptions.py` | 90% | 100% |
| `core/security.py` | 90% | 96% |
| `models/base_entity.py` | 90% | 95% |
| `models/skill.py` | 90% | 93% |
| `models/agent.py` | 90% | 91% |
| `security/cryptography.py` | 90% | 93% |
| `security/hash_chain.py` | 90% | 96% |
| `validators/` | 90% | 91% |
| **TOTAL** | **≥90%** | **93%** |

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install -r requirements.txt
```

### Issue: "Coverage below 90%"
```bash
# Generate HTML report to see uncovered lines
pytest --cov=core,models,validators --cov-report=html
open htmlcov/index.html

# Add tests for uncovered branches
# Commit with: "test(plant): increase unit test coverage to 95%"
```

### Issue: "Test hangs or times out"
```bash
# Run with timeout
pytest tests/unit/ --timeout=10

# Or set pytest timeout in pytest.ini:
addopts = --timeout=10
```

### Issue: "Import errors in tests"
```bash
# Ensure PYTHONPATH includes src/Plant/BackEnd
export PYTHONPATH=/workspaces/WAOOAW/src/Plant/BackEnd:$PYTHONPATH

# Or run from correct directory
cd /workspaces/WAOOAW/src/Plant/BackEnd
pytest tests/unit/
```

---

## Best Practices

1. **Unit Tests Only (No External Dependencies)**
   - No database calls in unit tests
   - Mock external services
   - Use fixtures for test data

2. **Fast Execution**
   - Unit tests should complete in <1 second each
   - ~50 unit tests total = <1 minute execution

3. **Clear Test Names**
   - `test_<function>_<scenario>_<expected_result>`
   - Example: `test_base_entity_creation_with_valid_data_succeeds`

4. **Assertions**
   - One assertion per test (or tightly related)
   - Use descriptive assertion messages
   - Example: `assert result.status == "active", "New entity should have active status"`

5. **Documentation**
   - Docstring explaining what's being tested
   - Example: `"""Test that BaseEntity creation sets all 7 sections correctly."""`

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Unit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r src/Plant/BackEnd/requirements.txt
      
      - name: Run unit tests
        run: |
          cd src/Plant/BackEnd
          pytest tests/unit/ -v -m unit --cov=core,models,validators,security --cov-fail-under=90
```

---

## Performance Baseline

**Expected Unit Test Execution Times:**
- test_base_entity.py: ~0.5s (6 tests)
- test_cryptography.py: ~0.8s (7 tests)
- test_hash_chain.py: ~0.6s (6 tests)
- test_validators.py: ~0.5s (5 tests)

**Total:** ~2.4 seconds for all unit tests

---

## Next Steps

1. **Execute unit tests:** `pytest tests/unit/ -v --cov=...`
2. **Achieve 90%+ coverage:** Add tests for uncovered code
3. **Integrate with CI/CD:** GitHub Actions on PR
4. **Setup Sonar Code Quality:** (Future phase)
5. **Load testing:** See LOAD_TESTS_GUIDE.md

---

**Last Updated:** 2026-01-14  
**Status:** Ready for Execution  
**Coverage Target:** ≥90%  
**Framework:** pytest + pytest-cov
