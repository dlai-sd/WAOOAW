# PP-FIX-1 — PP Portal Defect Fixes

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PP-FIX-1` |
| Feature area | PP Portal — 15 defect fixes (routes + UI) |
| Created | 2026-03-08 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `defect_list_8_Mar_2026.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 4 |
| Total epics | 11 |
| Total stories | 11 |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM |
| Binary inference only | Acceptance criteria are pass/fail |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. All patterns you need are in your card.

---

## PM Review Checklist

- [x] Epic titles name user outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] `waooaw_router()` snippet in every new route story
- [x] GET routes use `get_read_db_session()` not `get_db_session()`
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has time estimate and come-back datetime
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Backend epics before frontend epics within each iteration
- [x] No placeholders remain

---

## Vision Intake

1. **Area:** Plant BackEnd (prefix fix) + PP BackEnd (route path fixes) + PP FrontEnd (UI fixes)
2. **Outcome:** Operator loads the PP portal Hired Agents page, enters a customer email, and sees live subscription + hired agent data — all OPS panels (construct health, scheduler diagnostics) work without 404/401 errors.
3. **Out of scope:** JSONL-backed routes (approvals, exchange_credentials, agent_setups). Auth wiring beyond the Demo Login button. New Plant data endpoints beyond the one missing GET-by-ID.
4. **Lane:** A for most stories (wire existing Plant endpoints). One Lane B story (E4-S1: add missing `GET /hired-agents/{id}` to Plant).
5. **Urgency:** All 15 defects confirmed live on `pp.demo.waooaw.com` as of 2026-03-08.

<!-- END CHUNK 1 -->

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Critical backend path fixes unblocking the OPS portal | E1, E2, E3 | 4 | 2.5h | ✅ Done |
| 2 | Missing Plant endpoint + Demo Login button + hardcoded ID fix | E4, E5, E6 | 3 | 1.5h | 2026-03-08 18:30 IST |
| 3 | Nav/label accuracy + email customer lookup | E7, E8, E9 | 3 | 2h | 2026-03-09 10:00 IST |
| 4 | Dashboard live data + agent ID audit | E10, E11 | 2 | 1.5h | 2026-03-09 11:30 IST |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Path fix = 15–30 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

<!-- END CHUNK 2 -->

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
```

**Steps to launch:**
1. Open VS Code → Copilot Chat (`Ctrl+Alt+I` / `Cmd+Alt+I`)
2. Click model dropdown → **Agent mode**
3. Click `+` → type `@` → select **platform-engineer**
4. Paste the block below → press **Enter**
5. Come back: **2026-03-08 17:00 IST**

**Iteration 1 agent task (paste verbatim):**
```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python/FastAPI engineer, I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-FIX-1-portal-defects.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2, 3, or 4 content.
TIME BUDGET: 2.5h.

EXECUTION ORDER:
1. git status && git log --oneline -3 — must be clean on main. If not, HALT.
2. Read "Agent Execution Rules" section in this plan file.
3. Read "Iteration 1" section in this plan file. Read nothing else before starting.
4. Execute: E1 → E2 → E3 (in order).
5. When all epics are docker-tested, open the iteration PR. Post PR URL. HALT.
6. After each story completes: update Tracking Table status to 🟢 Done, commit, push.
7. After each epic completes: post "**Epic Exx complete ✅**" comment under the epic heading, commit, push.
8. After all iteration epics complete: update Iteration Summary table row to ✅ Done.
```

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(PP-FIX-1): iteration 1
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task (paste verbatim):**
```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior TypeScript/React engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-FIX-1-portal-defects.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5, E6. Do not touch other iterations.
TIME BUDGET: 1.5h.

PREREQUISITE CHECK (do before anything else):
  git log --oneline origin/main | head -5
  Must show: feat(PP-FIX-1): iteration 1
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute: E4 → E5 → E6. Open iteration PR when done. Post URL. HALT.
4. After each story: update Tracking Table to 🟢 Done, commit, push.
5. After each epic: post "**Epic Exx complete ✅**" under epic heading, commit, push.
6. After all iteration epics: update Iteration Summary row to ✅ Done.
```

**Come back at:** 2026-03-08 18:30 IST

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 2 merge commit.

**Iteration 3 agent task (paste verbatim):**
```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior TypeScript/React/Fluent UI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior TypeScript/React/Fluent UI engineer, I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-FIX-1-portal-defects.md
YOUR SCOPE: Iteration 3 only — Epics E7, E8, E9. Do not touch other iterations.
TIME BUDGET: 2h.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(PP-FIX-1): iteration 2
  If not: post "Blocked: Iteration 2 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 3" sections. Read nothing else.
3. Execute: E7 → E8 → E9. Open iteration PR when done. Post URL. HALT.
4. After each story: update Tracking Table to 🟢 Done, commit, push.
5. After each epic: post "**Epic Exx complete ✅**" under epic heading, commit, push.
6. After all iteration epics: update Iteration Summary row to ✅ Done.
```

**Come back at:** 2026-03-09 10:00 IST

---

### Iteration 4

> ⚠️ Do NOT launch until Iteration 3 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 3 merge commit.

**Iteration 4 agent task (paste verbatim):**
```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior TypeScript/React/Fluent UI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior TypeScript/React/Fluent UI engineer, I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-FIX-1-portal-defects.md
YOUR SCOPE: Iteration 4 only — Epics E10, E11. Do not touch other iterations.
TIME BUDGET: 1.5h.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(PP-FIX-1): iteration 3
  If not: post "Blocked: Iteration 3 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 4" sections. Read nothing else.
3. Execute: E10 → E11. Open iteration PR when done. Post URL. HALT.
4. After each story: update Tracking Table to 🟢 Done, commit, push.
5. After each epic: post "**Epic Exx complete ✅**" under epic heading, commit, push.
6. After all iteration epics: update Iteration Summary row to ✅ Done.
```

**Come back at:** 2026-03-09 11:30 IST

<!-- END CHUNK 3 -->

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas
Read the `EXPERT PERSONAS:` field from your task. Activate each persona now. Open every epic with:
> *"Acting as a [persona], I will [what you're building] by [approach]."*

### Rule 0 — Open tracking draft PR first (before writing any code)
```bash
git checkout main && git pull
git checkout -b feat/PP-FIX-1-itN-eN
git commit --allow-empty -m "chore(PP-FIX-1): start iteration N"
git push origin feat/PP-FIX-1-itN-eN

gh pr create \
  --base main \
  --head feat/PP-FIX-1-itN-eN \
  --draft \
  --title "tracking: PP-FIX-1 Iteration N — in progress" \
  --body "## tracking: PP-FIX-1 Iteration N
