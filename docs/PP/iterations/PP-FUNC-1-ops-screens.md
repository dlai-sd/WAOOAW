# PP-FUNC-1-ops-screens — PP Ops Screens Live Data Iteration Plan

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PP-FUNC-1-ops-screens` |
| Feature area | PP — HiredAgentsOps & Billing Screens Live Data |
| Created | 2026-06-10 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | N/A — vision provided inline at plan creation |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 4 |
| Total stories | 6 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — Senior Python/FastAPI engineer + Senior React/TypeScript engineer
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C — N/A (PP BackEnd)
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] GET route story cards do not use `get_read_db_session()` — PP BackEnd proxies only, no DB reads
- [x] No new env vars added — all env vars already present (`PLANT_BASE_URL`)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (E1, E2) before frontend (E3) before registration+tests (E4)
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — create PP BackEnd proxy routes + wire PP FrontEnd ops screens to live Plant data | 4 | 6 | ~4.5h | Your launch time + 5h |

**Estimate basis:** FE wiring = 30 min | New BE proxy file = 45 min | Registration = 30 min | BE tests = 45 min | Docker test = 15 min | PR = 10 min. +20% buffer for zero-cost model context loading.

---

## How to Launch Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` → select **platform-engineer**
6. Copy the block below → paste → press **Enter**
7. Go away. Come back at: **your launch time + 5 hours**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior React / TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-FUNC-1-ops-screens.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3, E4. This is a single-iteration plan.
TIME BUDGET: 4.5h. If you reach 5h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER (sequential — do not parallelise):
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this exact order: E1 → E2 → E3 → E4
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given. Activate now.
For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/PP/BackEnd/` | Senior Python 3.11 / FastAPI engineer |
| `src/PP/FrontEnd/` | Senior React / TypeScript engineer |

---

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
# 1. Create the first epic branch from main
git checkout main && git pull
git checkout -b feat/PP-FUNC-1-ops-screens-it1-e1

# 2. Push an empty init commit
git commit --allow-empty -m "chore(PP-FUNC-1-ops-screens): start iteration 1"
git push origin feat/PP-FUNC-1-ops-screens-it1-e1

# 3. Open draft PR — progress tracker
gh pr create \
  --base main \
  --head feat/PP-FUNC-1-ops-screens-it1-e1 \
  --draft \
  --title "tracking: PP-FUNC-1-ops-screens Iteration 1 — in progress" \
  --body "## tracking: PP-FUNC-1-ops-screens Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Create ops_subscriptions.py proxy routes
- [ ] [E2-S1] Create ops_hired_agents.py proxy routes
- [ ] [E3-S1] Wire HiredAgentsOps.tsx to new ops endpoints
- [ ] [E3-S2] Wire Billing.tsx to live subscription data
- [ ] [E4-S1] Register ops routers in main_proxy.py
- [ ] [E4-S2] Write pytest tests for ops routes

_Live updates posted as comments below ↓_"
```

After posting the draft PR URL: do NOT merge it. It is superseded by the iteration PR in Rule 7.

---

### Rule 1 — Branch discipline

One epic = one branch: `feat/PP-FUNC-1-ops-screens-it1-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a `# TODO` comment and move on.

### Rule 3 — Tests before the next story

Write every test in the story's test table before advancing to the next story.
Run the test command listed in the story card — not a generic command.

### Rule 4 — Commit + push + notify after every story

```bash
git add -A
git commit -m "feat(PP-FUNC-1-ops-screens): [story title]"
git push origin feat/PP-FUNC-1-ops-screens-it1-eN

# Update Tracking Table: change story status to Done
git add docs/PP/iterations/PP-FUNC-1-ops-screens.md
git commit -m "docs(PP-FUNC-1-ops-screens): mark [story-id] done"
git push origin feat/PP-FUNC-1-ops-screens-it1-eN

# Post progress comment to tracking draft PR
gh pr comment \
  $(gh pr list --head feat/PP-FUNC-1-ops-screens-it1-e1 --json number -q '.[0].number') \
  --body "✅ **[story-id] done** — $(git rev-parse --short HEAD)
Files changed: [list]
Tests: [T1 ✅ T2 ✅ ...]
Next: [next-story-id]"
```

### Rule 5 — Docker integration test after every epic

```bash
docker compose -f docker-compose.test.yml run --rm pp-backend-test pytest -v
exit_code=$?
docker compose -f docker-compose.test.yml down
exit $exit_code
```

Exit 0 → add `**Epic complete ✅**` under the epic heading, commit, push.
Non-zero → fix on same branch, retry. Max 3 attempts. Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)

```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/PP-FUNC-1-ops-screens-it1-eN
gh pr create \
  --base main \
  --head feat/PP-FUNC-1-ops-screens-it1-eN \
  --title "WIP: [story-id] — blocked" \
  --draft \
  --body "Blocked on: [test name]
Error: [exact error message — paste in full]
Attempted fixes:
1. [what I tried]
2. [what I tried]"
```

Post the draft PR URL. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)

```bash
git checkout main && git pull
git checkout -b feat/PP-FUNC-1-ops-screens-it1
git merge --no-ff feat/PP-FUNC-1-ops-screens-it1-e1
git merge --no-ff feat/PP-FUNC-1-ops-screens-it1-e2
git merge --no-ff feat/PP-FUNC-1-ops-screens-it1-e3
git merge --no-ff feat/PP-FUNC-1-ops-screens-it1-e4
git push origin feat/PP-FUNC-1-ops-screens-it1

gh pr create \
  --base main \
  --head feat/PP-FUNC-1-ops-screens-it1 \
  --title "feat(PP-FUNC-1-ops-screens): iteration 1 — PP ops screens live data" \
  --body "## PP-FUNC-1-ops-screens Iteration 1

### Stories completed
| E1-S1 | Create ops_subscriptions.py proxy routes | ✅ |
| E2-S1 | Create ops_hired_agents.py proxy routes | ✅ |
| E3-S1 | Wire HiredAgentsOps.tsx to new ops endpoints | ✅ |
| E3-S2 | Wire Billing.tsx to live subscription data | ✅ |
| E4-S1 | Register ops routers in main_proxy.py | ✅ |
| E4-S2 | Write pytest tests for ops routes | ✅ |

### Docker integration
All pp-backend-test containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter in new files
- [ ] PlantAPIClient._request() used — circuit breaker (PP-N1) inherited
- [ ] AuditLogger injected in every new route handler
- [ ] get_authorization_header forwarded to Plant on every route
- [ ] FE: loading + error + empty states on all new data-fetching components
- [ ] Tests >= 80% coverage on new BE code
- [ ] No env-specific values in new files"
```

