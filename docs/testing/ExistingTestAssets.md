# WAOOAW Existing Test Assets

> **Version**: 1.2  
> **Date**: 2026-03-03  
> **Status**: Living document — **update after every iteration PR** (not per epic/story)  

### Test Type Legend

| Type | Meaning |
|---|---|
| **UI** | React component render / interaction test (Jest + RNTL) |
| **UT** | Pure unit test — single class/function in isolation, no real I/O |
| **API** | Route-level test via in-process `TestClient` — tests HTTP handler end-to-end within one service |
| **Integration** | Involves real database, real Docker service, or multiple in-process components |
| **Contract** | Validates cross-service schemas, config parity, or OpenAPI shape |
| **E2E** | Full multi-service user journey from outside |
| **Middleware** | Tests request/response middleware chain in isolation |
| **Performance** | Load / latency measurement against a pass threshold |
| **Security** | Encryption, injection, and known-attack regression checks |
| **Smoke** | Minimal check that the service starts and returns 200 |
| **Accessibility** | axe / ARIA rule checks on rendered screens |

This document catalogues every test file in the repository, its location, tier, type, and purpose. Use it alongside [RegressionTestStrategy.md](./RegressionTestStrategy.md) to understand coverage and identify gaps.

---

## Summary Counts

| Component | Unit/API | Integration | Property/BDD | Contract/E2E/Perf | Total |
|---|---|---|---|---|---|
| Mobile (Jest) | 44 | 1 folder | — | Playwright (web) | ~44+ |
| Plant BackEnd | 93 | 20 | 3+1 BDD | Pact provider, E2E (6), Perf (2), Security | ~127 |
| Plant Gateway | 8 | — | — | Pact provider (1) | ~9 |
| CP BackEnd | 43 | 2 | 1 BDD | Pact consumer | ~47 |
| PP BackEnd | 17 | — | — | — | 17 |
| Cross-service | — | 3 | — | Playwright (3), Maestro (2) | ~8 |
| CP FrontEnd (Vitest) | 21 | — | — | Playwright | ~21 |
| **Total** | | | | | **~269** |

> **Last sync**: PR #840 (CP-SKILLS-2 tracking) + test gaps execution 2026-03-03 + MOBILE-COMP-1 Iteration 1 (2026-03-25). Delta since v1.1 (PR #758): +83 test files/specs + MOBILE-COMP-1 additions.

---

## 1. Cross-Service Tests — `/tests/`

Infrastructure for multi-service tests. Run with: `pytest tests/`

| File | Tier | Type | One-line Purpose |
|---|---|---|---|
| `conftest.py` | — | — | Shared fixtures for cross-service suite |
| `test_gateway_middleware_parity.py` | T2 | Contract | Asserts Plant Gateway middleware files are bit-for-bit identical in both Gateway and BackEnd trees |
| `test_local_compose_auth_config.py` | T2 | Contract | Validates auth service blocks in `docker-compose.local.yml` have all required env vars and port bindings |
| `test_plant_gateway_openapi.py` | T2 | Contract | Boots Plant Gateway and validates its OpenAPI schema and registered routes |
| `docker-compose.test.yml` | — | Docker Compose override for running integration tests in CI |
| `Dockerfile.test` | — | Test container image definition |
| `requirements.txt` | — | Python dependencies for cross-service tests |

---

## 2. Mobile Tests — `src/mobile/__tests__/`

Tooling: **Jest** + **React Native Testing Library**. Run with: `cd src/mobile && npx jest`

### Screen Tests (UI Components)

