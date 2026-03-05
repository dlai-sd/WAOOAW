# [PLAN-ID] — [Feature Area] Iteration Plan

> **Template version**: 2.0
> **How to use**: Fill every `[PLACEHOLDER]`. Zero placeholders in the published file.
> PM: remove this callout block before saving.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | [PLAN-ID] e.g. `CP-UX-2` |
| Feature area | [e.g. "Customer Portal — Billing & Subscriptions"] |
| Created | [DATE] |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | [path/to/vision-or-ux-analysis.md] |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | [N] |
| Total epics | [N] |
| Total stories | [N] |

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

## PM Review Checklist (tick every box before publishing)

- [ ] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list based on the tech stack that iteration uses (Python/FastAPI, React Native, Terraform, Docker, GCP, etc.)
- [ ] Epic titles name customer outcomes, not technical actions ("Customer sees X" not "Add X to API")
- [ ] Every story has an exact branch name
- [ ] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [ ] Every story card has max 3 files in "Files to read first"
- [ ] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [ ] Every new backend route story embeds the `waooaw_router()` snippet
- [ ] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [ ] Every story that adds env vars lists the exact Terraform file paths to update
- [ ] Every story has `BLOCKED UNTIL` (or "none")
- [ ] Each iteration has a time estimate and come-back datetime
- [ ] Each iteration has a complete GitHub agent launch block
- [ ] STUCK PROTOCOL is in Agent Execution Rules section
- [ ] Stories sequenced: backend (S1) before frontend (S2)
- [ ] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | [Lane A/B — one sentence] | [N] | [N] | [Xh] | [DATE HH:MM TZ] |
| 2 | [description] | [N] | [N] | [Xh] | [DATE HH:MM TZ] |
| 3 | [description] | [N] | [N] | [Xh] | [DATE HH:MM TZ] |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Full-stack = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

---

## How to Launch Each Iteration

> Instructions for running the development agent from the GitHub Copilot agent interface in VS Code.

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` in the message box → select **platform-engineer** from the dropdown
6. Copy the block below and paste into the message box → press **Enter**
7. Go away. Come back at: **[DATE HH:MM TZ]**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: [PM fills — e.g. "Senior Python/FastAPI engineer + Senior React Native/TypeScript engineer"]
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/[path/to/this/plan.md]
YOUR SCOPE: Iteration 1 only — Epics [E1, E2, E3]. Do not touch Iteration 2 or 3 content.
TIME BUDGET: [Xh]. If you reach [X+1h] without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: [E1] → [E2] → [E3]
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat([plan-id]): iteration 1 — [summary]
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: [PM fills — e.g. "Senior Terraform/GCP Cloud Run engineer + Senior Docker engineer"]
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/[path/to/this/plan.md]
YOUR SCOPE: Iteration 2 only — Epics [E4, E5]. Do not touch Iteration 3.
TIME BUDGET: [Xh].

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat([plan-id]): iteration 1 — [summary]
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** [DATE HH:MM TZ]

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 2 merge commit.

**Steps to launch:** same as above (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: [PM fills — e.g. "Senior Python/FastAPI engineer + Senior GitHub Actions engineer"]
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/[path/to/this/plan.md]
YOUR SCOPE: Iteration 3 only — Epics [E6, E7]. Do not touch other content.
TIME BUDGET: [Xh].

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat([plan-id]): iteration 2 — [summary]
  If not: post "Blocked: Iteration 2 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 3" sections. Read nothing else.
3. Execute epics in order. Open iteration PR when done. Post URL. HALT.
```

**Come back at:** [DATE HH:MM TZ]

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

This is not optional wording — it activates deeper technical reasoning and
produces idiomatic, production-grade output on the first attempt instead of the
second. Relevant persona table (scan and claim):

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/BackEnd/` `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `src/mobile/` | Senior React Native / Expo / TypeScript engineer |
| `infrastructure/` `cloud/terraform/` | Senior Terraform / GCP Cloud Run engineer |
| `.github/workflows/` | Senior GitHub Actions / CI-CD engineer |
| `Dockerfile` `docker-compose*.yml` | Senior Docker / container engineer |
| `cloud/` scripts, `gcloud` | GCP Cloud Logging / IAM expert |