Post the PR URL. **HALT.**

---

## NFR Quick Reference

> For PM review only. All relevant patterns are embedded inline in each story card.

| # | Rule | Consequence of violation |
|---|---|---|
| PP-N1 | `PlantAPIClient._request()` has class-level circuit breaker — always use it for outbound Plant calls | Cascading failure if Plant is down |
| PP-N3b | `waooaw_router()` factory — never bare `APIRouter()` | ruff TID251 ban — CI blocks PR |
| PP-N4 | `AuditLogger` from `services.audit_dependency` injected via `Depends(get_audit_logger)` | Audit trail missing |
| PP-N2 | OTel tracing already wired in `main_proxy.py` — no per-route work needed | N/A |
| FE-1 | loading + error + empty states on every data-fetching component | Silent failures for ops user |
| FE-2 | New `gatewayApiClient` methods use `withQuery()` helper for query string building | Broken filters |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Subscriptions proxy routes served | Create ops_subscriptions.py proxy routes | 🔴 Not Started | — |
| E2-S1 | 1 | Hired-agents proxy routes served | Create ops_hired_agents.py proxy routes | 🔴 Not Started | — |
| E3-S1 | 1 | HiredAgentsOps shows live data | Wire HiredAgentsOps.tsx to new ops endpoints | 🔴 Not Started | — |
| E3-S2 | 1 | Billing shows live subscription data | Wire Billing.tsx to live subscription counts | 🔴 Not Started | — |
| E4-S1 | 1 | Ops routes registered in app | Register ops routers in main_proxy.py | 🔴 Not Started | — |
| E4-S2 | 1 | Ops routes covered by tests | Write pytest tests for ops_subscriptions and ops_hired_agents | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — PP Ops Screens Live Data

**Scope:** PP ops users open HiredAgentsOps and Billing screens and see live subscription and hired-agent data from the Plant API — zero hardcoded or stub values remain.
**Lane:** A — wire existing Plant API endpoints through new PP BackEnd proxy routes to PP FrontEnd.
**⏱ Estimated:** ~4.5h | **Come back:** your launch time + 5 hours
**Epics:** E1, E2, E3, E4

### Dependency Map (Iteration 1)

```
E1-S1  ────────────────────────────────────────────────────────────► (independent)
E2-S1  ────────────────────────────────────────────────────────────► (independent)
E3-S1  ────────────────────────────────────────────────────────────► (independent — URL strings only)
E3-S2  ◄── BLOCKED until E3-S1 committed to feat/...-it1-e3
E4-S1  ◄── BLOCKED until E1-S1 AND E2-S1 committed to their branches
E4-S2  ◄── BLOCKED until E4-S1 committed to feat/...-it1-e4
```

**Note for E4:** E4-S1 requires `ops_subscriptions.py` and `ops_hired_agents.py` to exist locally.
Before writing E4-S1 content, the agent must run:
```bash
git checkout feat/PP-FUNC-1-ops-screens-it1-e1 -- src/PP/BackEnd/api/ops_subscriptions.py
git checkout feat/PP-FUNC-1-ops-screens-it1-e2 -- src/PP/BackEnd/api/ops_hired_agents.py
git commit -m "chore(PP-FUNC-1-ops-screens): bring ops API files into E4 branch for registration"
```
This copies the new files into the E4 branch for local registration and test work. The iteration PR merges all four branches cleanly — duplicate file additions with identical content cause no conflict.

---

### Epic E1: PP BackEnd serves subscription data to the ops screens

**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e1`
**User story:** As a PP ops user, I can call `/api/pp/ops/subscriptions` and `/api/pp/ops/subscriptions/{id}` on the PP BackEnd, so that the Billing screen has a dedicated, stable endpoint for live subscription data.

---

#### Story E1-S1: Create `ops_subscriptions.py` proxy routes

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e1`
**PP BackEnd pattern:** New dedicated proxy file — create `src/PP/BackEnd/api/ops_subscriptions.py` using `waooaw_router` + `PlantAPIClient._request()` to forward to Plant Gateway.