| File | Tier | Type | One-line Purpose |
|---|---|---|---|
| `App.test.tsx` | T1 | UI | Root `<App/>` mounts without crash, renders expected top-level component |
| `SignInScreen.test.tsx` | T1 | UI | Sign-in form renders, validates inputs, calls auth service on submit |
| `SignUpScreen.test.tsx` | T1 | UI | Sign-up form renders, validates phone/email, calls registration service |
| `OTPVerificationScreen.test.tsx` | T1 | UI | OTP input screen renders, submits code, shows error on wrong OTP |
| `OTPInput.test.tsx` | T1 | UI | Reusable OTP digit-box input component — keypress, paste, backspace |
| `MyAgentsScreen.test.tsx` | T1 | UI | Hired agents list renders, shows empty state, navigates to detail |
| `hireConfirmationScreen.test.tsx` | T1 | UI | Hire confirmation modal shows agent and plan details, confirm/cancel |
| `hireWizardScreen.test.tsx` | T1 | UI | Hire wizard 4-step flow: agent selection, connect platform preflight, goals form, payment form |
| `hireWizardFourSteps.test.tsx` | T1 | UI | 4-step wizard: step labels, preflight guidance card (E1-S2), post-hire navigation to TrialDashboard using real subscription_id |
| `connectorSetupCard.test.tsx` | T1 | UI | ConnectorSetupCard shows preflight guidance, "Setup after trial starts" chip, no fake connected toggle (E1-S2) |
| `NotificationsScreen.test.tsx` | T1 | UI | `resolveNavigationTarget` routing table; `deriveActionableNotifications` derives live alerts from hired-agent data — no demo IDs (E2-S1) |
| `agentCard.test.tsx` | T1 | UI | Agent card renders avatar, name, rating, status badge correctly |
| `agentDetailScreen.test.tsx` | T1 | UI | Agent detail screen loads agent data, shows hire CTA |
| `discoverScreen.test.tsx` | T1 | UI | Discover/browse screen renders agent list, supports search filter |
| `coreScreens.test.tsx` | T1 | UI | Core tab screens (Home, Discover, Account) mount without crash |
| `GoogleSignInButton.test.tsx` | T1 | UI | Google sign-in button renders, triggers OAuth on press |
| `ThemeProvider.test.tsx` | T1 | UI | Theme context provides dark/light tokens to children |
| `safeArea.test.tsx` | T1 | UI | Safe-area-context wrapper applies correct insets on iOS/Android |

### Service Tests (Business Logic)

| File | Tier | Type | One-line Purpose |
|---|---|---|---|
| `auth.service.test.ts` | T1 | UT | `AuthService` — login, logout, token refresh, error paths |
| `googleAuth.service.test.ts` | T1 | UT | `GoogleAuthService` — OAuth token exchange, sign-out before sign-in guard |
| `registration.service.test.ts` | T1 | UT | `RegistrationService` — `POST /auth/otp/start` and `/auth/otp/verify` API calls |
| `apiClient.test.ts` | T1 | UT | Axios instance — base URL, auth header injection, refresh interceptor |
| `api.config.test.ts` | T1 | UT | `API_CONFIG` constants resolve correctly per environment |
| `agentService.test.ts` | T1 | UT | `AgentService` — fetch agents list, search, fetch detail |
| `hiredAgentsService.test.ts` | T1 | UT | `HiredAgentsService` — list hired agents, end hire |
| `tokenManager.service.test.ts` | T1 | UT | `TokenManager` — secure storage read/write, expiry check, refresh |
| `razorpay.service.test.ts` | T1 | UT | `RazorpayService` — order creation, checkout launch, webhook handling |

### Store & Hook Tests

| File | Tier | Type | One-line Purpose |
|---|---|---|---|
| `authStore.test.ts` | T1 | UT | Zustand auth store — state transitions for login, logout, token update |
| `agentHooks.test.tsx` | T1 | UT | `useAgents` hook — data fetching, loading/error states |
| `hiredAgentsHooks.test.tsx` | T1 | UT | `useHiredAgents` hook — list, refetch, optimistic updates |
| `useGoogleAuth.test.ts` | T1 | UT | `useGoogleAuth` hook — triggers signOut before signIn (D2 fix) |
| `useRazorpay.test.ts` | T1 | UT | `useRazorpay` hook — payment initiation, success/failure callbacks |

