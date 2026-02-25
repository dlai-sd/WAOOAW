# WAOOAW Testing — Epics and Stories

> **Strategy Reference**: [TestingStrategy.md](./TestingStrategy.md)  
> **Last Status Update**: 2026-02-25  
> **Rule**: The progress table below is append-only. Add a new row when a story is completed. Do NOT edit existing rows.

---

## Branch Strategy

This plan is designed for **autonomous agent execution on an isolated branch**, keeping the owner's feature development fully unblocked at all times.

```
main
 ├── feat/testing-infra     ← Agent works here (all E1–E11 stories)
 └── feat/<your-work>       ← Owner works here, unaffected
```

**Why two-phase merging:**

| Phase | What merges | When | Who reviews |
|---|---|---|---|
| Phase 1 | E1 only (`feat/testing-infra` → `main`) | After S1.1–S1.3 complete | Owner — only merge review required |
| Phase 2 | E2–E11 (`feat/testing-infra` → `main`) | After all stories complete | Owner |

**Rationale:**  
E1 is the only epic that touches **shared config files** (`pytest.ini`, `requirements-test.txt`, `package.json`, `docker-compose.test.yml`). Merging E1 to `main` first means every subsequent owner feature branch picks up the test infrastructure automatically via rebase, with zero conflicts. E2–E11 stories are exclusively net-new files (test files, workflow files, scripts) and will never collide with feature work.

**Agent startup instructions:**
```bash
# One-time setup — agent runs this before starting S1.1
git checkout main && git pull origin main
git checkout -b feat/testing-infra
git push -u origin feat/testing-infra
```

All subsequent story commits and pushes target `feat/testing-infra`. After E1 is complete, open a PR to `main`, get owner approval, merge, then continue E2–E11 on the same branch.

---

## Progress Tracker (Append-Only)

| Story | Title | Status | Completed By | Date | Branch/Commit | Remarks |
|---|---|---|---|---|---|---|
| — | *No stories completed yet* | — | — | — | — | — |
| S1.1 | Create docker-compose.test.yml with all test service definitions | ✅ Done | @copilot | 2026-02-25 | copilot/feattesting-infra | `docker compose -f docker-compose.test.yml config` exits 0; all 9 services defined (postgres-test, redis-test, plant-backend-test, cp-backend-test, pp-backend-test, plant-gateway-test, mobile-test, playwright, maestro, locust, zap) |

---

## Execution Rules (Must Read Before Starting Any Story)

1. **Branch**: work exclusively on `feat/testing-infra` — never commit to `main` directly or to any owner feature branch.
2. **Docker only** — every command runs inside a Docker container (`docker compose run`). No `python`, `pip`, `npm`, `npx` on the host or CI runner.
3. **One story at a time** — mark in-progress, implement, run tests, commit, push, then update the progress table above with a new row.
4. **Commit message format**: `test(<scope>): <story-id> <short description>` e.g. `test(infra): S1.1 add docker-compose.test.yml`
5. **After each story**: commit all changed files → push to `feat/testing-infra` → add a row to the progress tracker → proceed to next story.
6. **After E1 completes**: open a PR `feat/testing-infra` → `main`, notify owner, wait for merge before starting E2.
7. **Test coverage at end of each story** — run coverage command specified in the story and record result in the progress table remarks.
8. **No changes to existing workflows** — `waooaw-deploy.yml` and `mobile-playstore-deploy.yml` are read-only. New workflows are separate files.
9. **Regression workflows are manual-trigger only** (`workflow_dispatch`) — never triggered by push or PR.

---

## Epic E1 — Test Infrastructure Foundation

**Goal**: Establish the Docker-based test infrastructure that all subsequent epics depend on.  
**Priority**: Critical — nothing else can proceed without this.

---

### Story S1.1 — Create `docker-compose.test.yml` with all test service definitions