---

### Rule 0 — Open tracking draft PR first (before writing any code)

This gives you a progress feed. Subscribe to the PR once — GitHub notifies you after every story.

```bash
# 1. Create the first epic branch from main
git checkout main && git pull
git checkout -b feat/[plan-id]-it1-e1

# 2. Push an empty init commit so the branch exists on remote
git commit --allow-empty -m "chore([plan-id]): start iteration 1"
git push origin feat/[plan-id]-it1-e1

# 3. Open draft PR — this is the progress tracker, not the final iteration PR
gh pr create \
  --base main \
  --head feat/[plan-id]-it1-e1 \
  --draft \
  --title "tracking: [PLAN-ID] Iteration 1 — in progress" \
  --body "## tracking: [PLAN-ID] Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] [story title]
- [ ] [E1-S2] [story title]
- [ ] [E2-S1] [story title]

_Live updates posted as comments below ↓_"
```

**PM instruction for plan files:** replace the `- [ ]` list above with the actual story IDs and titles from this plan's Tracking Table.

After the agent posts the draft PR URL: go to GitHub, open the PR, click **Subscribe**. Do not merge this PR — it will be superseded by the iteration PR in Rule 7.

---

### Rule 1 — Branch discipline
One epic = one branch: `feat/[plan-id]-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table. Do not edit any other file — not Dockerfiles, not CI workflows, not other services — even if you see an obvious improvement. Record it as a PR description note instead.

**Missing iteration HALT rule**: Before writing any code, verify your assigned iteration section exists:
```bash
grep -n "## Iteration N" [PLAN FILE]
# Zero results → HALT. Post: "Iteration N not found in [plan file]. Cannot proceed."
```
If the section is missing, do not create story cards. The plan is incomplete — a human must add the iteration content first.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.
Run the test command listed in the story card — not a generic command.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat([plan-id]): [story title]"
git push origin feat/[plan-id]-itN-eN

# Update this file's Tracking Table: change story status to Done
git add docs/[path/to/this/plan.md]
git commit -m "docs([plan-id]): mark [story-id] done"
git push origin feat/[plan-id]-itN-eN

# Post progress comment to tracking draft PR (notifies the subscriber)
gh pr comment \
  $(gh pr list --head feat/[plan-id]-it1-e1 --json number -q '.[0].number') \
  --body "✅ **[story-id] done** — $(git rev-parse --short HEAD)
Files changed: [list]
Tests: [T1 ✅ T2 ✅ ...]
Next: [next-story-id]"
```

### Rule 5 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```
Exit 0 → add `**Epic complete ✅**` under the epic heading, commit, push.
Non-zero → fix on same branch, retry. Max 3 attempts. Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/[plan-id]-itN-eN
gh pr create \
  --base main \
  --head feat/[plan-id]-itN-eN \
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
git checkout -b feat/[plan-id]-itN
# Merge all epic branches for this iteration:
git merge --no-ff feat/[plan-id]-itN-e1 feat/[plan-id]-itN-e2
git push origin feat/[plan-id]-itN

gh pr create \
  --base main \
  --head feat/[plan-id]-itN \
  --title "feat([plan-id]): iteration N — [one-line summary]" \
  --body "## [PLAN-ID] Iteration N