### Utility & Infrastructure Tests

| File | Tier | Type | One-line Purpose |
|---|---|---|---|
| `navigation.test.ts` | T1 | UI | `RootNavigator` respects auth state; asserts `HireWizard` is registered in DiscoverNavigator and deep-link config is aligned (E1-S1) |
| `RootNavigator.test.tsx` | T1 | UI | Root navigator renders correct stack based on auth store state |
| `oauth.config.test.ts` | T1 | UT | OAuth config object has correct Android/iOS client IDs per env |
| `offlineCache.test.ts` | T1 | UT | Offline cache read/write/expire for agent data |
| `secureStorage.test.ts` | T1 | UT | SecureStore wrapper — set, get, delete, error handling |
| `errorHandler.test.ts` | T1 | UT | Global error handler maps API errors to user-friendly messages |
| `performanceMonitoring.test.ts` | T1 | UT | Performance monitoring module records render times without crashing |
| `voiceCommandParser.test.ts` | T1 | UT | Voice command parser maps utterances to navigation intents |
| `theme.test.ts` | T1 | UT | Theme constants match design system tokens (colors, fonts, spacing) |
| `accessibility.test.ts` | T2 | Accessibility | Screens pass axe accessibility rules (labels, roles, contrast) |

### Integration Subfolder

| Path | Tier | Type | One-line Purpose |
|---|---|---|---|
| `__tests__/integration/` | T2 | Integration | Multi-component interaction tests (auth flow end-to-end within mobile) |

---

## 3. Plant BackEnd Tests — `src/Plant/BackEnd/tests/`

Tooling: **pytest**. Run with: `pytest src/Plant/BackEnd/tests/`

### Unit Tests (`tests/unit/` — 55 files)

#### Auth
| File | Type | Purpose |
|---|---|---|
| `test_auth_otp.py` | API | OTP start/verify endpoints — success, 404, 429 rate-limit, 400 invalid |
| `test_auth_register.py` | API | Customer registration — new, idempotent re-register, rate-limit |
| `test_auth_validate.py` | API | Token validation middleware — valid JWT, expired, malformed |

#### Agents & Catalog
| File | Type | Purpose |
|---|---|---|
| `test_agents_catalog_search_api.py` | API | Agent catalog search — filters by industry, rating, specialty |
| `test_agent_mold_*` (multiple) | UT | Agent mold (template) creation, update, validation |
| `test_agent_type_*` (multiple) | UT | Agent type taxonomy — name uniqueness, schema constraints |
| `test_reference_agents_api.py` | API | Reference agent seeding and lookup |

#### Trials & Hiring
| File | Type | Purpose |
|---|---|---|
| `test_trial_service.py` | UT | Trial start, extend, expire, cancel business logic |
| `test_trial_models.py` | UT | Trial ORM model constraints and defaults |
| `test_trial_schemas.py` | UT | Pydantic trial schemas — validation, serialization |
| `test_trial_status_simple_api.py` | API | `GET /trials/{id}/status` response shape |
| `test_trial_end_processing_api.py` | API | Trial end job — deliverable retention, cleanup |
| `test_metering_trial_caps.py` | UT | Usage caps enforced per trial tier |
| `test_hired_agents_*.py` (2) | API | Hire record creation, termination, active-hire uniqueness |
| `test_end_hire_cancel_api.py` | API | `POST /hire/{id}/cancel` flow |

#### Financials
| File | Type | Purpose |
|---|---|---|
| `test_payments_*.py` (2) | UT | Payment record creation and idempotency |
| `test_invoices_simple_api.py` | API | Invoice CRUD and line-item totals |
| `test_receipts_simple_api.py` | API | Receipt generation after confirmed payment |
| `test_deliverables_simple_api.py` | API | Deliverable upload and retrieval |