**Acceptance Criteria**:
- File exists at `/workspaces/WAOOAW/docker-compose.test.yml`
- Defines test variants of all backend services (plant, cp, pp, gateway) with `TEST_MODE=true`
- Defines `mobile-test`, `playwright`, `locust`, `zap` services
- All services share a `waooaw-test-network`
- A dedicated `postgres-test` and `redis-test` instance — isolated from local dev stack
- Running `docker compose -f docker-compose.test.yml config` succeeds without errors

**Implementation Steps**:

1. Create `/workspaces/WAOOAW/docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  # ── Infrastructure ────────────────────────────────
  postgres-test:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_USER: waooaw_test
      POSTGRES_PASSWORD: waooaw_test_password
      POSTGRES_DB: waooaw_test_db
    ports: ["5433:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U waooaw_test"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks: [waooaw-test-network]

  redis-test:
    image: redis:7-alpine
    ports: ["6380:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
    networks: [waooaw-test-network]

  # ── Plant BackEnd Test Runner ─────────────────────
  plant-backend-test:
    build:
      context: ./src/Plant/BackEnd
      dockerfile: Dockerfile
      target: test          # or base if no multi-stage yet
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=postgresql+asyncpg://waooaw_test:waooaw_test_password@postgres-test:5432/waooaw_test_db
      - REDIS_URL=redis://redis-test:6379/0
      - JWT_SECRET=test-secret-key
      - SECRET_KEY=test-secret-key
    depends_on:
      postgres-test: {condition: service_healthy}
      redis-test: {condition: service_healthy}
    volumes:
      - ./src/Plant/BackEnd:/app
      - ./main/Foundation/template/financials.yml:/config/financials.yml:ro
    networks: [waooaw-test-network]
    entrypoint: ["python", "-m", "pytest"]

  # ── CP BackEnd Test Runner ────────────────────────
  cp-backend-test:
    build:
      context: ./src/CP/BackEnd
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=postgresql+asyncpg://waooaw_test:waooaw_test_password@postgres-test:5432/waooaw_test_db
      - REDIS_URL=redis://redis-test:6379/0
      - JWT_SECRET=test-secret-key
      - SECRET_KEY=test-secret-key
      - PLANT_BASE_URL=http://plant-backend-test:8001
    depends_on:
      postgres-test: {condition: service_healthy}
    volumes:
      - ./src/CP/BackEnd:/app
    networks: [waooaw-test-network]
    entrypoint: ["python", "-m", "pytest"]

  # ── PP BackEnd Test Runner ────────────────────────
  pp-backend-test:
    build:
      context: ./src/PP/BackEnd
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=postgresql+asyncpg://waooaw_test:waooaw_test_password@postgres-test:5432/waooaw_test_db
      - JWT_SECRET=test-secret-key
      - SECRET_KEY=test-secret-key
      - PLANT_BASE_URL=http://plant-backend-test:8001
    depends_on:
      postgres-test: {condition: service_healthy}
    volumes:
      - ./src/PP/BackEnd:/app
    networks: [waooaw-test-network]
    entrypoint: ["python", "-m", "pytest"]

  # ── Plant Gateway Test Runner ─────────────────────
  plant-gateway-test:
    build:
      context: ./src/Plant/Gateway
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=test
      - PLANT_BACKEND_URL=http://plant-backend-test:8001
      - JWT_SECRET=test-secret-key
    volumes:
      - ./src/Plant/Gateway:/app
    networks: [waooaw-test-network]
    entrypoint: ["python", "-m", "pytest"]

  # ── Mobile Test Runner (Jest) ─────────────────────
  mobile-test:
    image: node:20-alpine
    working_dir: /app
    volumes:
      - ./src/mobile:/app
      - mobile-node-modules:/app/node_modules
    networks: [waooaw-test-network]
    entrypoint: ["npx", "jest"]
    command: ["--runInBand", "--coverage", "--passWithNoTests"]

  # ── Playwright (Web E2E) ──────────────────────────
  playwright:
    image: mcr.microsoft.com/playwright:v1.41.0-jammy
    working_dir: /tests
    volumes:
      - ./tests/e2e/web:/tests
    networks: [waooaw-test-network]
    entrypoint: ["npx", "playwright", "test"]

  # ── Locust (Performance) ──────────────────────────
  locust:
    image: locustio/locust:2.20.1
    volumes:
      - ./tests/performance:/mnt/locust
    networks: [waooaw-test-network]
    entrypoint: ["locust", "-f", "/mnt/locust/locustfile.py"]

  # ── OWASP ZAP (DAST) ─────────────────────────────
  zap:
    image: ghcr.io/zaproxy/zaproxy:stable
    networks: [waooaw-test-network]
    command: ["zap-baseline.py", "-t", "http://plant-gateway-test:8000", "-r", "/zap/wrk/zap-report.html"]
    volumes:
      - ./tests/security/reports:/zap/wrk

networks:
  waooaw-test-network:
    driver: bridge

volumes:
  mobile-node-modules:
```

