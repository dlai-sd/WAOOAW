# Running Commentary — 2026-03-10

> **Purpose:** Track the UI/UX revamp follow-through on CP, PP, and mobile so connection issues do not lose the plan or checkpoint state.
> **Branch:** `feat/ui-ux-revamp`
> **Fallback checkpoint:** `9237c55` (`fix(frontend): wire command centre fallback nav props`)

---

## Current State

The UI/UX revamp is implemented and pushed on `feat/ui-ux-revamp`.

### Completed baseline

| Area | Status | Notes |
|---|---|---|
| CP customer shell + discovery + command centre + spend/profile | ✅ Complete | visual hierarchy and customer operating surface upgraded |
| CP auth + hire setup | ✅ Complete | sign in, sign up, and hire wizard upgraded |
| PP shell + dashboard + contributor/ops pages | ✅ Complete | landing, dashboard, setup, ops, review, governance surfaces upgraded |
| Mobile customer surfaces | ✅ Complete | home, my agents, ops, profile, sign in, sign up upgraded |
| Node toolchain in container | ✅ Complete | `node v18.20.4`, `npm 9.2.0` on PATH |
| Disk cleanup | ✅ Complete | Docker prune recovered space from ~1.5G free to ~11G free |
| Validation checkpoint | ✅ Complete | CP build/test, PP build/test, mobile typecheck/test command path exited `0` |

### Current branch checkpoints

| Commit | Meaning |
|---|---|
| `2ddd8be` | main UI/UX revamp across CP, PP, and mobile |
| `9237c55` | final CP fallback prop wiring fix after validation |

---

## Next Sequence

The work should continue in small chunks, each ending in a checkpoint commit and push.

| Chunk | Goal | Status | Notes |
|---|---|---|---|
| 1 | Structured QA pass on CP user journeys | in progress | first validated sub-chunk complete |
| 2 | Structured QA pass on PP contributor journeys | planned | landing, dashboard, agent setup, hired agents ops, review queue, policy denials, audit |
| 3 | Structured QA pass on mobile journeys | planned | sign in, sign up, today, ops, profile, approvals |
| 4 | Fix defects from QA pass | planned | focus on layout, interaction, empty/loading/error states |
| 5 | Add targeted frontend test coverage for new flows | planned | CP shell navigation, PP shell/navigation, mobile home/ops/profile |
| 6 | Final smoke + PR prep | planned | branch summary, residual risks, open PR |

### Chunk 1A — CP QA sub-checkpoint

Validated and ready on branch before moving to the next CP slice.

| Area | Result |
|---|---|
| Discovery -> detail navigation | fixed so discovery uses the provided selection callback instead of bypassing the portal flow |
| Command Centre quick action | fixed dead `Add New Goal` action by wiring it to the goals page |
| Payment confirmation -> setup | upgraded `HireReceipt` so the user continues into setup instead of landing in a thin utility dead end |
| CP validation | `npm run build` + `npm run test:run` exited `0` after these fixes |

Files in Chunk 1A:
- `src/CP/FrontEnd/src/pages/AgentDiscovery.tsx`
- `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx`
- `src/CP/FrontEnd/src/pages/HireReceipt.tsx`
- `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx`
- `src/CP/FrontEnd/src/styles/globals.css`

---

## Iteration Guidance

### Iteration 1 — Journey QA

Do a real walkthrough of the revamped product surfaces and log defects by severity.

- CP customer journey:
  - sign in
  - sign up
  - discover
  - hire setup
  - command centre
  - billing
  - profile
- PP contributor journey:
  - landing
  - dashboard
  - agent type setup
  - hired agents ops
  - review queue
  - policy denials
  - audit console
- Mobile customer journey:
  - sign in
  - sign up
  - Today tab
  - Ops tab
  - profile
  - approvals flow

### Iteration 2 — Defect Fixes

Address the specific issues found in Iteration 1.

Priorities:
- responsive breakpoints
- spacing and hierarchy regressions
- empty/loading/error states
- language consistency across CP, PP, and mobile
- navigation rough edges

### Iteration 3 — Frontend Test Hardening

Add focused tests to protect the revamp.

Priority targets:
- CP portal navigation and command-centre routing
- CP hire/setup flow shell states
- PP dashboard and contributor-page render coverage
- mobile home, profile, and agent operations states

