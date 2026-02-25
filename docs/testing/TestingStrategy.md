# WAOOAW Testing Strategy and Tooling

> **Version**: 1.0  
> **Date**: 2026-02  
> **Author**: Test Architecture Review  
> **Status**: Approved — implementation tracked in [TestingEpics.md](./TestingEpics.md)

---

## 1. Platform Context

WAOOAW is a multi-service AI agent marketplace with four independently deployable components:

| Component | Technology | Role |
|---|---|---|
| **Plant BackEnd** | Python / FastAPI | Core agent marketplace engine, trials, billing, metering |
| **Plant Gateway** | Python / Sanic | API gateway — auth, RBAC, rate-limit, proxy |
| **CP BackEnd** | Python / FastAPI | Customer portal — hire wizard, payments, subscriptions |
| **PP BackEnd** | Python / FastAPI | Provider portal — agent management, approvals |
| **Mobile** | React Native / Expo | iOS + Android customer app |

All services run in Docker. **No virtualenv is used** — all test execution happens inside Docker containers.

---

## 2. Guiding Principles

1. **Zero-cost tooling** — every tool selected is free and open-source.
2. **Docker-only execution** — tests run inside containers; no host-level Python or Node environments.
3. **Separate regression trigger** — regression suites are manual `workflow_dispatch` batches, fully decoupled from the two existing deploy workflows (`waooaw-deploy.yml`, `mobile-playstore-deploy.yml`).
4. **Mobile and Web regression are independent** — triggered separately, fail independently.
5. **Tests as living documentation** — BDD specs and property-based invariants describe platform behaviour in plain language.
6. **Shift left** — static analysis and unit tests run on every commit; heavy suites run on-demand.
7. **Prove, don't just cover** — mutation testing validates that tests actually detect faults, not just execute code.

---

## 3. Testing Taxonomy and Tooling

### 3.1 Static Analysis

Catches defects before a single test runs.

| Language | Tool | What it checks | Free |
|---|---|---|---|
| Python | **ruff** | Style, import order, common bugs | ✅ |
| Python | **mypy** | Type correctness across all services | ✅ |
| Python | **Bandit** | Security anti-patterns (hardcoded secrets, SQL injection, etc.) | ✅ |
| Python | **Safety** | Known CVEs in `requirements.txt` dependencies | ✅ |
| Python | **Semgrep** (OSS rules) | Custom and community security rules | ✅ |
| JavaScript/TS | **ESLint** | Style, anti-patterns, React hooks rules | ✅ |
| JavaScript/TS | **tsc --noEmit** | TypeScript type correctness | ✅ |
| All | **openapi-diff / Optic** | Breaking semantic changes in Plant Gateway OpenAPI spec | ✅ |

**Execution**: `docker compose run <service> ruff check .` — no host tools required.

---

### 3.2 Unit Tests (UT)

Isolated function/class tests with mocked I/O.

| Component | Tool | Config |
|---|---|---|
| Plant BackEnd | **pytest** | `pytest.ini` — markers, asyncio_mode=auto |
| CP BackEnd | **pytest** | Per-service `pytest.ini` |
| PP BackEnd | **pytest** | Per-service `pytest.ini` |
| Plant Gateway | **pytest** | Middleware tests |
| Mobile | **Jest** | `jest.config.js` in `src/mobile/` |

**Coverage targets**: 80% minimum, 95% for auth and billing critical paths.

**Execution**:
```bash
docker compose run plant-backend pytest src/Plant/BackEnd/tests/unit/ -m unit
docker compose run cp-backend pytest src/CP/BackEnd/tests/ -m unit
docker compose run mobile-test npx jest --testPathPattern="__tests__" --coverage
```

---

### 3.3 API / Component Tests

Route-level tests via in-process `TestClient` — full HTTP handler without a real server.

| Component | Tool | Scope |
|---|---|---|
| All Python services | **FastAPI TestClient** (httpx) | All routes — success, validation, auth, edge |
| Mobile | **RNTL** | Component render + interaction |

These are the bulk of existing tests (~120 files) — well covered.

---

### 3.4 Property-Based / Semantic Tests

Validates invariants hold for **any** valid input — finds bugs example-based tests miss.

