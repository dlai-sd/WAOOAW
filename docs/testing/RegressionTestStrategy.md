# WAOOAW Regression Test Strategy

> **Version**: 1.0  
> **Date**: 2025-01  
> **Status**: Approved for implementation  

---

## Overview

WAOOAW consists of four independently deployable components:

| Component | Tech | Location |
|---|---|---|
| **CP BackEnd** | FastAPI (Python) | `src/CP/BackEnd/` |
| **PP BackEnd** | FastAPI (Python) | `src/PP/BackEnd/` |
| **Plant BackEnd + Gateway** | FastAPI + Sanic (Python) | `src/Plant/` |
| **Mobile** | React Native / Expo | `src/mobile/` |

Regression testing spans all four tiers to protect against regressions introduced during feature development, dependency upgrades, or infrastructure changes.

---

## Regression Tier Model

### T0 — Pre-Commit Smoke (< 2 min)

**Goal**: Block broken commits from CI pipeline entry.

| Check | Tooling | Target |
|---|---|---|
| Lint + type check | ruff / mypy (Python), ESLint / tsc (mobile) | All files changed in PR |
| Unit test subset (smoke) | pytest -m smoke / jest --testPathPattern | Tests tagged `smoke` |
| Build passes | `docker compose build --no-cache` | All services |

**Trigger**: every `git push` / pre-commit hook + PR opened.

---

### T1 — Functional Regression (< 15 min)

**Goal**: No existing API contract or business rule broken.

#### CP BackEnd
| Suite | File(s) | What it guards |
|---|---|---|
| Auth routes | `test_auth.py`, `test_jwt.py`, `test_jwt_advanced.py` | Login, token issue/refresh |
| Google OAuth | `test_google_oauth.py`, `test_google_oauth_integration.py` | OAuth code-exchange flow |
| OTP login | `test_cp_otp_login_routes.py`, `test_cp_otp_routes.py` | CP OTP start/verify |
| Registration | `test_cp_registration_routes.py` | New CP user signup |
| 2FA | `test_2fa_totp.py` | TOTP enrol/verify |
| Hire wizard | `test_hire_wizard_routes.py` | Draft, confirm, cancel hire |
| Payments | `test_payments_razorpay_routes.py`, `test_payments_coupon_routes.py`, `test_payments_config_routes.py` | Razorpay order + coupon validation |
| Subscriptions | `test_subscriptions_routes.py` | Subscribe, upgrade, cancel |
| Proxying | `test_proxy.py`, `test_hired_agents_proxy.py` | CP → Plant forwarding |
| Invoices / Receipts | `test_invoices_routes.py`, `test_receipts_routes.py` | Billing document retrieval |
| Trading | `test_trading_routes.py`, `test_trading_strategy_routes.py` | Delta Exchange order entry |

#### PP BackEnd
| Suite | File(s) | What it guards |
|---|---|---|
| Admin auth | `test_pp_admin_auth.py` | PP login/token |
| Agents lifecycle | `test_agents_routes.py`, `test_agent_setup_routes.py`, `test_agent_seeding_gating.py` | Create/update/publish agents |
| Approvals | `test_approval_routes.py` | Agent approval gate |
| Genesis | `test_genesis_routes.py` | First-time platform bootstrap |
| Plant client | `test_plant_client.py` | PP → Plant HTTP client |

#### Plant BackEnd
| Suite | File(s) | What it guards |
|---|---|---|
| OTP auth | `tests/unit/test_auth_otp.py`, `tests/unit/test_auth_register.py`, `tests/unit/test_auth_validate.py` | Mobile auth endpoints |
| Trials | `tests/unit/test_trial_service.py`, `tests/unit/test_trial_models.py`, `tests/unit/test_trial_schemas.py` | 7-day trial lifecycle |
| Usage metering | `tests/unit/test_usage_events.py`, `tests/unit/test_usage_ledger.py`, `tests/unit/test_metering_trial_caps.py` | Metering correctness |
| Hash chain | `tests/unit/test_hash_chain.py` | Audit integrity |
| Payments | `tests/unit/test_payments_*.py` | Payment record handling |
| Risk engine | `tests/unit/test_risk_engine*.py` | Delta Exchange position limits |
| Gateway middleware | `Gateway/middleware/tests/test_auth.py`, `test_budget.py`, `test_rbac.py`, `test_policy.py`, `test_proxy.py`, `test_error_handler.py` | Request auth, budgeting, routing |

#### Mobile
| Suite | File(s) | What it guards |
|---|---|---|
| Auth screens | `SignInScreen.test.tsx`, `SignUpScreen.test.tsx`, `OTPVerificationScreen.test.tsx` | Auth UI flows |
| Auth services | `auth.service.test.ts`, `googleAuth.service.test.ts`, `registration.service.test.ts` | Service-layer API calls |
| Token manager | `tokenManager.service.test.ts` | JWT storage/refresh |
| Navigation | `RootNavigator.test.tsx`, `navigation.test.ts` | Auth → app routing |
| API client | `apiClient.test.ts`, `api.config.test.ts` | HTTP client config |
| Hire flow | `hireConfirmationScreen.test.tsx`, `hireWizardScreen.test.tsx` | Hire wizard mobile UI |
| Agents | `agentCard.test.tsx`, `agentDetailScreen.test.tsx`, `agentService.test.ts` | Agent discovery |

**Trigger**: every PR targeting `develop` or `main`; and every merge to `develop`.

---

### T2 — Integration & Visual Regression (< 30 min)

**Goal**: Cross-service contracts hold; UI does not visually break.