2. Verify with: `docker compose -f docker-compose.test.yml config`

**Test Coverage Check**: N/A (infrastructure story)  
**Commit**: `test(infra): S1.1 add docker-compose.test.yml with all test services`

---

### Story S1.2 — Extend pytest markers across all service `pytest.ini` files

**Acceptance Criteria**:
- All four Python services have `pytest.ini` (or `pyproject.toml` `[tool.pytest.ini_options]`) with the full marker set
- Markers: `unit`, `api`, `integration`, `e2e`, `performance`, `security`, `property`, `bdd`, `contract`, `smoke`, `regression`
- Running `docker compose -f docker-compose.test.yml run plant-backend-test --co -q` lists tests without warnings about unknown markers
- `pytest --markers` inside each service container shows all markers

**Implementation Steps**:

1. Check which services have a `pytest.ini`:
   ```bash
   find /workspaces/WAOOAW/src -name "pytest.ini" -o -name "pyproject.toml" | grep -v node_modules
   ```

2. For each service **without** a `pytest.ini`, create one at the service root:

```ini
# pytest.ini (CP / PP / Gateway — adapt path)
[pytest]
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = --strict-markers --tb=short --import-mode=importlib
markers =
    unit: Single class/function, fully mocked
    api: Route-level via TestClient
    integration: Real DB or Docker services
    e2e: Full multi-service journey
    performance: Load / latency tests
    security: Security regression
    property: Hypothesis property-based tests
    bdd: pytest-bdd behaviour tests
    contract: Pact consumer/provider tests
    smoke: Minimal stack check (< 30 s)
    regression: Full regression suite
timeout = 300
```

3. Update the **root** `/workspaces/WAOOAW/pytest.ini` to add the new markers to its existing `markers` block.

4. Verify: `docker compose -f docker-compose.test.yml run plant-backend-test --markers`

**Test Coverage Check**: N/A  
**Commit**: `test(infra): S1.2 add full pytest marker set to all service configs`

---

### Story S1.3 — Create local test runner scripts

**Acceptance Criteria**:
- `/workspaces/WAOOAW/scripts/test-web.sh` — runs all web backend test stages via docker compose, accepts `--quick` flag (skips mutation + perf)
- `/workspaces/WAOOAW/scripts/test-mobile.sh` — runs mobile Jest suite via docker compose
- Both scripts are executable and print a pass/fail summary at the end
- Scripts use only `docker compose -f docker-compose.test.yml run ...` — no host tools

**Implementation steps**:

`scripts/test-web.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
QUICK=${1:-""}
DC="docker compose -f docker-compose.test.yml"

echo "=== [S1] Static Analysis ==="
$DC run plant-backend-test ruff check /app && $DC run plant-backend-test mypy /app --ignore-missing-imports
$DC run cp-backend-test ruff check /app && $DC run pp-backend-test ruff check /app

echo "=== [S2] Unit + API Tests ==="
$DC run plant-backend-test pytest src/Plant/BackEnd/tests/unit/ -m "unit or api" --cov=app
$DC run cp-backend-test pytest src/CP/BackEnd/tests/ -m "unit or api" --cov=app
$DC run pp-backend-test pytest src/PP/BackEnd/tests/ -m "unit or api" --cov=app
$DC run plant-gateway-test pytest src/Plant/Gateway/middleware/tests/ -m "unit or api" --cov=app

echo "=== [S3] Integration Tests ==="
$DC run plant-backend-test pytest src/Plant/BackEnd/tests/integration/ -m integration

echo "=== [S4] E2E Tests ==="
$DC run plant-backend-test pytest src/Plant/BackEnd/tests/e2e/ -m e2e

if [[ "$QUICK" != "--quick" ]]; then
  echo "=== [S5] Performance Tests ==="
  $DC run locust --headless -u 50 -r 5 --run-time 60s --html /mnt/locust/report.html

  echo "=== [S6] Security (DAST) ==="
  $DC run zap
fi

echo "=== DONE ==="
```