**What to do (self-contained — read this card, then act):**
> Create a new file `src/PP/BackEnd/api/ops_subscriptions.py`. It must contain two GET routes registered on a `waooaw_router` with `prefix="/ops/subscriptions"`:
> (1) `GET /` — list all subscriptions, forwarding all incoming query params (e.g. `customer_id`, `status`) to Plant `GET /api/v1/subscriptions` via `PlantAPIClient._request()`;
> (2) `GET /{subscription_id}` — get one subscription, forwarding to Plant `GET /api/v1/subscriptions/{subscription_id}`.
> Both routes must inject `AuditLogger` and call `await audit.log(...)` on success. Both must forward the caller's `Authorization` header to Plant via `get_authorization_header`. Both must catch `PlantAPIError` and raise `HTTPException(503)`.
> Do NOT register the router in `main_proxy.py` — that is E4-S1's job.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/api/agents.py` | 1–34 | `waooaw_router` import, `get_authorization_header` import, `PlantAPIClient` + `get_plant_client` import, `AuditLogger` + `get_audit_logger` import, router instantiation pattern |
| `src/PP/BackEnd/clients/plant_client.py` | 316–380 | `_request(method, path, params, headers, correlation_id)` signature — this is what the route calls to forward to Plant |
| `src/PP/BackEnd/api/deps.py` | 1–19 | `get_authorization_header` function signature — returns `Optional[str]` from `request.headers.get("authorization")` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/api/ops_subscriptions.py` | **create** | Full new file — see code pattern below |

**Code pattern to copy exactly** (adapt the `[PLANT_PATH]` and audit string values only):

```python
"""Ops proxy routes for subscription data.

Thin PP proxy routes that forward requests to Plant Gateway's subscription
endpoints. Circuit-breaker protection is inherited from PlantAPIClient._request().
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request

from api.deps import get_authorization_header
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from core.routing import waooaw_router  # PP-N3b: never use bare APIRouter
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

router = waooaw_router(prefix="/ops/subscriptions", tags=["ops-subscriptions"])


@router.get("", response_model=list)
async def list_subscriptions(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List all subscriptions — forwards all query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(  # PP-N1: circuit breaker lives inside _request
            method="GET",
            path="/api/v1/subscriptions",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log("pp_ops", "subscriptions_listed", "success")
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{subscription_id}", response_model=dict)
async def get_subscription(
    subscription_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """Get a single subscription by ID."""
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/subscriptions/{subscription_id}",
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops", "subscription_retrieved", "success",
                metadata={"subscription_id": subscription_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
```

**Acceptance criteria (binary pass/fail):**
1. `src/PP/BackEnd/api/ops_subscriptions.py` exists and is importable without error (`python -c "from api.ops_subscriptions import router"` exits 0)
2. `router.prefix` equals `"/ops/subscriptions"`
3. `router` was created with `waooaw_router()` — ruff lint passes: `ruff check src/PP/BackEnd/api/ops_subscriptions.py` exits 0
4. `list_subscriptions` calls `client._request("GET", "/api/v1/subscriptions", ...)` with `params=dict(request.query_params)`
5. `get_subscription` calls `client._request("GET", "/api/v1/subscriptions/{subscription_id}", ...)`
6. Both routes catch `PlantAPIError` and raise `HTTPException(503)`
7. Both routes call `await audit.log(...)` on the success path

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/PP/BackEnd/tests/test_ops_subscriptions.py` | These tests are written in **E4-S2** — E1-S1 only needs the file to be importable | File imports cleanly |

**Test command:**
```bash
# Importability check only at this stage — full tests written in E4-S2
cd src/PP/BackEnd && python -c "from api.ops_subscriptions import router; print('OK')"
```

**Commit message:** `feat(PP-FUNC-1-ops-screens): create ops_subscriptions.py proxy routes`

**Done signal:**
`"E1-S1 done. Created: src/PP/BackEnd/api/ops_subscriptions.py. Import check: OK. Router prefix: /ops/subscriptions."`

**Epic complete ✅** (single-story epic — after commit+push, run Rule 5 Docker test, then continue to E2)

---

### Epic E2: PP BackEnd serves hired-agent data to the ops screens

**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e2`
**User story:** As a PP ops user, I can call `/api/pp/ops/hired-agents` and its sub-routes on the PP BackEnd, so that the HiredAgentsOps screen has stable dedicated endpoints for hired-agent instances, goals, and deliverables.

---

#### Story E2-S1: Create `ops_hired_agents.py` proxy routes

**BLOCKED UNTIL:** none (independent from E1, starts from `main`)
**Estimated time:** 45 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e2`
**PP BackEnd pattern:** New dedicated proxy file — create `src/PP/BackEnd/api/ops_hired_agents.py` using `waooaw_router` + `PlantAPIClient._request()` to forward to Plant Gateway.

**What to do (self-contained — read this card, then act):**
> Create a new file `src/PP/BackEnd/api/ops_hired_agents.py`. It must contain four GET routes on a `waooaw_router` with `prefix="/ops/hired-agents"`:
> (1) `GET /` — list hired agent instances, forwarding all query params to Plant `GET /api/v1/hired-agents`;
> (2) `GET /{hired_instance_id}` — get one instance from Plant `GET /api/v1/hired-agents/{hired_instance_id}`;
> (3) `GET /{hired_instance_id}/deliverables` — from Plant `GET /api/v1/hired-agents/{hired_instance_id}/deliverables`;
> (4) `GET /{hired_instance_id}/goals` — from Plant `GET /api/v1/hired-agents/{hired_instance_id}/goals`.
> All four routes inject `AuditLogger`, forward the `Authorization` header, and catch `PlantAPIError` → `HTTPException(503)`.
> Do NOT register in `main_proxy.py` — that is E4-S1's job.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/api/agents.py` | 1–34 | Import block and `waooaw_router` instantiation to copy |
| `src/PP/BackEnd/clients/plant_client.py` | 316–380 | `_request(method, path, params, headers)` — exact call signature |
| `src/PP/BackEnd/api/deps.py` | 1–19 | `get_authorization_header` function signature |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/api/ops_hired_agents.py` | **create** | Full new file — see code pattern below |

**Code pattern to copy exactly:**

```python
"""Ops proxy routes for hired-agent data.

Thin PP proxy routes that forward requests to Plant Gateway's hired-agent
endpoints. Circuit-breaker protection is inherited from PlantAPIClient._request().
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request

from api.deps import get_authorization_header
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from core.routing import waooaw_router  # PP-N3b
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

router = waooaw_router(prefix="/ops/hired-agents", tags=["ops-hired-agents"])


@router.get("", response_model=list)
async def list_hired_agents(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List all hired agent instances — forwards all query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(
            method="GET",
            path="/api/v1/hired-agents",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log("pp_ops", "hired_agents_listed", "success")
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_instance_id}", response_model=dict)
async def get_hired_agent(
    hired_instance_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """Get a single hired agent instance by ID."""
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_instance_id}",
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops", "hired_agent_retrieved", "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_instance_id}/deliverables", response_model=dict)
async def list_hired_agent_deliverables(
    hired_instance_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List deliverables for a hired agent instance — forwards query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_instance_id}/deliverables",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops", "hired_agent_deliverables_listed", "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_instance_id}/goals", response_model=dict)
async def list_hired_agent_goals(
    hired_instance_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List goals for a hired agent instance — forwards query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_instance_id}/goals",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops", "hired_agent_goals_listed", "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
```

**Acceptance criteria (binary pass/fail):**
1. `src/PP/BackEnd/api/ops_hired_agents.py` exists and is importable: `python -c "from api.ops_hired_agents import router"` exits 0
2. `router.prefix` equals `"/ops/hired-agents"`
3. `ruff check src/PP/BackEnd/api/ops_hired_agents.py` exits 0 (no bare `APIRouter`)
4. Route `GET /` forwards `params=dict(request.query_params)` to Plant `/api/v1/hired-agents`
5. Route `GET /{hired_instance_id}/deliverables` forwards to Plant `/api/v1/hired-agents/{id}/deliverables`
6. Route `GET /{hired_instance_id}/goals` forwards to Plant `/api/v1/hired-agents/{id}/goals`
7. All four routes catch `PlantAPIError` and raise `HTTPException(503)`

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | Written in E4-S2 | — | File imports cleanly |

**Test command:**
```bash
cd src/PP/BackEnd && python -c "from api.ops_hired_agents import router; print('OK')"
```

**Commit message:** `feat(PP-FUNC-1-ops-screens): create ops_hired_agents.py proxy routes`

**Done signal:**
`"E2-S1 done. Created: src/PP/BackEnd/api/ops_hired_agents.py. Import check: OK. 4 routes: GET /, GET /{id}, GET /{id}/deliverables, GET /{id}/goals."`

**Epic complete ✅** (single-story epic — after commit+push, run Rule 5 Docker test, continue to E3)

---

### Epic E3: PP FrontEnd ops screens display live Plant data

**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e3`
**User story:** As a PP ops user, I open HiredAgentsOps and see live hired-agent data loaded from the new `/api/pp/ops/` routes; I open Billing and see live subscription counts — no hardcoded values remain in either screen.