#### Usage & Metering
| File | Type | Purpose |
|---|---|---|
| `test_usage_events.py` | UT | Usage event emit and storage |
| `test_usage_events_api.py` | API | `POST /usage/events` endpoint |
| `test_usage_ledger.py` | UT | Ledger balance calculation from event stream |
| `test_trusted_metering_envelope.py` | UT | HMAC-signed metering envelope validation |

#### Marketing
| File | Type | Purpose |
|---|---|---|
| `test_marketing_*.py` (5) | API | Campaign CRUD, content generation, approval, analytics, scheduling |

#### Trading (Delta Exchange)
| File | Type | Purpose |
|---|---|---|
| `test_trading_executor.py` | UT | Order execution logic — buy/sell, size calculation |
| `test_risk_engine.py` | UT | Position limit enforcement |
| `test_risk_engine_extended.py` | UT | Edge cases — margin call, stop-loss trigger |
| `test_delta_*.py` (5) | UT | Delta Exchange API client, authentication, order types, WebSocket feed |

#### Goals & Scheduling
| File | Type | Purpose |
|---|---|---|
| `test_goal_*.py` (3) | UT | Goal creation, progress tracking, completion criteria |
| `test_scheduler_*.py` (4) | UT | Celery job scheduling — trial expiry, billing, notifications, retry |

#### Notifications
| File | Type | Purpose |
|---|---|---|
| `test_notification_*.py` (4) | UT | Push, email, SMS, in-app notification dispatch |

#### Genesis & Platform
| File | Type | Purpose |
|---|---|---|
| `test_genesis_*.py` (3) | API | Platform bootstrap — first admin, seed data, schema init |
| `test_skill_playbook_pipeline.py` | UT | Skill→playbook→execution pipeline chain |

#### Infrastructure
| File | Type | Purpose |
|---|---|---|
| `test_config.py` | UT | Config loading, env var overrides, required-key validation |
| `test_database_connector.py` | UT | DB connection pool creation and teardown |
| `test_db_updates_admin.py` | API | Admin DB patch endpoints |
| `test_credential_resolver.py` | UT | Credential lookup — local, Vault, env fallback chain |
| `test_cryptography.py` | UT | AES-GCM encrypt/decrypt, key rotation |
| `test_hash_chain.py` | UT | SHA-256 hash chain — append, verify, tamper detection |
| `test_logging.py` | UT | Structured logging output format |
| `test_metrics.py` | UT | Prometheus metric registration and increment |
| `test_observability.py` | UT | OpenTelemetry trace/span emission |
| `test_security.py` | UT | Password hashing, JWT signing, CORS config |
| `test_security_throttle_customers.py` | UT | Per-customer request throttle with Redis |
| `test_validators.py` | UT | Input validators — phone, email, UUID, currency |
| `test_base_entity.py` | UT | Base ORM entity — timestamps, soft-delete |
| `test_customer_schemas.py` | UT | Customer Pydantic schemas — phone normalisation |
| `test_customers_duplicate_phone.py` | API | Duplicate phone registration returns 409 |

### Integration Tests (`tests/integration/` — 18 files)