| Area | Tooling | Tests |
|---|---|---|
| CP ↔ Plant integration | pytest + httpx against live docker-compose | `tests/test_plant_gateway_openapi.py`, `test_local_compose_auth_config.py` |
| Middleware parity | pytest | `tests/test_gateway_middleware_parity.py` |
| DB migrations | pytest + Alembic | `Plant/BackEnd/tests/integration/test_alembic_migrations.py` |
| RLS policies | pytest + Postgres | `tests/integration/test_rls_policies.py` |
| Social integrations | pytest mocked | `test_facebook_integration.py`, `test_instagram_integration.py`, `test_whatsapp_integration.py`, `test_youtube_integration.py` |
| Mobile UI visual | Detox (target) or Percy snapshot | `mobile/__tests__/integration/` |
| Accessibility | jest-axe | `mobile/__tests__/accessibility.test.ts` |

**Trigger**: merge to `develop`; nightly on `main`.

---

### T3 — E2E & Performance (< 60 min, parallelised)

**Goal**: Critical user journeys work end-to-end; system handles load.

#### E2E Journeys (Plant BackEnd)
| Journey | File |
|---|---|
| Customer signup → trial start → hire approval | `test_e2e_approval_gate.py` |
| Trial expires → auto-end processing | `test_e2e_trial_limits.py` |
| Full marketing campaign workflow | `test_e2e_marketing_workflow.py` |
| Multi-agent concurrent session | `test_e2e_multi_agent.py` |
| Delta Exchange trading workflow | `test_e2e_trading_workflow.py` |
| Error recovery & retry | `test_e2e_error_recovery.py` |

#### Performance Gates
| Test | File | Pass threshold |
|---|---|---|
| API throughput | `tests/performance/test_api_load.py` | p95 < 500 ms at 50 rps |
| DB query speed | `tests/performance/test_database_performance.py` | p99 < 100 ms per query |
| Trial concurrency | `tests/performance/test_trial_load.py` | 100 simultaneous trials, no data loss |

#### Security Gates
| Test | File | Pass criterion |
|---|---|---|
| Credential encryption | `tests/security/test_credential_encryption.py` | Secrets never in plaintext logs |
| Security regression | `tests/security/test_security_regression.py` | No known CVE patterns |

**Trigger**: before any production release tag; weekly scheduled runs.

---

## GitHub Actions Integration

```
┌──────────────────────────────────────────────────────────────────────┐
│  on: push / pull_request                                             │
│                                                                      │
│  T0-smoke (2 min)  ─────────────────────────────────┐               │
│      lint + mypy + tsc + build                       │ gate          │
│                                                      ▼               │
│  T1-functional (15 min, parallel matrix)  ──────────┐               │
│      [python-cp] [python-pp] [python-plant] [jest]   │ gate          │
│                                                      ▼               │
│  T2-integration (30 min)  ──────────────────────────┐               │
│      docker-compose up + API contract tests          │ gate          │
│                                                      ▼               │
│  on: tag v*.*.*  ─────────────────────────────────── ▼              │
│  T3-e2e-perf (60 min, manual approval before prod)                   │
└──────────────────────────────────────────────────────────────────────┘
```

### Recommended workflow files

| File | Contents |
|---|---|
| `.github/workflows/ci.yml` | T0 + T1 on every PR |
| `.github/workflows/integration.yml` | T2 on merge to `develop` |
| `.github/workflows/release.yml` | T3 on release tag, gated by manual approval |
| `.github/workflows/nightly.yml` | T2 + T3 on schedule (`0 1 * * *` UTC) |

---

## Coverage Targets

| Component | Minimum | Target |
|---|---|---|
| Plant BackEnd (unit) | 80% | 90% |
| CP BackEnd (unit) | 80% | 85% |
| PP BackEnd (unit) | 75% | 85% |
| Mobile (Jest) | 70% | 80% |
| Critical auth paths (all) | 95% | 95% |

Run coverage locally:

```bash
# Plant BackEnd
docker compose run backend pytest --cov=app --cov-report=html

# CP BackEnd
docker compose run cp-backend pytest --cov=app --cov-report=html

# Mobile
cd src/mobile && npx jest --coverage
```

---

## Branch Protection Rules

| Branch | Required checks before merge |
|---|---|
| `main` | T0 + T1 all services, T2 integration, PR review (1 approver) |
| `develop` | T0 + T1 all services |
| `feat/*` | T0 smoke only |

---

## Known Gaps & Backlog

| Gap | Priority | Suggested test |
|---|---|---|
| Mobile E2E (Detox) for hire flow | High | `mobile/e2e/hireAgent.e2e.ts` |
| Mobile E2E for auth OTP v mobile | High | `mobile/e2e/authOtp.e2e.ts` |
| PP ↔ Plant contract test | Medium | `tests/test_pp_plant_contract.py` |
| Payment webhook replay | Medium | `CP/BackEnd/tests/test_payments_webhook_replay.py` |
| Visual regression snapshots | Low | Percy / Storybook integration |
| DAST scan in T3 | Low | OWASP ZAP in release workflow |

---

## Running the Full Regression Suite Locally

```bash
# 1. Start all services
docker compose -f docker-compose.local.yml up -d

# 2. T1 Python (all services)
docker compose run plant-backend pytest src/Plant/BackEnd/tests/unit/ src/Plant/BackEnd/tests/middleware/ -v
docker compose run cp-backend pytest src/CP/BackEnd/tests/ -v
docker compose run pp-backend pytest src/PP/BackEnd/tests/ -v

# 3. T1 Mobile
cd src/mobile && npx jest --runInBand

# 4. T2 Cross-service
pytest tests/ -v

# 5. T3 E2E (requires full stack)
docker compose run plant-backend pytest src/Plant/BackEnd/tests/e2e/ -v
```

---

*This document should be updated whenever a new service, integration, or critical user journey is added to the platform.*