---

#### Story E3-S1: Wire HiredAgentsOps.tsx to the new ops endpoints

**BLOCKED UNTIL:** none (URL string changes — FE compiles independently; unit tests mock the API)
**Estimated time:** 45 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e3`
**PP BackEnd pattern:** N/A (frontend only)

**What to do (self-contained — read this card, then act):**
> `src/PP/FrontEnd/src/services/gatewayApiClient.ts` currently has methods `listSubscriptionsByCustomer`, `getHiredAgentBySubscription`, `listGoalsForHiredInstance`, and `listDeliverablesForHiredInstance` that call catch-all proxy paths (`/v1/...`) which may return 404. Add six new dedicated ops methods to `gatewayApiClient.ts` that call the new `/pp/ops/...` routes. Then update `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` to use these new methods in its `load()` and `loadDetails()` callbacks, replacing the four failing catch-all calls. The old methods on `gatewayApiClient` must NOT be removed (other callers may use them).

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | 92–101, 179–230 | `withQuery` helper (line 92–101), existing method pattern to copy (`listSubscriptionsByCustomer` at line 183, `listGoalsForHiredInstance` at line 189) |
| `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` | 132–222 | `load()` callback (lines 132–178): calls `listSubscriptionsByCustomer`, `getHiredAgentBySubscription`, `listGoalsForHiredInstance`; `loadDetails()` callback (lines 180–222): calls `listDeliverablesForHiredInstance` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | **modify** | After the `listApprovals` method (around line 350), add the six new ops methods shown in the code pattern below |
| `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` | **modify** | In `load()`: replace lines 146–163 with the updated version; in `loadDetails()`: replace line 191 with the updated call — see exact changes below |

**Code pattern — new methods to add to `gatewayApiClient.ts`** (add inside the `gatewayApiClient` object, after the `listApprovals` entry):

```typescript
  // Ops subscription routes (dedicated PP proxy — not catch-all)
  listOpsSubscriptions: (query?: {
    customer_id?: string
    status?: string
    as_of?: string
    limit?: number
  }) =>
    gatewayRequestJson<unknown[]>(withQuery('/pp/ops/subscriptions', query)),

  getOpsSubscription: (subscriptionId: string) =>
    gatewayRequestJson<unknown>(
      `/pp/ops/subscriptions/${encodeURIComponent(subscriptionId)}`
    ),

  // Ops hired-agent routes (dedicated PP proxy — not catch-all)
  listOpsHiredAgents: (query?: {
    subscription_id?: string
    customer_id?: string
    as_of?: string
    limit?: number
  }) =>
    gatewayRequestJson<unknown[]>(withQuery('/pp/ops/hired-agents', query)),

  getOpsHiredAgent: (hiredInstanceId: string) =>
    gatewayRequestJson<unknown>(
      `/pp/ops/hired-agents/${encodeURIComponent(hiredInstanceId)}`
    ),

  listOpsHiredAgentGoals: (
    hiredInstanceId: string,
    query?: { customer_id?: string; as_of?: string }
  ) =>
    gatewayRequestJson<unknown>(
      withQuery(
        `/pp/ops/hired-agents/${encodeURIComponent(hiredInstanceId)}/goals`,
        query
      )
    ),

  listOpsHiredAgentDeliverables: (
    hiredInstanceId: string,
    query?: { customer_id?: string; as_of?: string }
  ) =>
    gatewayRequestJson<unknown>(
      withQuery(
        `/pp/ops/hired-agents/${encodeURIComponent(hiredInstanceId)}/deliverables`,
        query
      )
    ),
```

**Exact changes in `HiredAgentsOps.tsx`:**

In `load()` callback — replace the entire `try` block body (lines 145–177 in the original) with:

```typescript
    try {
      // Use new dedicated ops routes (not the catch-all /v1/ proxy)
      const subs = (await gatewayApiClient.listOpsSubscriptions({
        customer_id: cust,
        as_of: normalizedAsOf,
      })) as Subscription[]

      const hiredInstances = await Promise.all(
        (subs || []).map(async (s) => {
          // Ops list endpoint returns an array; take first matching instance
          const hiredArr = (await gatewayApiClient.listOpsHiredAgents({
            subscription_id: s.subscription_id,
            customer_id: cust,
            as_of: normalizedAsOf,
          })) as HiredAgentInstance[]
          const hired = hiredArr?.[0]
          if (!hired?.hired_instance_id) return null

          const goalsRes = (await gatewayApiClient.listOpsHiredAgentGoals(
            hired.hired_instance_id,
            { customer_id: cust, as_of: normalizedAsOf }
          )) as GoalsListResponse

          return {
            subscription_id: s.subscription_id,
            hired,
            goals: goalsRes?.goals || [],
          } satisfies HiredRow
        })
      )

      const sorted = hiredInstances
        .filter((r): r is HiredRow => !!r?.hired?.hired_instance_id)
        .sort((a, b) => (a.hired.created_at || '').localeCompare(b.hired.created_at || ''))

      setRows(sorted)
    } catch (e: any) {
      setError(e)
    } finally {
      setIsLoading(false)
    }
```

In `loadDetails()` callback — replace only the `listDeliverablesForHiredInstance` call (line 191 in original) with:

```typescript
        gatewayApiClient.listOpsHiredAgentDeliverables(row.hired.hired_instance_id, {
          customer_id: cust,
          as_of: normalizedAsOf,
        }) as Promise<unknown>,