| File | Type | Purpose |
|---|---|---|
| `test_alembic_migrations.py` | Integration | All migrations apply cleanly head-to-head and rollback |
| `test_rls_policies.py` | Integration | PostgreSQL Row-Level Security — tenant isolation verified |
| `test_database_connection.py` | Integration | Pool connect/disconnect lifecycle in test DB |
| `test_connector_pooling.py` | Integration | Max connections not exceeded under load |
| `test_pgvector_functionality.py` | Integration | pgvector cosine-similarity search returns sorted results |
| `test_hired_agent_repository.py` | Integration | Hired agent repo — create, fetch, end — against real DB |
| `test_subscription_repository.py` | Integration | Subscription repo CRUD with FK constraints |
| `test_audit_trail.py` | Integration | Every mutating operation writes an audit row |
| `test_transactions.py` | Integration | DB transaction rollback on error |
| `test_phase1_db_mode_journey.py` | Integration | Full Phase-1 customer journey through DB layer |
| `test_trial_api.py` | Integration | Trial API against real DB — start, extend, expire |
| `test_platform_metrics.py` | Integration | Platform-level metric aggregation queries |
| `test_platform_retry.py` | Integration | Retry middleware honours `Retry-After` header |
| `test_facebook_integration.py` | Integration | Facebook Graph API client (mocked at HTTP layer) |
| `test_instagram_integration.py` | Integration | Instagram API client (mocked) |
| `test_whatsapp_integration.py` | Integration | WhatsApp Business API client (mocked) |
| `test_youtube_integration.py` | Integration | YouTube Data API client (mocked) |
| `test_agent_types_db_api.py` | Integration | Agent types stored and retrieved from DB |

### E2E Tests (`tests/e2e/` — 6 files)

| File | Type | Journey |
|---|---|---|
| `test_e2e_approval_gate.py` | E2E | Customer registers → starts trial → trial hits approval gate → agent approved/rejected |
| `test_e2e_trial_limits.py` | E2E | Trial runs → usage cap reached → agent paused → trial ends, deliverables retained |
| `test_e2e_marketing_workflow.py` | E2E | PP creates campaign → CP customer approves → content generated → analytics recorded |
| `test_e2e_multi_agent.py` | E2E | Customer hires 2 agents concurrently → both complete tasks → billing split correctly |
| `test_e2e_trading_workflow.py` | E2E | Trading agent placed order → executed → P&L recorded → position closed |
| `test_e2e_error_recovery.py` | E2E | Downstream service fails → retry → circuit-breaker opens → graceful degradation |

### Middleware Tests (`tests/middleware/` — 4 files)

| File | Type | Purpose |
|---|---|---|
| `test_comprehensive_audit.py` | Middleware | Every request writes audit log with user, action, timestamp |
| `test_input_validation.py` | Middleware | Malformed payloads return 422 with field-level error detail |
| `test_rate_limit.py` | Middleware | Per-IP and per-customer rate limits enforced by middleware |
| `test_security_headers.py` | Middleware | HSTS, CSP, X-Frame-Options present on all responses |

### Performance Tests (`tests/performance/` — 3 files)

| File | Type | Purpose |
|---|---|---|
| `test_api_load.py` | Performance | 50 rps sustained for 60 s — p95 latency < 500 ms |
| `test_database_performance.py` | Performance | Key DB queries — p99 execution time < 100 ms |
| `test_trial_load.py` | Performance | 100 concurrent trial starts — no data loss or deadlock |

### Security Tests (`tests/security/` — 2 files)

| File | Type | Purpose |
|---|---|---|
| `test_credential_encryption.py` | Security | Stored credentials are encrypted; plaintext never appears in logs |
| `test_security_regression.py` | Security | Known attack patterns (SQLi, path traversal, header injection) return 400/403 |

---

## 4. Plant Gateway Tests — `src/Plant/Gateway/middleware/tests/`

Tooling: **pytest**. Run with: `pytest src/Plant/Gateway/middleware/tests/`

| File | Type | Purpose |
|---|---|---|
| `test_auth.py` | Middleware | JWT validation middleware — valid token passes, expired/missing rejected |
| `test_budget.py` | Middleware | Per-customer spend cap — requests blocked when budget exceeded |
| `test_rbac.py` | Middleware | Role-based access — admin, customer, pp-admin scope checks |
| `test_policy.py` | Middleware | Request policy rules — allowed methods, paths, headers |
| `test_proxy.py` | Middleware | Upstream proxy — routes request to correct BackEnd service |
| `test_error_handler.py` | Middleware | Error handler wraps exceptions in standard `{error, code}` envelope |

---

## 5. CP BackEnd Tests — `src/CP/BackEnd/tests/`