---

## Hygiene Rules For This Branch

- Keep working in small chunks.
- After each chunk, commit and push immediately.
- Prefer checkpoint-style commit messages when a chunk is finished.
- Do not start the next chunk before the previous one is validated.
- If the session drops, resume from this file first, then `git log --oneline -5`.

---

# Running Commentary — 2026-03-05

> **Purpose:** Fix 3 UI/payment defects: coupon checkout error (D2), sign-out landing page redirect (D3), sign-in screen dividers + 6-digit OTP (D4).
> **Branch:** `fix/ui-coupon-signout-signin`

---

## Status Board

| Task | Status | Notes |
|---|---|---|
| D2: Coupon checkout blocked by PAYMENTS_MODE guard | ✅ Complete | Removed `_require_coupon_mode()` call + dead function |
| D3: Sign Out → sign-in screen instead of landing page | ✅ Complete | `handleLogout` wraps `logout` + `navigate('/')` in App.tsx |
| D4a: Horizontal dividers above footnote and Work email | ✅ Complete | Removed `border-top/padding-top` from CSS; removed `<div divider>` from AuthPanel |
| D4b: 6-digit OTP boxes (sign-in + register) | ✅ Complete | `signinOtpDigits` + `otpDigits` array state; 6 native inputs with auto-advance |
| Test update + PR | ✅ Complete | Updated `completeStep1` + `AuthPanel.step1otp.test.tsx` + `AuthModalRegistration.test.tsx`; fixed pre-existing "Create account" button name; 6-box OTP helpers added; frontend: 19 failed (all pre-existing) vs 25 baseline |

---

# Running Commentary — 2026-03-04

> **Purpose:** Live log of investigation progress across PR validation, deploy log analysis, login-redirect RCA, and Iteration 3 gap review.
> **Rule:** No code changes without explicit user permission.

---

## Status Board

| Task | Status | Notes |
|---|---|---|
| 1. Latest 4-5 PRs — what did we ship? | ✅ Complete | 5 PRs reviewed |
| 2. Workflow 'WAOOAW Deploy #156' analysis | ✅ Complete | Run DB 22633923789 |
| 3. RCA — My Agent page redirects to login | ✅ Complete | Root cause: Plant Backend 404 cascades to 401 |
| 4. Iteration 3 gap analysis | ✅ Complete | 3 gaps identified with reasons |

---

## Task 1 — Latest 5 Merged PRs

**Fetched from GitHub:** `gh pr list --state merged --limit 7`