| Component | Tool | Priority domains |
|---|---|---|
| Plant BackEnd | **Hypothesis** (free) | Usage ledger balance, trial billing arithmetic, hash chain integrity, risk engine limits |
| Mobile | **fast-check** (free npm) | Token manager expiry logic, voice command parser |

**Example invariant**: *"For any sequence of usage events totalling X units, the ledger balance must equal X"* — Hypothesis generates thousands of random event sequences to prove this.

**Execution**:
```bash
docker compose run plant-backend pytest src/Plant/BackEnd/tests/property/ -m property
```

---

### 3.5 Behaviour-Driven Tests (BDD)

Human-readable `Given/When/Then` specs as executable tests — bridges product and engineering.

| Component | Tool | Priority journeys |
|---|---|---|
| Plant BackEnd | **pytest-bdd** (free) | Customer signup → trial → hire → billing cycle |
| CP BackEnd | **pytest-bdd** | Hire wizard → payment → subscription |

**Example feature**:
```gherkin
Feature: 7-day trial lifecycle
  Scenario: Customer starts trial and keeps deliverables on cancel
    Given a registered customer
    When they hire an agent and start a 7-day trial
    And they cancel on day 3
    Then the trial is marked cancelled
    And all deliverables remain accessible
```

**Execution**:
```bash
docker compose run plant-backend pytest src/Plant/BackEnd/tests/bdd/ --gherkin-terminal-reporter
```

---

### 3.6 Integration Tests

Real database, real Redis, multiple services wired through Docker Compose.

| Scope | Tool | Target |
|---|---|---|
| Plant DB layer | **pytest + real Postgres** | Migrations, RLS, repo CRUD, pgvector |
| Social integrations | **pytest + httpx mocks** | Facebook, Instagram, WhatsApp, YouTube |
| CP↔Plant | **pytest + Docker network** | Auth proxy, hire forwarding |
| PP↔Plant | **pytest + Docker network** | Agent seeding, approval flow |

**Execution**:
```bash
docker compose -f docker-compose.local.yml up -d postgres redis
docker compose run plant-backend pytest src/Plant/BackEnd/tests/integration/
```

---

### 3.7 Contract Tests

Prevents breaking API changes between services without runtime discovery.

| Consumer | Provider | Tool |
|---|---|---|
| CP BackEnd | Plant Gateway | **Pact** (free OSS) |
| PP BackEnd | Plant Gateway | **Pact** |
| Mobile | Plant Gateway | **Pact** |

**How it works**: Each consumer defines its expected request/response shape as a Pact file. The provider verifies these Pacts on every push — a breaking change is caught before integration.

**Execution**:
```bash
docker compose run cp-backend pytest tests/pact/consumer/  # generate pacts
docker compose run plant-gateway pytest tests/pact/provider/  # verify pacts
```

---

### 3.8 End-to-End Tests

#### 3.8.1 Web E2E (CP, PP, Gateway, Plant)

Full user journey through the deployed stack using **Playwright** (free, open-source).

| Journey | Services involved |
|---|---|
| Customer register → OTP → hire → trial start | Mobile auth → Plant Gateway → Plant BackEnd |
| Hire wizard → payment → invoice → receipt | CP → Plant Gateway → Plant BackEnd |
| PP admin → create agent → approve → goes live | PP → Plant Gateway → Plant BackEnd |
| Marketing campaign → approval → analytics | PP + CP + Plant |

**Execution**:
```bash
docker compose -f docker-compose.test.yml run playwright npx playwright test
```

#### 3.8.2 Mobile E2E

Real device/simulator journeys using **Maestro** (free, YAML-driven, no boilerplate).

| Journey | File |
|---|---|
| OTP auth flow (register → OTP → home) | `mobile/e2e/auth_otp.yaml` |
| Hire an agent | `mobile/e2e/hire_flow.yaml` |
| Browse + search agents | `mobile/e2e/discover.yaml` |

**Execution** (Android emulator in CI):
```bash
docker compose run maestro maestro test mobile/e2e/auth_otp.yaml
```

---

### 3.9 Performance Tests

**Locust** (free, Python-native) — defines user behaviour as code, generates HTML reports.

| Suite | Target | Pass threshold |
|---|---|---|
| API load | Plant Gateway — auth + hire endpoints | p95 < 500 ms at 50 rps |
| DB performance | Direct Plant BackEnd DB queries | p99 < 100 ms |
| Trial concurrency | 100 simultaneous trial starts | Zero data loss |