`scripts/test-mobile.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
DC="docker compose -f docker-compose.test.yml"

echo "=== [M1] Mobile Unit + UI Tests ==="
$DC run mobile-test --runInBand --coverage

echo "=== [M2] Accessibility ==="
$DC run mobile-test --testPathPattern="accessibility" --runInBand

echo "=== DONE ==="
```

**Test Coverage Check**: Run `bash scripts/test-web.sh --quick` — all stages exit 0.  
**Commit**: `test(infra): S1.3 add local test runner scripts`

---

## Epic E2 — Static Analysis Pipeline

**Goal**: Catch bugs, security issues, and type errors before any test runs.

---

### Story S2.1 — Add static analysis tools to all Python service Dockerfiles

**Acceptance Criteria**:
- `ruff`, `mypy`, `bandit`, `safety` are installable in each Python service test container
- Each tool runs to completion via `docker compose -f docker-compose.test.yml run <service>-test <tool> .`
- Bandit produces a JSON report; Safety produces a text report
- No **new** violations are introduced (existing violations are baselined)
- A `tests/static/bandit-baseline.json` file is committed per service to track accepted known issues

**Implementation Steps**:

1. For each Python service Dockerfile, ensure dev/test dependencies include:
   ```
   ruff>=0.3.0
   mypy>=1.8.0
   bandit>=1.7.7
   safety>=3.0.0
   ```
   Add to `requirements-dev.txt` (or `requirements-test.txt`) in each service.

2. Create `src/Plant/BackEnd/tests/static/` folder.

3. Generate baseline (first run — accept existing issues):
   ```bash
   docker compose -f docker-compose.test.yml run plant-backend-test \
     bandit -r /app -f json -o /app/tests/static/bandit-baseline.json --exit-zero
   ```

4. Repeat for CP, PP, Gateway.

5. Document run commands in `scripts/static-analysis.sh`.

**Test Coverage Check**: All four `bandit` runs exit 0 against baseline.  
**Commit**: `test(static): S2.1 add ruff/mypy/bandit/safety to all Python service test containers`

---

### Story S2.2 — Add OpenAPI semantic diff (Optic) to Gateway

**Acceptance Criteria**:
- `optic` CLI is available in a Docker container
- Plant Gateway OpenAPI spec is captured at `tests/contracts/plant-gateway-openapi.json`
- Running `docker compose -f docker-compose.test.yml run optic-diff` compares current spec vs baseline and exits non-zero on breaking changes
- An `optic` Docker service is added to `docker-compose.test.yml`

**Implementation Steps**:

1. Add to `docker-compose.test.yml`:
   ```yaml
   optic:
     image: useoptic/optic:latest
     volumes:
       - ./tests/contracts:/specs
     networks: [waooaw-test-network]
   ```

2. Capture current spec:
   ```bash
   docker compose -f docker-compose.test.yml run plant-gateway-test \
     python -c "from main import app; import json; print(json.dumps(app.openapi()))" \
     > tests/contracts/plant-gateway-openapi.json
   ```

3. Add Optic config `tests/contracts/.optic/config.yml`:
   ```yaml
   ruleset:
     - breaking-changes
   ```

4. Run diff: `docker compose -f docker-compose.test.yml run optic diff /specs/plant-gateway-openapi.json --check`

**Test Coverage Check**: Optic exits 0 on current spec.  
**Commit**: `test(static): S2.2 add Optic OpenAPI semantic diff for Plant Gateway`