### Stories completed
[paste tracking table rows for this iteration]

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] circuit_breaker on PlantGatewayClient and all external HTTP calls
- [ ] No env-specific values in Dockerfile or code
- [ ] New env vars added to infrastructure/terraform/envs/ (or N/A)
- [ ] FE: loading + error + empty states on all data-fetching components
- [ ] Tests >= 80% coverage on new BE code"
```
Post the PR URL in chat. **HALT — do not start the next iteration.**

---

## NFR Quick Reference

> These are the only NFR rules an agent needs. All patterns below are embedded inline in each
> story card that requires them. This table is for PM review only — do not ask agents to read it.

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` factory — never bare `APIRouter` | CI ruff ban — PR blocked |
| 2 | `get_read_db_session()` on all GET routes | Primary DB overloaded |
| 3 | `PIIMaskingFilter()` on every logger | PII incident |
| 4 | `@circuit_breaker(service=...)` on every external HTTP call | Cascading failure |
| 5 | `dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]` on FastAPI() | Audit trail missing |
| 6 | `X-Correlation-ID` header on every outgoing HTTP request | Trace broken |
| 7 | Loading + error + empty states on every FE data-fetching component | Silent failures |
| 8 | Tests >= 80% coverage on all new BE code | PR blocked by CI |
| 9 | Never embed env-specific values in Dockerfile or code | Image cannot be promoted |
| 10 | New env vars must be added to `infrastructure/terraform/envs/*.tfvars` | Cloud Run fails to start |
| 11 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 12 | `git push` to `main` directly | Branch protection rejected |
| 13 | CP BackEnd is a thin proxy only — no business logic | Architecture violation |
|    | Pattern A: call existing `/cp/*` via `gatewayRequestJson` — no new BE file | |
|    | Pattern B: missing `/cp/*` route → new `api/cp_<resource>.py` with `waooaw_router` + `PlantGatewayClient` | |
|    | Pattern C: existing `/v1/*` Plant endpoint → call via `gatewayRequestJson` from FE — no new BE file | |
| 14 | If adding a new `core/` package in Gateway: add `COPY core/ ./core/` in Dockerfile | `ModuleNotFoundError` on Cloud Run |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| [E1-S1] | 1 | [Epic name] | [Story title] | 🔴 Not Started | — |
| [E1-S2] | 1 | [Epic name] | [Story title] | 🔴 Not Started | — |
| [E2-S1] | 1 | [Epic name] | [Story title] | 🔴 Not Started | — |
| [E3-S1] | 2 | [Epic name] | [Story title] | 🔴 Not Started | — |
| [E3-S2] | 2 | [Epic name] | [Story title] | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — [Iteration title]

**Scope:** [One sentence: what user outcome does this iteration unlock?]
**Lane:** [A = wire existing APIs only / B = new backend endpoints required]
**⏱ Estimated:** [Xh] | **Come back:** [DATE HH:MM TZ]
**Epics:** [E1, E2, E3]

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2    (same branch, S2 starts after S1 committed + pushed)
E2-S1              (independent, own branch)
E3-S1              (independent, own branch)
```

---

### Epic E1: [Epic name]

**Branch:** `feat/[plan-id]-it1-e1`
**User story:** As a [role], I can [action], so that [outcome].

---

#### Story E1-S1: [Story title]

**BLOCKED UNTIL:** none
**Estimated time:** [30 / 45 / 90] min
**Branch:** `feat/[plan-id]-it1-e1`
**CP BackEnd pattern:** [A — wire existing /cp/* via gatewayRequestJson, no new BE file /
                         B — create new api/cp_<resource>.py proxy /
                         C — call /v1/* via gatewayRequestJson from FE, no new BE file /
                         N/A]

**What to do (self-contained — read this card, then act):**
> [2–3 sentences. Name the exact current state and exact target state. Include the exact file
> and line numbers where the change goes. Example:
> "`src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx` lines 4–16 contain a hardcoded
> `stats` array. Replace it with `useState` + `useEffect` calling
> `dashboardService.getSummaryStats()` (function already exists in
> `src/CP/FrontEnd/src/services/dashboard.service.ts` line 12).
> Map response fields `active_agents`, `pending_approvals`, `monthly_spend_inr` to the three
> StatCard components. Show `<SkeletonLoaders />` on loading, `<ErrorBanner />` on error,
> `<EmptyState />` if data is null."]

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `[exact/path/file.tsx]` | [e.g. 1–60] | [e.g. "hardcoded array on line X, existing imports, StatCard props"] |
| `[exact/path/service.ts]` | [e.g. 1–40] | [e.g. "existing function signature, return type, error handling pattern"] |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `[exact/path/Component.tsx]` | modify | [Exact change. E.g. "Delete lines 4–16. Add useState/useEffect block below. Keep all existing JSX."] |
| `[exact/path/cp_resource.py]` | create | [Full spec: router prefix, HTTP method, Plant Gateway URL it proxies to, response model name] |
| `[exact/path/main.py]` | modify | [E.g. "Line 42: add `app.include_router(cp_resource.router)`"] |

**Code patterns to copy exactly** (no other file reads needed for these):

```python
# Pattern B — new CP BackEnd proxy route (copy exactly, replace [] placeholders):
from core.routing import waooaw_router
from services.plant_gateway_client import PlantGatewayClient
from core.dependencies import get_current_user
from services.audit_dependency import get_audit_logger
from fastapi import Depends