**Execution**:
```bash
docker compose run locust locust -f tests/performance/locustfile.py --headless -u 50 -r 5 --run-time 60s
```

---

### 3.10 Security Tests

| Tool | Type | Scope |
|---|---|---|
| **Bandit** | SAST | All Python source — run in static stage |
| **Safety** | Dependency CVE | All `requirements.txt` |
| **Semgrep** (free OSS rules) | SAST | Custom rules for WAOOAW patterns |
| **OWASP ZAP** (free) | DAST | Plant Gateway running in Docker — injection, header, auth attacks |
| Existing `tests/security/` | Regression | Credential encryption, known-attack patterns |

**DAST Execution**:
```bash
docker compose run zap zap-baseline.py -t http://plant-gateway:8000 -r zap-report.html
```

---

### 3.11 Mutation Testing

Proves tests detect faults — not just execute code.

| Component | Tool | Scope | Cadence |
|---|---|---|---|
| Plant BackEnd (auth + billing) | **mutmut** (free) | `services/otp_service.py`, `services/trial_service.py`, `utils/usage_ledger.py` | Weekly |
| Mobile (auth service) | **Stryker** (free) | `auth.service.ts`, `tokenManager.service.ts` | Weekly |

**Execution**:
```bash
docker compose run plant-backend mutmut run --paths-to-mutate src/Plant/BackEnd/services/
docker compose run mobile-test npx stryker run
```

---

### 3.12 Accessibility Tests

| Tool | Scope | Execution |
|---|---|---|
| **jest-axe** (free) | All mobile screens | `npx jest accessibility.test.ts` |
| **axe-core** via Playwright | CP/PP web UI | `playwright test accessibility/` |

---

## 4. Regression Batch Architecture

Regression suites are **not part of any deploy pipeline**. They are independent `workflow_dispatch` GitHub Actions workflows triggered on demand.

```
┌────────────────────────────────────────────────────────────────────┐
│  EXISTING WORKFLOWS (unchanged)                                    │
│  ├── waooaw-deploy.yml          (deploy CP, Plant, PP, Gateway)    │
│  └── mobile-playstore-deploy.yml (deploy mobile to Play Store)     │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  NEW REGRESSION WORKFLOWS (manual trigger only)                    │
│                                                                    │
│  ├── waooaw-regression.yml      (web: CP + PP + Plant + Gateway)   │
│  │     Stage 1: Static analysis (ruff, mypy, bandit, semgrep)     │
│  │     Stage 2: Unit + API tests (pytest, all services)            │
│  │     Stage 3: Property + BDD tests                               │
│  │     Stage 4: Integration tests (Docker Compose stack)           │
│  │     Stage 5: Contract tests (Pact verify)                       │
│  │     Stage 6: E2E (Playwright against full docker stack)         │
│  │     Stage 7: Performance (Locust)                               │
│  │     Stage 8: Security (Bandit, ZAP)                             │
│  │     Stage 9: Report generation (Allure/HTML)                    │
│  │                                                                  │
│  └── mobile-regression.yml     (mobile: Jest + Maestro)           │
│        Stage 1: Static (ESLint, tsc)                               │
│        Stage 2: Unit + UI tests (Jest, all suites)                 │
│        Stage 3: Accessibility (jest-axe)                           │
│        Stage 4: E2E (Maestro on Android emulator)                  │
│        Stage 5: Mutation (Stryker — auth module only)              │
│        Stage 6: Report generation                                   │
└────────────────────────────────────────────────────────────────────┘
```

### Trigger
Both regression workflows use `workflow_dispatch` with an optional `scope` input:

| Input | Options | Default |
|---|---|---|
| `scope` | `full`, `quick` (skip mutation + perf) | `full` |
| `environment` | `local`, `demo` | `local` |

---

## 5. Docker-Only Execution Model

All test commands use `docker compose run <service> <command>`. No `python`, `npm`, or `npx` runs directly on the host or CI runner.

### Service definitions (in `docker-compose.test.yml`):