---

## Epic E3 — Property-Based Tests (Hypothesis)

**Goal**: Prove that billing, metering, and security invariants hold for any valid input.

---

### Story S3.1 — Hypothesis property tests for Plant BackEnd core invariants

**Acceptance Criteria**:
- New test file: `src/Plant/BackEnd/tests/property/test_usage_ledger_invariants.py`
- New test file: `src/Plant/BackEnd/tests/property/test_trial_billing_invariants.py`
- New test file: `src/Plant/BackEnd/tests/property/test_hash_chain_invariants.py`
- All tagged `@pytest.mark.property`
- Hypothesis runs with at least 100 examples per property (`settings(max_examples=100)`)
- `docker compose -f docker-compose.test.yml run plant-backend-test pytest -m property` passes

**Implementation Steps**:

1. Add `hypothesis>=6.100.0` to `src/Plant/BackEnd/requirements-test.txt`

2. Implement property tests in `tests/property/` — see TestingStrategy.md §3.4 for example patterns.

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run plant-backend-test \
  pytest src/Plant/BackEnd/tests/property/ -m property -v --tb=short
```
**Commit**: `test(property): S3.1 Hypothesis invariant tests for ledger, billing, hash chain`

---

### Story S3.2 — fast-check property tests for Mobile token manager

**Acceptance Criteria**:
- New test file: `src/mobile/__tests__/tokenManager.property.test.ts`
- Tagged with Jest `describe('property', ...)` block
- Verifies: token is always considered expired if `expiresAt < now`; refresh is never called for a fresh token
- `docker compose -f docker-compose.test.yml run mobile-test --testPathPattern="tokenManager.property"` passes

**Implementation Steps**:

1. Add `fast-check` to `src/mobile/package.json` devDependencies.

2. Implement property tests using fast-check — see TestingStrategy.md §3.4 for example patterns.

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run mobile-test \
  --testPathPattern="tokenManager.property" --verbose
```
**Commit**: `test(property): S3.2 fast-check property tests for mobile token manager`

---

## Epic E4 — BDD Feature Specs (pytest-bdd)

**Goal**: Express critical platform journeys as human-readable Gherkin specs that product and QA can review.

---

### Story S4.1 — BDD specs for 7-day trial lifecycle (Plant BackEnd)

**Acceptance Criteria**:
- Feature file: `src/Plant/BackEnd/tests/bdd/features/trial_lifecycle.feature`
- Step definitions: `src/Plant/BackEnd/tests/bdd/test_trial_lifecycle.py`
- Covers: start trial, usage cap, cancel and keep deliverables, auto-expiry
- All scenarios tagged `@pytest.mark.bdd`
- `docker compose -f docker-compose.test.yml run plant-backend-test pytest src/Plant/BackEnd/tests/bdd/ -m bdd` passes

**Implementation Steps**:

1. Add `pytest-bdd>=7.0.0` to `src/Plant/BackEnd/requirements-test.txt`

2. Create feature file and step definitions covering the trial lifecycle scenarios.

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run plant-backend-test \
  pytest src/Plant/BackEnd/tests/bdd/ -m bdd -v
```
**Commit**: `test(bdd): S4.1 Gherkin feature specs for 7-day trial lifecycle`

---

### Story S4.2 — BDD specs for hire wizard flow (CP BackEnd)

**Acceptance Criteria**:
- Feature file: `src/CP/BackEnd/tests/bdd/features/hire_wizard.feature`
- Step definitions: `src/CP/BackEnd/tests/bdd/test_hire_wizard.py`
- Covers: draft, step advance, payment, confirmation, cancellation
- `docker compose -f docker-compose.test.yml run cp-backend-test pytest src/CP/BackEnd/tests/bdd/ -m bdd` passes

**Implementation Steps**:

1. Add `pytest-bdd>=7.0.0` to `src/CP/BackEnd/requirements-test.txt`

2. Create feature file and step definitions for the hire wizard flow.

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run cp-backend-test \
  pytest src/CP/BackEnd/tests/bdd/ -m bdd -v
```
**Commit**: `test(bdd): S4.2 Gherkin feature specs for CP hire wizard`