Tooling: **pytest**. Run with: `pytest src/CP/BackEnd/tests/`

### Added by CP-SKILLS-1 (PR #836 iteration 1)

| File | Tier | Type | Purpose |
|---|---|---|---|
| `test_cp_skills_routes.py` | T1 | API | CP→Plant proxy for hired-agent skills: GET list, GET skill, PATCH goal-config (CP-SKILLS-2 appended 3 more cases) |

### Added by CP-MY-AGENTS-1 (PR #839)

| File | Tier | Type | Purpose |
|---|---|---|---|
| `unit/test_my_agents_summary_fallback.py` | T1 | API | My Agents summary: fallback to Plant by-customer, Plant-down graceful degrade, 404 path |

### Added by test gap execution (2026-03-03)

| File | Tier | Type | Purpose |
|---|---|---|---|
| `bdd/test_hire_wizard.py` | T2 | BDD | Hire wizard lifecycle Gherkin spec (pytest-bdd) |
| `pact/consumer/` | T2 | Contract | Pact consumer contracts: CP→Plant Gateway |

### Full test list (unchanged since PR #758)

| File | Tier | Type | Purpose |
|---|---|---|---|
| `test_auth.py` | T1 | API | Auth route unit tests — login, logout, invalid credentials |
| `test_auth_models.py` | T1 | UT | Auth Pydantic models — validation and serialisation |
| `test_jwt.py` | T1 | UT | JWT issue, verify, expiry handling |
| `test_jwt_advanced.py` | T1 | UT | JWT edge cases — algorithm confusion, claim tampering |
| `test_2fa_totp.py` | T1 | API | TOTP enrol, verify, backup-code fallback |
| `test_google_oauth.py` | T1 | UT | Google OAuth helpers — code exchange, profile fetch |
| `test_google_oauth_integration.py` | T2 | Integration | Google OAuth with mocked HTTP against real handler |
| `test_cp_otp_routes.py` | T1 | API | CP OTP registration — start, verify, resend |
| `test_cp_otp_login_routes.py` | T1 | API | CP OTP login — start, verify, session issue |
| `test_cp_registration_routes.py` | T1 | API | Customer registration route — new, duplicate, validation errors |
| `test_hire_wizard_routes.py` | T1 | API | Hire wizard — draft persist, step advance, confirm, cancel |
| `test_proxy.py` | T1 | API | CP → Plant proxy — path rewriting, auth header forwarding |
| `test_hired_agents_proxy.py` | T1 | API | Hired agents proxy endpoint — list, detail forwarding |
| `test_routes.py` | T1 | Smoke | Misc route smoke tests |
| `test_dependencies.py` | T1 | UT | FastAPI dependency injection — DB session, current user |
| `test_user_store.py` | T1 | UT | In-memory user store (dev mode) — CRUD |
| `test_config.py` | T1 | UT | Config loading per environment |
| `test_debug_routes.py` | T1 | API | Debug endpoints only accessible in non-prod |
| `test_exchange_setup_routes.py` | T1 | API | Exchange credential setup routes |
| `test_platform_credentials_routes.py` | T1 | API | Platform (social/exchange) credential CRUD |
| `test_payments_razorpay_routes.py` | T1 | API | Razorpay order creation and verification |
| `test_payments_coupon_routes.py` | T1 | API | Coupon validation and discount application |
| `test_payments_config_routes.py` | T1 | API | Payment method config (gateway selection) |
| `test_subscriptions_routes.py` | T1 | API | Subscription create, upgrade, cancel |
| `test_invoices_routes.py` | T1 | API | Invoice list and download |
| `test_receipts_routes.py` | T1 | API | Receipt generation post-payment |
| `test_trading_routes.py` | T1 | API | Trading order placement via CP |
| `test_trading_strategy_routes.py` | T1 | API | Strategy CRUD and activation |
| `test_marketing_review_routes.py` | T1 | API | Marketing content review approval flow |
| `test_my_agents_summary_routes.py` | T1 | API | Hired agent summary dashboard data |
| `test_integration.py` | T2 | Integration | Full CP auth flow integration (register → OTP → login) |
| `test_auth_load.py` | T3 | Performance | Auth endpoint load test — concurrent logins |
| `test_internal_plant_credential_resolver.py` | T1 | UT | CP internal call to Plant credential resolver |