```

The other two calls in `loadDetails()` (`listApprovals` and `listPolicyDenials`) remain unchanged.

**Acceptance criteria (binary pass/fail):**
1. `gatewayApiClient.ts` compiles without TypeScript errors: `npx tsc --noEmit` exits 0 in `src/PP/FrontEnd`
2. `gatewayApiClient` object contains the six new ops methods: `listOpsSubscriptions`, `getOpsSubscription`, `listOpsHiredAgents`, `getOpsHiredAgent`, `listOpsHiredAgentGoals`, `listOpsHiredAgentDeliverables`
3. `listOpsSubscriptions` builds the URL `/pp/ops/subscriptions` (verified in unit test T1)
4. `listOpsHiredAgentGoals` builds the URL `/pp/ops/hired-agents/{id}/goals` (verified in unit test T2)
5. `HiredAgentsOps.tsx` no longer calls `listSubscriptionsByCustomer` or `getHiredAgentBySubscription` or `listGoalsForHiredInstance` or `listDeliverablesForHiredInstance` — confirmed by grep
6. `HiredAgentsOps.tsx` compiles without TypeScript errors

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/PP/FrontEnd/src/__tests__/gatewayApiClient.ops.test.ts` | Mock global `fetch` to capture URL; call `gatewayApiClient.listOpsSubscriptions({ customer_id: 'C1' })` | Captured URL contains `/pp/ops/subscriptions` and query param `customer_id=C1` |
| E3-S1-T2 | same file | Call `gatewayApiClient.listOpsHiredAgentGoals('inst-1', { customer_id: 'C1' })` | URL contains `/pp/ops/hired-agents/inst-1/goals` and `customer_id=C1` |
| E3-S1-T3 | same file | Call `gatewayApiClient.listOpsHiredAgentDeliverables('inst-1', { customer_id: 'C1' })` | URL contains `/pp/ops/hired-agents/inst-1/deliverables` |
| E3-S1-T4 | same file | Verify `gatewayApiClient` has key `listOpsSubscriptions` | `typeof gatewayApiClient.listOpsSubscriptions === 'function'` |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run src/__tests__/gatewayApiClient.ops.test.ts --reporter=verbose
```

**Commit message:** `feat(PP-FUNC-1-ops-screens): wire HiredAgentsOps.tsx to new ops endpoints`

**Done signal:**
`"E3-S1 done. Modified: gatewayApiClient.ts (6 new methods), HiredAgentsOps.tsx (load + loadDetails updated). Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E3-S2: Wire Billing.tsx to live subscription counts

**BLOCKED UNTIL:** E3-S1 committed to `feat/PP-FUNC-1-ops-screens-it1-e3` (needs `listOpsSubscriptions` method)
**Estimated time:** 30 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e3` (continue from E3-S1)
**PP BackEnd pattern:** N/A (frontend only)

**What to do (self-contained — read this card, then act):**
> `src/PP/FrontEnd/src/pages/Billing.tsx` currently shows four hardcoded metric cards (₹2,400,000, 2.3%, ₹1,945, 12) and a hardcoded revenue breakdown. Replace the entire file content with a live-data version: add `useState` + `useEffect` to fetch from `gatewayApiClient.listOpsSubscriptions({})`, derive four live metrics (total count, active count, trial count, inactive count) from the response array, and replace all hardcoded numbers with these derived values. Add loading (Spinner), error (error-banner div), and empty-state handling as required by NFR FE-1.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/pages/Billing.tsx` | 1–47 | Full current file — all imports, card structure, hardcoded values to replace |
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | 179–185 | `listOpsSubscriptions` method signature just added by E3-S1 — confirm it's present |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/pages/Billing.tsx` | **replace entirely** | Replace with the full content shown in the code pattern below |

**Code pattern — full replacement `Billing.tsx` content:**

```typescript
import { useEffect, useState } from 'react'
import { Body1, Card, CardHeader, Spinner, Text } from '@fluentui/react-components'

import { gatewayApiClient } from '../services/gatewayApiClient'

type SubscriptionRecord = {
  subscription_id: string
  status?: string | null
  agent_id?: string | null
  duration?: string | null
}

export default function Billing() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    gatewayApiClient
      .listOpsSubscriptions({})
      .then((data) => setSubscriptions((data as SubscriptionRecord[]) || []))
      .catch(() => setError('Failed to load subscription data. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  const total = subscriptions.length
  const active = subscriptions.filter((s) => s.status === 'active').length
  const trial = subscriptions.filter((s) => s.status === 'trial').length
  const inactive = total - active - trial

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">
          Billing & Revenue
        </Text>
        <Body1>Live subscription data from Plant API</Body1>
      </div>

      {error && (
        <div className="error-banner" style={{ color: '#ef4444', padding: '12px 0' }}>
          {error}
        </div>
      )}

      {loading ? (
        <Spinner label="Loading subscription data..." style={{ marginTop: 32 }} />
      ) : (
        <>
          <div className="dashboard-grid">
            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Total Subscriptions</Text>} />
              <Text size={700}>{total}</Text>
            </Card>

            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Active Subscriptions</Text>} />
              <Text size={700}>{active}</Text>
            </Card>

            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Trial Subscriptions</Text>} />
              <Text size={700}>{trial}</Text>
            </Card>

            <Card className="metric-card">
              <CardHeader header={<Text weight="semibold">Inactive / Other</Text>} />
              <Text size={700}>{inactive}</Text>
            </Card>
          </div>

          {subscriptions.length === 0 ? (
            <Card style={{ marginTop: '24px' }}>
              <div style={{ padding: '16px' }}>
                <Text>No subscriptions found.</Text>
              </div>
            </Card>
          ) : (
            <Card style={{ marginTop: '24px' }}>
              <CardHeader header={<Text weight="semibold">Subscription Status Breakdown</Text>} />
              <div style={{ padding: '16px' }}>
                {Array.from(
                  new Set(subscriptions.map((s) => s.status ?? 'unknown'))
                ).map((status) => (
                  <div key={status} style={{ marginBottom: 4 }}>
                    <Text>
                      {status}:{' '}
                      {subscriptions.filter((s) => (s.status ?? 'unknown') === status).length}
                    </Text>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
```

**Acceptance criteria (binary pass/fail):**
1. `Billing.tsx` contains no hardcoded currency values (₹2,400,000, ₹800K, ₹1.2M) — confirmed by grep: `grep -n "2,400,000\|800K\|1\.2M\|2\.3%\|1,945" src/PP/FrontEnd/src/pages/Billing.tsx` returns 0 lines
2. `Billing.tsx` imports `useState`, `useEffect`, and `gatewayApiClient`
3. `Billing.tsx` calls `gatewayApiClient.listOpsSubscriptions({})` inside a `useEffect`
4. `Billing.tsx` renders a `<Spinner>` when `loading` is true (verified by unit test T2)
5. `Billing.tsx` renders the string from `error` state inside an element with class `error-banner` when `error` is set (verified by unit test T3)
6. `Billing.tsx` renders a `<Text>` showing `total` count when data is loaded (verified by unit test T1)
7. `npx tsc --noEmit` exits 0 in `src/PP/FrontEnd`

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/PP/FrontEnd/src/__tests__/Billing.test.tsx` | Mock `gatewayApiClient.listOpsSubscriptions` to resolve with `[{subscription_id:'s1',status:'active'},{subscription_id:'s2',status:'trial'}]`; render `<Billing />` | DOM contains text "2" in the "Total Subscriptions" card |
| E3-S2-T2 | same file | `listOpsSubscriptions` hangs (never resolves); render `<Billing />` | DOM contains an element with role "status" (the Spinner) |
| E3-S2-T3 | same file | `listOpsSubscriptions` rejects with `new Error('fail')`; render `<Billing />`; await loading | DOM contains "Failed to load subscription data" text |
| E3-S2-T4 | same file | `listOpsSubscriptions` resolves with `[]`; render `<Billing />` | DOM contains "No subscriptions found." text |

**Test command:**
```bash
cd src/PP/FrontEnd && npx vitest run src/__tests__/Billing.test.tsx --reporter=verbose
```

**Commit message:** `feat(PP-FUNC-1-ops-screens): wire Billing.tsx to live subscription data`

**Done signal:**
`"E3-S2 done. Modified: Billing.tsx (full replacement — 4 live metric cards, status breakdown). Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

