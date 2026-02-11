# Plant — Context Session Snapshot
**Date**: 2026-02-10
**Scope**: PR #652 pre-check triage (CP coverage + Docker Build Smoke), Docker-only verification, and merge readiness for Agent Phase 1
**Status**: ✅ CI unblocked; ✅ PR merged; ✅ deployment pending (owner)

---

## 1) What we completed today (high signal)

### A) PR #652 pre-check triage and fixes (CP BackEnd)
**Problem**: PR #652 initially failed pre-checks:
- **Backend Unit Tests (CP)** failed due to **coverage gate** (min 76%).
- **Docker Build Smoke** reported failure on the old run (needed reproduction + rerun confirmation).

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| CP BackEnd total coverage slightly below 76% | CI blocks merge even though tests pass | Add targeted unit tests for newly added Plant-proxy modules and edge/error paths to exceed gate |
| Test expectations didn’t match helper function signatures in `api/my_agents_summary.py` | Newly added tests failed, reducing coverage further | Align tests to actual signatures and add a small behavior fix for missing `PLANT_GATEWAY_URL` in Plant-subscriptions mode |

**Fixes implemented**
- Added coverage-driving unit tests for CP → Plant proxy behaviors and edge cases.
- Adjusted CP My Agents subscription listing behavior to return HTTP 503 when Plant base URL is missing while Plant-subscriptions mode is enabled.

**Validation performed (Docker-only)**
- Built CP BackEnd image and ran pytest inside container with CI-like env.
- Result: **Required test coverage of 76% reached. Total coverage: 76.47%**.

**Primary files touched (CP BackEnd)**
- `src/CP/BackEnd/api/my_agents_summary.py`
- `src/CP/BackEnd/tests/test_hired_agents_proxy.py`
- `src/CP/BackEnd/tests/test_my_agents_summary_routes.py`

**Minor cleanup (CP FrontEnd)**
- Removed a duplicate import in `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx`.

**Tracking**
- PR: https://github.com/dlai-sd/WAOOAW/pull/652
- Branch (during fix): `feat/cp-payments-mode-config`
- Fix commit pushed during triage: `daefacf` (coverage + tests + minor cleanup)

---

### B) Docker Build Smoke reproduction
**Goal**: Reproduce the CI Docker builds locally to ensure there is no deterministic build failure.

**Validation performed**
- Reproduced CI build steps locally:
  - CP BackEnd docker build
  - CP FrontEnd docker build (with `VITE_GOOGLE_CLIENT_ID` + `VITE_ENVIRONMENT=ci`)
  - PP BackEnd docker build
  - PP FrontEnd docker build (same build args)
  - Plant BackEnd docker build

**Result**: All builds completed successfully locally.

---

### C) DB changes request confirmation (Phase 1)
**Request**: “Send me all DB changes in this PR (DDL/data) for PP DB management deployment.”

**Answer**: **No DB changes in PR #652.**
- Phase 1 agent configuration/goals/deliverables use **in-memory/simple stores** (no migrations/DDL/seed scripts added).
- Plant/PP persistence work is intentionally out of scope for this Phase 1 PR.

---

## 2) Key invariants reaffirmed (Phase 1)
- **Docker-only tests** for validation (no local virtualenv-based testing).
- **Single door**: CP FrontEnd → CP BackEnd `/api/*` only; CP BackEnd proxies to Plant Gateway.
- **Secrets stay in CP**: Plant receives refs/ids only; Plant enforces that raw secrets are not accepted.
- **Deterministic trading**: no LLM trading recommendations in Phase 1.
- **Plant is non-bypassable enforcement**: approvals required for external side effects; auditable denials.

---

## 3) Deployment notes / quick smoke suggestions
After deployment, the highest-signal endpoints to validate the Phase 1 flow:
- CP: `GET /api/cp/my-agents/summary`
- CP: `GET /api/cp/hired-agents/by-subscription/{subscription_id}`
- Plant: `GET /api/v1/agent-types`
- Plant: `GET /api/v1/hired-agents/{hired_instance_id}/deliverables`

Also confirm expected behavior when Plant URL is not configured:
- CP should return **503** (service unavailable) for Plant-backed subscription listing when `PLANT_GATEWAY_URL` is missing.