---

## 6. PP BackEnd Tests — `src/PP/BackEnd/tests/`

Tooling: **pytest**. Run with: `pytest src/PP/BackEnd/tests/`

| File | Tier | Type | Purpose |
|---|---|---|---|
| `test_pp_admin_auth.py` | T1 | API | PP admin login and JWT issue |
| `test_agents_routes.py` | T1 | API | Agent CRUD — create, update, publish, archive |
| `test_agent_setup_routes.py` | T1 | API | Agent setup wizard — profile, skills, pricing steps |
| `test_agent_types_routes.py` | T1 | API | Agent type taxonomy management |
| `test_agent_seeding_gating.py` | T1 | API | New agent seeding is gated by approval before going live |
| `test_approval_routes.py` | T1 | API | Agent and content approval workflow |
| `test_genesis_routes.py` | T1 | API | Platform genesis — first-admin creation, initial seed data |
| `test_audit_routes.py` | T1 | API | Audit log query routes |
| `test_db_updates_routes.py` | T1 | API | Admin DB schema patch endpoints |
| `test_exchange_credentials_routes.py` | T1 | API | Exchange API key storage and rotation |
| `test_plant_client.py` | T1 | UT | PP → Plant HTTP client — request building, auth header |
| `test_plant_base_url.py` | T1 | UT | Plant base URL resolved correctly from config |
| `test_proxy.py` | T1 | API | PP reverse-proxy to Plant — forwarding headers |
| `test_health_routes.py` | T1 | Smoke | `GET /health` and `GET /ready` response shape |
| `test_health_and_api_root.py` | T1 | Smoke | Root `/` and health combined smoke |
| `test_metering_debug.py` | T1 | API | Metering debug endpoint returns current usage snapshot |
| `test_config.py` | T1 | UT | PP config loading and env var validation |

---

## Coverage by Regression Tier

| Tier | Components covered | Gap |
|---|---|---|
| T0 (smoke) | All — lint/build | No dedicated smoke markers yet |
| T1 (functional) | CP ✅, PP ✅, Plant Unit ✅, Gateway ✅, Mobile ✅ | PP integration tests missing |
| T2 (integration) | Cross-service ✅, Plant integration ✅, Mobile accessibility ✅ | Mobile Detox E2E not yet written |
| T3 (E2E/perf) | Plant E2E ✅, Plant perf ✅, Plant security ✅, CP load ✅ | Mobile E2E, PP E2E, payment webhook replay |

---

*Last updated: **PR #840 (CP-SKILLS-2) + test gap execution 2026-03-03** — PR #836 = CP-SKILLS-1, PR #839 = CP-MY-AGENTS-1, test gap session added migration 025 column assertion, Gateway goal-config proxy tests, `agentSkills.service.test.ts`, `SkillsPanel.test.tsx`. See [RegressionTestStrategy.md](./RegressionTestStrategy.md) for run instructions and CI integration.*

---

## 7. New Test Infrastructure (Testing Epics — in-repo, NOT yet in CI regression workflow)

> These suites exist on disk and run via Docker. They are NOT yet wired into `waooaw-regression.yml` (that is Epic E11).

### Plant BackEnd — Property-Based (`tests/property/`)

| File | Type | Invariants tested |
|---|---|---|
| `test_hash_chain_invariants.py` | Property (Hypothesis) | SHA-256 hash chain: append/verify/tamper on any input sequence |
| `test_usage_ledger_invariants.py` | Property (Hypothesis) | Usage ledger balance = sum of all events for any event sequence |
| `test_trial_billing_invariants.py` | Property (Hypothesis) | Trial billing arithmetic: correct proration for any duration/start |