---

## Epic E5 — Contract Tests (Pact)

**Goal**: Prevent breaking API changes between CP/PP/Mobile and Plant Gateway from reaching integration.

---

### Story S5.1 — CP BackEnd consumer Pact definitions

**Acceptance Criteria**:
- New folder: `src/CP/BackEnd/tests/pact/consumer/`
- Pact contracts defined for: `POST /auth/otp/start`, `POST /auth/otp/verify`, `GET /agents`, `POST /hire`
- Running `docker compose -f docker-compose.test.yml run cp-backend-test pytest src/CP/BackEnd/tests/pact/consumer/ -m contract` generates pact JSON files
- Pact JSON files are committed to the repo

**Implementation Steps**:

1. Add `pact-python>=2.2.0` to `src/CP/BackEnd/requirements-test.txt`

2. Create consumer Pact tests in `src/CP/BackEnd/tests/pact/consumer/`.

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run cp-backend-test \
  pytest src/CP/BackEnd/tests/pact/consumer/ -m contract -v
```
**Commit**: `test(contract): S5.1 CP BackEnd consumer Pact definitions for Plant Gateway`

---

### Story S5.2 — Mobile consumer Pact definitions

**Acceptance Criteria**:
- New folder: `src/mobile/__tests__/pact/`
- Contracts defined for: `POST /auth/otp/start`, `POST /auth/otp/verify`, `GET /agents`, `POST /hire/{id}/confirm`
- Uses `@pact-foundation/pact` npm package (free)
- Running `docker compose -f docker-compose.test.yml run mobile-test --testPathPattern="pact"` generates JSON pact files

**Implementation Steps**:

1. Add `@pact-foundation/pact` to `src/mobile/package.json` devDependencies.

2. Create `src/mobile/__tests__/pact/plantGateway.pact.test.ts` with consumer interactions.

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run mobile-test \
  --testPathPattern="pact" --runInBand
```
**Commit**: `test(contract): S5.2 Mobile consumer Pact definitions for Plant Gateway`

---

### Story S5.3 — Plant Gateway provider Pact verification

**Acceptance Criteria**:
- New folder: `src/Plant/Gateway/tests/pact/provider/`
- Provider verification reads pact files from `tests/contracts/pacts/`
- Running `docker compose -f docker-compose.test.yml run plant-gateway-test pytest -m contract` verifies all consumer pacts
- Any breaking change to Plant Gateway routes causes this test to fail

**Implementation Steps**:

1. Add `pact-python>=2.2.0` to `src/Plant/Gateway/requirements-test.txt`

2. Create provider verification test in `src/Plant/Gateway/tests/pact/provider/`.

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run plant-gateway-test \
  pytest src/Plant/Gateway/tests/pact/ -m contract -v
```
**Commit**: `test(contract): S5.3 Plant Gateway provider Pact verification`

---

## Epic E6 — Web E2E (Playwright)

**Goal**: Validate critical user journeys against a fully running Docker stack.

---

### Story S6.1 — Playwright setup + OTP auth journey

**Acceptance Criteria**:
- `tests/e2e/web/` folder created with Playwright config
- `tests/e2e/web/auth/otp_auth.spec.ts` covers: navigate to CP login → enter phone → enter OTP → land on dashboard
- `docker compose -f docker-compose.test.yml run playwright` executes and passes
- Playwright HTML report saved to `tests/e2e/web/reports/`

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run playwright npx playwright test auth/
```
**Commit**: `test(e2e): S6.1 Playwright setup and OTP auth E2E journey`

---

### Story S6.2 — Playwright hire wizard + payment journey

**Acceptance Criteria**:
- `tests/e2e/web/hire/hire_wizard.spec.ts` covers the full hire flow via CP API
- Tests: draft creation → step advance → coupon apply → payment → hire confirmed → trial active

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run playwright npx playwright test hire/
```
**Commit**: `test(e2e): S6.2 Playwright hire wizard and payment E2E journey`

---

### Story S6.3 — Playwright PP agent creation + approval journey

**Acceptance Criteria**:
- `tests/e2e/web/admin/agent_approval.spec.ts` covers PP admin flow: create agent → submit for approval → approve → agent goes live in catalog

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run playwright npx playwright test admin/
```
**Commit**: `test(e2e): S6.3 Playwright PP agent creation and approval E2E journey`