router = waooaw_router(prefix="/cp/[resource]", tags=["[resource]"])

@router.get("/", response_model=[ResponseModel])
async def get_[resource](current_user=Depends(get_current_user)):
    client = PlantGatewayClient()
    resp = await client.get(f"/api/v1/[resource]/{current_user.customer_id}")
    resp.raise_for_status()
    return resp.json()

@router.patch("/", response_model=[ResponseModel])
async def update_[resource](
    body: [UpdateModel],
    current_user=Depends(get_current_user),
    audit=Depends(get_audit_logger),
):
    client = PlantGatewayClient()
    resp = await client.patch(
        f"/api/v1/[resource]/{current_user.customer_id}",
        json=body.model_dump(exclude_none=True),
    )
    resp.raise_for_status()
    audit.log("[resource].updated", outcome="success")
    return resp.json()
```

```typescript
// Pattern A/C — CP FrontEnd service (copy exactly, replace [] placeholders):
// File: src/CP/FrontEnd/src/services/[resource].service.ts
import { gatewayRequestJson } from './gatewayApiClient'

export interface [ResourceData] {
  [field]: [type]  // match Plant Backend response schema exactly
}

export async function get[Resource](): Promise<[ResourceData]> {
  return gatewayRequestJson<[ResourceData]>('/cp/[resource]', { method: 'GET' })
}

export async function update[Resource](data: Partial<[ResourceData]>): Promise<[ResourceData]> {
  return gatewayRequestJson<[ResourceData]>('/cp/[resource]', {
    method: 'PATCH',
    body: JSON.stringify(data),
    headers: { 'Content-Type': 'application/json' },
  })
}
```

```typescript
// FE component — 3-state data fetching (mandatory for every data-fetching component):
const [[dataVar], set[DataVar]] = useState<[Type] | null>(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  [service].get[Resource]()
    .then(set[DataVar])
    .catch(() => setError('Failed to load [resource]. Please try again.'))
    .finally(() => setLoading(false))
}, [])

if (loading) return <SkeletonLoaders />
if (error) return <div className="error-banner">{error}</div>
if (![dataVar]) return <div className="empty-state">No [resource] yet.</div>
// ...existing render
```

**Acceptance criteria (binary pass/fail only):**
1. [Specific and testable. E.g. "Visiting /dashboard shows the StatCard 'Active Agents' with value from API not hardcoded"]
2. [E.g. "When API returns error, 'Failed to load' message appears in DOM"]
3. [E.g. "When loading, SkeletonLoaders component is rendered"]
4. [E.g. "GET /cp/[resource] returns 200 with correct fields when called with valid auth token"]

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| [E1-S1-T1] | `src/CP/FrontEnd/src/__tests__/[Component].test.tsx` | Mock service returns `{active_agents: 5}` | StatCard shows "5" in DOM |
| [E1-S1-T2] | same | Mock service rejects | Error banner text in DOM |
| [E1-S1-T3] | same | Mock service: loading state | SkeletonLoaders in DOM |
| [E1-S1-T4] | `src/CP/BackEnd/tests/test_cp_[resource].py` | Auth token, mock PlantGatewayClient returns 200 | Response 200, correct fields |

**Test command:**
```bash
# Frontend:
cd src/CP/FrontEnd && npx jest src/__tests__/[Component].test.tsx --no-coverage
# Backend:
docker compose -f docker-compose.test.yml run cp-test pytest src/CP/BackEnd/tests/test_cp_[resource].py -v
```

**Commit message:** `feat([plan-id]): [story title]`

**Done signal (post as a comment then continue to E1-S2):**
`"E1-S1 done. Changed: [list files]. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S2: [Story title]