**Epic complete ✅** (after both stories committed+pushed, run Rule 5 Docker test for FE, continue to E4)

---

### Epic E4: Ops routes are registered in the app and fully tested

**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e4`
**User story:** As a PP ops user, I can call `/api/pp/ops/subscriptions` and `/api/pp/ops/hired-agents` on the live PP BackEnd and receive real data, because the routers are registered in the app and all routes have passing pytest coverage.

---

#### Story E4-S1: Register ops routers in `main_proxy.py`

**BLOCKED UNTIL:** E1-S1 committed to `feat/PP-FUNC-1-ops-screens-it1-e1` AND E2-S1 committed to `feat/PP-FUNC-1-ops-screens-it1-e2`
**Estimated time:** 30 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e4`
**PP BackEnd pattern:** Modify `main_proxy.py` — add two `app.include_router` calls for the new ops routers.

**What to do (self-contained — read this card, then act):**
> The two new files `ops_subscriptions.py` and `ops_hired_agents.py` are not yet imported or registered in `src/PP/BackEnd/main_proxy.py`. This story makes them active in the FastAPI app.
>
> **Step 1 — Bring the new files into this branch** (they live on E1 and E2 branches, not yet in main):
> ```bash
> git checkout feat/PP-FUNC-1-ops-screens-it1-e1 -- src/PP/BackEnd/api/ops_subscriptions.py
> git checkout feat/PP-FUNC-1-ops-screens-it1-e2 -- src/PP/BackEnd/api/ops_hired_agents.py
> git commit -m "chore(PP-FUNC-1-ops-screens): bring ops API files into E4 branch"
> ```
>
> **Step 2 — Register the routers**: In `main_proxy.py` line 11, the existing import is `from api import agents, audit, auth, genesis, db_updates, metering_debug, agent_setups, exchange_credentials, approvals, agent_types`. Append `, ops_subscriptions, ops_hired_agents` to this import.
> Then after line 121 (`app.include_router(db_updates.router, prefix="/api/pp")`), add two new lines:
> ```python
> app.include_router(ops_subscriptions.router, prefix="/api/pp")
> app.include_router(ops_hired_agents.router, prefix="/api/pp")
> ```
> These two lines MUST appear BEFORE the catch-all proxy route at line 124 (`@app.api_route("/api/{path:path}", ...)`). If they are placed after the catch-all, the ops routes will be shadowed and never reached.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/main_proxy.py` | 1–125 | Line 11: existing `from api import ...` line to extend; lines 112–124: existing `app.include_router` calls and the catch-all route — new routers must be inserted BEFORE line 124 |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/api/ops_subscriptions.py` | **copy from E1 branch** | `git checkout feat/PP-FUNC-1-ops-screens-it1-e1 -- src/PP/BackEnd/api/ops_subscriptions.py` |
| `src/PP/BackEnd/api/ops_hired_agents.py` | **copy from E2 branch** | `git checkout feat/PP-FUNC-1-ops-screens-it1-e2 -- src/PP/BackEnd/api/ops_hired_agents.py` |
| `src/PP/BackEnd/main_proxy.py` | **modify** | Line 11: add `, ops_subscriptions, ops_hired_agents` to the `from api import` statement; after line 121 and before the catch-all route: add 2 `app.include_router` lines |

**Exact diff for `main_proxy.py`:**

```python
# Line 11 — BEFORE:
from api import agents, audit, auth, genesis, db_updates, metering_debug, agent_setups, exchange_credentials, approvals, agent_types

# Line 11 — AFTER:
from api import agents, audit, auth, genesis, db_updates, metering_debug, agent_setups, exchange_credentials, approvals, agent_types, ops_subscriptions, ops_hired_agents

# After line 121 (app.include_router(db_updates.router, prefix="/api/pp")), ADD:
app.include_router(ops_subscriptions.router, prefix="/api/pp")
app.include_router(ops_hired_agents.router, prefix="/api/pp")
# These two lines MUST come before the @app.api_route("/api/{path:path}", ...) catch-all
```

**Acceptance criteria (binary pass/fail):**
1. `python -c "from main_proxy import app; print('OK')"` (run from `src/PP/BackEnd/`) exits 0
2. `GET /api/pp/ops/subscriptions` is listed in the FastAPI OpenAPI routes: `python -c "from main_proxy import app; routes = [r.path for r in app.routes]; assert '/api/pp/ops/subscriptions' in routes, routes"`
3. `GET /api/pp/ops/hired-agents` is listed: same check for `/api/pp/ops/hired-agents`
4. `GET /api/pp/ops/hired-agents/{hired_instance_id}/goals` is listed
5. The catch-all route (`/api/{path:path}`) still exists and is still last in the route list
6. `ruff check src/PP/BackEnd/main_proxy.py` exits 0

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/PP/BackEnd/tests/test_health_routes.py` (already exists — add assertion only) | Import `app` from `main_proxy` | `[r.path for r in app.routes]` contains `'/api/pp/ops/subscriptions'` |

**Test command:**
```bash
cd src/PP/BackEnd && python -c "
from main_proxy import app
routes = [r.path for r in app.routes]
assert '/api/pp/ops/subscriptions' in routes, f'Missing route. Found: {routes}'
assert '/api/pp/ops/hired-agents' in routes, f'Missing route. Found: {routes}'
print('E4-S1 route registration: OK')
"
```

**Commit message:** `feat(PP-FUNC-1-ops-screens): register ops routers in main_proxy.py`

**Done signal:**
`"E4-S1 done. Modified: main_proxy.py (2 new imports, 2 new include_router calls before catch-all). Route check: /api/pp/ops/subscriptions ✅ /api/pp/ops/hired-agents ✅"`

---

#### Story E4-S2: Write pytest tests for ops_subscriptions and ops_hired_agents routes

**BLOCKED UNTIL:** E4-S1 committed to `feat/PP-FUNC-1-ops-screens-it1-e4` (tests use `app` which must have routers registered)
**Estimated time:** 45 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it1-e4` (continue from E4-S1)
**PP BackEnd pattern:** N/A (test files only)