---

## Epic E7 — Mobile E2E (Maestro)

**Goal**: Validate mobile app critical journeys on a real Android emulator.

---

### Story S7.1 — Maestro Docker setup + OTP auth flow

**Acceptance Criteria**:
- `tests/e2e/mobile/` folder with Maestro YAML flows
- `tests/e2e/mobile/auth_otp.yaml` covers: app launch → OTP screen → enter phone → enter code → home screen visible
- Maestro Docker service in `docker-compose.test.yml` is correctly configured
- Flow runs successfully in CI (GitHub Actions with Android emulator)

**Test Coverage Check**: Flow passes in Android emulator; record screenshot artefacts path.  
**Commit**: `test(e2e): S7.1 Maestro Docker setup and OTP auth flow`

---

### Story S7.2 — Maestro hire agent flow

**Acceptance Criteria**:
- `tests/e2e/mobile/hire_flow.yaml` covers: browse agents → tap agent → tap Hire → complete wizard → confirm

**Test Coverage Check**: Flow passes; commit Maestro HTML report artefact.  
**Commit**: `test(e2e): S7.2 Maestro mobile hire agent E2E flow`

---

## Epic E8 — Performance Baseline (Locust)

**Goal**: Establish measurable performance thresholds and prevent regressions under load.

---

### Story S8.1 — Locust setup + Plant Gateway load test

**Acceptance Criteria**:
- `tests/performance/locustfile.py` defines `AuthUser` and `BrowseUser` behaviour classes
- Locust service runs headless: 50 users, 5 ramp-up/s, 60 s run
- p95 response time < 500 ms for auth endpoints
- HTML report saved to `tests/performance/reports/`

**Test Coverage Check**:
```bash
docker compose -f docker-compose.test.yml run locust \
  --headless -u 50 -r 5 --run-time 60s \
  --html /mnt/locust/reports/report.html
```
**Commit**: `test(perf): S8.1 Locust load test for Plant Gateway`

---

### Story S8.2 — Trial concurrency load test

**Acceptance Criteria**:
- `tests/performance/trial_concurrency.py` simulates 100 concurrent trial starts
- Zero data integrity errors
- Completes within 30 s

**Test Coverage Check**: 100 users, 0 errors, DB has exactly 100 trial records.  
**Commit**: `test(perf): S8.2 trial concurrency load test`

---

## Epic E9 — Security Pipeline

**Goal**: Automated detection of code-level and runtime security issues.

---

### Story S9.1 — Bandit + Safety + Semgrep for all Python services

**Acceptance Criteria**:
- `scripts/security-scan.sh` runs Bandit, Safety, and Semgrep via Docker for all four Python services
- All three tools produce JSON/HTML reports saved to `tests/security/reports/`
- Bandit high-severity findings exit with code 1

**Test Coverage Check**: All scans complete; no HIGH findings in baseline.  
**Commit**: `test(security): S9.1 Bandit, Safety, Semgrep scans via Docker`

---

### Story S9.2 — OWASP ZAP DAST against Plant Gateway

**Acceptance Criteria**:
- ZAP baseline scan runs against `plant-gateway-test` container
- HTML report saved to `tests/security/reports/zap-report.html`
- ZAP exits 1 on MEDIUM or HIGH findings

**Test Coverage Check**: ZAP completes; report reviewed; no unaccepted MEDIUM+ findings.  
**Commit**: `test(security): S9.2 OWASP ZAP DAST baseline scan for Plant Gateway`

---

## Epic E10 — Mutation Testing

**Goal**: Prove that existing tests detect real faults — not just execute code.

---

### Story S10.1 — mutmut for Plant BackEnd auth and billing modules