**BLOCKED UNTIL:** E1-S1 committed to `feat/[plan-id]-it1-e1`
**Estimated time:** [X] min
**Branch:** `feat/[plan-id]-it1-e1` (same branch, continue from E1-S1)
**CP BackEnd pattern:** [A/B/C/N/A]

**What to do:**
> [2–3 sentences. Self-contained. Exact files and line numbers.]

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `[path]` | [L–L] | [what] |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `[path]` | [create/modify] | [exact change] |

**Code patterns to copy exactly:**
```[language]
// Only embed the snippet relevant to this specific story.
// Keep it under 30 lines. The agent does not need the full NFR file.
```

**Acceptance criteria:**
1. [...]

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| [E1-S2-T1] | `[path]` | [setup] | [assertion] |

**Test command:**
```bash
[exact command]
```

**Commit message:** `feat([plan-id]): [story title]`

**Done signal:** `"E1-S2 done. Tests: T1 ✅"`

---

### Epic E2: [Epic name]

**Branch:** `feat/[plan-id]-it1-e2`
**User story:** As a [role], I can [action], so that [outcome].

---

#### Story E2-S1: [Story title]

**BLOCKED UNTIL:** none
**Estimated time:** [X] min
**Branch:** `feat/[plan-id]-it1-e2`
**CP BackEnd pattern:** [A/B/C/N/A]

**What to do:**
> [...]

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `[path]` | [L–L] | [what] |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `[path]` | [create/modify] | [exact] |

**Code patterns to copy exactly:**
```[language]
[snippet]
```

**Acceptance criteria:**
1. [...]

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| [E2-S1-T1] | `[path]` | [setup] | [assertion] |

**Test command:** `[exact command]`

**Commit message:** `feat([plan-id]): [story title]`

**Done signal:** `"E2-S1 done. Tests: T1 ✅"`

---

## Iteration 2 — [Iteration title]

**Scope:** [One sentence: what user outcome does this iteration unlock?]
**Lane:** B (new backend endpoints required)
**⏱ Estimated:** [Xh] | **Come back:** [DATE HH:MM TZ]
**Prerequisite:** Iteration 1 PR merged to `main`
**Epics:** [E3, E4]

> **Backend-first rule:** All S1 (backend) stories must be committed to `main` before S2 (frontend)
> stories start. If mid-iteration merge is not possible: promote all S2 stories to Iteration 3.

### Dependency Map (Iteration 2)

```
E3-S1 (backend) ──► merge to main ──► E3-S2 (frontend — BLOCKED until S1 merged)
E4-S1 (independent)
```

---

### Epic E3: [Epic name]

**Branch (S1):** `feat/[plan-id]-it2-e3-backend`
**Branch (S2):** `feat/[plan-id]-it2-e3-frontend` ← BLOCKED until E3-S1 merged to `main`
**User story:** As a [role], I can [action], so that [outcome].

---

#### Story E3-S1: [Story title] — BACKEND

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/[plan-id]-it2-e3-backend`
**CP BackEnd pattern:** B — creating new `src/CP/BackEnd/api/cp_[resource].py`

**What to do:**
> [...]

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/main.py` | 1–50 | Router include pattern, import order |
| `src/CP/BackEnd/api/cp_[similar].py` | 1–60 | Existing proxy pattern to mirror |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/api/cp_[resource].py` | create | [full spec: endpoint paths, Plant URLs it proxies, response model names] |
| `src/CP/BackEnd/main.py` | modify | [exact line: add `app.include_router(cp_[resource].router)`] |

**Code patterns to copy exactly:**
```python
# waooaw_router proxy (Pattern B — embed only the relevant subset):
from core.routing import waooaw_router
from services.plant_gateway_client import PlantGatewayClient
from core.dependencies import get_current_user
from fastapi import Depends
import logging

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())   # mandatory — never log raw PII