**What to do (self-contained — read this card, then act):**
> Create two new pytest test files for the ops routes. The test pattern in this codebase: use `app.dependency_overrides[get_plant_client]` to inject a `SimpleNamespace` mock that has `_request` as an `AsyncMock` returning a `MagicMock` with `.status_code = 200` and `.json.return_value = [...]` or `{...}`. Both test files follow the existing `conftest.py` fixture (`app` and `client`). Cover: 200 success, 503 when `PlantAPIError` is raised, 404 passthrough when Plant returns 404.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/tests/conftest.py` | 1–29 | `app` fixture (imports `main_proxy.app`), `client` fixture (`httpx.ASGITransport`) — copy these patterns |
| `src/PP/BackEnd/tests/test_agents_routes.py` | 1–61 | `app.dependency_overrides[get_plant_client] = lambda: plant` pattern with `SimpleNamespace` mock |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/tests/test_ops_subscriptions.py` | **create** | Full test file — see code pattern below |
| `src/PP/BackEnd/tests/test_ops_hired_agents.py` | **create** | Full test file — see code pattern below |

**Code pattern — `test_ops_subscriptions.py`:**

```python
"""Tests for ops_subscriptions proxy routes (E1-S1)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_plant(status_code: int, body):
    """Return a mock PlantAPIClient whose _request returns a controlled response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_resp.text = str(body)
    plant = SimpleNamespace(_request=AsyncMock(return_value=mock_resp))
    return plant


@pytest.mark.unit
async def test_list_subscriptions_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [{"subscription_id": "sub-1", "status": "active"}])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["subscription_id"] == "sub-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_subscriptions_forwards_query_params(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        await client.get("/api/pp/ops/subscriptions?customer_id=C1&status=active")
        call_kwargs = plant._request.call_args
        assert call_kwargs.kwargs.get("params") == {"customer_id": "C1", "status": "active"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_subscriptions_503_on_plant_error(app, client):
    from clients.plant_client import PlantAPIError, get_plant_client

    plant = SimpleNamespace(_request=AsyncMock(side_effect=PlantAPIError("circuit open")))
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_subscription_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"subscription_id": "sub-1", "status": "active"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions/sub-1")
        assert resp.status_code == 200
        assert resp.json()["subscription_id"] == "sub-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_subscription_passthrough_404(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(404, {"detail": "not found"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/subscriptions/does-not-exist")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
```

**Code pattern — `test_ops_hired_agents.py`:**

```python
"""Tests for ops_hired_agents proxy routes (E2-S1)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_plant(status_code: int, body):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_resp.text = str(body)
    return SimpleNamespace(_request=AsyncMock(return_value=mock_resp))


@pytest.mark.unit
async def test_list_hired_agents_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [{"hired_instance_id": "inst-1", "agent_id": "agent-1"}])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents")
        assert resp.status_code == 200
        assert resp.json()[0]["hired_instance_id"] == "inst-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agents_forwards_query_params(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, [])
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        await client.get("/api/pp/ops/hired-agents?subscription_id=sub-1&customer_id=C1")
        call_kwargs = plant._request.call_args
        assert call_kwargs.kwargs.get("params") == {
            "subscription_id": "sub-1",
            "customer_id": "C1",
        }
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agents_503_on_plant_error(app, client):
    from clients.plant_client import PlantAPIError, get_plant_client

    plant = SimpleNamespace(_request=AsyncMock(side_effect=PlantAPIError("timeout")))
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_hired_agent_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"hired_instance_id": "inst-1", "agent_id": "agent-1"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/inst-1")
        assert resp.status_code == 200
        assert resp.json()["hired_instance_id"] == "inst-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agent_deliverables_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"hired_instance_id": "inst-1", "deliverables": []})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/inst-1/deliverables")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_hired_agent_goals_returns_200(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(200, {"hired_instance_id": "inst-1", "goals": []})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/inst-1/goals")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_hired_agent_deliverables_passthrough_404(app, client):
    from clients.plant_client import get_plant_client

    plant = _make_plant(404, {"detail": "not found"})
    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get("/api/pp/ops/hired-agents/missing/deliverables")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
```

**Acceptance criteria (binary pass/fail):**
1. `test_ops_subscriptions.py` — all 5 tests pass
2. `test_ops_hired_agents.py` — all 7 tests pass
3. `pytest tests/test_ops_subscriptions.py tests/test_ops_hired_agents.py -v` exits 0 in Docker
4. No existing tests are broken — `pytest tests/ -v` exits 0 in Docker
5. Coverage on `api/ops_subscriptions.py` ≥ 80% (5 tests × 2 routes)
6. Coverage on `api/ops_hired_agents.py` ≥ 80% (7 tests × 4 routes)

**Tests to write:** (the story IS the tests — write the two files above)

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm pp-backend-test \
  pytest tests/test_ops_subscriptions.py tests/test_ops_hired_agents.py -v --tb=short
```

**Full regression (run after passing):**
```bash
docker compose -f docker-compose.test.yml run --rm pp-backend-test pytest tests/ -v --tb=short
```

**Commit message:** `feat(PP-FUNC-1-ops-screens): pytest tests for ops_subscriptions and ops_hired_agents routes`

**Done signal:**
`"E4-S2 done. Created: test_ops_subscriptions.py (5 tests ✅), test_ops_hired_agents.py (7 tests ✅). Full regression: all existing tests still pass ✅"`

**Epic complete ✅** — after commit+push, run Rule 7 to open the iteration PR.
```

---

## Iteration 2 — Redis Caching for PP Ops Proxy Routes

**Scope:** PP ops proxy routes (`/ops/subscriptions` and `/ops/hired-agents`) cache successful Plant API responses in Redis (TTL 60 s), reducing Plant load for repeated ops-screen requests. Caching is transparent: if Redis is unavailable every request falls through to Plant unchanged (graceful degradation).
**Lane:** A — augment existing Iteration 1 proxy routes with a new Redis cache service.
**⏱ Estimated:** ~3h | **Come back:** your launch time + 3.5 hours
**Epics:** E5, E6
**Expert personas:** Senior Python/FastAPI engineer + Senior Redis/backend engineer