| Service name | Base image | Purpose |
|---|---|---|
| `plant-backend-test` | Plant BackEnd Dockerfile | pytest for Plant |
| `cp-backend-test` | CP BackEnd Dockerfile | pytest for CP |
| `pp-backend-test` | PP BackEnd Dockerfile | pytest for PP |
| `mobile-test` | node:20-alpine | Jest + Stryker for Mobile |
| `playwright` | mcr.microsoft.com/playwright | Web E2E |
| `maestro` | mobile-ci/maestro Docker image | Mobile E2E |
| `locust` | locustio/locust | Performance |
| `zap` | ghcr.io/zaproxy/zaproxy:stable | DAST |

---

## 6. Test Markers (pytest)

Add to `pytest.ini` `markers` section:

```ini
markers =
    unit:         Single class/function, fully mocked (existing)
    api:          Route-level via TestClient (existing)
    integration:  Real DB or Docker services (existing)
    e2e:          Full multi-service journey (existing)
    performance:  Load / latency tests (existing)
    security:     Security regression (existing)
    property:     Hypothesis property-based tests (NEW)
    bdd:          pytest-bdd behaviour tests (NEW)
    contract:     Pact consumer/provider tests (NEW)
    mutation:     Mutation test targets (NEW)
    smoke:        < 30 s, minimal stack check (NEW)
    regression:   Full regression suite marker (NEW)
```

---

## 7. Coverage Targets (Final State)

| Component | Current | Target | Critical path target |
|---|---|---|---|
| Plant BackEnd | ~70% | 85% | 95% (auth, billing, metering) |
| CP BackEnd | ~65% | 82% | 95% (auth, payments) |
| PP BackEnd | ~60% | 80% | 90% (agent approval, genesis) |
| Plant Gateway | ~75% | 88% | 95% (auth, RBAC middleware) |
| Mobile | ~65% | 80% | 95% (auth service, token manager) |

---

## 8. Tooling Summary

| Tool | Purpose | License | Docker image |
|---|---|---|---|
| pytest + plugins | Python test runner | MIT | Each service image |
| Jest | JS/TS test runner | MIT | node:20-alpine |
| Hypothesis | Property-based (Python) | MPL-2.0 | Each Python service |
| fast-check | Property-based (JS) | MIT | node:20-alpine |
| pytest-bdd | BDD feature specs (Python) | MIT | Each Python service |
| Pact | Contract testing | MIT | Standalone broker optional |
| Playwright | Web E2E | Apache-2.0 | mcr.microsoft.com/playwright |
| Maestro | Mobile E2E | Apache-2.0 | Maestro Docker |
| Locust | Performance / load | MIT | locustio/locust |
| Bandit | Python SAST | Apache-2.0 | Each Python service |
| Safety | Python CVE scan | MIT | Each Python service |
| Semgrep | Multi-language SAST | LGPL-2.1 | returntocorp/semgrep |
| OWASP ZAP | DAST | Apache-2.0 | ghcr.io/zaproxy/zaproxy |
| mutmut | Python mutation | MIT | Each Python service |
| Stryker | JS/TS mutation | Apache-2.0 | node:20-alpine |
| jest-axe | Accessibility | MIT | node:20-alpine |
| ruff | Python linter | MIT | Each Python service |
| mypy | Python type checker | MIT | Each Python service |
| Optic | OpenAPI semantic diff | MIT | useoptic/optic |

**Total additional tooling cost: $0**

---

## 9. Implementation Roadmap

See [TestingEpics.md](./TestingEpics.md) for full epic/story breakdown with execution details.

| Epic | Title | Stories | Priority |
|---|---|---|---|
| E1 | Test Infrastructure Foundation | 3 | Critical |
| E2 | Static Analysis Pipeline | 2 | High |
| E3 | Property-Based Tests | 2 | High |
| E4 | BDD Feature Specs | 2 | Medium |
| E5 | Contract Tests (Pact) | 3 | High |
| E6 | Web E2E (Playwright) | 3 | High |
| E7 | Mobile E2E (Maestro) | 2 | High |
| E8 | Performance Baseline (Locust) | 2 | Medium |
| E9 | Security Pipeline (DAST + SAST) | 2 | High |
| E10 | Mutation Testing | 2 | Medium |
| E11 | Regression Workflows (GitHub Actions) | 2 | Critical |

---

*This document is the authoritative testing strategy for WAOOAW. Tooling choices may be revised only via a documented ADR.*