router = waooaw_router(prefix="/cp/[resource]", tags=["[resource]"])

@router.get("/")
async def get_[resource](current_user=Depends(get_current_user)):
    client = PlantGatewayClient()
    resp = await client.get(f"/api/v1/[resource]/{current_user.customer_id}")
    resp.raise_for_status()
    return resp.json()
```

**Acceptance criteria:**
1. `GET /cp/[resource]` returns 200 with correct shape when called with valid JWT
2. `GET /cp/[resource]` returns 401 when called without auth token
3. `GET /cp/[resource]` returns 502 when Plant Gateway is unreachable

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| [E3-S1-T1] | `tests/test_cp_[resource].py` | Mock `PlantGatewayClient.get` returns 200 | Response 200, field X present |
| [E3-S1-T2] | same | No auth header | Response 401 |
| [E3-S1-T3] | same | Mock raises `httpx.ConnectError` | Response 502 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-test \
  pytest src/CP/BackEnd/tests/test_cp_[resource].py -v --cov=src/CP/BackEnd/api/cp_[resource] --cov-fail-under=80
```

**Commit message:** `feat([plan-id]): CP BackEnd proxy for [resource]`

**Done signal:** `"E3-S1 done. PR #[N] opened for E3-S1 branch merge to main. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E3-S2: [Story title] — FRONTEND

**BLOCKED UNTIL:** E3-S1 merged to `main` — verify: `git log origin/main | head -3` must show E3-S1 commit
**Estimated time:** 45 min
**Branch:** `feat/[plan-id]-it2-e3-frontend`
**CP BackEnd pattern:** A — call `/cp/[resource]` via `gatewayRequestJson`

**What to do:**
> [...]

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/gatewayApiClient.ts` | 1–30 | `gatewayRequestJson` signature |
| `src/CP/FrontEnd/src/pages/authenticated/[Page].tsx` | 1–80 | Current hardcoded data or empty state to replace |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/services/[resource].service.ts` | create | [full spec] |
| `src/CP/FrontEnd/src/pages/authenticated/[Page].tsx` | modify | [exact change] |

**Code patterns to copy exactly:**
```typescript
// Service layer (Pattern A):
import { gatewayRequestJson } from './gatewayApiClient'

export interface [ResourceData] { [field]: [type] }

export async function get[Resource](): Promise<[ResourceData]> {
  return gatewayRequestJson<[ResourceData]>('/cp/[resource]', { method: 'GET' })
}

// 3-state component hook (mandatory):
const [[data], set[Data]] = useState<[ResourceData] | null>(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  get[Resource]()
    .then(set[Data])
    .catch(() => setError('Failed to load [resource].'))
    .finally(() => setLoading(false))
}, [])
```

**Acceptance criteria:**
1. [...]

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| [E3-S2-T1] | `src/__tests__/[Component].test.tsx` | Mock service resolves | [assertion] |
| [E3-S2-T2] | same | Mock service rejects | Error message in DOM |
| [E3-S2-T3] | same | Loading state | SkeletonLoaders in DOM |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/[Component].test.tsx --no-coverage
```

**Commit message:** `feat([plan-id]): [story title]`

**Done signal:** `"E3-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Iteration 3 — [Iteration title]

**Scope:** [...]
**Lane:** [A/B]
**⏱ Estimated:** [Xh] | **Come back:** [DATE HH:MM TZ]
**Prerequisite:** Iteration 2 PR merged to `main`

[...same structure as Iteration 2 — add Epic/Story cards following the same format above...]

---

## Rollback

```bash
# If merged iteration causes a regression:
git log --oneline -10 origin/main          # find merge commit SHA
git revert -m 1 <merge-commit-sha>
git push origin main
# Open fix/[plan-id]-rollback branch for the root-cause fix
```