| PR | Merged | Title | Scope |
|---|---|---|---|
| [#846](https://github.com/dlai-sd/WAOOAW/pull/846) | 2026-03-03 | feat(PLANT-SKILLS-1): it3 — OPA gateway fix + Secret Manager credentials + FE field alignment | 11 files: `policy.py` fix, `secret_manager.py` (new), `cp_skills.py` update, `requirements.txt`, OPA tests (+5), `platformConnections.service.ts` FE alignment, `SkillsPanel.tsx` fix, `cloud/terraform/stacks/cp/main.tf` (+env vars) |
| [#845](https://github.com/dlai-sd/WAOOAW/pull/845) | 2026-03-03 | fix(PLANT-OPA-1): bring it2 Terraform + deploy changes to main | 6 files: deploy workflow + plant Terraform stack with OPA Cloud Run module |
| [#844](https://github.com/dlai-sd/WAOOAW/pull/844) | 2026-03-03 | feat(PLANT-OPA-1): Iteration 2 — Terraform Cloud Run + deploy pipeline | 6 files: same as #845 (it2 feature, #845 brought hotfix) |
| [#843](https://github.com/dlai-sd/WAOOAW/pull/843) | 2026-03-03 | tracking: PLANT-OPA-1 Iteration 1 — 5 Rego policies + OPA Dockerfile + CI job | 14 files: all OPA policy files, tests, Dockerfile, CI workflow update |
| [#842](https://github.com/dlai-sd/WAOOAW/pull/842) | 2026-03-03 | feat(CP-HIRE-1): hire journey full DB persistence on GCP | 10 files: Terraform CP + Plant stacks, `hire_wizard.py` route, test coverage |

**What was shipped overall (these 5 PRs):**
1. Full OPA policy engine deployed on Cloud Run (Rego RBAC, trial, governor, budget, sandbox) with IAM wiring
2. Hire journey (HireSetupWizard) now persists to GCP PostgreSQL 
3. CP BackEnd gets Secret Manager adapter — credentials for platform connections go to GCP Secret Manager, NOT to the database
4. OPA policy.py fix — DELETE on agent sub-resources no longer misfires the `delete_agent` governor check
5. CP FrontEnd `SkillsPanel.tsx` and `platformConnections.service.ts` field alignment to Plant's canonical names (`id`/`platform_key`)
6. CVE fix for `google-cloud-secret-manager` (2.18.2→2.26.0) + `protobuf==5.29.6` — included in the PR #846 merge commit

---

## Task 2 — WAOOAW Deploy #156 Analysis

**Run ID:** `22633923789`  
**Triggered:** `workflow_dispatch` at 2026-03-03T17:02 UTC  
**Trigger context:** Manual dispatch after PR #846 merged to `main` (merge commit `da7c66b`)  
**Total duration:** ~12m 57s  
**Overall result:** ✅ SUCCESS

### Jobs breakdown

| Job | Duration | Result | Notes |
|---|---|---|---|
| Detect Components | 6s | ✅ | All 4 components detected (has_cp, has_pp, has_plant, has_plant_gateway) |
| Resolve Inputs | 3s | ✅ | Image tag resolved to `da7c66b-156` |
| Dependency Vulnerability Scan | 1m 12s | ✅ (warning) | Pip: 2 known vulns in 2 packages. **npm: 3 vulns (1 moderate, 2 high)** — uploaded as artifact, NOT blocking |
| Build & Push Images | 7m 20s | ✅ | `cp-backend:da7c66b-156`, `cp:da7c66b-156` (and plant services) built. Pip root-user warning (cosmetic). |
| Terraform Apply (Stacks) | 4m 0s | ✅ | **Plant stack: 0 added, 3 changed, 0 destroyed** (plant_backend, plant_gateway, plant_opa in-place). **CP stack: 0 added, 2 changed, 0 destroyed** (cp_backend, cp_frontend in-place). PP stack: No changes. |
| Terraform Plan (Stacks) | 0s | — | Skipped (apply ran instead) |
| Summary | 3s | ✅ | |

### What Terraform applied

**Plant stack (3 changed):**
- `module.plant_backend.google_cloud_run_v2_service.service` → new image tag `da7c66b-156`
- `module.plant_gateway.google_cloud_run_v2_service.service` → new image tag `da7c66b-156` (includes the `policy.py` OPA fix)
- `module.plant_opa.google_cloud_run_v2_service.service` → new image tag `da7c66b-156`

**CP stack (2 changed):**
- `module.cp_backend.google_cloud_run_v2_service.service` → new image + **new env vars `GCP_PROJECT_ID=waooaw-oauth` and `SECRET_MANAGER_BACKEND=gcp`**
- `module.cp_frontend.google_cloud_run_v2_service.service` → new image tag

### Issues / flags

| Issue | Severity | Details |
|---|---|---|
| npm vulnerabilities | ⚠️ Medium | 3 vulns (1 moderate, 2 high) in npm packages — scan was non-blocking, artifacts saved. Needs follow-up. |
| OPA IAM 403 | 🔴 High | Plant Gateway cannot invoke Plant OPA Cloud Run service — `plant_gateway_sa` is missing `roles/run.invoker` on OPA. Budget check fails every request (fail-open → requests pass) but creates error noise. |
| Retention days warning | ℹ️ Info | Artifact retention capped at 1 day by repo policy. Non-blocking. |

**Verdict:** Deploy succeeded mechanically (all job ✅). Two operational concerns post-deploy: (a) OPA budget IAM not wired, (b) npm vulns need tracking.

---

## Task 3 — RCA: My Agent Page → Login Redirect (no error shown)

### Symptom
After deployment of PR #846 (Deploy #156), user navigates to "My Agents" authenticated page → silently redirected to login screen with no error message.

### Evidence chain (GCP Cloud Run logs — `waooaw-plant-gateway-demo`)

| Timestamp (UTC) | Log entry | Significance |
|---|---|---|
| 02:47:09.128865Z | `INFO:httpx: GET https://waooaw-plant-backend-demo-ryvhxvrdna-el.a.run.app/api/v1/auth/validate "HTTP/1.1 404 Not Found"` | ← **Root cause:** Plant Backend returns 404 for auth/validate |
| 02:47:09.129902Z | `INFO: "GET /api/v1/payments/subscriptions/by-customer/1a5ab779-... HTTP/1.1" 401 Unauthorized` | Gateway converts 404 → 401 and returns to client |
| 02:46:42.849703Z | `WARNING: Budget check failed, allowing request` + traceback `403 Forbidden` from OPA | Separate issue — budget IAM; fail-open so request proceeds |

### Root cause breakdown

**Step 1 — User opens My Agents page** → CP FrontEnd calls CP BackEnd → CP BackEnd proxies to Plant Gateway → Plant Gateway `auth.py` middleware calls `GET /api/v1/auth/validate` on Plant Backend.

**Step 2 — Plant Backend's `validate_token` handler:**
- Extracts Bearer token from `X-Original-Authorization` header
- Verifies JWT signature/expiry (passes — token is valid)
- Calls `CustomerService.get_customer_by_id(claims["sub"])` where `sub = "1a5ab779-..."`
- **Customer ID `1a5ab779-...` does NOT exist in Plant Backend's `customers` table** → raises `HTTPException(status_code=404)`

**Step 3 — Plant Gateway `auth.py` at line ~383:**
```python
if res.status_code == status.HTTP_404_NOT_FOUND:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found")
```
404 from Plant Backend → Gateway returns **401 Unauthorized** to CP Backend.

**Step 4 — CP FrontEnd `gatewayApiClient.ts` lines 141–160:**
```typescript
if (res.status === 401) {
    const newToken = await authService.silentRefresh()  // tries refresh
    if (newToken) { res = await doFetch(newToken) }      // retry — still 401
}
// still 401:
markAuthExpiredAndBroadcast()  // ← triggers silent redirect to login, no error dialog
```

### Why "no error message"
`markAuthExpiredAndBroadcast()` fires a global auth-expired event. The app's `AuthProvider` catches it and redirects to `/login` — no `GatewayApiError` is surfaced to the user. The error detail `"Customer not found"` from the gateway is swallowed by the 401 handler.

### Why the customer is missing from Plant Backend

**Primary hypothesis:** The user (`1a5ab779-...`) holds a valid JWT issued by CP Backend auth, but their `Customer` record was never created in Plant Backend's `customers` table — or was created against an old DB instance that was replaced/migrated.

**Supporting evidence:**
- User `1232255a-...` authenticates successfully at 02:46:42 (different user ID, record exists in Plant DB)
- User `1a5ab779-...` fails at 02:47:09 immediately after (record absent)
- PR #842 (hire journey DB persistence) was merged 2026-03-03 — it may have changed the customer-creation flow or migration schema
- The Plant Backend had a middleware-stack exception at 2026-03-03T12:11 (before the 17:02 deploy) suggesting earlier instability

### What is NOT the cause
- JWT token expiry (token is verified valid before 404 path is reached)
- The CVE fix / Secret Manager library (deployed correctly — `google-cloud-secret-manager==2.26.0` + `protobuf==5.29.6` confirmed in the merge commit)
- The OPA budget 403 IAM issue (fail-open — lets requests through)

### Impact
Any CP user whose `customer_id` (JWT `sub` claim) doesn't exist in Plant Backend's `customers` table gets silently redirected to login from any page that calls Plant-Gateway-proxied APIs. Affected page set: all authenticated portal pages that call Plant Gateway.

---

## Task 4 — Iteration 3 Gap Analysis

### What the plan required vs what was delivered

| Story | Required deliverable | Status | Delivered? |
|---|---|---|---|
| E6-S1 | `api/cp_skills.py` — 8 proxy routes, `waooaw_router`, Secret Manager integration | ✅ Done | 311 lines, all routes present |
| **E6-S2** | `GoalConfigForm.tsx` — dynamic form renderer from `goal_schema.fields` | **❌ Missing** | Component file does not exist; Goals tab in `MyAgents.tsx` has no `goal_schema`-driven form |
| **E7-S1** | `PlatformConnectionsPanel.tsx` + wire into Configure tab | **❌ Missing** | Panel component not created; `MyAgents.tsx` has old `platform_credentials` flow, not the new `PlatformConnection` Secret Manager flow |
| E7-S1 (service) | `platformConnections.service.ts` with 3 exported functions | ✅ Done | 85 lines, all 3 functions present, interfaces aligned |
| E7-S2 (service) | `performanceStats.service.ts` with `getPerformanceStats` | ✅ Done | File exists, `listPerformanceStats` exported |
| E7-S2 (FE) | Performance tab with Fluent UI table, skill filter, loading/empty states | ✅ Done (inline) | `PerformancePanel` implemented inline in `MyAgents.tsx` at line 1448; imports `listPerformanceStats`; renders loading, empty, and data states |

### Why these gaps occurred

**Gap 1 — `GoalConfigForm.tsx` not built (E6-S2)**

The agent that executed PR #846 focused on the three **pre-existing bugs** listed in the PR description (OPA policy regression, raw credentials stored in DB, FE field name mismatch). Those bugs were blocking end-to-end functionality and had higher urgency. The `GoalConfigForm.tsx` component, while in the Iteration 3 plan, doesn't block any observable production flow yet — no existing workflow calls `goal_schema` today. The agent applied the patch for highest-impact visible bugs and didn't circle back to the remaining FE component.

**Gap 2 — `PlatformConnectionsPanel.tsx` not wired (E7-S1 partial)**

The E7-S1 service (`platformConnections.service.ts`) WAS completed and correctly aligned to the Secret Manager flow. However, the visual component (`PlatformConnectionsPanel.tsx`) and its wiring into the Configure tab were skipped. The agent correctly identified that the `SkillsPanel.tsx` field-alignment fix (`id`/`platform_key`) was the observable problem in the current sprint, and fixed that existing component instead of building the new Panel. The new panel isn't needed until the connect-credentials flow is tested end-to-end.

**Structural reason for both gaps:** PR #846 was a **bug-fix** PR masquerading as an iteration-completion PR. The commit message says "it3 — OPA gateway fix + Secret Manager credentials + FE field alignment" — all three deliverables in the title are bug fixes, not the two remaining E2/E3 FE components. The iteration plan story E6-S2 and E7-S1 (panel) were not the day's fires.

---

## Final Summary

**PR overview (5 PRs):** All 5 PRs shipped Thursday evening delivering the OPA policy engine on Cloud Run, Secret Manager credential storage for platform connections, the hire journey DB persistence, and a full set of bug fixes — the codebase moved from zero governance enforcement to live OPA policing in a single day.

**Deploy #156 correctness:** The deploy completed without errors — all 5 Cloud Run services (plant-backend, plant-gateway, plant-opa, cp-backend, cp-frontend) received new images and Terraform applied 5 in-place changes; two post-deploy operational flags exist: npm package vulnerabilities (non-blocking, need tracking) and OPA-budget IAM not wired (fail-open, not user-facing).

**My Agent → login redirect RCA:** A valid user (`1a5ab779-...`) has a JWT whose `customer_id` doesn't exist in Plant Backend's `customers` table — Plant Backend correctly returns 404 from `auth/validate`, Plant Gateway converts that 404 to 401 (`"Customer not found"`), and the CP FrontEnd silently redirects to login via `markAuthExpiredAndBroadcast()`; the fix needed is either backfilling the missing customer record in Plant DB or adding a more descriptive error screen instead of the silent redirect.

**Iteration 3 gaps:** Two deliverables from the Iteration 3 plan were not built: `GoalConfigForm.tsx` (the `goal_schema`-driven dynamic form, E6-S2) and `PlatformConnectionsPanel.tsx` (the Configure-tab connector UI, E7-S1 panel); the agent prioritised three high-urgency bug fixes (OPA DELETE regression, raw credentials in DB, field-name mismatch) over the remaining FE components, leaving the services ready but the visual layer incomplete.


---

## Session 3 — OPA Identity Token, Customer Error UX, E6-S2/E7-S1 FE Components

### What was done

**1. OPA Identity Token Fix** (`budget.py`, `rbac.py`, `policy.py`)

Root cause confirmed: Plant Gateway middleware called OPA with plain `httpx.post()` — no `Authorization` header. Cloud Run requires a GCP Identity Token even when the service account has `roles/run.invoker` (IAM binding was already correct for `270293855600-compute@developer.gserviceaccount.com`).

Fix: Added `_get_opa_id_token(audience)` async helper to all three middleware files. Helper fetches a self-signed identity token from the GCP metadata server (`http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=<OPA_URL>`), caches it with 60-second early-expiry, and injects it as `Authorization: Bearer <token>` on every OPA HTTP call.

No secrets are baked in the image — `OPA_URL` / `OPA_SERVICE_URL` is injected by Terraform at deploy time.

Files changed:
- `src/Plant/Gateway/middleware/budget.py` 
- `src/Plant/Gateway/middleware/rbac.py`
- `src/Plant/Gateway/middleware/policy.py`

**2. "Customer Not Found" UX Guard** (`gatewayApiClient.ts`)

Root cause: Plant Backend `auth/validate` returns 404 when the customer row is missing → Plant Gateway converts to 401 with `detail: "Customer not found"` → CP FrontEnd called `markAuthExpiredAndBroadcast()` → silent login redirect.

Fix: Before calling `markAuthExpiredAndBroadcast()` on 401, check if `problem.detail.toLowerCase().includes('customer not found')`. If so, throw `GatewayApiError` with `'Your account setup is incomplete. Please contact support to activate your account.'` — no redirect, user sees an actionable error.

File changed: `src/CP/FrontEnd/src/services/gatewayApiClient.ts`

**3. Customer DB Backfill (investigation)**

Customer `1a5ab779-f9b0-4efe-bc22-fb83368451d1` is missing from Plant Backend DB. The `validate_token` endpoint in `auth.py` looks up the customer by email claim from JWT. No Cloud Run logs found for this customer within 30-day window.

The exact SQL to backfill is embedded in `src/Plant/BackEnd/api/v1/auth.py` (see the `detail` variable in `validate_token` around line 290). To run the backfill:

```sql
DO $$
DECLARE new_id UUID := '1a5ab779-f9b0-4efe-bc22-fb83368451d1';
BEGIN
  INSERT INTO base_entity (id, entity_type, status)
  VALUES (new_id, 'Customer', 'active')
  ON CONFLICT (id) DO NOTHING;
  
  INSERT INTO customer_entity (id, email, phone, full_name, business_name,
                               business_industry, business_address,
                               preferred_contact_method, consent)
  VALUES (new_id, '<USER_EMAIL>', '+91-0000000000', 'Display Name',
          'Company', 'Technology', 'India', 'email', true)
  ON CONFLICT (id) DO NOTHING;
END $$;
```

Replace `<USER_EMAIL>` with the affected user's email before running against Plant Backend DB.

**4. GoalConfigForm.tsx (E6-S2)** — created as separate component file

`src/CP/FrontEnd/src/components/GoalConfigForm.tsx` — extracted from inline definition in `SkillsPanel.tsx` into a standalone exported component. Adds:

- `show_if` conditional field visibility (was missing in SkillsPanel's inline version)
- `GoalFieldRenderer` as a named export (reusable)
- `SkillsGoalConfigSection` — loads all skills for a hired agent and renders one `GoalConfigForm` per skill
- `GoalSchemaField.show_if` added to `agentSkills.service.ts` interface

**5. PlatformConnectionsPanel.tsx (E7-S1)** — created as separate component file

`src/CP/FrontEnd/src/components/PlatformConnectionsPanel.tsx` — extracted from SkillsPanel and enhanced:

- Status badges with correct Fluent UI `color` prop: `success` (connected), `warning` (pending), `danger` (error/failed)
- `ConnectForm` sub-component — inline form with `type="password"` for API key + secret; credentials cleared from React state immediately after successful submit
- "Connect [platform]" CTA for each unconnected required platform (from `requiredPlatformKeys` prop)
- "+ Add platform connection" for arbitrary platforms
- DELETE per connection

**6. Wired into MyAgents.tsx Configure tab**

`PlatformConnectionsPanel` imported and rendered below `ConfigureAgentPanel` in the Configure tab. Gated on `selectedInstance.hired_instance_id` existing.

### Build result

```
tsc && vite build  →  ✓ built in 15.27s  (0 TypeScript errors)
```

### Remaining (needs deploy)

- OPA + FE guard changes are uncommitted — need `git commit` then push + PR
- Customer backfill SQL above needs to be run against production Plant Backend DB with the correct email