### Dependency Map (Iteration 2)

```
E5-S1  ────── create ops_cache.py service (independent)
E5-S2  ◄──── BLOCKED until E5-S1 (needs ops_cache module for imports)
E6-S1  ◄──── BLOCKED until E5-S2 (tests need wired routes + cache service)
```

---

### Epic E5: PP BackEnd caches ops proxy responses in Redis

**Branch:** `feat/PP-FUNC-1-ops-screens-it2-e5`
**User story:** As a PP ops user, repeated requests to `/api/pp/ops/subscriptions` and `/api/pp/ops/hired-agents` return cached data within the TTL window — Plant API receives fewer requests and the ops screens respond faster.

---

#### Story E5-S1: Create `ops_cache.py` Redis cache service

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it2-e5`

**What to do:**
> Create `src/PP/BackEnd/services/ops_cache.py` — an async Redis cache with graceful degradation.
> Add `redis==5.0.1` to `src/PP/BackEnd/requirements.txt`.
> Add `REDIS_URL: str = ""` and `OPS_CACHE_TTL_SECONDS: int = 60` to `src/PP/BackEnd/core/config.py` `Settings` class.
> Expose two async functions: `cache_get(namespace, path, params) -> Optional[Any]` and `cache_set(namespace, path, value, params, ttl_seconds)`.
> If `REDIS_URL` is empty or Redis raises any exception, both functions must silently no-op (return None for get; ignore on set). No exceptions must propagate to callers.

**Files to create / modify:**

| File | Action |
|---|---|
| `src/PP/BackEnd/requirements.txt` | add `redis==5.0.1` |
| `src/PP/BackEnd/core/config.py` | add `REDIS_URL` and `OPS_CACHE_TTL_SECONDS` fields |
| `src/PP/BackEnd/services/ops_cache.py` | **create** |

**Commit message:** `feat(PP-FUNC-1-ops-screens): create ops_cache.py Redis response cache service`

---

#### Story E5-S2: Wire Redis cache into ops_subscriptions.py and ops_hired_agents.py

**BLOCKED UNTIL:** E5-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it2-e5` (continue)

**What to do:**
> In both `ops_subscriptions.py` and `ops_hired_agents.py`, import `cache_get` and `cache_set` from `services.ops_cache`.
> For every GET route: (1) attempt `cache_get` before calling Plant — return cached value on hit; (2) on Plant 200, call `cache_set` with the response body before returning it.
> Non-200 responses and errors are **not** cached.
> Update `docker-compose.test.yml`: add `REDIS_URL=redis://redis-test:6379/2` to pp-backend-test env and `redis-test` to its `depends_on`.

**Files to modify:**

| File | Action |
|---|---|
| `src/PP/BackEnd/api/ops_subscriptions.py` | add cache_get before Plant call + cache_set on 200 |
| `src/PP/BackEnd/api/ops_hired_agents.py` | same pattern for all 4 routes |
| `docker-compose.test.yml` | add `REDIS_URL` env var + `redis-test` depends_on for pp-backend-test |

**Acceptance criteria (binary pass/fail):**
1. `ops_subscriptions.py` imports `cache_get`, `cache_set` from `services.ops_cache`
2. `list_subscriptions` checks cache before Plant call; sets cache on 200
3. `ops_hired_agents.py` all 4 routes follow the same pattern
4. `ruff check src/PP/BackEnd/api/ops_subscriptions.py src/PP/BackEnd/api/ops_hired_agents.py` exits 0
5. `python -c "from api.ops_subscriptions import router; from api.ops_hired_agents import router"` exits 0

**Commit message:** `feat(PP-FUNC-1-ops-screens): wire Redis cache into ops_subscriptions and ops_hired_agents`

**Epic complete ✅** — run Rule 5 Docker test, then continue to E6

---

### Epic E6: ops_cache service is fully tested

**Branch:** `feat/PP-FUNC-1-ops-screens-it2-e6`
**User story:** As a platform engineer, I can verify that the Redis cache service behaves correctly — serving hits from cache, falling through on misses, and degrading gracefully when Redis is unavailable — without requiring a live Redis instance.

---

#### Story E6-S1: Write pytest tests for ops_cache.py

**BLOCKED UNTIL:** E5-S2 committed (test imports depend on the wired modules)
**Estimated time:** 45 min
**Branch:** `feat/PP-FUNC-1-ops-screens-it2-e6`

**What to do:**
> Create `src/PP/BackEnd/tests/test_ops_cache.py`.
> All tests use `unittest.mock.patch` to inject fake Redis mocks — no live Redis required.
> Cover: _build_key determinism, cache miss (no REDIS_URL), cache miss (key absent), cache hit (returns deserialized value), graceful get error, graceful set error, round-trip (set then get), noop when REDIS_URL empty.

**Files to create:**

| File | Action |
|---|---|
| `src/PP/BackEnd/tests/test_ops_cache.py` | **create** — full test file |

**Acceptance criteria (binary pass/fail):**
1. All tests in `test_ops_cache.py` pass
2. `pytest tests/test_ops_cache.py -v` exits 0 in Docker
3. No existing tests broken — `pytest tests/ -v` exits 0 in Docker
4. Coverage on `services/ops_cache.py` ≥ 80%

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm pp-backend-test \
  pytest tests/test_ops_cache.py -v --tb=short
```

**Commit message:** `feat(PP-FUNC-1-ops-screens): pytest tests for ops_cache Redis service`

**Done signal:** `"E6-S1 done. Created: test_ops_cache.py (11 tests ✅). Full regression: all existing tests still pass ✅"`

**Epic complete ✅** — run Rule 7 to open the iteration PR.

---

## Plan ready: PP-FUNC-1-ops-screens

**File:** `docs/PP/iterations/PP-FUNC-1-ops-screens.md`

| Iteration | Scope | ⏱ Est | Come back |
|---|---|---|---|
| 1 | Lane A — 2 new PP BackEnd proxy files + FE wiring for HiredAgentsOps + Billing | ~4.5h | Your launch time + 5h |
| 2 | Lane A — Redis response caching for ops proxy routes | ~3h | Your launch time + 3.5h |

---

## To start Iteration 1 — paste this into GitHub Copilot agent mode:

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior React / TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-FUNC-1-ops-screens.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3, E4. This is a single-iteration plan.
TIME BUDGET: 4.5h. If you reach 5h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER (sequential — do not parallelise):
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this exact order: E1 → E2 → E3 → E4
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.