### Plant BackEnd — BDD (`tests/bdd/`)

| File | Type | Feature |
|---|---|---|
| `test_trial_lifecycle.py` | BDD (pytest-bdd) | 7-day trial lifecycle: start → deliver → cancel, keep deliverables |

### Plant Gateway — Pact Provider (`tests/pact/provider/`)

| File | Type | Purpose |
|---|---|---|
| `test_plant_gateway_provider.py` | Contract (Pact) | Verifies Plant Gateway fulfils all consumer Pact contracts (CP, PP, Mobile) |

### Plant BackEnd — New tests added 2026-03-03 (test gap session)

| File | Type | Purpose |
|---|---|---|
| `tests/integration/test_alembic_migrations.py` | Integration | +2 tests: `test_migration_025_agent_skills_goal_config_column`, `test_migration_025_agent_skills_goal_config_nullable` |

### Plant Gateway — New tests added 2026-03-03 (test gap session)

| File | Type | Purpose |
|---|---|---|
| `middleware/tests/test_proxy.py` | Middleware | +2 tests: `test_proxy_proxies_patch_goal_config_to_plant`, `test_proxy_goal_config_patch_requires_authentication` |

### Plant BackEnd — New integration test added by CP-MY-AGENTS-1 (PR #839)

| File | Type | Purpose |
|---|---|---|
| `tests/unit/test_hired_agents_by_customer.py` | UT | Plant `/hired-agents/by-customer/{id}` endpoint: DB path, in-memory fallback |

### CP FrontEnd — Vitest (`src/CP/FrontEnd/src/__tests__/`)

Added by CP-SKILLS-2 + test gap execution 2026-03-03:

| File | Tier | Type | Purpose |
|---|---|---|---|
| `agentSkills.service.test.ts` | T1 | UT | `agentSkills.service`: `listHiredAgentSkills` (3 cases), `saveGoalConfig` PATCH path + error + URL encoding |
| `SkillsPanel.test.tsx` | T1 | UI | `SkillsPanel` component: loading/error/empty/skills-list states, save success, save error, readOnly mode |

### Web E2E — Playwright (`tests/e2e/web/`)

| File | Type | Journey |
|---|---|---|
| `auth/otp_auth.spec.ts` | E2E (Playwright) | Customer OTP auth: register → OTP verify → authenticated portal |
| `hire/hire_wizard.spec.ts` | E2E (Playwright) | Hire wizard: browse → select agent → coupon checkout → My Agents |
| `admin/agent_approval.spec.ts` | E2E (Playwright) | PP admin: create agent → approve → agent goes live in CP marketplace |

### Mobile E2E — Maestro (`tests/e2e/mobile/`)

| File | Type | Journey |
|---|---|---|
| `auth_otp.yaml` | E2E (Maestro) | OTP auth: register → OTP input → home screen |
| `hire_flow.yaml` | E2E (Maestro) | Browse agents → tap agent → hire wizard → confirm |

### Performance — Locust (`tests/performance/`)

| File | Type | Target |
|---|---|---|
| `locustfile.py` | Performance (Locust) | Plant Gateway: auth + browse endpoints, 50 users, p95 < 500 ms |
| `trial_concurrency.py` | Performance (Locust) | 100 concurrent trial starts, zero data loss |

### CP BDD (`src/CP/BackEnd/tests/bdd/`)

| File | Type | Feature |
|---|---|---|
| `test_hire_wizard.py` | BDD (pytest-bdd) | Hire wizard flow: OTP auth → hire → subscription active |

### CP Pact Consumer (`src/CP/BackEnd/tests/pact/consumer/`)

| File | Type | Purpose |
|---|---|---|
| *(consumer pact files)* | Contract (Pact) | CP→Plant Gateway consumer contracts |