**Acceptance Criteria**:
- `mutmut` runs against `src/Plant/BackEnd/services/otp_service.py` and `services/trial_service.py`
- Mutation score ≥ 80%
- HTML report saved to `tests/mutation/reports/plant-mutmut.html`

**Test Coverage Check**: Mutation score ≥ 80%.  
**Commit**: `test(mutation): S10.1 mutmut mutation tests for Plant otp_service and trial_service`

---

### Story S10.2 — Stryker for Mobile auth service

**Acceptance Criteria**:
- Stryker configured for `src/mobile/src/services/auth.service.ts` and `tokenManager.service.ts`
- Mutation score ≥ 80%
- HTML report saved to `tests/mutation/reports/mobile-stryker/`

**Test Coverage Check**: Mutation score ≥ 80%.  
**Commit**: `test(mutation): S10.2 Stryker mutation tests for mobile auth and token manager`

---

## Epic E11 — Regression Workflows (GitHub Actions)

**Goal**: Two independent, manually-triggered regression workflows that run the full test suite via Docker.

---

### Story S11.1 — `waooaw-regression.yml` (Web Backend)

**Acceptance Criteria**:
- New file: `.github/workflows/waooaw-regression.yml`
- Trigger: `workflow_dispatch` only — with `scope` input (`full` / `quick`)
- Does NOT modify `waooaw-deploy.yml` or `mobile-playstore-deploy.yml`
- Stages: static → unit+api → property+bdd → integration → contract → e2e → performance (full only) → security → report

**Test Coverage Check**: Trigger workflow with `scope=quick` — all jobs pass.  
**Commit**: `test(ci): S11.1 waooaw-regression.yml — manual web backend regression workflow`

---

### Story S11.2 — `mobile-regression.yml`

**Acceptance Criteria**:
- New file: `.github/workflows/mobile-regression.yml`
- Trigger: `workflow_dispatch` only — with `scope` input (`full` / `quick`)
- Does NOT modify `mobile-playstore-deploy.yml`
- Stages: static → unit+ui → accessibility → e2e Maestro (full only) → mutation (full only) → report

**Test Coverage Check**: Trigger with `scope=quick` — static + unit-ui + accessibility jobs pass.  
**Commit**: `test(ci): S11.2 mobile-regression.yml — manual mobile regression workflow`

---

## Quick Reference — All Docker Test Commands

```bash
# Unit + API (Plant)
docker compose -f docker-compose.test.yml run plant-backend-test pytest src/Plant/BackEnd/tests/unit/ -m "unit or api"

# Unit + API (CP)
docker compose -f docker-compose.test.yml run cp-backend-test pytest src/CP/BackEnd/tests/ -m "unit or api"

# Unit + API (PP)
docker compose -f docker-compose.test.yml run pp-backend-test pytest src/PP/BackEnd/tests/ -m "unit or api"

# Property-based (Plant)
docker compose -f docker-compose.test.yml run plant-backend-test pytest -m property

# BDD (Plant)
docker compose -f docker-compose.test.yml run plant-backend-test pytest -m bdd

# Integration (Plant)
docker compose -f docker-compose.test.yml run plant-backend-test pytest -m integration

# Mobile Unit + UI
docker compose -f docker-compose.test.yml run mobile-test --runInBand --coverage

# Web E2E
docker compose -f docker-compose.test.yml run playwright npx playwright test

# Mobile E2E
docker compose -f docker-compose.test.yml run maestro maestro test tests/e2e/mobile/auth_otp.yaml

# Performance
docker compose -f docker-compose.test.yml run locust --headless -u 50 -r 5 --run-time 60s

# Security (SAST)
bash scripts/security-scan.sh

# DAST
docker compose -f docker-compose.test.yml run zap

# Mutation (Plant)
docker compose -f docker-compose.test.yml run plant-backend-test mutmut run

# Mutation (Mobile)
docker compose -f docker-compose.test.yml run mobile-test npx stryker run

# Full web regression (local)
bash scripts/test-web.sh

# Quick web regression
bash scripts/test-web.sh --quick

# Mobile regression
bash scripts/test-mobile.sh
```