Subscribe to this PR for story completion notifications.
### Stories
- [ ] [story IDs from this iteration's Tracking Table rows]
_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/PP-FIX-1-itN-eN`.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing. Run the exact test command in the card.

### Rule 4 — Commit + push + mark done after every story
```bash
git add -A
git commit -m "feat(PP-FIX-1): [story title]"
git push origin feat/PP-FIX-1-itN-eN

# Update Tracking Table: change story status to 🟢 Done
git add docs/PP/iterations/PP-FIX-1-portal-defects.md
git commit -m "docs(PP-FIX-1): mark [story-id] done"
git push origin feat/PP-FIX-1-itN-eN
```

### Rule 5 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```
Exit 0 → add `**Epic Exx complete ✅**` under the epic heading in this plan file, commit, push.
Non-zero → fix on same branch, retry. Max 3 attempts. Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/PP-FIX-1-itN-eN
gh pr create \
  --base main \
  --head feat/PP-FIX-1-itN-eN \
  --title "WIP: [story-id] — blocked" \
  --draft \
  --body "Blocked on: [test name]
Error: [exact error message]
Attempted fixes:
1. [what I tried]
2. [what I tried]"
```
Post the draft PR URL. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
```bash
git checkout main && git pull
git checkout -b feat/PP-FIX-1-itN
git merge --no-ff feat/PP-FIX-1-itN-e1 feat/PP-FIX-1-itN-e2  # merge all epic branches
git push origin feat/PP-FIX-1-itN

gh pr create \
  --base main \
  --head feat/PP-FIX-1-itN \
  --title "feat(PP-FIX-1): iteration N — [one-line summary]" \
  --body "## PP-FIX-1 Iteration N
### Stories completed
[paste Tracking Table rows for this iteration]
### Docker integration: all containers exited 0 ✅
### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] No env-specific values in code
- [ ] Tests >= 80% coverage on new BE code
- [ ] FE: loading + error + empty states on data-fetching components"
```
Post the PR URL. **HALT.**

### CHECKPOINT RULE
After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(PP-FIX-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

<!-- END CHUNK 4 -->

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: Construct health reaches Plant without 401 | Fix construct_diagnostics.py double-v1 prefixes | 🟢 Done | — |
| E2-S1 | 1 | E2: Operators see live subscription list | Fix ops_subscriptions.py list route path | 🟢 Done | — |
| E2-S2 | 1 | E2: Operators see live subscription list | Fix ops_subscriptions.py single-get route path | 🟢 Done | — |
| E3-S1 | 1 | E3: Operators see live hired-agent list | Fix ops_hired_agents.py list route path | 🟢 Done | — |
| E4-S1 | 2 | E4: Operators fetch a hired agent by instance ID | Add GET /hired-agents/{id} to Plant | 🔴 Not Started | — |
| E5-S1 | 2 | E5: Demo Login button appears on pp.demo.waooaw.com | Fix allowDemoLogin condition in App.tsx | 🔴 Not Started | — |
| E6-S1 | 2 | E6: Review Queue requires explicit IDs | Clear hardcoded demo IDs in ReviewQueue.tsx | 🔴 Not Started | — |
| E7-S1 | 3 | E7: Nav labels match actual page content | Fix nav labels and page titles | 🔴 Not Started | — |
| E8-S1 | 3 | E8: Nav icons are distinct and pages are grouped | Assign unique icons + section headers | 🔴 Not Started | — |
| E9-S1 | 3 | E9: Operators look up customers by email | Add email lookup to HiredAgentsOps | 🔴 Not Started | — |
| E10-S1 | 4 | E10: Dashboard shows real agent count | Wire listAgents, null fake MRR/Churn/Customers | 🔴 Not Started | — |
| E11-S1 | 4 | E11: No hardcoded agent type IDs + section divider | Audit AgentManagement.tsx for hardcoded IDs | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

<!-- END CHUNK 5 -->

---

## Iteration 1 — Critical backend path fixes unblocking the OPS portal

**Scope:** Fix all Plant path mismatches in PP Backend and Plant Backend so subscriptions + hired agents load successfully on `pp.demo.waooaw.com`.
**Lane:** A (all existing Plant endpoints — just fixed paths)
**⏱ Estimated:** 2.5h | **Come back:** 2026-03-08 17:00 IST
**Epics:** E1, E2, E3

### Dependency Map (Iteration 1)

```
E1-S1  (independent — Plant Backend, own branch)
E2-S1 ──► E2-S2  (same branch; E2-S2 starts after E2-S1 committed)
E3-S1  (independent — PP Backend, own branch)
```

---

### Epic E1: Construct health reaches Plant without 401 (DEF-005)

**Branch:** `feat/PP-FIX-1-it1-e1`
**User story:** As an operator, when I expand a hired-agent row to view construct health or scheduler diagnostics, the data loads without 401 errors.

---

#### Story E1-S1: Fix double-v1 prefixes in construct_diagnostics.py

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/PP-FIX-1-it1-e1`

**What to do:**
`src/Plant/BackEnd/api/v1/construct_diagnostics.py` declares two routers with their own `/v1` prefix. These routers are already mounted inside `api_v1_router` (prefix `/api/v1`) in `src/Plant/BackEnd/api/v1/router.py`, so FastAPI concatenates to `/api/v1/v1/...`. Fix: remove the inner `/v1` from both router prefixes.
- Line 24: `router = waooaw_router(prefix="/v1/hired-agents", ...)` → change to `prefix="/hired-agents"`
- Line 284: `ops_router = waooaw_router(prefix="/v1/ops", ...)` → change to `prefix="/ops"`
Also update the test file `src/Plant/BackEnd/tests/test_construct_diagnostics_api.py`: every URL path that currently says `/api/v1/v1/hired-agents/...` or `/api/v1/v1/ops/...` must be changed to `/api/v1/hired-agents/...` and `/api/v1/ops/...`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/construct_diagnostics.py` | 20–30 | Line 24 — current prefix `/v1/hired-agents` |
| `src/Plant/BackEnd/api/v1/construct_diagnostics.py` | 280–290 | Line 284 — current prefix `/v1/ops` |
| `src/Plant/BackEnd/tests/test_construct_diagnostics_api.py` | 1–60 | All URL strings using `/api/v1/v1/` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/construct_diagnostics.py` | modify | Line 24: change `prefix="/v1/hired-agents"` to `prefix="/hired-agents"`. Line 284: change `prefix="/v1/ops"` to `prefix="/ops"`. |
| `src/Plant/BackEnd/tests/test_construct_diagnostics_api.py` | modify | Replace every `/api/v1/v1/hired-agents` with `/api/v1/hired-agents` and every `/api/v1/v1/ops` with `/api/v1/ops`. |

**Code patterns to copy exactly:**
```python
# waooaw_router — correct usage (no inner /v1 when already inside api_v1_router):
from core.routing import waooaw_router
router = waooaw_router(prefix="/hired-agents", tags=["construct-diagnostics"])
ops_router = waooaw_router(prefix="/ops", tags=["ops-diagnostics"])
```

**Acceptance criteria:**
1. `GET /api/v1/hired-agents/{id}/construct-health` returns 404 (unknown ID) — NOT 401 or 404-from-wrong-path.
2. `GET /api/v1/ops/dlq` returns 200 or 404 — NOT 401.
3. All existing construct_diagnostics tests pass with updated path strings.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/test_construct_diagnostics_api.py` | existing test updated | Path `/api/v1/hired-agents/{id}/construct-health` returns 404 for unknown ID |
| E1-S1-T2 | same | existing test updated | Path `/api/v1/ops/dlq` reachable |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-backend-test pytest src/Plant/BackEnd/tests/test_construct_diagnostics_api.py -v
```

**Commit message:** `fix(PP-FIX-1): remove double-v1 prefix from construct_diagnostics routers`

**Done signal:** `"E1-S1 done. Changed: construct_diagnostics.py lines 24+284, test_construct_diagnostics_api.py path strings. Tests: T1 ✅ T2 ✅"`

<!-- END CHUNK 6 -->

---

### Epic E2: Operators see live subscription data (DEF-001, DEF-002)

**Branch:** `feat/PP-FIX-1-it1-e2`
**User story:** As an operator, when I load the Hired Agents page for a customer, the subscription list loads with live data from Plant.

---

#### Story E2-S1: Fix list_subscriptions route — wrong path + wrong param style (DEF-001)

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PP-FIX-1-it1-e2`

**What to do:**
`src/PP/BackEnd/api/ops_subscriptions.py` `list_subscriptions` function (line 32) calls `plant_path = "/api/v1/subscriptions"` which does not exist in Plant. The correct Plant endpoint for listing a customer's subscriptions is `GET /api/v1/payments/subscriptions/by-customer/{customer_id}`. The current code also passes `customer_id` as a query param; it must be extracted and injected as a path segment.

Change:
```python
# OLD (line 32):
plant_path = "/api/v1/subscriptions"
```
To:
```python
# NEW — extract customer_id from query params, inject as path segment:
params = dict(request.query_params)
customer_id = params.pop("customer_id", None)
if not customer_id:
    raise HTTPException(status_code=400, detail="customer_id is required")
plant_path = f"/api/v1/payments/subscriptions/by-customer/{customer_id}"
```
The cache key must also change to include the new plant_path (it uses `plant_path` already — no extra change needed there).

Also update `src/PP/BackEnd/tests/test_ops_subscriptions.py`:
- `test_list_subscriptions_forwards_query_params`: currently asserts `params == {"customer_id": "C1", "status": "active"}`. Change to assert `customer_id` is in the **path** (not params) i.e. assert `plant._request.call_args.kwargs["path"]` ends with `/by-customer/C1` and `params == {"status": "active"}`.
- Add test `test_list_subscriptions_returns_400_without_customer_id`: call without `customer_id` query param → assert 400.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/api/ops_subscriptions.py` | 1–60 | Full list_subscriptions function, cache_get/cache_set usage |
| `src/PP/BackEnd/tests/test_ops_subscriptions.py` | 1–80 | Existing test assertions to update |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/api/ops_subscriptions.py` | modify | Replace `plant_path = "/api/v1/subscriptions"` and fix params extraction as shown above |
| `src/PP/BackEnd/tests/test_ops_subscriptions.py` | modify | Fix `test_list_subscriptions_forwards_query_params`; add `test_list_subscriptions_returns_400_without_customer_id` |

**Code patterns to copy exactly:**
```python
# PP Backend proxy pattern — extract path param from query, call Plant:
params = dict(request.query_params)
customer_id = params.pop("customer_id", None)
if not customer_id:
    raise HTTPException(status_code=400, detail="customer_id is required")
plant_path = f"/api/v1/payments/subscriptions/by-customer/{customer_id}"

cached = await cache_get("subs", plant_path, params)
if cached is not None:
    return cached

resp = await client._request(
    method="GET",
    path=plant_path,
    params=params or None,
    headers={"Authorization": auth_header} if auth_header else None,
)
```

**Acceptance criteria:**
1. `GET /api/pp/ops/subscriptions?customer_id=C1&status=active` calls Plant at `/api/v1/payments/subscriptions/by-customer/C1` with `params={"status": "active"}`.
2. `GET /api/pp/ops/subscriptions` (no customer_id) returns 400.
3. Plant 200 response is returned as-is and cached.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/PP/BackEnd/tests/test_ops_subscriptions.py` | mock Plant 200; call with `?customer_id=C1&status=active` | `plant._request.call_args.kwargs["path"]` == `/api/v1/payments/subscriptions/by-customer/C1`; params == `{"status":"active"}` |
| E2-S1-T2 | same | call without customer_id | response 400 |
| E2-S1-T3 | same | existing 200+list test | still passes |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-backend-test pytest src/PP/BackEnd/tests/test_ops_subscriptions.py -v
```

**Commit message:** `fix(PP-FIX-1): fix list_subscriptions path to payments/subscriptions/by-customer`

**Done signal:** `"E2-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E2-S2: Fix get_subscription route — missing /payments segment (DEF-002)

**BLOCKED UNTIL:** E2-S1 committed to `feat/PP-FIX-1-it1-e2`
**Estimated time:** 15 min
**Branch:** `feat/PP-FIX-1-it1-e2` (same branch, continue from E2-S1)

**What to do:**
`src/PP/BackEnd/api/ops_subscriptions.py` `get_subscription` function (line 62) calls `plant_path = f"/api/v1/subscriptions/{subscription_id}"`. Change to `plant_path = f"/api/v1/payments/subscriptions/{subscription_id}"`.

Also add test `test_get_subscription_uses_payments_path` to `test_ops_subscriptions.py`: mock Plant 200; call `GET /api/pp/ops/subscriptions/sub-1`; assert `plant._request.call_args.kwargs["path"]` == `/api/v1/payments/subscriptions/sub-1`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/api/ops_subscriptions.py` | 55–85 | Line 62 — current plant_path for get_subscription |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/api/ops_subscriptions.py` | modify | Line 62: change `"/api/v1/subscriptions/{subscription_id}"` → `"/api/v1/payments/subscriptions/{subscription_id}"` |
| `src/PP/BackEnd/tests/test_ops_subscriptions.py` | modify | Add `test_get_subscription_uses_payments_path` |

**Code patterns to copy exactly:**
```python
# Single-get fix — just the path change:
plant_path = f"/api/v1/payments/subscriptions/{subscription_id}"
```

**Acceptance criteria:**
1. `GET /api/pp/ops/subscriptions/sub-1` calls Plant at `/api/v1/payments/subscriptions/sub-1`.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/PP/BackEnd/tests/test_ops_subscriptions.py` | mock Plant 200; call `GET /pp/ops/subscriptions/sub-1` | path == `/api/v1/payments/subscriptions/sub-1` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-backend-test pytest src/PP/BackEnd/tests/test_ops_subscriptions.py -v
```

**Commit message:** `fix(PP-FIX-1): fix get_subscription path to payments/subscriptions/{id}`

**Done signal:** `"E2-S2 done. Tests: T1 ✅"`

<!-- END CHUNK 7 -->

---

### Epic E3: Operators see live hired-agent list (DEF-003)

**Branch:** `feat/PP-FIX-1-it1-e3`
**User story:** As an operator, after subscriptions load, the hired agent list for each subscription loads correctly.

---

#### Story E3-S1: Fix list_hired_agents route — wrong path + wrong param style (DEF-003)

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PP-FIX-1-it1-e3`

**What to do:**
`src/PP/BackEnd/api/ops_hired_agents.py` `list_hired_agents` function (line 44) calls `plant_path = "/api/v1/hired-agents"` with `subscription_id` as a query param. Plant has no root list GET on the `/hired-agents` router.

**CRITICAL:** Plant's `GET /api/v1/hired-agents/by-subscription/{subscription_id}` (in `hired_agents_simple.py` line 871) returns a **single** `HiredAgentInstanceResponse` object, NOT a list. The PP backend must wrap it in a list before returning.

Change the function to:
```python
params = dict(request.query_params)
subscription_id = params.pop("subscription_id", None)
customer_id = params.pop("customer_id", None)

if subscription_id:
    plant_path = f"/api/v1/hired-agents/by-subscription/{subscription_id}"
elif customer_id:
    plant_path = f"/api/v1/hired-agents/by-customer/{customer_id}"
else:
    raise HTTPException(status_code=400, detail="subscription_id or customer_id is required")
```
After getting the Plant response, check: if `by-subscription` was called and the response is a `dict` (not a list), wrap it: `body = [body]` before returning.

Also update `src/PP/BackEnd/tests/test_ops_hired_agents.py`:
- `test_list_hired_agents_forwards_query_params`: change to assert subscription_id is in the **path**, not params.
- Add `test_list_hired_agents_wraps_single_object_response`: when Plant returns a dict (by-subscription), assert PP returns a list of length 1.
- Add `test_list_hired_agents_returns_400_without_ids`: call without subscription_id or customer_id → assert 400.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/api/ops_hired_agents.py` | 1–80 | Full list_hired_agents function |
| `src/PP/BackEnd/tests/test_ops_hired_agents.py` | 1–60 | Existing tests to update |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/api/ops_hired_agents.py` | modify | Replace `list_hired_agents` function body as described above |
| `src/PP/BackEnd/tests/test_ops_hired_agents.py` | modify | Fix `test_list_hired_agents_forwards_query_params`; add T2 and T3 |

**Code patterns to copy exactly:**
```python
# PP Backend: extract path param, route on subscription_id or customer_id:
params = dict(request.query_params)
subscription_id = params.pop("subscription_id", None)
customer_id = params.pop("customer_id", None)

if subscription_id:
    plant_path = f"/api/v1/hired-agents/by-subscription/{subscription_id}"
elif customer_id:
    plant_path = f"/api/v1/hired-agents/by-customer/{customer_id}"
else:
    raise HTTPException(status_code=400, detail="subscription_id or customer_id is required")

resp = await client._request(
    method="GET",
    path=plant_path,
    params=params or None,
    headers={"Authorization": auth_header} if auth_header else None,
)
if resp.status_code == 200:
    body = resp.json()
    # by-subscription returns a single object; normalize to list
    if isinstance(body, dict):
        body = [body]
    await audit.log("pp_ops", "hired_agents_listed", "success")
    return body
raise HTTPException(status_code=resp.status_code, detail=resp.text)
```

**Acceptance criteria:**
1. `GET /api/pp/ops/hired-agents?subscription_id=sub-1` calls Plant at `/api/v1/hired-agents/by-subscription/sub-1`.
2. If Plant returns a single dict, PP returns a list with that one item.
3. `GET /api/pp/ops/hired-agents?customer_id=C1` calls Plant at `/api/v1/hired-agents/by-customer/C1`.
4. No subscription_id or customer_id → 400.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/PP/BackEnd/tests/test_ops_hired_agents.py` | mock Plant 200 `{"hired_instance_id":"i1",...}`; call with `?subscription_id=sub-1` | path == `/api/v1/hired-agents/by-subscription/sub-1`; response is a list of length 1 |
| E3-S1-T2 | same | mock Plant 200 `[{...}]`; call with `?customer_id=C1` | path == `/api/v1/hired-agents/by-customer/C1` |
| E3-S1-T3 | same | call without any ID param | response 400 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-backend-test pytest src/PP/BackEnd/tests/test_ops_hired_agents.py -v
```

**Commit message:** `fix(PP-FIX-1): fix list_hired_agents to use by-subscription path param`

**Done signal:** `"E3-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

**Iteration 1 Done Signal:** Three PRs merged to main. All 4 stories 🟢 Done in Tracking Table. Live test: `curl -s -H "Authorization: Bearer $TOKEN" "https://pp.demo.waooaw.com/api/pp/ops/subscriptions?customer_id=<UUID>"` returns 200.

<!-- END CHUNK 8 -->

---

## Iteration 2 — Missing Plant endpoint + Demo Login button + hardcoded IDs

**Scope:** Add the missing `GET /hired-agents/{id}` Plant endpoint, fix the Demo Login button on demo env, and clear hardcoded test IDs from ReviewQueue.
**Lane:** B for E4 (new Plant endpoint). A for E5, E6 (FE-only fixes).
**⏱ Estimated:** 1.5h | **Come back:** 2026-03-08 18:30 IST
**Epics:** E4, E5, E6

### Dependency Map (Iteration 2)

```
E4-S1  (Plant Backend, own branch — Lane B)
E5-S1  (PP FrontEnd, own branch — independent)
E6-S1  (PP FrontEnd, own branch — independent)
```

---

### Epic E4: Operators fetch a hired agent by instance ID (DEF-004)

**Branch:** `feat/PP-FIX-1-it2-e4`
**User story:** As an operator, when the PP backend calls `GET /pp/ops/hired-agents/{id}`, Plant returns the single hired agent record.

---

#### Story E4-S1: Add GET /hired-agents/{hired_instance_id} to Plant

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PP-FIX-1-it2-e4`

**What to do:**
`src/Plant/BackEnd/api/v1/hired_agents_simple.py` has no bare `GET /{hired_instance_id}` route. Add it after the existing `GET /by-customer/{customer_id}` route (around line 989).

The helper function `_get_record_by_id` already exists and calls `HiredAgentRepository(db).get_by_id(hired_instance_id)`. The response model `HiredAgentInstanceResponse` already exists. Use `_get_read_hired_agents_db_session` as the DB session dependency (already defined in the file) — this is the read-replica session for GET routes.

Add:
```python
@router.get("/{hired_instance_id}", response_model=HiredAgentInstanceResponse)
async def get_hired_agent_by_id(
    hired_instance_id: str,
    db: AsyncSession | None = Depends(_get_read_hired_agents_db_session),
) -> HiredAgentInstanceResponse:
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")
    return _to_response(record)
```

**IMPORTANT:** This route must be added AFTER `by-subscription` and `by-customer` routes (lines 871 and 916), and BEFORE `/{hired_instance_id}/goals` (line 991) — otherwise FastAPI route matching will conflict.

Add test `test_get_hired_agent_by_id_returns_200` and `test_get_hired_agent_by_id_returns_404` to `src/Plant/BackEnd/tests/unit/test_hired_agents_api.py`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | 871–995 | by-subscription/by-customer routes + _get_record_by_id helper position |
| `src/Plant/BackEnd/tests/unit/test_hired_agents_api.py` | 1–50 | Existing test pattern to copy |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | modify | Add GET `/{hired_instance_id}` route between line 989 and line 991 as shown above |
| `src/Plant/BackEnd/tests/unit/test_hired_agents_api.py` | modify | Add two tests: 200 for known ID, 404 for unknown |

**Code patterns to copy exactly:**
```python
# New GET-by-ID route — paste between by-customer and /{id}/goals:
@router.get("/{hired_instance_id}", response_model=HiredAgentInstanceResponse)
async def get_hired_agent_by_id(
    hired_instance_id: str,
    db: AsyncSession | None = Depends(_get_read_hired_agents_db_session),
) -> HiredAgentInstanceResponse:
    """Get a single hired agent instance by its ID (read-replica, no auth required for PP ops)."""
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")
    return _to_response(record)
```

**Acceptance criteria:**
1. `GET /api/v1/hired-agents/{known_id}` returns 200 with `HiredAgentInstanceResponse` fields.
2. `GET /api/v1/hired-agents/nonexistent` returns 404.
3. Route does not conflict with `/by-subscription/`, `/by-customer/`, or `/{id}/goals`.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/Plant/BackEnd/tests/unit/test_hired_agents_api.py` | Create a draft hired agent via PUT /draft, then GET /{hired_instance_id} | 200 + `hired_instance_id` in response |
| E4-S1-T2 | same | GET /api/v1/hired-agents/nonexistent-id | 404 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-backend-test pytest src/Plant/BackEnd/tests/unit/test_hired_agents_api.py -v
```

**Commit message:** `feat(PP-FIX-1): add GET /hired-agents/{hired_instance_id} to Plant Backend`

**Done signal:** `"E4-S1 done. Tests: T1 ✅ T2 ✅"`

<!-- END CHUNK 9 -->

---

### Epic E5: Demo Login button appears on pp.demo.waooaw.com (DEF-011)

**Branch:** `feat/PP-FIX-1-it2-e5`
**User story:** As a tester on `pp.demo.waooaw.com`, I see the Demo Login button so I can get a dev token from the UI.

---

#### Story E5-S1: Fix allowDemoLogin condition in App.tsx

**BLOCKED UNTIL:** none
**Estimated time:** 15 min
**Branch:** `feat/PP-FIX-1-it2-e5`

**What to do:**
`src/PP/FrontEnd/src/App.tsx` line 85 has:
```typescript
const allowDemoLogin = config.name === 'codespace' || config.name === 'development'
```
The deployed demo env has `config.name === 'demo'`. Add it to the condition:
```typescript
const allowDemoLogin = config.name === 'codespace' || config.name === 'development' || config.name === 'demo'
```

No new test file needed — this is a one-line boolean fix. Add a comment above the line: `// demo env also shows the button (PP-FIX-1 DEF-011)`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/App.tsx` | 80–95 | Line 85 — current allowDemoLogin condition |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/App.tsx` | modify | Line 85: add `\|\| config.name === 'demo'` to allowDemoLogin condition |

**Code patterns to copy exactly:**
```typescript
// PP-FIX-1 DEF-011: demo env also shows the Dev Token login button
const allowDemoLogin = config.name === 'codespace' || config.name === 'development' || config.name === 'demo'
```

**Acceptance criteria:**
1. When `config.name` is `'demo'`, `allowDemoLogin` is `true`.
2. When `config.name` is `'production'`, `allowDemoLogin` is `false`.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S1-T1 | `src/PP/FrontEnd/src/__tests__/App.test.tsx` (create if absent) | Mock `config.name = 'demo'`; render App | Demo Login button present in DOM |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run --no-coverage
```

**Commit message:** `fix(PP-FIX-1): show Demo Login button on demo environment`

**Done signal:** `"E5-S1 done. Tests: T1 ✅"`

---

### Epic E6: Review Queue requires explicit IDs (DEF-010)

**Branch:** `feat/PP-FIX-1-it2-e6`
**User story:** As an operator opening the Review Queue page, the Customer ID and Agent ID inputs are empty so I must enter real values.

---

#### Story E6-S1: Clear hardcoded demo IDs in ReviewQueue.tsx

**BLOCKED UNTIL:** none
**Estimated time:** 15 min
**Branch:** `feat/PP-FIX-1-it2-e6`

**What to do:**
`src/PP/FrontEnd/src/pages/ReviewQueue.tsx` lines 30–31:
```typescript
const [customerId, setCustomerId] = useState('CUST-001')   // line 30
const [agentId, setAgentId] = useState('AGT-MKT-HEALTH-001')  // line 31
```
Change both to empty strings:
```typescript
const [customerId, setCustomerId] = useState('')
const [agentId, setAgentId] = useState('')
```

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/pages/ReviewQueue.tsx` | 28–35 | Lines 30-31 — useState with hardcoded IDs |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/pages/ReviewQueue.tsx` | modify | Line 30: `useState('')`. Line 31: `useState('')`. |

**Code patterns to copy exactly:**
```typescript
const [customerId, setCustomerId] = useState('')
const [agentId, setAgentId] = useState('') 
```

**Acceptance criteria:**
1. On page load, Customer ID input is empty.
2. On page load, Agent ID input is empty.
3. No `CUST-001` or `AGT-MKT-HEALTH-001` strings remain in the file.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E6-S1-T1 | `src/PP/FrontEnd/src/__tests__/ReviewQueue.test.tsx` (create if absent) | Render ReviewQueue | Customer ID input value is `""` |
| E6-S1-T2 | same | Render ReviewQueue | Agent ID input value is `""` |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run --no-coverage
```

**Commit message:** `fix(PP-FIX-1): remove hardcoded demo IDs from ReviewQueue`

**Done signal:** `"E6-S1 done. Tests: T1 ✅ T2 ✅"`

---

**Iteration 2 Done Signal:** Three PRs merged to main. All stories 🟢 Done. Live test: Demo Login button visible on `pp.demo.waooaw.com`.

<!-- END CHUNK 10 -->

---

## Iteration 3 — Nav/label accuracy + email customer lookup

**Scope:** Fix misleading nav labels and page titles, deduplicate nav icons, add email-to-customer-ID lookup on HiredAgentsOps page.
**Lane:** A (PP FrontEnd only — all Plant endpoints already exist)
**⏱ Estimated:** 2h | **Come back:** 2026-03-09 10:00 IST
**Epics:** E7, E8, E9

### Dependency Map (Iteration 3)

```
E7-S1  (independent — nav labels + page titles)
E8-S1  (independent — icons + section headers)
E9-S1  (independent — email lookup)
```

---

### Epic E7: Nav labels match actual page content (DEF-007, DEF-008, DEF-009)

**Branch:** `feat/PP-FIX-1-it3-e7`
**User story:** As an operator, each nav item label describes what I'll actually find on that page.

---

#### Story E7-S1: Fix nav labels and page titles for Customers, Governor, Billing

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/PP-FIX-1-it3-e7`

**What to do:**
Four changes across four files:

1. `src/PP/FrontEnd/src/components/Layout.tsx` line 37: `label: 'Customers'` → `label: 'Usage Events'`
2. `src/PP/FrontEnd/src/components/Layout.tsx` line 44: `label: 'Governor'` → `label: 'Reference Agents'`  
   *(Note: line numbers are approximate — read the file to confirm. The `{ path: '/customers', ...}` and `{ path: '/governor', ...}` items are the targets.)*
3. `src/PP/FrontEnd/src/pages/CustomerManagement.tsx` line 113: `Customer Management` → `Usage Events`
4. `src/PP/FrontEnd/src/pages/GovernorConsole.tsx` line 131: `Governor Console` → `Reference Agents`
5. `src/PP/FrontEnd/src/pages/Billing.tsx` lines 34–35: `Billing & Revenue` (the h1 text) → `Subscription Overview`

Do NOT rename the Billing nav item in Layout.tsx (it is already `'Billing'` which is close enough; only the page h1 title needs updating).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/components/Layout.tsx` | 29–50 | navItems array — find `/customers` and `/governor` entries |
| `src/PP/FrontEnd/src/pages/CustomerManagement.tsx` | 110–118 | h1 text on line 113 |
| `src/PP/FrontEnd/src/pages/GovernorConsole.tsx` | 128–135 | h1 text on line 131 |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/components/Layout.tsx` | modify | `/customers` nav item: `label` → `'Usage Events'`. `/governor` nav item: `label` → `'Reference Agents'`. |
| `src/PP/FrontEnd/src/pages/CustomerManagement.tsx` | modify | Line 113: `Customer Management` → `Usage Events` |
| `src/PP/FrontEnd/src/pages/GovernorConsole.tsx` | modify | Line 131: `Governor Console` → `Reference Agents` |
| `src/PP/FrontEnd/src/pages/Billing.tsx` | modify | h1 text `Billing & Revenue` → `Subscription Overview` |

**Code patterns to copy exactly:**
```typescript
// Layout.tsx nav item change:
{ path: '/customers', label: 'Usage Events', icon: <Database24Regular /> },
{ path: '/governor', label: 'Reference Agents', icon: <Beaker24Regular /> },

// Page h1 patterns:
<Text as="h1" size={900} weight="semibold">Usage Events</Text>
<Text as="h1" size={900} weight="semibold">Reference Agents</Text>
<Text as="h1" size={900} weight="semibold">Subscription Overview</Text>
```

**Acceptance criteria:**
1. Nav shows "Usage Events" for `/customers` route.
2. Nav shows "Reference Agents" for `/governor` route.
3. CustomerManagement page h1 reads "Usage Events".
4. GovernorConsole page h1 reads "Reference Agents".
5. Billing page h1 reads "Subscription Overview".

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E7-S1-T1 | `src/PP/FrontEnd/src/__tests__/Layout.test.tsx` (create if absent) | Render Layout | "Usage Events" in nav, "Governor" not in nav |
| E7-S1-T2 | same | Render Layout | "Reference Agents" in nav |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run --no-coverage
```

**Commit message:** `fix(PP-FIX-1): fix nav labels and page titles to match actual content`

**Done signal:** `"E7-S1 done. Tests: T1 ✅ T2 ✅"`

<!-- END CHUNK 11 -->

---

### Epic E8: Nav icons are distinct and pages are grouped (DEF-013)

**Branch:** `feat/PP-FIX-1-it3-e8`
**User story:** As an operator scanning the nav, I can visually distinguish each item by its icon and find items by their logical group.

---

#### Story E8-S1: Assign unique icons and add section headers to Layout.tsx

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PP-FIX-1-it3-e8`

**What to do:**
`src/PP/FrontEnd/src/components/Layout.tsx` currently has:
- `ShieldTask24Regular` used on 4 items (Approvals Queue, Review Queue, Audit, Governor/Policy Denials)
- `Bot24Regular` used on 3 items (Agent Management, Agent Setup, Agent Type Setup)
- 16 flat items with no grouping

Changes:
1. Add new icon imports from `@fluentui/react-icons` (they are already installed):
   - `DocumentCheckmark24Regular` for Approvals Queue
   - `DocumentEdit24Regular` for Review Queue (rename label to `'Draft Review'`)
   - `ClipboardTask24Regular` for Audit
   - `AlertBadge24Regular` for Policy Denials
2. Add section headers by inserting divider objects into the navItems array. Represent them as `{ type: 'section', label: 'Operations' }` etc., and render them as non-clickable `<Text>` headers in the nav.

Section grouping:
- **Operations:** Dashboard, Hired Agents, Usage Events (Customers), Subscriptions (Billing)
- **Management:** Agent Management, Agent Setup, Agent Type Setup, Reference Agents (Governor)
- **Compliance:** Approvals Queue, Draft Review (Review Queue), Audit, Policy Denials
- **Tools:** AgentSpec Tools, Genesis, DB Updates

3. Keep the existing `navItems.map(...)` logic but handle the new `type: 'section'` entries to render as section headers.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/components/Layout.tsx` | 1–100 | Full file — imports, navItems array, render logic |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/components/Layout.tsx` | modify | Add icon imports; update navItems with distinct icons and section header objects; update render logic to handle `type: 'section'` items as non-link headers. |

**Code patterns to copy exactly:**
```typescript
// Import new icons (add to existing import from '@fluentui/react-icons'):
import {
  DocumentCheckmark24Regular,
  DocumentEdit24Regular,
  ClipboardTask24Regular,
  AlertBadge24Regular,
} from '@fluentui/react-icons'

// navItems with section headers (type: 'section' = non-link divider):
type NavItem =
  | { type?: undefined; path: string; label: string; icon: ReactNode }
  | { type: 'section'; label: string }

const navItems: NavItem[] = [
  { type: 'section', label: 'Operations' },
  { path: '/', label: 'Dashboard', icon: <Home24Regular /> },
  { path: '/hired-agents', label: 'Hired Agents', icon: <People24Regular /> },
  { path: '/customers', label: 'Usage Events', icon: <Database24Regular /> },
  { path: '/billing', label: 'Subscriptions', icon: <Money24Regular /> },
  { type: 'section', label: 'Management' },
  { path: '/agents', label: 'Agent Management', icon: <Bot24Regular /> },
  { path: '/agent-setup', label: 'Agent Setup', icon: <Bot24Regular /> },
  { path: '/agent-type-setup', label: 'Agent Type Setup', icon: <Certificate24Regular /> },
  { path: '/governor', label: 'Reference Agents', icon: <Beaker24Regular /> },
  { path: '/genesis', label: 'Genesis', icon: <Certificate24Regular /> },
  { type: 'section', label: 'Compliance' },
  { path: '/approvals-queue', label: 'Approvals Queue', icon: <DocumentCheckmark24Regular /> },
  { path: '/review-queue', label: 'Draft Review', icon: <DocumentEdit24Regular /> },
  { path: '/audit', label: 'Audit', icon: <ClipboardTask24Regular /> },
  { path: '/policy-denials', label: 'Policy Denials', icon: <AlertBadge24Regular /> },
  { type: 'section', label: 'Tools' },
  { path: '/agent-spec-tools', label: 'AgentSpec Tools', icon: <Certificate24Regular /> },
  { path: '/db-updates', label: 'DB Updates', icon: <Database24Regular /> },
  { path: '/reference-agents', label: 'Reference Data', icon: <Beaker24Regular /> },
]

// Updated render (inside navItems.map):
{navItems.map((item, idx) => {
  if (item.type === 'section') {
    return (
      <Text key={`section-${idx}`} size={100} style={{ padding: '12px 16px 4px', color: 'var(--colorNeutralForeground3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {item.label}
      </Text>
    )
  }
  const active = item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path)
  return (
    <Link key={item.path} to={item.path} className={`nav-item ${active ? 'active' : ''}`}>
      {item.icon}
      <span>{item.label}</span>
    </Link>
  )
})}
```

**Acceptance criteria:**
1. Nav shows section headers "Operations", "Management", "Compliance", "Tools".
2. Approvals Queue, Draft Review, Audit, Policy Denials each have distinct icons.
3. Nav compiles and renders without TypeScript errors.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E8-S1-T1 | `src/PP/FrontEnd/src/__tests__/Layout.test.tsx` | Render Layout | "Operations" section header text present |
| E8-S1-T2 | same | Render Layout | "Draft Review" present; "Review Queue" not present as nav link |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run --no-coverage
```

**Commit message:** `fix(PP-FIX-1): assign unique nav icons and add section groupings`

**Done signal:** `"E8-S1 done. Tests: T1 ✅ T2 ✅"`

<!-- END CHUNK 12 -->

---

### Epic E9: Operators look up customers by email (DEF-014)

**Branch:** `feat/PP-FIX-1-it3-e9`
**User story:** As an operator, I type a customer's email address into the Hired Agents page and the system resolves it to a customer ID automatically.

---

#### Story E9-S1: Add email lookup to gatewayApiClient + HiredAgentsOps

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PP-FIX-1-it3-e9`

**What to do:**
Plant already has `GET /api/v1/customers/lookup?email={email}` (confirmed at `src/Plant/BackEnd/api/v1/customers.py` line 196). The PP frontend catch-all proxy forwards `/v1/*` routes to Plant.

**Step 1:** Add `lookupCustomerByEmail` to `src/PP/FrontEnd/src/services/gatewayApiClient.ts` (after the existing `getOpsConstructHealth` area, around line 404).

**Step 2:** Add email input + Lookup button to `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx`.
- The component currently has `customerId` state at line 116 already initialized to `''`.
- Add `email` state: `const [email, setEmail] = useState('')`
- Add `emailError` state: `const [emailError, setEmailError] = useState<string | null>(null)`
- Add a "Lookup" button that calls `lookupCustomerByEmail(email)` → on success sets `customerId`; on failure sets `emailError`.
- Place the email input + Lookup button above the existing Customer ID input (so the flow is: enter email → lookup → auto-fills Customer ID → load).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | 395–425 | Insertion point after getOpsConstructHealth |
| `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` | 115–145 | current state declarations and load() callback |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | modify | Add `lookupCustomerByEmail` method in the `gatewayApiClient` object |
| `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` | modify | Add `email` + `emailError` state; add email input + Lookup button in JSX |

**Code patterns to copy exactly:**
```typescript
// gatewayApiClient.ts — add this method in the exported object:
lookupCustomerByEmail: (email: string) =>
  gatewayRequestJson<{ customer_id: string; email: string; full_name?: string }>(
    `/v1/customers/lookup?email=${encodeURIComponent(email)}`
  ),
```

```typescript
// HiredAgentsOps.tsx — new state declarations (add after line 116):
const [email, setEmail] = useState('')
const [emailError, setEmailError] = useState<string | null>(null)

// Lookup handler (add as a callback in the component):
const lookupByEmail = useCallback(async () => {
  const e = email.trim()
  if (!e) return
  setEmailError(null)
  try {
    const result = await gatewayApiClient.lookupCustomerByEmail(e) as { customer_id: string }
    setCustomerId(result.customer_id)
  } catch {
    setEmailError('Customer not found for this email address.')
  }
}, [email])

// JSX — add above the Customer ID input:
<div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', marginBottom: 8 }}>
  <Field label="Customer Email">
    <Input
      placeholder="email@example.com"
      value={email}
      onChange={(_, d) => setEmail(d.value)}
    />
  </Field>
  <Button appearance="secondary" onClick={lookupByEmail}>Lookup</Button>
</div>
{emailError && <Text style={{ color: 'var(--colorPaletteRedForeground1)', fontSize: 12 }}>{emailError}</Text>}
```

**Acceptance criteria:**
1. Email input + Lookup button render above the Customer ID input.
2. Clicking Lookup with a valid email calls `GET /v1/customers/lookup?email=...` and populates Customer ID.
3. If email not found, error message "Customer not found for this email address." appears.
4. `lookupCustomerByEmail` is exported from `gatewayApiClient`.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E9-S1-T1 | `src/PP/FrontEnd/src/__tests__/HiredAgentsOps.test.tsx` (create if absent) | Mock `lookupCustomerByEmail` returns `{customer_id: "C1"}`; enter email and click Lookup | Customer ID input shows "C1" |
| E9-S1-T2 | same | Mock `lookupCustomerByEmail` throws; enter email and click Lookup | Error message visible in DOM |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run --no-coverage
```

**Commit message:** `feat(PP-FIX-1): add email-to-customer-id lookup on HiredAgentsOps page`

**Done signal:** `"E9-S1 done. Tests: T1 ✅ T2 ✅"`

---

**Iteration 3 Done Signal:** Three PRs merged to main. All stories 🟢 Done. Nav labels updated and email lookup operational on demo.

<!-- END CHUNK 13 -->

---

## Iteration 4 — Dashboard live data + final cleanup

**Prerequisites:** Iterations 1, 2, and 3 merged to main.
**Goal:** Replace the last hardcoded metric (Active Agents count) with a live API call. Mark the remaining static KPIs clearly as "coming soon". Audit AgentManagement for DEF-015 and add a proper Fluent Divider for DEF-012.
**Timeline:** 2 × 30-minute stories.

**Dependency map:**
- E10-S1 and E11-S1 are independent — run in parallel if desired.

---

### Epic E10: Dashboard shows live active-agent count (DEF-006)

**Branch:** `feat/PP-FIX-1-it4-e10`
**User story:** As a portal user, the Dashboard displays a real agent count pulled from the API rather than a hardcoded placeholder.

---

#### Story E10-S1: Wire Dashboard Active Agents card to listAgents API

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/PP-FIX-1-it4-e10`

**Context:** `src/PP/FrontEnd/src/pages/Dashboard.tsx` is ~40 lines. It renders 4 metric cards, all with hardcoded values. No imports from react hooks. `gatewayApiClient.listAgents()` exists at line 243 of `gatewayApiClient.ts` and returns the agents list. The PP Frontend proxy forwards `/pp/agents` → Plant.

**Files to read first (max 1):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/pages/Dashboard.tsx` | 1–40 | Full file — component structure, hardcoded values |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/pages/Dashboard.tsx` | modify | Add hooks; wire Active Agents; mark others "coming soon" |

**Code patterns to copy exactly:**
```tsx
// Dashboard.tsx — final shape after edit:
import React, { useEffect, useState } from 'react'
import { Text, Card, CardHeader, Spinner } from '@fluentui/react-components'
import { gatewayApiClient } from '../services/gatewayApiClient'

export const Dashboard: React.FC = () => {
  const [agentCount, setAgentCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    gatewayApiClient.listAgents()
      .then((agents: unknown[]) => setAgentCount(agents.length))
      .catch(() => setError('Failed to load'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ padding: 24 }}>
      <Text as="h1" size={900} weight="semibold" style={{ marginBottom: 24 }}>
        Dashboard
      </Text>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <Card>
          <CardHeader header={<Text weight="semibold">MRR</Text>} />
          <Text size={700}>N/A</Text>
          <Text size={200} style={{ color: '#888' }}>Coming soon</Text>
        </Card>
        <Card>
          <CardHeader header={<Text weight="semibold">Active Agents</Text>} />
          {loading ? (
            <Spinner size="tiny" />
          ) : error ? (
            <Text style={{ color: 'red' }}>—</Text>
          ) : (
            <Text size={700}>{agentCount ?? '—'}</Text>
          )}
        </Card>
        <Card>
          <CardHeader header={<Text weight="semibold">Customers</Text>} />
          <Text size={700}>N/A</Text>
          <Text size={200} style={{ color: '#888' }}>Coming soon</Text>
        </Card>
        <Card>
          <CardHeader header={<Text weight="semibold">Churn Rate</Text>} />
          <Text size={700}>N/A</Text>
          <Text size={200} style={{ color: '#888' }}>Coming soon</Text>
        </Card>
      </div>
    </div>
  )
}
```

**Acceptance criteria:**
1. Active Agents card calls `listAgents()` on mount and shows the returned count.
2. MRR, Customers, and Churn Rate cards show "N/A" + "Coming soon" subtitle.
3. During loading, a `Spinner` renders in the Active Agents card.
4. On API error, Active Agents card shows "—".
5. No hardcoded numbers in the file.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E10-S1-T1 | `src/PP/FrontEnd/src/__tests__/Dashboard.test.tsx` (create if absent) | Mock `listAgents` returns array of 5 items | "5" visible in DOM |
| E10-S1-T2 | same | Mock `listAgents` throws | "—" visible; "5" not in DOM |
| E10-S1-T3 | same | All 3 other KPI cards | "Coming soon" text visible 3 times |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run --no-coverage
```

**Commit message:** `feat(PP-FIX-1): wire Dashboard active-agent count to listAgents API`

**Done signal:** `"E10-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

<!-- END CHUNK 14 -->

---

### Epic E11: AgentManagement section divider + DEF-015 audit (DEF-012 + DEF-015)

**Branch:** `feat/PP-FIX-1-it4-e11`
**User story:** As a user, the AgentManagement page has a clear visual divider between the Agents table and the Agent Type Definitions section; hardcoded agent IDs do not exist anywhere in source.

---

#### Story E11-S1: Fluent Divider + confirm no hardcoded AGT-* IDs

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/PP-FIX-1-it4-e11`

**Context:**
- `src/PP/FrontEnd/src/pages/AgentManagement.tsx` currently separates the two sections with `<div style={{ height: 16 }} />` (confirmed around line 194).
- DEF-012 asks for a proper Fluent `<Divider />` component with visible margin.
- DEF-015 requires: confirm no `AGT-*` literals are hardcoded; add an explicit comment so future readers never need to re-audit.
- Agents are sourced from `listAgents()` (line 37). AgentTypes from `listAgentTypeDefinitions()` (line 59). No `AGT-` literals found in grep — DEF-015 audit passes.

**Files to read first (max 1):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/pages/AgentManagement.tsx` | 188–202 | Divider location and surrounding context |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/pages/AgentManagement.tsx` | modify | Replace spacer div with `<Divider>`; add audit comment |

**Code patterns to copy exactly:**
```typescript
// Step 1 — add Divider to the @fluentui/react-components import
// Find the existing import:
import { ..., Text } from '@fluentui/react-components'
// Add Divider to it (just add to the list):
import { ..., Divider, Text } from '@fluentui/react-components'

// Step 2 — replace the spacer div in JSX:
// OLD:
<div style={{ height: 16 }} />
// NEW:
{/* PP-FIX-1: DEF-015 audit — no hardcoded AGT-* IDs found; agents sourced from listAgents() */}
<Divider style={{ margin: '24px 0' }} />
```

**Acceptance criteria:**
1. `import { Divider }` present in `AgentManagement.tsx`.
2. `<Divider style={{ margin: '24px 0' }} />` exists in JSX where `<div style={{ height: 16 }} />` was.
3. A code comment `// PP-FIX-1: DEF-015 audit — no hardcoded AGT-* IDs found` is present in the file.
4. `grep -r "AGT-" src/PP/FrontEnd/src/` returns zero results.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E11-S1-T1 | `src/PP/FrontEnd/src/__tests__/AgentManagement.test.tsx` (create if absent) | Mock `listAgents` + `listAgentTypeDefinitions` with empty arrays | Renders without error; no "AGT-" text in DOM |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run --no-coverage
```

**Commit message:** `feat(PP-FIX-1): replace AgentManagement spacer with Fluent Divider; DEF-015 audit pass`

**Done signal:** `"E11-S1 done. Tests: T1 ✅ DEF-015 grep clean ✅"`

---

**Iteration 4 Done Signal:** Two PRs merged to main. All 11 epics 🟢 Done in Tracking Table. All 15 defects from `defect_list_8_Mar_2026.md` resolved and verifiable by the acceptance criteria in this plan.

---

*End of PP-FIX-1 plan.*
<!-- END CHUNK 15 -->
