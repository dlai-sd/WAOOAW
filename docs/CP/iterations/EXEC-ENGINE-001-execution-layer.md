# EXEC-ENGINE-001 — Execution Layer: Flow, Component & Agent Runtime

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `EXEC-ENGINE-001` |
| Feature area | Plant BackEnd (execution engine) + CP FrontEnd + PP FrontEnd |
| Created | 2026-03-08 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §3, §5 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 6 |
| Total epics | 14 |
| Total stories | 29 |

**Branch:** `feat/execution-engine-v1`  
**Status:** IN PROGRESS — skeleton committed, story cards being written per iteration  

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

## Vision Intake (Locked)

| Question | Answer |
|---|---|
| **User outcome** | A customer hires a Share Trader or Marketing Agent, configures it, sets a goal, sees it run on schedule, approves or rejects output, and views delivered results — all persisted to DB. A PP operator monitors the fleet and drills into any agent's health. |
| **Out of scope** | PP Compose UI (FlowDef/ComponentDef authoring via browser), mobile app, billing/Razorpay, any agent type beyond Share Trader and Marketing Agent |
| **Lane** | Lane B — new backend tables: `flow_run`, `component_run`, `skill_config`; new Celery component queues; `BaseComponent` interface |
| **Timeline** | 6 iterations, P0 gaps closed by Iteration 2 |

---

## Constitutional Architecture (Locked — reference for all stories)

```
DEFINITION LAYER (PP governs, versioned, immutable once approved)
  AgentTypeDef  →  [SkillDef]  →  [FlowDef]  →  [ComponentDef]

INSTANCE LAYER (customer governs at hire)
  HiredAgent (pins definition_version_id)  →  SkillConfig  →  RunContext template

EXECUTION LAYER (Plant executes, ephemeral, fully audited)
  AgentRun  →  SkillRun  →  FlowRun  →  ComponentRun
  Postgres owns workflow state. Redis/Celery owns job transport.
```

### BaseComponent Interface (agreed — every component implements this)
```python
from dataclasses import dataclass
from uuid import UUID
from abc import ABC, abstractmethod

@dataclass
class ComponentInput:
    flow_run_id: UUID
    customer_id: UUID
    skill_config: dict        # PP-locked + customer-filled values
    run_context: dict         # dynamic params injected per run cycle
    previous_step_output: dict | None

@dataclass
class ComponentOutput:
    success: bool
    data: dict
    error_message: str | None
    duration_ms: int

class BaseComponent(ABC):
    @abstractmethod
    async def execute(self, input: ComponentInput) -> ComponentOutput: ...
```

### FlowRun Status Machine (agreed)
```
pending → running → awaiting_approval → running → completed
                                               ↘ partial_failure
                  → failed
```

### Celery Queue Routing (agreed)
```python
task_routes = {
    "execute_pump":      {"queue": "pump"},
    "execute_processor": {"queue": "processor"},
    "execute_publisher": {"queue": "publisher"},
}
```

### Approval Gate Rule (constitutional)
Gate is a step inside FlowDef. `goal.auto_execute` / `goal.customer_reviews` is a boolean the FlowRun executor checks at that step. No wiring at Skill or Agent level.

### Fan-out Rule (constitutional)
`FlowDef.parallel_steps: list[str]` dispatches one ComponentRun per entry. Fan-in: all complete → `completed`; any fail → `partial_failure` with per-branch outcome in `component_run`.

---

## NFR Pattern (embed in every Plant BackEnd route story)
```python
from core.routing import waooaw_router
router = waooaw_router(prefix="/resource", tags=["resource"])

# GET routes
async def list_things(db=Depends(get_read_db_session)): ...

# POST/PATCH routes  
async def create_thing(db=Depends(get_db_session)): ...

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

with tracer.start_as_current_span("service.operation"):
    pass

@circuit_breaker(service="external_service_name")
async def call_external(): ...
```

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — DB foundation: `flow_run`, `component_run`, `skill_config` tables + migrations | E1, E2 | 5 | 4h | 2026-03-08 12:00 IST |
| 2 | Lane B — `BaseComponent`, `ComponentInput/Output`, Celery component queues, FlowRun executor | E3, E4 | 5 | 4.5h | 2026-03-08 17:00 IST |
| 3 | Lane B — Share Trader components + end-to-end sequential flow | E5, E6 | 5 | 5h | 2026-03-09 10:00 IST |
| 4 | Lane B — Marketing Agent components + fan-out executor + PARTIAL_FAILURE + approvals | E7, E8 | 5 | 5h | 2026-03-09 16:00 IST |
| 5 | Lane A — CP Portal UI: marketplace, hire wizard, my agents, approval queue | E9, E10, E11 | 5 | 5h | 2026-03-10 11:00 IST |
| 6 | Lane A — PP Portal UI: fleet dashboard, health drill-in, DLQ + CP proxies | E12, E13, E14 | 4 | 3.5h | 2026-03-10 15:30 IST |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Full-stack = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: flow_run table | Add `flow_run` table with status machine | 🔴 Not Started | — |
| E1-S2 | 1 | E1: flow_run table | Add `component_run` table | 🔴 Not Started | — |
| E1-S3 | 1 | E1: flow_run table | Add `skill_config` table | 🔴 Not Started | — |
| E2-S1 | 1 | E2: hired_agents column | Add `definition_version_id` to `hired_agents` | 🔴 Not Started | — |
| E2-S2 | 1 | E2: hired_agents column | Register models + smoke test | 🔴 Not Started | — |
| E3-S1 | 2 | E3: BaseComponent | Define `BaseComponent`, `ComponentInput`, `ComponentOutput` | 🟢 Done | — |
| E3-S2 | 2 | E3: BaseComponent | Celery component task routing + worker queue config | 🟢 Done | — |
| E3-S3 | 2 | E3: BaseComponent | Component registry | 🟢 Done | — |
| E4-S1 | 2 | E4: FlowRun executor | FlowRun executor: sequential step runner | 🟢 Done | — |
| E4-S2 | 2 | E4: FlowRun executor | FlowRun executor: fan-out (parallel) + PARTIAL_FAILURE | 🟢 Done | — |
| E5-S1 | 3 | E5: Share Trader components | `DeltaExchangePump` component | 🟢 Done | — |
| E5-S2 | 3 | E5: Share Trader components | `RSIProcessor` component | 🟢 Done | — |
| E5-S3 | 3 | E5: Share Trader components | `DeltaPublisher` component | 🟢 Done | — |
| E6-S1 | 3 | E6: Share Trader flow | Share Trader FlowDef + end-to-end run | 🟢 Done | — |
| E6-S2 | 3 | E6: Share Trader flow | Deliverable written at FlowRun completion | 🟢 Done | — |
| E7-S1 | 4 | E7: Marketing components | `GoalConfigPump` component | 🟢 Done | — |
| E7-S2 | 4 | E7: Marketing components | `ContentProcessor` component | 🟢 Done | — |
| E7-S3 | 4 | E7: Marketing components | `LinkedInPublisher` + `YouTubePublisher` components | 🟢 Done | — |
| E8-S1 | 4 | E8: Marketing flow | Marketing Agent FlowDef + fan-out end-to-end | 🟢 Done | — |
| E8-S2 | 4 | E8: Marketing flow | `POST /v1/approvals/{flow_run_id}/approve` endpoint | 🟢 Done | — |
| E9-S1 | 5 | E9: CP UI components | Reusable `AgentCard` + `StatusDot` | 🔴 Not Started | — |
| E10-S1 | 5 | E10: CP marketplace | Marketplace screen with hire CTA | 🔴 Not Started | — |
| E10-S2 | 5 | E10: CP marketplace | Hire wizard: skill config + goal setting | 🔴 Not Started | — |
| E11-S1 | 5 | E11: CP my agents | My Agents + `FlowRunTimeline` + `DeliverableCard` | 🔴 Not Started | — |
| E11-S2 | 5 | E11: CP my agents | Approval queue + `ApprovalQueueItem` | 🔴 Not Started | — |
| E12-S1 | 6 | E12: PP fleet | PP Fleet dashboard with agent health map | 🔴 Not Started | — |
| E13-S1 | 6 | E13: PP health | Per-agent health drill-in with `ComponentRunRow` | 🔴 Not Started | — |
| E14-S1 | 6 | E14: PP DLQ + proxies | DLQ panel: view, requeue, skip | 🔴 Not Started | — |
| E14-S2 | 6 | E14: PP DLQ + proxies | CP proxy routes for flow-runs + component-runs | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given. Activate each persona now.
For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy / Celery engineer |
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI thin-proxy engineer |
| `frontend/` `src/CP/FrontEnd/` | Senior HTML5 / CSS3 / vanilla JS or React engineer |
| `src/PP/BackEnd/` | Senior Python 3.11 / FastAPI engineer |
| `infrastructure/` | Senior Terraform / GCP Cloud Run engineer |

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
# 1. Create the epic branch from main
git checkout main && git pull
git checkout -b feat/EXEC-ENGINE-001-itN-eN   # replace N with iteration and epic numbers

# 2. Push an empty init commit
git commit --allow-empty -m "chore(EXEC-ENGINE-001): start iteration N epic N"
git push origin feat/EXEC-ENGINE-001-itN-eN

# 3. Open draft PR — progress tracker
gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-itN-eN \
  --draft \
  --title "tracking: EXEC-ENGINE-001 Iteration N — in progress" \
  --body "## tracking: EXEC-ENGINE-001 Iteration N
Subscribe to this PR to receive one notification per story completion.
### Stories
- [ ] [paste story IDs from Tracking Table for this iteration]
_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/EXEC-ENGINE-001-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

**Missing iteration HALT rule**: Before writing any code:
```bash
grep -n "## Iteration N" docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
# Zero results → HALT. Post: "Iteration N not found in plan file. Cannot proceed."
```

### Rule 3 — Tests before the next story
Write every test listed in the story's "Tests to write" table before advancing to the next story.
Run the exact test command in the story card.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(EXEC-ENGINE-001): [story title]"
git push origin feat/EXEC-ENGINE-001-itN-eN

# Update Tracking Table in this plan file: change story status to 🟢 Done
git add docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
git commit -m "docs(EXEC-ENGINE-001): mark [story-id] done"
git push origin feat/EXEC-ENGINE-001-itN-eN

# Post progress comment to tracking draft PR
gh pr comment \
  $(gh pr list --head feat/EXEC-ENGINE-001-itN-eN --json number -q '.[0].number') \
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
Non-zero → fix on same branch, retry. Max 3 attempts. Then: **STUCK PROTOCOL** (Rule 6).

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/EXEC-ENGINE-001-itN-eN
gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-itN-eN \
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
git checkout -b feat/EXEC-ENGINE-001-itN
git merge --no-ff feat/EXEC-ENGINE-001-itN-e1 feat/EXEC-ENGINE-001-itN-e2
git push origin feat/EXEC-ENGINE-001-itN

gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-itN \
  --title "feat(EXEC-ENGINE-001): iteration N — [one-line summary]" \
  --body "## EXEC-ENGINE-001 Iteration N

### Stories completed
[paste Tracking Table rows for this iteration]

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] @circuit_breaker on all external HTTP calls
- [ ] No env-specific values in Dockerfile or code
- [ ] Tests >= 80% coverage on new BE code
- [ ] Postgres owns flow state; Redis only transports jobs"
```
Post the PR URL in chat. **HALT — do not start the next iteration.**

---

## NFR Quick Reference (PM review only — agents do not read this)

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` factory — never bare `APIRouter` | CI ruff ban — PR blocked |
| 2 | `get_read_db_session()` on all GET routes | Primary DB overloaded |
| 3 | `PIIMaskingFilter()` on every logger | PII incident |
| 4 | `@circuit_breaker(service=...)` on every external HTTP call | Cascading failure |
| 5 | `dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]` on FastAPI() | Audit trail missing |
| 6 | `X-Correlation-ID` header on every outgoing HTTP request | Trace broken |
| 7 | Tests >= 80% coverage on all new BE code | PR blocked by CI |
| 8 | Never embed env-specific values in Dockerfile or code | Image cannot be promoted |
| 9 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 10 | CP BackEnd is a thin proxy only — no business logic | Architecture violation |
| 11 | Pattern B: missing `/cp/*` route → new `api/cp_<resource>.py` with `waooaw_router` | Architecture violation |
| 12 | Postgres owns workflow state; Redis/Celery owns job transport only | State loss on Redis restart |

---

## Reusable UI Components (defined here, referenced by name in stories)

| Component | First defined | Purpose |
|---|---|---|
| `AgentCard` | Iteration 5 — S1 | Marketplace + My Agents card with avatar, status dot, specialty, rating |
| `StatusDot` | Iteration 5 — S1 | Colour-coded status pill: 🟢 running / 🟡 awaiting_approval / 🔴 failed / ⚫ paused |
| `ApprovalQueueItem` | Iteration 5 — S3 | Single approval request row with preview, approve/reject CTAs |
| `FlowRunTimeline` | Iteration 5 — S4 | Horizontal stepper showing FlowRun steps and per-step status |
| `ComponentRunRow` | Iteration 6 — S2 | Table row for a single ComponentRun: type, status, duration, input/output expand |
| `DeliverableCard` | Iteration 5 — S4 | Deliverable output card with type badge, content preview, download link |

---

<!-- ITERATION STORIES BEGIN BELOW — written and committed one iteration at a time -->

---

## How to Launch Each Iteration

> **One iteration = one feature branch + one PR to `main`.** Never start iteration N+1 until the iteration N PR is merged and the user confirms.

### Steps to launch any iteration
1. Open VS Code → Copilot Chat (`Ctrl+Alt+I` / `Cmd+Alt+I`)
2. Click model dropdown → **Agent mode**
3. Click `+` → type `@` → select **platform-engineer**
4. Copy the iteration's agent task block below and paste it verbatim → press **Enter**

---

### Iteration 1 agent task (paste verbatim)

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
```

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy / Alembic engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11 / FastAPI / SQLAlchemy / Alembic engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2. Do not touch Iteration 2 or later content.
TIME BUDGET: 4h. If you reach 5h without finishing, follow STUCK PROTOCOL (Rule 6) now.

PREREQUISITE CHECK (do before anything else):
  Run: git status && git log --oneline -3
  Must show: clean tree on main.
  If not: post why and HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" section in this plan file (Rules -1 through 7).
2. Read "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Execute epics in order: E1 (stories E1-S1, E1-S2, E1-S3) → E2 (stories E2-S1, E2-S2).
5. After each story: commit + push + notify (Rule 4).
6. After each epic: Docker integration test (Rule 5).
7. When all epics are docker-tested, open the iteration PR (Rule 7). Post PR URL. HALT.
```

**Come back at: 2026-03-08 12:00 IST**

---

### Iteration 2 agent task (paste verbatim)

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(EXEC-ENGINE-001): iteration 1 commit
```

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy / Celery engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11 / FastAPI / SQLAlchemy / Celery engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4. Do not touch Iteration 3 or later content.
TIME BUDGET: 4.5h. If you reach 5.5h without finishing, follow STUCK PROTOCOL (Rule 6) now.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(EXEC-ENGINE-001): iteration 1 — DB foundation
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute epics in order: E3 (stories E3-S1, E3-S2, E3-S3) → E4 (stories E4-S1, E4-S2).
4. After each story: commit + push + notify (Rule 4).
5. After each epic: Docker integration test (Rule 5).
6. When all epics are docker-tested, open the iteration PR (Rule 7). Post PR URL. HALT.
```

**Come back at: 2026-03-08 17:00 IST**

---

### Iteration 3 agent task (paste verbatim)

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 2 merge commit.

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy / Celery engineer + Senior httpx / circuit-breaker / API integration engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
YOUR SCOPE: Iteration 3 only — Epics E5, E6. Do not touch other content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL (Rule 6) now.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(EXEC-ENGINE-001): iteration 2 — BaseComponent + Celery queues
  If not: post "Blocked: Iteration 2 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 3" sections. Read nothing else.
3. Execute epics: E5 (E5-S1, E5-S2, E5-S3) → E6 (E6-S1, E6-S2).
4. After each story: commit + push + notify (Rule 4).
5. After each epic: Docker integration test (Rule 5).
6. Open iteration PR when done. Post URL. HALT.
```

**Come back at: 2026-03-09 10:00 IST**

---

### Iteration 4 agent task (paste verbatim)

> ⚠️ Do NOT launch until Iteration 3 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 3 merge commit.

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / Celery engineer + Senior LLM API integration engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
YOUR SCOPE: Iteration 4 only — Epics E7, E8. Do not touch other content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL (Rule 6) now.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(EXEC-ENGINE-001): iteration 3 — Share Trader end-to-end
  If not: post "Blocked: Iteration 3 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 4" sections. Read nothing else.
3. Execute epics: E7 (E7-S1, E7-S2, E7-S3) → E8 (E8-S1, E8-S2).
4. After each story: commit + push + notify (Rule 4).
5. After each epic: Docker integration test (Rule 5).
6. Open iteration PR when done. Post URL. HALT.
```

**Come back at: 2026-03-09 16:00 IST**

---

### Iteration 5 agent task (paste verbatim)

> ⚠️ Do NOT launch until Iteration 4 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 4 merge commit.

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior HTML5 / CSS3 / vanilla JS frontend engineer with WAOOAW dark-theme design system expertise
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior HTML5 / CSS3 / vanilla JS frontend engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
YOUR SCOPE: Iteration 5 only — Epics E9, E10, E11. Do not touch other content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL (Rule 6) now.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(EXEC-ENGINE-001): iteration 4 — Marketing Agent fan-out flow
  If not: post "Blocked: Iteration 4 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 5" sections. Read nothing else.
3. Execute epics: E9 (E9-S1) → E10 (E10-S1, E10-S2) → E11 (E11-S1, E11-S2).
4. After each story: commit + push + notify (Rule 4).
5. After each epic: Docker integration test (Rule 5).
6. Open iteration PR when done. Post URL. HALT.
```

**Come back at: 2026-03-10 11:00 IST**

---

### Iteration 6 agent task (paste verbatim)

> ⚠️ Do NOT launch until Iteration 5 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 5 merge commit.

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior HTML5 / CSS3 / vanilla JS frontend engineer + Senior Python 3.11 / FastAPI thin-proxy engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md
YOUR SCOPE: Iteration 6 only — Epics E12, E13, E14. Do not touch other content.
TIME BUDGET: 3.5h. If you reach 4.5h without finishing, follow STUCK PROTOCOL (Rule 6) now.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(EXEC-ENGINE-001): iteration 5 — CP portal UI
  If not: post "Blocked: Iteration 5 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 6" sections. Read nothing else.
3. Execute epics: E12 (E12-S1) → E13 (E13-S1) → E14 (E14-S1, E14-S2).
4. After each story: commit + push + notify (Rule 4).
5. After each epic: Docker integration test (Rule 5).
6. Open iteration PR when done. Post URL. HALT. 🎉
```

**Come back at: 2026-03-10 15:30 IST**

---

## Iteration 1 — DB Foundation

**Scope:** Customer and PP operator data is persisted to three new Postgres tables (`flow_runs`, `component_runs`, `skill_configs`) + `definition_version_id` on `hired_agents` — the structural foundation every subsequent iteration builds on.
**Lane:** B — new backend tables and Alembic migrations; no frontend changes.
**⏱ Estimated:** 4h | **Come back:** 2026-03-08 12:00 IST
**Epics:** E1, E2

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2 ──► E1-S3    (same branch feat/EXEC-ENGINE-001-it1-e1, sequential)
E2-S1 ──► E2-S2               (branch feat/EXEC-ENGINE-001-it1-e2, sequential; E2-S1 can start after E1-S1 merged)
```

---

### Epic E1: flow_run, component_run, skill_config tables

**Branch:** `feat/EXEC-ENGINE-001-it1-e1`
**User story:** As a PP operator, I can query `flow_runs`, `component_runs`, and `skill_configs` in Postgres so that I have a complete execution and config audit trail.

---

#### Story E1-S1: Add `flow_run` table with status machine

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it1-e1`
**CP BackEnd pattern:** N/A — Plant BackEnd model only

**What to do:**
`src/Plant/BackEnd/models/goal_run.py` tracks runs with only `pending | running | completed | failed`. Create a new `flow_run.py` model with a 6-status machine (`pending | running | awaiting_approval | completed | failed | partial_failure`) and an `idempotency_key` unique constraint. Create the corresponding Alembic migration. `GoalRunModel` is kept as-is for backward compatibility.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/goal_run.py` | 1–60 | Existing column shape, Base import, SQLAlchemy patterns used |
| `src/Plant/BackEnd/models/hired_agent.py` | 1–40 | PK type (String/UUID) to match FK target |
| `src/Plant/BackEnd/database/migrations/versions/` | last file | Highest revision ID to generate the next one |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/flow_run.py` | create | Full model as per code pattern below |
| `src/Plant/BackEnd/database/migrations/versions/<next_rev>_add_flow_runs.py` | create | Alembic migration: `op.create_table("flow_runs", ...)` with all columns and indexes |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/models/flow_run.py
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

FLOW_RUN_STATUSES = (
    "pending", "running", "awaiting_approval",
    "completed", "failed", "partial_failure"
)

class FlowRunModel(Base):
    __tablename__ = "flow_runs"
    id = Column(String, primary_key=True, nullable=False)
    hired_instance_id = Column(String, nullable=False, index=True)
    skill_id = Column(String, nullable=False)
    flow_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    current_step = Column(String, nullable=True)
    run_context = Column(JSONB, nullable=False, default=dict)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(JSONB, nullable=True)
    __table_args__ = (
        Index("ix_flow_runs_hired_instance_id", "hired_instance_id"),
        Index("ix_flow_runs_status", "status"),
        Index("ix_flow_runs_idempotency_key", "idempotency_key"),
    )
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/models/test_flow_run.py` | Create `FlowRunModel` row with status `"pending"` | Row exists in DB, `status == "pending"` |
| E1-S1-T2 | same | Transition status to each of the 6 values | All 6 set without constraint error |
| E1-S1-T3 | same | Insert two rows with same `idempotency_key` | Second insert raises `IntegrityError` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/models/test_flow_run.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E1-S1 — add flow_run table with status machine`

**Done signal:**
`"E1-S1 done. Changed: models/flow_run.py, migrations/<rev>_add_flow_runs.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E1-S2: Add `component_run` table

**BLOCKED UNTIL:** E1-S1 committed to `feat/EXEC-ENGINE-001-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
There is no per-component audit record. Create `src/Plant/BackEnd/models/component_run.py` with a `flow_run_id` FK to `flow_runs.id`, JSONB `input_context` and `output` columns, and `duration_ms`. Create the Alembic migration.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/flow_run.py` | 1–40 | PK type to use as FK target |
| `src/Plant/BackEnd/database/migrations/versions/` | last file | Highest revision ID |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/component_run.py` | create | Full model as per code pattern below |
| `src/Plant/BackEnd/database/migrations/versions/<next_rev>_add_component_runs.py` | create | Alembic migration creating `component_runs` table with FK constraint |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/models/component_run.py
from sqlalchemy import Column, String, DateTime, Integer, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

COMPONENT_RUN_STATUSES = ("pending", "running", "completed", "failed")

class ComponentRunModel(Base):
    __tablename__ = "component_runs"
    id = Column(String, primary_key=True, nullable=False)
    flow_run_id = Column(String, ForeignKey("flow_runs.id"), nullable=False, index=True)
    component_type = Column(String, nullable=False, index=True)
    step_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    input_context = Column(JSONB, nullable=False, default=dict)
    output = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    __table_args__ = (
        Index("ix_component_runs_flow_run_id", "flow_run_id"),
        Index("ix_component_runs_component_type", "component_type"),
        Index("ix_component_runs_status", "status"),
    )
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/Plant/BackEnd/tests/models/test_component_run.py` | Create parent `FlowRunModel` then `ComponentRunModel` with `status="running"` | Row exists, `flow_run_id` is set |
| E1-S2-T2 | same | Mark `status="completed"`, set `output={"candles": []}`, `duration_ms=120` | All fields persisted |
| E1-S2-T3 | same | Mark `status="failed"`, set `error_message="timeout"` | `error_message` persisted |
| E1-S2-T4 | same | Insert `ComponentRunModel` with non-existent `flow_run_id` | Raises `IntegrityError` (FK violated) |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/models/test_component_run.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E1-S2 — add component_run table`

**Done signal:**
`"E1-S2 done. Changed: models/component_run.py, migrations/<rev>_add_component_runs.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S3: Add `skill_config` table + PATCH endpoint

**BLOCKED UNTIL:** E1-S2 committed to `feat/EXEC-ENGINE-001-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it1-e1`
**CP BackEnd pattern:** N/A (Plant BackEnd route only)

**What to do:**
`HiredAgentModel.config` is a single JSONB blob. Create `src/Plant/BackEnd/models/skill_config.py` separating `pp_locked_fields` from `customer_fields` with a `(hired_instance_id, skill_id)` unique constraint. Add `PATCH /v1/skill-configs/{hired_instance_id}/{skill_id}` endpoint that only accepts `customer_fields` updates.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/hired_agent.py` | 1–50 | PK type, existing `config` blob shape |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | 1–60 | `waooaw_router()` usage pattern, `get_db_session` import |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/skill_config.py` | create | Full model as per code pattern below |
| `src/Plant/BackEnd/api/v1/skill_configs.py` | create | PATCH endpoint — see code pattern |
| `src/Plant/BackEnd/main.py` | modify | Add `app.include_router(skill_configs.router)` |
| `src/Plant/BackEnd/database/migrations/versions/<next_rev>_add_skill_configs.py` | create | Alembic migration: `op.create_table("skill_configs", ...)` |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/models/skill_config.py
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

class SkillConfigModel(Base):
    __tablename__ = "skill_configs"
    id = Column(String, primary_key=True, nullable=False)
    hired_instance_id = Column(String, nullable=False, index=True)
    skill_id = Column(String, nullable=False)
    definition_version_id = Column(String, nullable=False)
    pp_locked_fields = Column(JSONB, nullable=False, default=dict)
    customer_fields = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("hired_instance_id", "skill_id", name="uq_skill_config_per_hire"),
        Index("ix_skill_configs_hired_instance_id", "hired_instance_id"),
    )

# src/Plant/BackEnd/api/v1/skill_configs.py
from core.routing import waooaw_router
from core.database import get_db_session
from models.skill_config import SkillConfigModel
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

router = waooaw_router(prefix="/v1/skill-configs", tags=["skill-configs"])

class CustomerFieldsUpdate(BaseModel):
    customer_fields: dict

@router.patch("/{hired_instance_id}/{skill_id}")
async def update_skill_config(
    hired_instance_id: str,
    skill_id: str,
    body: CustomerFieldsUpdate,
    db: Session = Depends(get_db_session),
):
    row = db.query(SkillConfigModel).filter_by(
        hired_instance_id=hired_instance_id, skill_id=skill_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="skill_config not found")
    row.customer_fields = body.customer_fields
    db.commit()
    return {"id": row.id, "customer_fields": row.customer_fields}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S3-T1 | `src/Plant/BackEnd/tests/models/test_skill_config.py` | Insert two `SkillConfigModel` rows with same `(hired_instance_id, skill_id)` | Second insert raises `IntegrityError` |
| E1-S3-T2 | `src/Plant/BackEnd/tests/api/test_skill_configs.py` | PATCH `/v1/skill-configs/{id}/{skill}` with `{"customer_fields": {"rsi_period": 14}}` | HTTP 200, `customer_fields` persisted |
| E1-S3-T3 | same | PATCH with unknown `hired_instance_id` | HTTP 404 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/models/test_skill_config.py src/Plant/BackEnd/tests/api/test_skill_configs.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E1-S3 — add skill_config table + PATCH endpoint`

**Done signal:**
`"E1-S3 done. Changed: models/skill_config.py, api/v1/skill_configs.py, main.py, migration. Tests: T1 ✅ T2 ✅ T3 ✅"`

**Epic E1 complete ✅** — run Docker integration test (Rule 5) before starting E2.

---

### Epic E2: hired_agents column + model registration

**Branch:** `feat/EXEC-ENGINE-001-it1-e2`
**User story:** As the platform, I pin every hired agent to the exact definition version active at hire time so that PP definition updates never silently affect live agents.

---

#### Story E2-S1: Add `definition_version_id` to `hired_agents`

**BLOCKED UNTIL:** none (E2 branch independent of E1 branch; can start after E1-S1 merged to main, but may start in parallel on a separate branch)
**Estimated time:** 30 min
**Branch:** `feat/EXEC-ENGINE-001-it1-e2`
**CP BackEnd pattern:** N/A

**What to do:**
`HiredAgentModel` has `agent_type_id` as a live pointer. Add nullable `definition_version_id` String column via Alembic migration. Update the hire endpoint in `hired_agents_simple.py` to populate it from `agent_type_definitions.version` at hire time.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/hired_agent.py` | 1–60 | Existing column list, `__tablename__`, Base import |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | 1–80 | Hire endpoint — where `HiredAgentModel` is instantiated |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/hired_agent.py` | modify | Add `definition_version_id = Column(String, nullable=True)` after `agent_type_id` |
| `src/Plant/BackEnd/database/migrations/versions/<next_rev>_add_definition_version_id.py` | create | `op.add_column("hired_agents", sa.Column("definition_version_id", sa.String(), nullable=True))` |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | modify | At hire: query `agent_type_definitions` for the current version and set `hired_agent.definition_version_id = version` |

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/Plant/BackEnd/tests/api/test_hired_agents.py` | POST hire endpoint with valid `agent_type_id` | Response body contains non-null `definition_version_id` |
| E2-S1-T2 | same | Query existing hire row from DB | `definition_version_id` column exists and is set |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/api/test_hired_agents.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E2-S1 — add definition_version_id to hired_agents`

**Done signal:**
`"E2-S1 done. Changed: models/hired_agent.py, migrations/<rev>, api/v1/hired_agents_simple.py. Tests: T1 ✅ T2 ✅"`

---

#### Story E2-S2: Register all new models in `__init__.py` + smoke test

**BLOCKED UNTIL:** E2-S1 committed to `feat/EXEC-ENGINE-001-it1-e2`
**Estimated time:** 30 min
**Branch:** `feat/EXEC-ENGINE-001-it1-e2`
**CP BackEnd pattern:** N/A

**What to do:**
`src/Plant/BackEnd/models/__init__.py` imports all models for Alembic autodiscovery. Add imports for `FlowRunModel`, `ComponentRunModel`, `SkillConfigModel`. Verify `alembic upgrade head` runs cleanly and round-trips. Add a smoke test confirming all three tables exist and are queryable.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/__init__.py` | 1–30 | Existing import list pattern |
| `src/Plant/BackEnd/database/migrations/env.py` | 1–40 | `target_metadata` assignment — must use `Base.metadata` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/__init__.py` | modify | Add three lines: `from .flow_run import FlowRunModel`, `from .component_run import ComponentRunModel`, `from .skill_config import SkillConfigModel` |
| `src/Plant/BackEnd/tests/models/test_smoke.py` | create | Smoke test — see code pattern |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/tests/models/test_smoke.py
from sqlalchemy import text

def test_all_new_tables_exist(db_session):
    """Verify all three new tables are present and queryable."""
    for table in ("flow_runs", "component_runs", "skill_configs"):
        result = db_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        assert result == 0, f"Table {table} not found or not empty after migration"
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/Plant/BackEnd/tests/models/test_smoke.py` | Fresh test DB after `alembic upgrade head` | `flow_runs`, `component_runs`, `skill_configs` all return `COUNT(*) = 0` |
| E2-S2-T2 | same | `alembic downgrade -1` then `alembic upgrade head` | No error; all three tables still exist |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/models/test_smoke.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E2-S2 — register new models + smoke test`

**Done signal:**
`"E2-S2 done. Changed: models/__init__.py, tests/models/test_smoke.py. Tests: T1 ✅ T2 ✅"`

**Epic E2 complete ✅** — run Docker integration test (Rule 5) before opening iteration PR.

---

### Iteration 1 — Completion Checkpoint

After ALL E1 and E2 epics complete and Docker integration test passes:

```bash
git checkout main && git pull
git checkout -b feat/EXEC-ENGINE-001-it1
git merge --no-ff feat/EXEC-ENGINE-001-it1-e1 feat/EXEC-ENGINE-001-it1-e2
git push origin feat/EXEC-ENGINE-001-it1

gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-it1 \
  --title "feat(EXEC-ENGINE-001): iteration 1 — DB foundation" \
  --body "## EXEC-ENGINE-001 Iteration 1

### Stories completed
| E1-S1 | flow_run table + status machine | 🟢 Done |
| E1-S2 | component_run table | 🟢 Done |
| E1-S3 | skill_config table + PATCH endpoint | 🟢 Done |
| E2-S1 | definition_version_id on hired_agents | 🟢 Done |
| E2-S2 | model registration + smoke test | 🟢 Done |

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] No env-specific values in Dockerfile or code
- [ ] Tests >= 80% coverage on new BE code
- [ ] Postgres owns flow state; Redis only transports jobs"
```

Post PR URL. **STOP — do not start Iteration 2 until this PR is merged to `main`.**

---

## Iteration 2 — BaseComponent Interface + Celery Component Queues

**Scope:** Define the `BaseComponent` / `ComponentInput` / `ComponentOutput` ABC, the component registry, Celery component queues, and the FlowRun executor (sequential + parallel fan-out).
**Lane:** B — new Python packages; no frontend changes.
**⏱ Estimated:** 4.5h | **Come back:** 2026-03-08 17:00 IST
**Epics:** E3, E4

> **⛔ ITERATION 2 GATE:** Verify before writing any code:
> ```bash
> git fetch origin
> git log --oneline origin/main | head -3
> # Must show: feat(EXEC-ENGINE-001): iteration 1 — DB foundation
> ```
> If absent: **STOP** — "Iteration 2 is blocked — the Iteration 1 PR must be merged to main first."

### Dependency Map (Iteration 2)

```
E3-S1 ──► E3-S2 ──► E3-S3    (branch feat/EXEC-ENGINE-001-it2-e3, sequential)
                       │
                       ▼
E4-S1 ──► E4-S2               (branch feat/EXEC-ENGINE-001-it2-e4; E4-S1 needs E3-S3)
```

---

### Epic E3: BaseComponent ABC + registry + Celery queues

**Branch:** `feat/EXEC-ENGINE-001-it2-e3`
**User story:** As the execution engine, I can call any component via a single `component.safe_execute(input)` call so that the executor is decoupled from component implementations.

---

#### Story E3-S1: Define `BaseComponent`, `ComponentInput`, `ComponentOutput`

**BLOCKED UNTIL:** none (Iteration 2 must be on `main` first)
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it2-e3`
**CP BackEnd pattern:** N/A

**What to do:**
There is no abstract base class for components. Create `src/Plant/BackEnd/components/__init__.py` (empty) and `src/Plant/BackEnd/components/base.py` with `ComponentInput` dataclass, `ComponentOutput` dataclass, and `BaseComponent` ABC with `component_type` property, `execute()` abstract method, and `safe_execute()` wrapper that catches exceptions and populates `duration_ms`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/component_run.py` | 1–40 | Field names that `execute()` output must match |
| `src/Plant/BackEnd/core/observability.py` | 1–30 | OTel tracer import pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/__init__.py` | create | Empty file — marks package |
| `src/Plant/BackEnd/components/base.py` | create | Full ABC as per code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/base.py
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ComponentInput:
    flow_run_id: str
    customer_id: str
    skill_config: dict[str, Any]
    run_context: dict[str, Any]
    previous_step_output: dict[str, Any] | None = None

@dataclass
class ComponentOutput:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    duration_ms: int = 0

class BaseComponent(ABC):
    """Stateless execution unit. Implement execute() in every subclass."""

    @property
    @abstractmethod
    def component_type(self) -> str:
        """Unique string identifier, e.g. 'DeltaExchangePump'."""
        ...

    @abstractmethod
    async def execute(self, input: ComponentInput) -> ComponentOutput:
        """Execute component logic. Must be idempotent."""
        ...

    async def safe_execute(self, input: ComponentInput) -> ComponentOutput:
        """Wraps execute() with timing and exception catch."""
        start = time.monotonic()
        try:
            result = await self.execute(input)
            result.duration_ms = int((time.monotonic() - start) * 1000)
            return result
        except Exception as exc:
            return ComponentOutput(
                success=False,
                data={},
                error_message=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/Plant/BackEnd/tests/components/test_base.py` | Concrete subclass with `execute()` returning success | `safe_execute()` returns `success=True`, `duration_ms >= 0` |
| E3-S1-T2 | same | Concrete subclass with `execute()` raising `RuntimeError("boom")` | `safe_execute()` returns `success=False`, `error_message="boom"`, `duration_ms >= 0` |
| E3-S1-T3 | same | Attempt `BaseComponent()` (no concrete subclass) | `TypeError` raised at instantiation |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_base.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E3-S1 — define BaseComponent ComponentInput ComponentOutput`

**Done signal:**
`"E3-S1 done. Changed: components/__init__.py, components/base.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E3-S2: Celery component task routing + worker queue config

**BLOCKED UNTIL:** E3-S1 committed to `feat/EXEC-ENGINE-001-it2-e3`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it2-e3`
**CP BackEnd pattern:** N/A

**What to do:**
`src/Plant/BackEnd/worker/celery_app.py` has no component queues. Add `pump`, `processor`, `publisher` to `task_routes`. Create `src/Plant/BackEnd/worker/tasks/component_tasks.py` with three Celery tasks (`execute_pump`, `execute_processor`, `execute_publisher`) each delegating to `_run_component()` with retry configs: pump 3×/5s, processor 3×/10s, publisher 3×/15s.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/worker/celery_app.py` | 1–60 | Existing `task_routes` dict, `autodiscover_tasks()` call |
| `src/Plant/BackEnd/components/base.py` | 1–50 | `ComponentInput` fields (from E3-S1) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/worker/celery_app.py` | modify | Add 3 routes to `task_routes`; add `"worker.tasks.component_tasks"` to `autodiscover_tasks` |
| `src/Plant/BackEnd/worker/tasks/component_tasks.py` | create | Three Celery tasks + `_run_component` helper — see code pattern |

**Code patterns to copy exactly:**
```python
# Add to celery_app.py task_routes dict:
"execute_pump":      {"queue": "pump"},
"execute_processor": {"queue": "processor"},
"execute_publisher": {"queue": "publisher"},

# src/Plant/BackEnd/worker/tasks/component_tasks.py
import asyncio
from worker.celery_app import celery_app
from components.registry import get_component
from components.base import ComponentInput

@celery_app.task(name="execute_pump", bind=True, max_retries=3, default_retry_delay=5, acks_late=True)
def execute_pump(self, component_type: str, input_dict: dict, flow_run_id: str):
    _run_component(self, component_type, input_dict, flow_run_id)

@celery_app.task(name="execute_processor", bind=True, max_retries=3, default_retry_delay=10, acks_late=True)
def execute_processor(self, component_type: str, input_dict: dict, flow_run_id: str):
    _run_component(self, component_type, input_dict, flow_run_id)

@celery_app.task(name="execute_publisher", bind=True, max_retries=3, default_retry_delay=15, acks_late=True)
def execute_publisher(self, component_type: str, input_dict: dict, flow_run_id: str):
    _run_component(self, component_type, input_dict, flow_run_id)

def _run_component(task, component_type: str, input_dict: dict, flow_run_id: str):
    component = get_component(component_type)
    comp_input = ComponentInput(**input_dict)
    result = asyncio.get_event_loop().run_until_complete(component.safe_execute(comp_input))
    if not result.success:
        raise task.retry(exc=RuntimeError(result.error_message))
    return result.data
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/Plant/BackEnd/tests/worker/test_component_tasks.py` | Mock `get_component` returns component whose `safe_execute` returns `success=True, data={"ok": 1}` | `execute_pump` returns `{"ok": 1}` |
| E3-S2-T2 | same | Mock component returns `success=False, error_message="fail"` | `execute_pump` calls `task.retry` |
| E3-S2-T3 | same | Inspect `celery_app.conf.task_routes` | Contains `pump`, `processor`, `publisher` keys |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/worker/test_component_tasks.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E3-S2 — Celery component task routing pump processor publisher`

**Done signal:**
`"E3-S2 done. Changed: worker/celery_app.py, worker/tasks/component_tasks.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E3-S3: Component registry

**BLOCKED UNTIL:** E3-S2 committed to `feat/EXEC-ENGINE-001-it2-e3`
**Estimated time:** 30 min
**Branch:** `feat/EXEC-ENGINE-001-it2-e3`
**CP BackEnd pattern:** N/A

**What to do:**
`_run_component` calls `get_component(component_type)` but the registry doesn't exist yet. Create `src/Plant/BackEnd/components/registry.py` with `register_component()`, `get_component()` (raises `KeyError` with available list if not found), and `list_registered()`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/components/base.py` | 1–50 | `BaseComponent` type to use in type hints |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/registry.py` | create | Full registry as per code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/registry.py
from components.base import BaseComponent

_REGISTRY: dict[str, BaseComponent] = {}

def register_component(component: BaseComponent) -> None:
    """Register component instance under its component_type. Second registration overwrites."""
    _REGISTRY[component.component_type] = component

def get_component(component_type: str) -> BaseComponent:
    if component_type not in _REGISTRY:
        raise KeyError(
            f"Component '{component_type}' not registered. "
            f"Available: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[component_type]

def list_registered() -> list[str]:
    return list(_REGISTRY.keys())
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S3-T1 | `src/Plant/BackEnd/tests/components/test_registry.py` | Register a mock component with `component_type="TestComp"` | `get_component("TestComp")` returns the instance |
| E3-S3-T2 | same | `get_component("unknown")` | Raises `KeyError` with message containing `"Available:"` |
| E3-S3-T3 | same | Register two components with same type | Second overwrites; `list_registered()` has only one entry for that type |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_registry.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E3-S3 — component registry`

**Done signal:**
`"E3-S3 done. Changed: components/registry.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

**Epic E3 complete ✅** — run Docker integration test (Rule 5) before starting E4.

---

### Epic E4: FlowRun executor (sequential + fan-out)

**Branch:** `feat/EXEC-ENGINE-001-it2-e4`
**User story:** As the execution engine, I can run a sequence of components and a fan-out of parallel components so that Share Trader and Marketing Agent flows execute end-to-end with full DB audit records.

---

#### Story E4-S1: FlowRun executor — sequential step runner + approval gate

**BLOCKED UNTIL:** E3-S3 committed to `feat/EXEC-ENGINE-001-it2-e3` (registry must exist)
**Estimated time:** 90 min
**Branch:** `feat/EXEC-ENGINE-001-it2-e4`
**CP BackEnd pattern:** N/A

**What to do:**
No engine exists to dispatch steps in order. Create `src/Plant/BackEnd/engine/__init__.py` (empty) and `src/Plant/BackEnd/engine/flow_executor.py` with `execute_sequential_flow()`. The function iterates `sequential_steps`, checks for an `approval_gate_index` (sets `awaiting_approval` and returns if `auto_execute=false`), calls `component.safe_execute()`, writes a `ComponentRunModel` record for each step, and sets `flow_run.status` accordingly. Uses `PIIMaskingFilter` on logger.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/flow_run.py` | 1–45 | Status values, JSONB `run_context`, `current_step` field |
| `src/Plant/BackEnd/models/component_run.py` | 1–40 | Fields to populate: `id`, `flow_run_id`, `component_type`, `step_name`, `status`, `input_context`, `output`, `duration_ms` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/engine/__init__.py` | create | Empty file |
| `src/Plant/BackEnd/engine/flow_executor.py` | create | `execute_sequential_flow()` — see code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/engine/flow_executor.py
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.flow_run import FlowRunModel
from models.component_run import ComponentRunModel
from components.registry import get_component
from components.base import ComponentInput
from core.logging import get_logger, PIIMaskingFilter

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

async def execute_sequential_flow(
    flow_run: FlowRunModel,
    sequential_steps: list[dict],
    db: Session,
    approval_gate_index: int | None = None,
) -> None:
    prev_output = flow_run.run_context.get("previous_step_output")
    for idx, step in enumerate(sequential_steps):
        if approval_gate_index is not None and idx == approval_gate_index:
            if not flow_run.run_context.get("auto_execute", False):
                flow_run.status = "awaiting_approval"
                flow_run.current_step = step["step_name"]
                flow_run.updated_at = datetime.now(timezone.utc)
                db.commit()
                return
        flow_run.current_step = step["step_name"]
        db.commit()
        comp = get_component(step["component_type"])
        comp_input = ComponentInput(
            flow_run_id=flow_run.id,
            customer_id=flow_run.run_context.get("customer_id", ""),
            skill_config=flow_run.run_context.get("skill_config", {}),
            run_context=flow_run.run_context,
            previous_step_output=prev_output,
        )
        comp_run = ComponentRunModel(
            id=str(uuid.uuid4()),
            flow_run_id=flow_run.id,
            component_type=step["component_type"],
            step_name=step["step_name"],
            status="running",
            input_context=comp_input.__dict__,
            started_at=datetime.now(timezone.utc),
        )
        db.add(comp_run)
        db.commit()
        result = await comp.safe_execute(comp_input)
        comp_run.status = "completed" if result.success else "failed"
        comp_run.output = result.data
        comp_run.error_message = result.error_message
        comp_run.duration_ms = result.duration_ms
        comp_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        if not result.success:
            flow_run.status = "failed"
            flow_run.error_details = {"step": step["step_name"], "error": result.error_message}
            flow_run.updated_at = datetime.now(timezone.utc)
            db.commit()
            return
        prev_output = result.data
    flow_run.status = "completed"
    flow_run.completed_at = datetime.now(timezone.utc)
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/Plant/BackEnd/tests/engine/test_flow_executor.py` | 3 mock components all succeed | `flow_run.status="completed"`, 3 `component_run` rows with `status="completed"` |
| E4-S1-T2 | same | Step 2 fails | `flow_run.status="failed"`, step 3 **not** executed (no row) |
| E4-S1-T3 | same | Gate at index 1, `auto_execute=false` | `flow_run.status="awaiting_approval"` after step 0; step 1 not executed |
| E4-S1-T4 | same | Gate at index 1, `auto_execute=true` | Gate skipped; all 3 steps run; `flow_run.status="completed"` |
| E4-S1-T5 | same | Verify `previous_step_output` chaining | Step N+1 receives `previous_step_output` equal to step N's `result.data` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/engine/test_flow_executor.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E4-S1 — sequential FlowRun executor with approval gate`

**Done signal:**
`"E4-S1 done. Changed: engine/__init__.py, engine/flow_executor.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅"`

---

#### Story E4-S2: FlowRun executor — fan-out parallel runner + PARTIAL_FAILURE

**BLOCKED UNTIL:** E4-S1 committed to `feat/EXEC-ENGINE-001-it2-e4`
**Estimated time:** 90 min
**Branch:** `feat/EXEC-ENGINE-001-it2-e4`
**CP BackEnd pattern:** N/A

**What to do:**
Marketing Agent's `PublishingFlow` dispatches `LinkedInPublisher` and `YouTubePublisher` concurrently. Add `execute_parallel_flow()` to the existing `engine/flow_executor.py`. It launches all steps via `asyncio.gather()`, writes a `ComponentRunModel` per step, and sets `flow_run.status` to `completed` (all ok), `partial_failure` (some ok), or `failed` (all failed).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/engine/flow_executor.py` | 1–70 | Existing imports and `execute_sequential_flow` pattern to follow |
| `src/Plant/BackEnd/models/flow_run.py` | 1–20 | `FLOW_RUN_STATUSES` — confirm `partial_failure` is valid |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/engine/flow_executor.py` | modify | Append `execute_parallel_flow()` function after the existing `execute_sequential_flow` function |

**Code patterns to copy exactly:**
```python
# Append to engine/flow_executor.py
import asyncio

async def execute_parallel_flow(
    flow_run: FlowRunModel,
    parallel_steps: list[dict],
    db: Session,
    shared_input: dict,
) -> None:
    flow_run.status = "running"
    db.commit()

    async def run_one(step: dict) -> tuple[str, bool, dict]:
        comp = get_component(step["component_type"])
        comp_input = ComponentInput(
            flow_run_id=flow_run.id,
            customer_id=flow_run.run_context.get("customer_id", ""),
            skill_config=flow_run.run_context.get("skill_config", {}),
            run_context=flow_run.run_context,
            previous_step_output=shared_input,
        )
        comp_run = ComponentRunModel(
            id=str(uuid.uuid4()),
            flow_run_id=flow_run.id,
            component_type=step["component_type"],
            step_name=step["step_name"],
            status="running",
            input_context=comp_input.__dict__,
            started_at=datetime.now(timezone.utc),
        )
        db.add(comp_run)
        db.commit()
        result = await comp.safe_execute(comp_input)
        comp_run.status = "completed" if result.success else "failed"
        comp_run.output = result.data
        comp_run.error_message = result.error_message
        comp_run.duration_ms = result.duration_ms
        comp_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        return step["step_name"], result.success, result.data

    outcomes = await asyncio.gather(*[run_one(s) for s in parallel_steps])
    all_ok = all(ok for _, ok, _ in outcomes)
    any_ok = any(ok for _, ok, _ in outcomes)
    if all_ok:
        flow_run.status = "completed"
    elif any_ok:
        flow_run.status = "partial_failure"
        flow_run.error_details = {"failed_steps": [n for n, ok, _ in outcomes if not ok]}
    else:
        flow_run.status = "failed"
    flow_run.completed_at = datetime.now(timezone.utc)
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S2-T1 | `src/Plant/BackEnd/tests/engine/test_flow_executor_parallel.py` | Both steps succeed | `flow_run.status="completed"` |
| E4-S2-T2 | same | LinkedIn ✓ + YouTube ✗ | `flow_run.status="partial_failure"`, `error_details.failed_steps=["youtube"]` |
| E4-S2-T3 | same | Both fail | `flow_run.status="failed"` |
| E4-S2-T4 | same | Both steps succeed | Two `component_run` rows exist, both `status="completed"` |
| E4-S2-T5 | same | Verify concurrency: both mock steps record their start time before either completes | Start times overlap (delta < 50ms) — confirms `asyncio.gather` not serial |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/engine/test_flow_executor_parallel.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E4-S2 — parallel FlowRun executor + PARTIAL_FAILURE`

**Done signal:**
`"E4-S2 done. Changed: engine/flow_executor.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅"`

**Epic E4 complete ✅** — run Docker integration test (Rule 5) before opening iteration PR.

---

### Iteration 2 — Completion Checkpoint

After ALL E3 and E4 epics complete and Docker integration test passes:

```bash
git checkout main && git pull
git checkout -b feat/EXEC-ENGINE-001-it2
git merge --no-ff feat/EXEC-ENGINE-001-it2-e3 feat/EXEC-ENGINE-001-it2-e4
git push origin feat/EXEC-ENGINE-001-it2

gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-it2 \
  --title "feat(EXEC-ENGINE-001): iteration 2 — BaseComponent + Celery queues + FlowRun executor" \
  --body "## EXEC-ENGINE-001 Iteration 2

### Stories completed
| E3-S1 | BaseComponent ComponentInput ComponentOutput | 🟢 Done |
| E3-S2 | Celery component task routing | 🟢 Done |
| E3-S3 | Component registry | 🟢 Done |
| E4-S1 | Sequential FlowRun executor + approval gate | 🟢 Done |
| E4-S2 | Parallel FlowRun executor + PARTIAL_FAILURE | 🟢 Done |

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] @circuit_breaker on all external HTTP calls
- [ ] No env-specific values in Dockerfile or code
- [ ] Tests >= 80% coverage on new BE code
- [ ] Postgres owns flow state; Redis only transports jobs"
```

Post PR URL. **STOP — do not start Iteration 3 until this PR is merged to `main`.**

---
## Iteration 3 — Share Trader: Components + End-to-End Flow

**Scope:** Customer with Share Trader hired can trigger market data fetch → RSI analysis → trade execution with full audit records persisted to DB and a deliverable delivered.
**Lane:** B — new component implementations and Plant API endpoints; no frontend changes.
**⏱ Estimated:** 5h | **Come back:** 2026-03-09 10:00 IST
**Epics:** E5, E6

> **⛔ ITERATION 3 GATE — verify before writing any code:** Iteration 2 PR must be merged to `main`:
> ```bash
> git fetch origin
> git show origin/main:docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md | grep "Iteration 2"
> ```
> If Iteration 2 content is absent from `main`, **STOP** and tell the user: "Iteration 3 is blocked — the Iteration 2 PR must be merged to main first."

### Dependency Map (Iteration 3)

```
E5-S1 ──► E5-S2 ──► E5-S3    (branch feat/EXEC-ENGINE-001-it3-e5, sequential)
                       │
                       ▼
E6-S1 ──► E6-S2               (branch feat/EXEC-ENGINE-001-it3-e6; E6-S1 needs E5-S3)
```

---

### Epic E5: Customer delegates market analysis and trade execution to Share Trader agent

**Branch:** `feat/EXEC-ENGINE-001-it3-e5`
**User story:** As a Buy/Sell trader with Share Trader hired, I can see WAOOAW fetch market data, analyze RSI signals, and place orders on my behalf so that I delegate day-trading execution to the agent.

---

#### Story E5-S1: `DeltaExchangePump` component

**BLOCKED UNTIL:** none (Iteration 3 must be on `main` first)
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it3-e5`
**CP BackEnd pattern:** N/A — Plant BackEnd component only

**What to do:**
There is no concrete component that fetches market data. Create the `components/share_trader/` package and `delta_exchange_pump.py`, the first `BaseComponent` implementation. It pulls OHLCV candle data from the Delta Exchange API for the customer's configured instrument, wraps the HTTP call with `@circuit_breaker(service="delta_exchange_api")`, and registers itself at module import. API key must never appear in logs.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/components/base.py` | 1–50 | `BaseComponent`, `ComponentInput`, `ComponentOutput` interface |
| `src/Plant/BackEnd/components/registry.py` | 1–30 | `register_component()` call pattern |
| `src/Plant/BackEnd/core/encryption.py` | 1–40 | API key decryption pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/share_trader/__init__.py` | create | Empty file — marks package |
| `src/Plant/BackEnd/components/share_trader/delta_exchange_pump.py` | create | Full component as per code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/share_trader/delta_exchange_pump.py
import httpx
from core.logging import get_logger, PIIMaskingFilter
from core.security import circuit_breaker
from components.base import BaseComponent, ComponentInput, ComponentOutput
from components.registry import register_component

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

class DeltaExchangePump(BaseComponent):
    @property
    def component_type(self) -> str:
        return "DeltaExchangePump"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        instrument = input.skill_config.get("customer_fields", {}).get("instrument", "NIFTY")
        api_key = input.skill_config.get("customer_fields", {}).get("delta_api_key", "")
        candles = await self._fetch_candles(instrument, api_key)
        return ComponentOutput(success=True, data={"candles": candles, "instrument": instrument})

    @circuit_breaker(service="delta_exchange_api")
    async def _fetch_candles(self, instrument: str, api_key: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.delta.exchange/v2/history/candles",
                params={"symbol": instrument, "resolution": "1m", "limit": 50},
                headers={"api-key": api_key},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json().get("result", [])

register_component(DeltaExchangePump())
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S1-T1 | `src/Plant/BackEnd/tests/components/test_delta_exchange_pump.py` | Mock `httpx.AsyncClient.get` returns 200 with candle list | `execute()` returns `success=True`, `data["candles"]` populated |
| E5-S1-T2 | same | Mock returns HTTP 500 | `safe_execute()` returns `success=False`, `error_message` non-empty |
| E5-S1-T3 | same | Call `get_component("DeltaExchangePump")` after module import | Returns instance without `KeyError` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_delta_exchange_pump.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E5-S1 — DeltaExchangePump component`

**Done signal:**
`"E5-S1 done. Changed: components/share_trader/__init__.py, components/share_trader/delta_exchange_pump.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E5-S2: `RSIProcessor` component

**BLOCKED UNTIL:** E5-S1 committed to `feat/EXEC-ENGINE-001-it3-e5`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it3-e5`
**CP BackEnd pattern:** N/A

**What to do:**
There is no signal processor component. Create `components/share_trader/rsi_processor.py`. It reads `previous_step_output["candles"]` (from `DeltaExchangePump`), calculates RSI for a customer-configurable period, and classifies the signal as `BUY | SELL | HOLD`. No external HTTP — pure calculation. Empty candles → `ComponentOutput(success=False)`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/components/base.py` | 1–50 | `ComponentInput.previous_step_output` field type |
| `src/Plant/BackEnd/components/registry.py` | 1–30 | `register_component()` call |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/share_trader/rsi_processor.py` | create | Full component as per code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/share_trader/rsi_processor.py
from core.logging import get_logger, PIIMaskingFilter
from components.base import BaseComponent, ComponentInput, ComponentOutput
from components.registry import register_component

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

class RSIProcessor(BaseComponent):
    @property
    def component_type(self) -> str:
        return "RSIProcessor"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        candles = (input.previous_step_output or {}).get("candles", [])
        if not candles:
            return ComponentOutput(success=False, error_message="Insufficient data")
        period = int(input.skill_config.get("customer_fields", {}).get("rsi_period", 14))
        rsi_value = self._calculate_rsi(candles, period)
        if rsi_value < 30:
            signal = "BUY"
        elif rsi_value > 70:
            signal = "SELL"
        else:
            signal = "HOLD"
        return ComponentOutput(success=True, data={"rsi_value": rsi_value, "signal": signal, "confidence": 0.9})

    def _calculate_rsi(self, candles: list[dict], period: int) -> float:
        closes = [float(c.get("close", 0)) for c in candles]
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d for d in deltas[-period:] if d > 0]
        losses = [-d for d in deltas[-period:] if d < 0]
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))

register_component(RSIProcessor())
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S2-T1 | `src/Plant/BackEnd/tests/components/test_rsi_processor.py` | `previous_step_output` with candles producing RSI < 30 | `data["signal"] == "BUY"` |
| E5-S2-T2 | same | Candles producing RSI > 70 | `data["signal"] == "SELL"` |
| E5-S2-T3 | same | Candles producing 30 ≤ RSI ≤ 70 | `data["signal"] == "HOLD"` |
| E5-S2-T4 | same | `previous_step_output` with empty `candles` list | `success=False`, `error_message="Insufficient data"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_rsi_processor.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E5-S2 — RSIProcessor component`

**Done signal:**
`"E5-S2 done. Changed: components/share_trader/rsi_processor.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E5-S3: `DeltaPublisher` component

**BLOCKED UNTIL:** E5-S2 committed to `feat/EXEC-ENGINE-001-it3-e5`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it3-e5`
**CP BackEnd pattern:** N/A

**What to do:**
There is no order placement component. Create `components/share_trader/delta_publisher.py`. It reads the trade signal from `previous_step_output`, decrypts the Delta Exchange API key from `skill_config.customer_fields.delta_api_key` using `core.encryption`, and places a market order with `@circuit_breaker(service="delta_exchange_api")`. API key must never appear in logs. HOLD signal → skip without placing order.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/components/base.py` | 1–50 | `ComponentInput` + `ComponentOutput` interface |
| `src/Plant/BackEnd/core/encryption.py` | 1–40 | `decrypt_field()` call pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/share_trader/delta_publisher.py` | create | Full component as per code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/share_trader/delta_publisher.py
import httpx
from core.logging import get_logger, PIIMaskingFilter
from core.security import circuit_breaker
from core.encryption import decrypt_field
from components.base import BaseComponent, ComponentInput, ComponentOutput
from components.registry import register_component

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

class DeltaPublisher(BaseComponent):
    @property
    def component_type(self) -> str:
        return "DeltaPublisher"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        signal = (input.previous_step_output or {}).get("signal", "HOLD")
        if signal == "HOLD":
            return ComponentOutput(success=True, data={"status": "skipped", "reason": "HOLD signal"})
        encrypted_key = input.skill_config.get("customer_fields", {}).get("delta_api_key", "")
        api_key = decrypt_field(encrypted_key)
        instrument = input.skill_config.get("customer_fields", {}).get("instrument", "NIFTY")
        result = await self._place_order(instrument, signal, api_key)
        return ComponentOutput(success=True, data=result)

    @circuit_breaker(service="delta_exchange_api")
    async def _place_order(self, instrument: str, side: str, api_key: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.delta.exchange/v2/orders",
                json={"product_symbol": instrument, "side": side.lower(),
                      "order_type": "market_order", "size": 1},
                headers={"api-key": api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json().get("result", {})
            return {"order_id": data.get("id", ""), "fill_price": data.get("avg_fill_price", 0.0),
                    "status": "filled"}

register_component(DeltaPublisher())
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S3-T1 | `src/Plant/BackEnd/tests/components/test_delta_publisher.py` | `previous_step_output.signal="BUY"`, mock HTTP 200 with order response | `success=True`, `data["order_id"]` set |
| E5-S3-T2 | same | `previous_step_output.signal="HOLD"` | `success=True`, `data["status"]="skipped"` |
| E5-S3-T3 | same | Mock HTTP 4xx (order rejected) | `safe_execute()` returns `success=False` |
| E5-S3-T4 | same | Inspect log records captured during execute | API key value does NOT appear in any log record |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_delta_publisher.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E5-S3 — DeltaPublisher component`

**Done signal:**
`"E5-S3 done. Changed: components/share_trader/delta_publisher.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

**Epic E5 complete ✅** — run Docker integration test (Rule 5) before starting E6.

---

### Epic E6: Customer sees Share Trader deliver end-to-end trade results

**Branch:** `feat/EXEC-ENGINE-001-it3-e6`
**User story:** As a customer with Share Trader hired, I can trigger a full market analysis → approval gate → trade execution cycle via the Plant API and see a deliverable with my order confirmation appear in the CP dashboard.

---

#### Story E6-S1: Share Trader FlowDef + `POST /v1/flow-runs` + `GET /v1/flow-runs/{id}` endpoints

**BLOCKED UNTIL:** E5-S3 committed to `feat/EXEC-ENGINE-001-it3-e5` (all three Share Trader components must exist)
**Estimated time:** 90 min
**Branch:** `feat/EXEC-ENGINE-001-it3-e6`
**CP BackEnd pattern:** Pattern B — new `/cp/flow-runs` proxy is added in Iteration 6 (E14-S2); this story adds only the Plant `/v1/flow-runs` source endpoints

**What to do:**
Wire `DeltaExchangePump → RSIProcessor → DeltaPublisher` into FlowDef Python constants stored in `flows/share_trader.py`. Add `POST /v1/flow-runs` (creates `FlowRunModel`, triggers `execute_sequential_flow` as a background task) and `GET /v1/flow-runs/{flow_run_id}` (read-replica, returns status + current_step). Register the router in `main.py`. Use `waooaw_router()` — no bare `APIRouter`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/engine/flow_executor.py` | 1–80 | `execute_sequential_flow()` signature — `flow_run`, `sequential_steps`, `db`, `approval_gate_index` |
| `src/Plant/BackEnd/models/flow_run.py` | 1–45 | Column list, JSONB `run_context`, `idempotency_key` unique constraint |
| `src/Plant/BackEnd/api/v1/skill_configs.py` | 1–40 | `waooaw_router()` + `get_db_session` / `get_read_db_session` import pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/flows/__init__.py` | create | Empty file — marks package |
| `src/Plant/BackEnd/flows/share_trader.py` | create | Flow constants + `FLOW_REGISTRY` dict as per code pattern below |
| `src/Plant/BackEnd/api/v1/flow_runs.py` | create | `POST /` and `GET /{id}` endpoints as per code pattern below |
| `src/Plant/BackEnd/main.py` | modify | Add `from api.v1 import flow_runs` and `app.include_router(flow_runs.router)` |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/flows/share_trader.py
MARKET_ANALYSIS_FLOW = {
    "flow_name": "MarketAnalysisFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "DeltaExchangePump"},
        {"step_name": "step_2", "component_type": "RSIProcessor"},
    ],
    "approval_gate_index": None,
}
EXECUTE_TRADE_FLOW = {
    "flow_name": "ExecuteTradeFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "DeltaPublisher"},
    ],
    "approval_gate_index": 0,  # Gate fires before DeltaPublisher
}
FLOW_REGISTRY = {
    "MarketAnalysisFlow": MARKET_ANALYSIS_FLOW,
    "ExecuteTradeFlow": EXECUTE_TRADE_FLOW,
}

# src/Plant/BackEnd/api/v1/flow_runs.py
import uuid
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.routing import waooaw_router
from core.database import get_db_session, get_read_db_session
from core.logging import get_logger, PIIMaskingFilter
from models.flow_run import FlowRunModel
from flows.share_trader import FLOW_REGISTRY
from engine.flow_executor import execute_sequential_flow

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

router = waooaw_router(prefix="/v1/flow-runs", tags=["flow-runs"])

class FlowRunRequest(BaseModel):
    hired_instance_id: str
    flow_name: str
    run_context: dict

@router.post("/", status_code=201)
async def create_flow_run(
    body: FlowRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
):
    flow_def = FLOW_REGISTRY.get(body.flow_name)
    if not flow_def:
        raise HTTPException(status_code=400, detail=f"Unknown flow: {body.flow_name}")
    flow_run = FlowRunModel(
        id=str(uuid.uuid4()),
        hired_instance_id=body.hired_instance_id,
        skill_id=body.run_context.get("skill_id", ""),
        flow_name=body.flow_name,
        status="pending",
        run_context=body.run_context,
        idempotency_key=body.run_context.get("idempotency_key", str(uuid.uuid4())),
        started_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(flow_run)
    db.commit()
    background_tasks.add_task(
        execute_sequential_flow,
        flow_run, flow_def["sequential_steps"], db, flow_def.get("approval_gate_index"),
    )
    return {"id": flow_run.id, "status": flow_run.status}

@router.get("/{flow_run_id}")
async def get_flow_run(
    flow_run_id: str,
    db: Session = Depends(get_read_db_session),
):
    row = db.query(FlowRunModel).filter_by(id=flow_run_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="flow_run not found")
    return {"id": row.id, "status": row.status, "current_step": row.current_step,
            "flow_name": row.flow_name}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E6-S1-T1 | `src/Plant/BackEnd/tests/api/test_flow_runs.py` | `POST /v1/flow-runs` with `flow_name="MarketAnalysisFlow"` | HTTP 201, body contains `id` and `status="pending"` |
| E6-S1-T2 | same | `POST /v1/flow-runs` with unknown `flow_name` | HTTP 400 |
| E6-S1-T3 | same | `GET /v1/flow-runs/{id}` after creating a run | HTTP 200, `status` and `current_step` present |
| E6-S1-T4 | same | `GET /v1/flow-runs/{unknown_id}` | HTTP 404 |
| E6-S1-T5 | same | Two POSTs with same `idempotency_key` in `run_context` | Second raises `IntegrityError` → HTTP 409 or 500 with unique key violation |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/api/test_flow_runs.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E6-S1 — Share Trader FlowDef + flow-runs endpoints`

**Done signal:**
`"E6-S1 done. Changed: flows/__init__.py, flows/share_trader.py, api/v1/flow_runs.py, main.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅"`

---

#### Story E6-S2: Deliverable written at FlowRun completion

**BLOCKED UNTIL:** E6-S1 committed to `feat/EXEC-ENGINE-001-it3-e6`
**Estimated time:** 30 min
**Branch:** `feat/EXEC-ENGINE-001-it3-e6`
**CP BackEnd pattern:** N/A — Plant BackEnd engine hook only

**What to do:**
When `execute_sequential_flow` sets `flow_run.status = "completed"`, no `DeliverableModel` row is written yet. Add a post-completion hook at the end of `execute_sequential_flow` in `engine/flow_executor.py` that creates a `DeliverableModel` row using the last step's output as `content`, reading `hired_instance_id`, `goal_instance_id`, and `deliverable_type` from `flow_run.run_context`. Failed flows must NOT create a deliverable.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/deliverable.py` | 1–50 | Column list — `hired_instance_id`, `goal_instance_id`, `type`, `content`, `created_at` fields |
| `src/Plant/BackEnd/engine/flow_executor.py` | 55–90 | Post-loop `flow_run.status = "completed"` + `db.commit()` block to extend |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/engine/flow_executor.py` | modify | Add `from models.deliverable import DeliverableModel` to imports; insert deliverable-creation block immediately after the `db.commit()` on completed status at end of function |

**Code patterns to copy exactly:**
```python
# Add to top-of-file imports in flow_executor.py:
from models.deliverable import DeliverableModel

# Deliverable hook — insert after db.commit() at the end of execute_sequential_flow,
# AFTER flow_run.status has been set to "completed":
_deliverable = DeliverableModel(
    id=str(uuid.uuid4()),
    hired_instance_id=flow_run.run_context.get("hired_instance_id", flow_run.hired_instance_id),
    goal_instance_id=flow_run.run_context.get("goal_instance_id"),
    type=flow_run.run_context.get("deliverable_type", "trade_execution"),
    content=prev_output or {},
    created_at=datetime.now(timezone.utc),
)
db.add(_deliverable)
db.commit()
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E6-S2-T1 | `src/Plant/BackEnd/tests/engine/test_deliverable_hook.py` | `execute_sequential_flow` with all mock steps succeeding, `deliverable_type="trade_execution"` in `run_context` | `DeliverableModel` row exists with `type="trade_execution"` and `content == last_step_output` |
| E6-S2-T2 | same | Successful run with `goal_instance_id="goal-123"` in `run_context` | `deliverable.goal_instance_id == "goal-123"` |
| E6-S2-T3 | same | Step 2 fails — `flow_run.status = "failed"` | No `DeliverableModel` row written |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/engine/test_deliverable_hook.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E6-S2 — deliverable written at FlowRun completion`

**Done signal:**
`"E6-S2 done. Changed: engine/flow_executor.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

**Epic E6 complete ✅** — run Docker integration test (Rule 5) before opening iteration PR.

---

### Iteration 3 — Completion Checkpoint

After ALL E5 and E6 epics complete and Docker integration test passes:

```bash
git checkout main && git pull
git checkout -b feat/EXEC-ENGINE-001-it3
git merge --no-ff feat/EXEC-ENGINE-001-it3-e5 feat/EXEC-ENGINE-001-it3-e6
git push origin feat/EXEC-ENGINE-001-it3

gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-it3 \
  --title "feat(EXEC-ENGINE-001): iteration 3 — Share Trader end-to-end" \
  --body "## EXEC-ENGINE-001 Iteration 3

### Stories completed
| E5-S1 | DeltaExchangePump component | 🟢 Done |
| E5-S2 | RSIProcessor component | 🟢 Done |
| E5-S3 | DeltaPublisher component | 🟢 Done |
| E6-S1 | Share Trader FlowDef + flow-runs endpoints | 🟢 Done |
| E6-S2 | Deliverable written at FlowRun completion | 🟢 Done |

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] @circuit_breaker on all external HTTP calls
- [ ] No env-specific values in Dockerfile or code
- [ ] Tests >= 80% coverage on new BE code
- [ ] Postgres owns flow state; Redis only transports jobs"
```

Post PR URL. **STOP — do not start Iteration 4 until this PR is merged to `main`.**

---

## Iteration 4 — Marketing Agent: Components + Fan-out Flow

**Scope:** Customer with Marketing Agent hired can configure a campaign brief, generate platform-specific content via LLM, approve it at the gate, and publish to LinkedIn and YouTube in parallel — with `partial_failure` handled gracefully.
**Lane:** B — new component implementations, Marketing FlowDef, and approvals endpoint.
**⏱ Estimated:** 5h | **Come back:** 2026-03-09 16:00 IST
**Epics:** E7, E8

> **⛔ ITERATION 4 GATE — verify before writing any code:** Iteration 3 PR must be merged to `main`:
> ```bash
> git fetch origin
> git show origin/main:docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md | grep "Iteration 3"
> ```
> If Iteration 3 content is absent from `main`, **STOP** and tell the user: "Iteration 4 is blocked — the Iteration 3 PR must be merged to main first."

### Dependency Map (Iteration 4)

```
E7-S1 ──► E7-S2 ──► E7-S3    (branch feat/EXEC-ENGINE-001-it4-e7, sequential)
                       │
                       ▼
E8-S1 ──► E8-S2               (branch feat/EXEC-ENGINE-001-it4-e8; E8-S1 needs E7-S3)
```

---

### Epic E7: Customer's Marketing Agent produces platform-specific content via LLM

**Branch:** `feat/EXEC-ENGINE-001-it4-e7`
**User story:** As a Marketing Manager with Marketing Agent hired, I can provide a campaign brief and see the agent extract my goal context, call an LLM to generate platform-specific variants, and prepare content for LinkedIn and YouTube so that my publishing workflow is automated.

---

#### Story E7-S1: `GoalConfigPump` component

**BLOCKED UNTIL:** none (Iteration 4 must be on `main` first)
**Estimated time:** 30 min
**Branch:** `feat/EXEC-ENGINE-001-it4-e7`
**CP BackEnd pattern:** N/A — Plant BackEnd component only

**What to do:**
Create the `components/marketing/` package and `goal_config_pump.py`. This is the first step of the Marketing Agent flow — it reads the customer's campaign brief and platform targets from `flow_run.run_context.goal_context`, normalises them, and returns a structured `brief_payload` for `ContentProcessor`. No external HTTP calls — pure context extraction. Missing `campaign_brief` → failure.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/components/base.py` | 1–50 | `ComponentInput.run_context` field, `ComponentOutput` interface |
| `src/Plant/BackEnd/components/registry.py` | 1–30 | `register_component()` call pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/marketing/__init__.py` | create | Empty file — marks package |
| `src/Plant/BackEnd/components/marketing/goal_config_pump.py` | create | Full component as per code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/marketing/goal_config_pump.py
from core.logging import get_logger, PIIMaskingFilter
from components.base import BaseComponent, ComponentInput, ComponentOutput
from components.registry import register_component

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

class GoalConfigPump(BaseComponent):
    @property
    def component_type(self) -> str:
        return "GoalConfigPump"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        goal_context = input.run_context.get("goal_context", {})
        campaign_brief = goal_context.get("campaign_brief")
        if not campaign_brief:
            return ComponentOutput(success=False, error_message="campaign_brief required")
        content_type = goal_context.get("content_type", "post")
        target_platforms = input.skill_config.get("customer_fields", {}).get(
            "target_platforms", ["linkedin"]
        )
        platform_specs = [{"platform": p, "format": content_type} for p in target_platforms]
        return ComponentOutput(
            success=True,
            data={
                "brief_payload": {
                    "campaign_brief": campaign_brief,
                    "content_type": content_type,
                    "brand_name": input.skill_config.get("customer_fields", {}).get("brand_name", ""),
                    "tone": input.skill_config.get("customer_fields", {}).get("tone", "professional"),
                    "audience": input.skill_config.get("customer_fields", {}).get("audience", ""),
                },
                "platform_specs": platform_specs,
            },
        )

register_component(GoalConfigPump())
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E7-S1-T1 | `src/Plant/BackEnd/tests/components/test_goal_config_pump.py` | `run_context.goal_context` with `campaign_brief` set and `target_platforms=["linkedin","youtube"]` | `success=True`, `data["platform_specs"]` has 2 entries |
| E7-S1-T2 | same | `run_context.goal_context` missing `campaign_brief` | `success=False`, `error_message="campaign_brief required"` |
| E7-S1-T3 | same | Call `get_component("GoalConfigPump")` after module import | Returns instance without `KeyError` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_goal_config_pump.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E7-S1 — GoalConfigPump component`

**Done signal:**
`"E7-S1 done. Changed: components/marketing/__init__.py, components/marketing/goal_config_pump.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E7-S2: `ContentProcessor` component

**BLOCKED UNTIL:** E7-S1 committed to `feat/EXEC-ENGINE-001-it4-e7`
**Estimated time:** 90 min
**Branch:** `feat/EXEC-ENGINE-001-it4-e7`
**CP BackEnd pattern:** N/A

**What to do:**
Create `components/marketing/content_processor.py`. It takes `GoalConfigPump` output from `previous_step_output`, reads `skill_config.pp_locked_fields.brand_voice_model` (e.g. `gpt-4o`), decrypts the OpenAI API key from `skill_config.customer_fields`, and calls the LLM to generate platform-specific post variants. Uses `@circuit_breaker(service="openai_api")`. API key must never appear in logs.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/components/base.py` | 1–50 | `ComponentInput.previous_step_output` — this contains `brief_payload` from E7-S1 |
| `src/Plant/BackEnd/core/encryption.py` | 1–40 | `decrypt_field()` call pattern for OpenAI API key |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/marketing/content_processor.py` | create | Full component as per code pattern below |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/marketing/content_processor.py
import httpx
from core.logging import get_logger, PIIMaskingFilter
from core.security import circuit_breaker
from core.encryption import decrypt_field
from components.base import BaseComponent, ComponentInput, ComponentOutput
from components.registry import register_component

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

class ContentProcessor(BaseComponent):
    @property
    def component_type(self) -> str:
        return "ContentProcessor"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        brief_payload = (input.previous_step_output or {}).get("brief_payload", {})
        platform_specs = (input.previous_step_output or {}).get("platform_specs", [])
        model = input.skill_config.get("pp_locked_fields", {}).get("brand_voice_model", "gpt-4o-mini")
        encrypted_key = input.skill_config.get("customer_fields", {}).get("openai_api_key", "")
        api_key = decrypt_field(encrypted_key)
        variants = {}
        for spec in platform_specs:
            platform = spec["platform"]
            prompt = self._build_prompt(brief_payload, spec)
            text = await self._call_llm(prompt, model, api_key)
            variants[platform] = {"post_text": text, "hashtags": [], "format": spec["format"]}
        return ComponentOutput(
            success=True,
            data={"post_text": list(variants.values())[0]["post_text"] if variants else "",
                  "hashtags": [], "per_platform_variants": variants},
        )

    def _build_prompt(self, brief: dict, spec: dict) -> str:
        return (f"Write a {spec['format']} for {spec['platform']} about: {brief.get('campaign_brief', '')}. "
                f"Brand: {brief.get('brand_name', '')}. Tone: {brief.get('tone', 'professional')}. "
                f"Audience: {brief.get('audience', 'general')}.")

    @circuit_breaker(service="openai_api")
    async def _call_llm(self, prompt: str, model: str, api_key: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

register_component(ContentProcessor())
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E7-S2-T1 | `src/Plant/BackEnd/tests/components/test_content_processor.py` | Mock LLM returns `"Great post!"`, `platform_specs=[{platform:linkedin}]` | `success=True`, `data["per_platform_variants"]["linkedin"]["post_text"]="Great post!"` |
| E7-S2-T2 | same | Mock LLM returns HTTP 429 (rate limit) | `safe_execute()` returns `success=False` |
| E7-S2-T3 | same | Inspect log records captured during execute | OpenAI API key value does NOT appear in any log record |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_content_processor.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E7-S2 — ContentProcessor component`

**Done signal:**
`"E7-S2 done. Changed: components/marketing/content_processor.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E7-S3: `LinkedInPublisher` + `YouTubePublisher` components

**BLOCKED UNTIL:** E7-S2 committed to `feat/EXEC-ENGINE-001-it4-e7`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it4-e7`
**CP BackEnd pattern:** N/A

**What to do:**
Create two publisher components: `components/marketing/linkedin_publisher.py` and `youtube_publisher.py`. Both implement `BaseComponent`, read their platform variant from `previous_step_output["per_platform_variants"]`, decrypt the platform API key from `skill_config.customer_fields`, and post via the platform API with `@circuit_breaker`. API keys must never appear in logs. Both registered at module import.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/components/base.py` | 1–50 | `ComponentInput.previous_step_output` — contains `per_platform_variants` from E7-S2 |
| `src/Plant/BackEnd/core/encryption.py` | 1–40 | `decrypt_field()` call pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/components/marketing/linkedin_publisher.py` | create | Full LinkedIn component as per code pattern below |
| `src/Plant/BackEnd/components/marketing/youtube_publisher.py` | create | Full YouTube component following identical structure with `service="youtube_api"` |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/components/marketing/linkedin_publisher.py
import httpx
from core.logging import get_logger, PIIMaskingFilter
from core.security import circuit_breaker
from core.encryption import decrypt_field
from components.base import BaseComponent, ComponentInput, ComponentOutput
from components.registry import register_component

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

class LinkedInPublisher(BaseComponent):
    @property
    def component_type(self) -> str:
        return "LinkedInPublisher"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        variants = (input.previous_step_output or {}).get("per_platform_variants", {})
        variant = variants.get("linkedin", {})
        if not variant:
            return ComponentOutput(success=False, error_message="No LinkedIn variant in previous output")
        encrypted_key = input.skill_config.get("customer_fields", {}).get("linkedin_access_token", "")
        token = decrypt_field(encrypted_key)
        result = await self._post_to_linkedin(variant["post_text"], token)
        return ComponentOutput(success=True, data=result)

    @circuit_breaker(service="linkedin_api")
    async def _post_to_linkedin(self, text: str, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                json={"author": "urn:li:person:me", "lifecycleState": "PUBLISHED",
                      "specificContent": {"com.linkedin.ugc.ShareContent":
                          {"shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}}},
                headers={"Authorization": f"Bearer {token}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            return {"platform_post_id": resp.headers.get("x-linkedin-id", ""),
                    "published_url": "", "platform": "linkedin"}

register_component(LinkedInPublisher())

# src/Plant/BackEnd/components/marketing/youtube_publisher.py follows identical
# structure: component_type="YouTubePublisher", service="youtube_api",
# reads variants["youtube"], uses skill_config.customer_fields.youtube_api_key
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E7-S3-T1 | `src/Plant/BackEnd/tests/components/test_linkedin_publisher.py` | `previous_step_output.per_platform_variants.linkedin` set, mock HTTP 200 | `success=True`, `data["platform"]="linkedin"` |
| E7-S3-T2 | same | LinkedIn API returns HTTP 4xx (post rejected) | `safe_execute()` returns `success=False`, error message contains "linkedin" |
| E7-S3-T3 | `src/Plant/BackEnd/tests/components/test_youtube_publisher.py` | `previous_step_output.per_platform_variants.youtube` set, mock HTTP 200 | `success=True`, `data["platform"]="youtube"` |
| E7-S3-T4 | same | YouTube API returns HTTP 5xx (server error) | `safe_execute()` returns `success=False` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/components/test_linkedin_publisher.py src/Plant/BackEnd/tests/components/test_youtube_publisher.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E7-S3 — LinkedInPublisher + YouTubePublisher components`

**Done signal:**
`"E7-S3 done. Changed: components/marketing/linkedin_publisher.py, components/marketing/youtube_publisher.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

**Epic E7 complete ✅** — run Docker integration test (Rule 5) before starting E8.

---

### Epic E8: Customer approves and publishes Marketing Agent content end-to-end

**Branch:** `feat/EXEC-ENGINE-001-it4-e8`
**User story:** As a customer with Marketing Agent hired, I can configure a campaign, see generated content stop at the approval gate, approve it, and watch parallel publishing to LinkedIn and YouTube succeed — with partial failure handled gracefully — and then see a deliverable row in my CP dashboard.

---

#### Story E8-S1: Marketing Agent FlowDef + fan-out end-to-end

**BLOCKED UNTIL:** E7-S3 committed to `feat/EXEC-ENGINE-001-it4-e7` (all three Marketing components must exist)
**Estimated time:** 90 min
**Branch:** `feat/EXEC-ENGINE-001-it4-e8`
**CP BackEnd pattern:** N/A — Plant BackEnd flows only

**What to do:**
Create `flows/marketing_agent.py` with `CONTENT_CREATION_FLOW` (sequential, approval gate after content generation) and `PUBLISHING_FLOW` (parallel fan-out to LinkedIn + YouTube). Register both in `FLOW_REGISTRY` in `api/v1/flow_runs.py`. Write an end-to-end integration test proving: brief → LLM (mocked) → stop at gate → approve → fan-out publish → `partial_failure` when one platform fails. Add Marketing deliverable type `"content_post"` to the deliverable hook.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/engine/flow_executor.py` | 1–120 | `execute_sequential_flow` + `execute_parallel_flow` signatures |
| `src/Plant/BackEnd/flows/share_trader.py` | 1–30 | `FLOW_REGISTRY` pattern to follow |
| `src/Plant/BackEnd/api/v1/flow_runs.py` | 1–50 | `FLOW_REGISTRY` import — extend to include marketing flows |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/flows/marketing_agent.py` | create | Flow constants + registry entries as per code pattern below |
| `src/Plant/BackEnd/api/v1/flow_runs.py` | modify | Import `from flows.marketing_agent import MARKETING_FLOW_REGISTRY`; merge into existing `FLOW_REGISTRY` dict |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/flows/marketing_agent.py
CONTENT_CREATION_FLOW = {
    "flow_name": "ContentCreationFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "GoalConfigPump"},
        {"step_name": "step_2", "component_type": "ContentProcessor"},
    ],
    "approval_gate_index": 2,  # Gate fires AFTER ContentProcessor, BEFORE publishing
    "deliverable_type": "content_post",
}
PUBLISHING_FLOW = {
    "flow_name": "PublishingFlow",
    "parallel_steps": [
        {"step_name": "linkedin", "component_type": "LinkedInPublisher"},
        {"step_name": "youtube", "component_type": "YouTubePublisher"},
    ],
    "deliverable_type": "content_post",
}
MARKETING_FLOW_REGISTRY = {
    "ContentCreationFlow": CONTENT_CREATION_FLOW,
    "PublishingFlow": PUBLISHING_FLOW,
}

# In api/v1/flow_runs.py — add after existing FLOW_REGISTRY import:
from flows.marketing_agent import MARKETING_FLOW_REGISTRY
FLOW_REGISTRY = {**FLOW_REGISTRY, **MARKETING_FLOW_REGISTRY}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E8-S1-T1 | `src/Plant/BackEnd/tests/flows/test_marketing_flow.py` | `POST /v1/flow-runs` with `flow_name="ContentCreationFlow"`, `customer_reviews=true` | `flow_run.status = "awaiting_approval"` after ContentProcessor step |
| E8-S1-T2 | same | `customer_reviews=false` | Gate skipped; `flow_run.status = "completed"` (all mocked steps succeed) |
| E8-S1-T3 | same | `POST /v1/flow-runs` with `flow_name="PublishingFlow"`, LinkedIn mock succeeds + YouTube mock fails | `flow_run.status = "partial_failure"`, `error_details.failed_steps = ["youtube"]` |
| E8-S1-T4 | same | Both LinkedIn + YouTube mocks succeed | `flow_run.status = "completed"`, two `component_run` rows with `status="completed"` |
| E8-S1-T5 | same | Both fail | `flow_run.status = "failed"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/flows/test_marketing_flow.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E8-S1 — Marketing Agent FlowDef + fan-out end-to-end`

**Done signal:**
`"E8-S1 done. Changed: flows/marketing_agent.py, api/v1/flow_runs.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅"`

---

#### Story E8-S2: `POST /v1/approvals/{flow_run_id}/approve` + `/reject` endpoints

**BLOCKED UNTIL:** E8-S1 committed to `feat/EXEC-ENGINE-001-it4-e8`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it4-e8`
**CP BackEnd pattern:** Pattern B — new `/cp/approvals/*` proxy is added in Iteration 6 (E14-S2); this story adds only the Plant `/v1/approvals/*` source endpoints

**What to do:**
When `flow_run.status = "awaiting_approval"`, the customer must be able to approve or reject it. Create `api/v1/approvals.py` with `POST /v1/approvals/{flow_run_id}/approve` (transitions to `running`, sets `auto_execute=True` in `run_context`, re-enqueues remaining steps) and `POST /v1/approvals/{flow_run_id}/reject` (transitions to `failed`, sets `error_details.reason="customer_rejected"`). Non-`awaiting_approval` status → HTTP 409. Register router in `main.py`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/flow_run.py` | 1–45 | `status` column, `run_context` JSONB, `error_details` JSONB |
| `src/Plant/BackEnd/api/v1/skill_configs.py` | 1–40 | `waooaw_router()` + `get_db_session` usage pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/approvals.py` | create | Approve + reject endpoints as per code pattern below |
| `src/Plant/BackEnd/main.py` | modify | Add `from api.v1 import approvals` and `app.include_router(approvals.router)` |

**Code patterns to copy exactly:**
```python
# src/Plant/BackEnd/api/v1/approvals.py
from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from core.routing import waooaw_router
from core.database import get_db_session
from core.logging import get_logger, PIIMaskingFilter
from models.flow_run import FlowRunModel

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

router = waooaw_router(prefix="/v1/approvals", tags=["approvals"])

@router.post("/{flow_run_id}/approve")
async def approve_flow_run(
    flow_run_id: str,
    db: Session = Depends(get_db_session),
):
    flow_run = db.query(FlowRunModel).filter_by(id=flow_run_id).first()
    if not flow_run or flow_run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Not awaiting approval")
    flow_run.status = "running"
    flow_run.run_context = {**flow_run.run_context, "auto_execute": True}
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": flow_run_id, "status": flow_run.status}

@router.post("/{flow_run_id}/reject")
async def reject_flow_run(
    flow_run_id: str,
    db: Session = Depends(get_db_session),
):
    flow_run = db.query(FlowRunModel).filter_by(id=flow_run_id).first()
    if not flow_run or flow_run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Not awaiting approval")
    flow_run.status = "failed"
    flow_run.error_details = {"reason": "customer_rejected"}
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": flow_run_id, "status": flow_run.status}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E8-S2-T1 | `src/Plant/BackEnd/tests/api/test_approvals.py` | Create `FlowRunModel` with `status="awaiting_approval"`, call `POST /v1/approvals/{id}/approve` | HTTP 200, DB row `status="running"`, `run_context["auto_execute"] == True` |
| E8-S2-T2 | same | Create row with `status="awaiting_approval"`, call `/reject` | HTTP 200, DB row `status="failed"`, `error_details["reason"]="customer_rejected"` |
| E8-S2-T3 | same | Call approve on `flow_run.status="running"` (not awaiting) | HTTP 409 |
| E8-S2-T4 | same | Call reject on `flow_run.status="completed"` | HTTP 409 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/api/test_approvals.py -v --cov=app --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E8-S2 — approvals approve + reject endpoints`

**Done signal:**
`"E8-S2 done. Changed: api/v1/approvals.py, main.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

**Epic E8 complete ✅** — run Docker integration test (Rule 5) before opening iteration PR.

---

### Iteration 4 — Completion Checkpoint

After ALL E7 and E8 epics complete and Docker integration test passes:

```bash
git checkout main && git pull
git checkout -b feat/EXEC-ENGINE-001-it4
git merge --no-ff feat/EXEC-ENGINE-001-it4-e7 feat/EXEC-ENGINE-001-it4-e8
git push origin feat/EXEC-ENGINE-001-it4

gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-it4 \
  --title "feat(EXEC-ENGINE-001): iteration 4 — Marketing Agent fan-out flow" \
  --body "## EXEC-ENGINE-001 Iteration 4

### Stories completed
| E7-S1 | GoalConfigPump component | 🟢 Done |
| E7-S2 | ContentProcessor component | 🟢 Done |
| E7-S3 | LinkedInPublisher + YouTubePublisher components | 🟢 Done |
| E8-S1 | Marketing Agent FlowDef + fan-out end-to-end | 🟢 Done |
| E8-S2 | Approvals approve + reject endpoints | 🟢 Done |

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] @circuit_breaker on all external HTTP calls
- [ ] No env-specific values in Dockerfile or code
- [ ] Tests >= 80% coverage on new BE code
- [ ] Postgres owns flow state; Redis only transports jobs"
```

Post PR URL. **STOP — do not start Iteration 5 until this PR is merged to `main`.**

---

## Iteration 5 — CP Portal UI

**Scope:** Customer can browse the marketplace, hire an agent with skill configuration and goal setting, monitor live agent runs with timeline view, see deliverables, and approve or reject content from an approval queue — all in the CP dark-theme UI.
**Lane:** A — wires existing Plant API endpoints; no new backend required beyond what Iteration 4 delivered.
**⏱ Estimated:** 5h | **Come back:** 2026-03-10 11:00 IST
**Epics:** E9, E10, E11

> **⛔ ITERATION 5 GATE — verify before writing any code:** Iteration 4 PR must be merged to `main`:
> ```bash
> git fetch origin
> git show origin/main:docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md | grep "Iteration 4"
> ```
> If Iteration 4 content is absent from `main`, **STOP** and tell the user: "Iteration 5 is blocked — the Iteration 4 PR must be merged to main first."

### Dependency Map (Iteration 5)

```
E9-S1                             (branch feat/EXEC-ENGINE-001-it5-e9; foundational UI components)
  │
  ▼
E10-S1 ──► E10-S2                 (branch feat/EXEC-ENGINE-001-it5-e10; depends on E9-S1)
E11-S1 ──► E11-S2                 (branch feat/EXEC-ENGINE-001-it5-e11; depends on E9-S1)
```

---

### Epic E9: Customer discovers and browses the WAOOAW agent marketplace

**Branch:** `feat/EXEC-ENGINE-001-it5-e9`
**User story:** As a prospective customer, I can browse the agent marketplace and see agent cards with live status, specialty, and ratings so that I can compare agents before hiring.

---

#### Story E9-S1: Reusable `AgentCard` + `StatusDot` UI components

**BLOCKED UNTIL:** none (Iteration 5 must be on `main` first)
**Estimated time:** 30 min
**Branch:** `feat/EXEC-ENGINE-001-it5-e9`
**CP BackEnd pattern:** N/A — frontend components only; no API call in this story

**What to do:**
Create `frontend/components/AgentCard.js` and `frontend/components/StatusDot.js` as reusable vanilla-JS components used across Marketplace, My Agents, and PP Fleet. Both must use WAOOAW dark-theme design tokens exclusively. `AgentCard` renders avatar (initials + gradient background), agent name, industry tag, status dot, specialty, rating (⭐ n.n), monthly price, and a CTA button. `StatusDot` renders an 8px circle mapped from status string to CSS color token with a hover tooltip.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `frontend/` (directory listing) | — | Existing component conventions and import patterns |
| `frontend/pages/` (any existing page) | 1–40 | How existing JS components are imported/exported |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/components/AgentCard.js` | create | Full component as per code pattern below |
| `frontend/components/StatusDot.js` | create | Full component as per code pattern below |

**Code patterns to copy exactly:**
```javascript
// frontend/components/StatusDot.js
const STATUS_COLORS = {
  running:            'var(--status-green)',    // #10b981
  awaiting_approval:  'var(--status-yellow)',   // #f59e0b
  failed:             'var(--status-red)',       // #ef4444
  paused:             'var(--status-gray)',      // #6b7280
  completed:          'var(--status-green)',
};
const STATUS_LABELS = {
  running: 'Running', awaiting_approval: 'Needs Approval',
  failed: 'Failed', paused: 'Paused', completed: 'Done',
};
export function renderStatusDot(status) {
  const color = STATUS_COLORS[status] || 'var(--status-gray)';
  const label = STATUS_LABELS[status] || status;
  return `<span class="status-dot" style="background:${color}" title="${label}"
    aria-label="${label}"></span>`;
}

// frontend/components/AgentCard.js
// CSS vars: --bg-card:#18181b, --color-neon-cyan:#00f2fe, --border-dark:rgba(255,255,255,0.08)
import { renderStatusDot } from './StatusDot.js';
export function renderAgentCard({ id, name, industry, status, specialty, rating, price,
                                   ctaLabel = 'View', ctaHref = '#' }) {
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  return `
<article class="agent-card" data-agent-id="${id}">
  <div class="agent-card__avatar">${initials}</div>
  <div class="agent-card__info">
    <div class="agent-card__header">
      <h3 class="agent-card__name">${name}</h3>
      ${renderStatusDot(status)}
    </div>
    <span class="agent-card__industry">${industry}</span>
    <p class="agent-card__specialty">${specialty}</p>
    <div class="agent-card__meta">
      <span class="agent-card__rating">⭐ ${rating?.toFixed(1) ?? '—'}</span>
      <span class="agent-card__price">₹${price?.toLocaleString('en-IN') ?? '—'}/mo</span>
    </div>
  </div>
  <a href="${ctaHref}" class="btn btn--cyan agent-card__cta">${ctaLabel}</a>
</article>`;
}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E9-S1-T1 | `frontend/tests/components/test_agent_card.spec.js` | Render `AgentCard` with all props | HTML contains agent name, status dot span, CTA link |
| E9-S1-T2 | same | Render with `status="failed"` | StatusDot color maps to `--status-red` |
| E9-S1-T3 | same | Render with missing optional props (`rating=undefined`) | No JS exception thrown; renders `⭐ —` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/components/test_agent_card.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E9-S1 — AgentCard + StatusDot reusable UI components`

**Done signal:**
`"E9-S1 done. Changed: frontend/components/AgentCard.js, frontend/components/StatusDot.js. Tests: T1 ✅ T2 ✅ T3 ✅"`

**Epic E9 complete ✅** — run Docker integration test (Rule 5) before starting E10.

---

### Epic E10: Customer hires an agent with skill configuration and goal setting

**Branch:** `feat/EXEC-ENGINE-001-it5-e10`
**User story:** As a customer, I can browse the marketplace, click "Start 7-day trial" on an agent card, complete a three-step hire wizard with skill config and goal setting, and land on My Agents — all without page reload errors.

---

#### Story E10-S1: Marketplace screen with hire CTA

**BLOCKED UNTIL:** E9-S1 merged to `main` (needs `AgentCard` + `StatusDot` components)
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it5-e10`
**CP BackEnd pattern:** Pattern A — calls existing `GET /cp/agents` proxy (already in `src/CP/BackEnd/api/`)

**What to do:**
Create `frontend/pages/marketplace.html` and `frontend/pages/marketplace.js`. Fetch agents from `GET /cp/agents`, render using `AgentCard` with `ctaLabel="Start 7-day trial"` and `ctaHref="/hire/{agent_id}"`. Include a search bar and filter row (Industry, Status, Rating). The page must feel like browsing talent (Upwork/Fiverr) — not a SaaS feature list. Dark theme with `#0a0a0a` background.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `frontend/components/AgentCard.js` | 1–40 | `renderAgentCard()` props interface |
| `src/CP/BackEnd/api/` (list files) | — | Confirm `GET /cp/agents` exists; note response shape |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/pages/marketplace.html` | create | HTML shell with search bar, filter row, `#agent-grid` container, dark theme, font imports |
| `frontend/pages/marketplace.js` | create | Fetch + filter + render logic as per code pattern below |

**Code patterns to copy exactly:**
```javascript
// frontend/pages/marketplace.js
import { renderAgentCard } from '../components/AgentCard.js';

const API_BASE = window.API_BASE || '';
let allAgents = [];

async function loadAgents() {
  const res = await fetch(`${API_BASE}/cp/agents`);
  if (!res.ok) throw new Error('Failed to fetch agents');
  allAgents = await res.json();
  renderGrid(allAgents);
}

function renderGrid(agents) {
  const grid = document.getElementById('agent-grid');
  if (!agents.length) {
    grid.innerHTML = `<div class="empty-state">No agents found — <button onclick="resetFilters()">reset filters</button></div>`;
    return;
  }
  grid.innerHTML = agents.map(a => renderAgentCard({
    id: a.id, name: a.name, industry: a.industry, status: a.status,
    specialty: a.specialty, rating: a.rating, price: a.price,
    ctaLabel: 'Start 7-day trial', ctaHref: `/hire/${a.id}`,
  })).join('');
}

function applyFilters() {
  const query = document.getElementById('search-input').value.toLowerCase();
  const industry = document.getElementById('filter-industry').value;
  const minRating = parseFloat(document.getElementById('filter-rating').value || 0);
  const filtered = allAgents.filter(a =>
    (a.name.toLowerCase().includes(query) || a.specialty.toLowerCase().includes(query)) &&
    (!industry || a.industry === industry) &&
    (a.rating >= minRating)
  );
  renderGrid(filtered);
}

function resetFilters() {
  document.getElementById('search-input').value = '';
  document.getElementById('filter-industry').value = '';
  document.getElementById('filter-rating').value = '';
  renderGrid(allAgents);
}

document.addEventListener('DOMContentLoaded', () => {
  loadAgents().catch(err => { document.getElementById('agent-grid').innerHTML = `<p class="error">${err.message}</p>`; });
  document.getElementById('search-input').addEventListener('input', applyFilters);
  document.getElementById('filter-industry').addEventListener('change', applyFilters);
  document.getElementById('filter-rating').addEventListener('change', applyFilters);
});
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E10-S1-T1 | `frontend/tests/pages/test_marketplace.spec.js` | Mock `GET /cp/agents` returns 2 agents | Grid renders 2 `agent-card` articles |
| E10-S1-T2 | same | Filter by `industry="marketing"` | Only marketing-industry agents visible |
| E10-S1-T3 | same | Mock returns empty array | Empty state message with reset button shown |
| E10-S1-T4 | same | Mock `GET /cp/agents` returns HTTP 500 | Error message displayed in grid container |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/pages/test_marketplace.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E10-S1 — Marketplace screen with hire CTA`

**Done signal:**
`"E10-S1 done. Changed: frontend/pages/marketplace.html, frontend/pages/marketplace.js. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E10-S2: Hire wizard — skill config + goal setting

**BLOCKED UNTIL:** E10-S1 committed to `feat/EXEC-ENGINE-001-it5-e10`
**Estimated time:** 90 min
**Branch:** `feat/EXEC-ENGINE-001-it5-e10`
**CP BackEnd pattern:** Pattern A — calls existing `POST /cp/hired-agents`, `PATCH /cp/skill-configs/{id}/{skill_id}`, `POST /cp/goal-instances` proxies

**What to do:**
Create `frontend/pages/hire.html` and `frontend/pages/hire.js` — a three-step wizard. Step 1: Confirm agent + nickname. Step 2: Fill skill config `customer_fields` (form is dynamic; API key fields use `type=password`). Step 3: Schedule + approval preference. API errors display inline under the relevant field, not `alert()`. On completion redirect to `/my-agents`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/api/hired_agents_proxy.py` | 1–50 | `POST /cp/hired-agents` response shape — need `id` field |
| `frontend/pages/marketplace.js` | 1–40 | Fetch pattern and `API_BASE` convention to match |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/pages/hire.html` | create | Three-step wizard HTML with step indicators, form containers, Back/Next/Submit buttons, inline error spans, trial badge |
| `frontend/pages/hire.js` | create | Wizard state machine + API calls as per code pattern below |

**Code patterns to copy exactly:**
```javascript
// frontend/pages/hire.js
const API_BASE = window.API_BASE || '';
let wizardState = { step: 1, agentId: null, hiredInstanceId: null, skillConfigId: null };

async function goToStep(n) {
  document.querySelectorAll('.wizard-step').forEach((el, i) => {
    el.hidden = i + 1 !== n;
  });
  wizardState.step = n;
}

async function submitStep1() {
  const nickname = document.getElementById('nickname').value.trim();
  if (!nickname) { showError('nickname-error', 'Nickname is required'); return; }
  const res = await fetch(`${API_BASE}/cp/hired-agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: wizardState.agentId, nickname }),
  });
  if (!res.ok) { showError('step1-error', (await res.json()).detail); return; }
  const data = await res.json();
  wizardState.hiredInstanceId = data.id;
  goToStep(2);
}

async function submitStep2() {
  const customerFields = readFormFields('skill-config-form');
  const res = await fetch(`${API_BASE}/cp/skill-configs/${wizardState.hiredInstanceId}/default`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_fields: customerFields }),
  });
  if (!res.ok) { showError('step2-error', (await res.json()).detail); return; }
  goToStep(3);
}

async function submitStep3() {
  const schedule = document.getElementById('schedule').value;
  const customerReviews = document.getElementById('approval-toggle').checked;
  const res = await fetch(`${API_BASE}/cp/goal-instances`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hired_instance_id: wizardState.hiredInstanceId,
                           schedule, customer_reviews: customerReviews }),
  });
  if (!res.ok) { showError('step3-error', (await res.json()).detail); return; }
  window.location.href = '/my-agents';
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) { el.textContent = message; el.hidden = false; }
}

function readFormFields(formId) {
  const form = document.getElementById(formId);
  const result = {};
  new FormData(form).forEach((v, k) => { result[k] = v; });
  return result;
}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E10-S2-T1 | `frontend/tests/pages/test_hire_wizard.spec.js` | Submit Step 1 with empty nickname | `showError` called with "Nickname is required"; page stays on step 1 |
| E10-S2-T2 | same | Mock `POST /cp/hired-agents` returns 201 with `id` | Wizard advances to step 2 |
| E10-S2-T3 | same | Mock `PATCH /cp/skill-configs` returns 500 | Inline error shown; step does not advance |
| E10-S2-T4 | same | Full happy path (all APIs mock 200) | Final step triggers redirect to `/my-agents` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/pages/test_hire_wizard.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E10-S2 — hire wizard skill config + goal setting`

**Done signal:**
`"E10-S2 done. Changed: frontend/pages/hire.html, frontend/pages/hire.js. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

**Epic E10 complete ✅** — run Docker integration test (Rule 5) before starting E11.

---

### Epic E11: Customer monitors live agent runs, views deliverables, and approves output

**Branch:** `feat/EXEC-ENGINE-001-it5-e11`
**User story:** As a customer with agents hired, I can see all my agents with live status, open any agent to watch the flow run step-by-step in a timeline, view delivered results, and approve or reject pending content — all from the CP portal.

---

#### Story E11-S1: My Agents screen + `FlowRunTimeline` + `DeliverableCard` components

**BLOCKED UNTIL:** E9-S1 merged to `main` (needs `AgentCard` + `StatusDot`)
**Estimated time:** 90 min
**Branch:** `feat/EXEC-ENGINE-001-it5-e11`
**CP BackEnd pattern:** Pattern A — calls `GET /cp/hired-agents` (existing), `GET /cp/flow-runs?hired_instance_id=X` (E14-S2 proxy, BLOCKED UNTIL E14-S2 merged; frontenc calls it anyway — guard with empty-state fallback)

**What to do:**
Create `frontend/pages/my-agents.html`, `frontend/pages/my-agents.js`, `frontend/components/FlowRunTimeline.js`, and `frontend/components/DeliverableCard.js`. My Agents lists hired agents (compact `AgentCard`) with a "Needs Approval" badge when `flow_run.status = "awaiting_approval"`. Per-agent detail shows `FlowRunTimeline` (auto-refreshes every 5s when running) and a `DeliverableCard` list. Error and empty states required.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `frontend/components/AgentCard.js` | 1–40 | Import path and props interface |
| `frontend/components/StatusDot.js` | 1–20 | `renderStatusDot()` import path |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/components/FlowRunTimeline.js` | create | Renders horizontal stepper — each step node with `step_name`, status icon, `duration_ms`; highlights `current_step` with pulse CSS class when `status="running"` |
| `frontend/components/DeliverableCard.js` | create | Renders type badge, creation time, 120-char truncated preview, "View full" inline expand toggle, download link |
| `frontend/pages/my-agents.html` | create | Agent list container + per-agent detail panel (hidden by default), dark theme |
| `frontend/pages/my-agents.js` | create | Load agents, load flow runs, render components, 5s polling when `status="running"` |

**Code patterns to copy exactly:**
```javascript
// frontend/components/FlowRunTimeline.js
export function renderFlowRunTimeline(flowRun, componentRuns) {
  if (!flowRun) return '<p class="empty-state">No runs yet — your first run will appear here.</p>';
  const steps = componentRuns.map(cr => {
    const icon = { completed: '✓', running: '⏳', failed: '✗', pending: '⏸' }[cr.status] || '•';
    const pulse = cr.status === 'running' ? ' timeline-step--pulse' : '';
    return `<div class="timeline-step timeline-step--${cr.status}${pulse}">
      <span class="timeline-step__icon">${icon}</span>
      <span class="timeline-step__name">${cr.step_name}</span>
      ${cr.duration_ms ? `<span class="timeline-step__dur">${cr.duration_ms}ms</span>` : ''}
    </div>`;
  }).join('<span class="timeline-arrow">→</span>');
  return `<div class="flow-timeline" data-flow-run-id="${flowRun.id}" data-status="${flowRun.status}">${steps}</div>`;
}

// frontend/components/DeliverableCard.js
export function renderDeliverableCard(d) {
  const preview = JSON.stringify(d.content).slice(0, 120);
  return `<div class="deliverable-card">
    <span class="deliverable-card__type-badge">${d.type}</span>
    <time class="deliverable-card__time">${new Date(d.created_at).toLocaleString()}</time>
    <p class="deliverable-card__preview">${preview}…</p>
    <button class="deliverable-card__expand" onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden">View full</button>
    <pre class="deliverable-card__full" hidden>${JSON.stringify(d.content, null, 2)}</pre>
  </div>`;
}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E11-S1-T1 | `frontend/tests/components/test_flow_run_timeline.spec.js` | Pass `flowRun.status="running"` and 3 component runs | Renders 3 step nodes; running step has `--pulse` class |
| E11-S1-T2 | same | `flowRun = null` | Renders empty-state paragraph |
| E11-S1-T3 | `frontend/tests/components/test_deliverable_card.spec.js` | Pass deliverable with `content={order_id:"X"}` | Preview contains `order_id`; "View full" button present |
| E11-S1-T4 | `frontend/tests/pages/test_my_agents.spec.js` | Mock `GET /cp/hired-agents` returns 1 agent with `awaiting_approval` flow_run | "Needs Approval" badge rendered on that agent's card |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/components/test_flow_run_timeline.spec.js frontend/tests/components/test_deliverable_card.spec.js frontend/tests/pages/test_my_agents.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E11-S1 — My Agents + FlowRunTimeline + DeliverableCard`

**Done signal:**
`"E11-S1 done. Changed: frontend/components/FlowRunTimeline.js, components/DeliverableCard.js, pages/my-agents.html, pages/my-agents.js. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E11-S2: Approval queue + `ApprovalQueueItem` component

**BLOCKED UNTIL:** E11-S1 committed to `feat/EXEC-ENGINE-001-it5-e11`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it5-e11`
**CP BackEnd pattern:** Pattern A — calls `POST /cp/approvals/{id}/approve` + `/reject` (E14-S2 proxy, BLOCKED UNTIL E14-S2 merged; fallback gracefully if unavailable)

**What to do:**
Create `frontend/pages/approvals.html`, `frontend/pages/approvals.js`, and `frontend/components/ApprovalQueueItem.js`. The approval queue is accessible from the main nav with a badge count. Each `ApprovalQueueItem` renders the agent name + avatar, a content preview from `deliverable.content`, and Approve (neon cyan) / Reject (red) buttons. Approve is optimistic (disabled immediately). Reject requires a confirmation dialog. Empty queue shows a congratulations message.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `frontend/components/AgentCard.js` | 1–40 | Avatar initials rendering pattern to reuse |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/components/ApprovalQueueItem.js` | create | Full component as per code pattern below |
| `frontend/pages/approvals.html` | create | Nav badge, approval list container, empty state, dark theme |
| `frontend/pages/approvals.js` | create | Fetch pending approvals from `GET /cp/flow-runs?status=awaiting_approval`, render items, handle approve/reject actions |

**Code patterns to copy exactly:**
```javascript
// frontend/components/ApprovalQueueItem.js
const API_BASE = window.API_BASE || '';

export function renderApprovalQueueItem(flowRun, deliverable, agentName) {
  const preview = deliverable
    ? (deliverable.content?.per_platform_variants
        ? `Publish to platforms: ${Object.keys(deliverable.content.per_platform_variants).join(', ')}`
        : `Place trade: ${JSON.stringify(deliverable.content).slice(0, 80)}`)
    : 'Pending output preview';
  return `
<div class="approval-item" data-flow-run-id="${flowRun.id}">
  <div class="approval-item__agent">${agentName}</div>
  <p class="approval-item__preview">${preview}</p>
  <div class="approval-item__actions">
    <button class="btn btn--cyan" onclick="approveFlowRun('${flowRun.id}', this)">Approve</button>
    <button class="btn btn--red" onclick="rejectFlowRun('${flowRun.id}')">Reject</button>
  </div>
</div>`;
}

async function approveFlowRun(flowRunId, btn) {
  btn.disabled = true;
  const res = await fetch(`${API_BASE}/cp/approvals/${flowRunId}/approve`, { method: 'POST' });
  if (!res.ok) { btn.disabled = false; alert('Approval failed — try again'); return; }
  document.querySelector(`[data-flow-run-id="${flowRunId}"]`)?.remove();
}

async function rejectFlowRun(flowRunId) {
  if (!confirm('Reject this agent output? The run will be marked as failed.')) return;
  await fetch(`${API_BASE}/cp/approvals/${flowRunId}/reject`, { method: 'POST' });
  document.querySelector(`[data-flow-run-id="${flowRunId}"]`)?.remove();
}
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E11-S2-T1 | `frontend/tests/components/test_approval_queue_item.spec.js` | Render item with `deliverable.content.per_platform_variants={linkedin:{}}` | Preview text contains "linkedin" |
| E11-S2-T2 | same | Mock `POST /cp/approvals/{id}/approve` returns 200, click Approve | Button disabled immediately; item removed from DOM after response |
| E11-S2-T3 | `frontend/tests/pages/test_approvals.spec.js` | Mock `GET /cp/flow-runs?status=awaiting_approval` returns empty array | Empty queue message displayed |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/components/test_approval_queue_item.spec.js frontend/tests/pages/test_approvals.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E11-S2 — approval queue + ApprovalQueueItem component`

**Done signal:**
`"E11-S2 done. Changed: frontend/components/ApprovalQueueItem.js, pages/approvals.html, pages/approvals.js. Tests: T1 ✅ T2 ✅ T3 ✅"`

**Epic E11 complete ✅** — run Docker integration test (Rule 5) before opening iteration PR.

---

### Iteration 5 — Completion Checkpoint

After ALL E9, E10, and E11 epics complete and Docker integration test passes:

```bash
git checkout main && git pull
git checkout -b feat/EXEC-ENGINE-001-it5
git merge --no-ff feat/EXEC-ENGINE-001-it5-e9 feat/EXEC-ENGINE-001-it5-e10 feat/EXEC-ENGINE-001-it5-e11
git push origin feat/EXEC-ENGINE-001-it5

gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-it5 \
  --title "feat(EXEC-ENGINE-001): iteration 5 — CP portal UI" \
  --body "## EXEC-ENGINE-001 Iteration 5

### Stories completed
| E9-S1 | AgentCard + StatusDot reusable UI components | 🟢 Done |
| E10-S1 | Marketplace screen with hire CTA | 🟢 Done |
| E10-S2 | Hire wizard skill config + goal setting | 🟢 Done |
| E11-S1 | My Agents + FlowRunTimeline + DeliverableCard | 🟢 Done |
| E11-S2 | Approval queue + ApprovalQueueItem component | 🟢 Done |

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter (N/A — FE only iteration)
- [ ] Dark theme: #0a0a0a background, neon cyan #00f2fe accents
- [ ] No raw API keys/secrets in frontend code or localStorage
- [ ] Loading + error + empty states on every data-fetching screen
- [ ] Keyboard navigation on Marketplace and Hire wizard
- [ ] StatusDot tooltip shows human-readable label"
```

Post PR URL. **STOP — do not start Iteration 6 until this PR is merged to `main`.**

---

## Iteration 6 — PP Portal UI: Fleet + Health + DLQ

**Scope:** Partner can see the full WAOOAW agent fleet health dashboard, drill into per-agent component run history, manage the Dead Letter Queue (requeue or skip failed tasks), and the Customer Portal gains proxy routes for flow-runs and component-runs so the frontend stories in Iteration 5 work end-to-end.
**Lane:** A (E12–E14 frontend wires existing Plant Gateway endpoints) + Lane B (E14-S2 adds thin CP proxy routes).
**⏱ Estimated:** 3h 45 min | **Come back:** 2026-03-11 11:00 IST
**Epics:** E12, E13, E14

> **⛔ ITERATION 6 GATE — verify before writing any code:** Iteration 5 PR must be merged to `main`:
> ```bash
> git fetch origin
> git show origin/main:docs/CP/iterations/EXEC-ENGINE-001-execution-layer.md | grep "Iteration 5"
> ```
> If Iteration 5 content is absent from `main`, **STOP** and tell the user: "Iteration 6 is blocked — the Iteration 5 PR must be merged to main first."

### Dependency Map (Iteration 6)

```
E12-S1                     (branch feat/EXEC-ENGINE-001-it6-e12; standalone PP fleet dashboard)
E13-S1                     (branch feat/EXEC-ENGINE-001-it6-e13; standalone PP per-agent drill-in)
E14-S1                     (branch feat/EXEC-ENGINE-001-it6-e14; PP DLQ panel)
E14-S2  ◄── MUST MERGE     (same branch feat/EXEC-ENGINE-001-it6-e14; CP proxy routes that unlock
 │              first       Iteration 5 E11-S1/E11-S2 live flow data; merge to main before E14-S1)
 └──► E14-S1
```

---

### Epic E12: Partner sees the full agent fleet health at a glance

**Branch:** `feat/EXEC-ENGINE-001-it6-e12`
**User story:** As a WAOOAW partner, I can open the PP portal Fleet dashboard and see all deployed agents, their live status, active run counts, and error rates in a single dark-theme grid so that I can identify struggling agents immediately.

---

#### Story E12-S1: PP Fleet dashboard with agent health map

**BLOCKED UNTIL:** none — Iteration 6 gate verified
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it6-e12`
**CP BackEnd pattern:** N/A — PP portal wires Plant Gateway directly; calls `GET /v1/agents` and `GET /v1/component-runs/summary` on Plant Gateway

**What to do:**
Create `frontend/pp-portal/pages/fleet.html` and `frontend/pp-portal/pages/fleet.js`. Fetch all agents from `GET /v1/agents`, then for each fetch component run summary from `GET /v1/component-runs/summary?agent_id={id}`. Render a `FleetAgentRow` per agent: name, instance count, status distribution (running / failed / completed bars), error rate %. Auto-refresh every 10s. Empty state and error state required.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `frontend/components/StatusDot.js` | 1–20 | `renderStatusDot()` import pattern |
| `src/Plant/Gateway/main.py` or `src/Plant/Gateway/api/` | 1–40 | Confirm `GET /v1/agents` and `GET /v1/component-runs/summary` route paths |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/pp-portal/pages/fleet.html` | create | Dark-theme shell with PP nav, fleet grid container, auto-refresh counter |
| `frontend/pp-portal/pages/fleet.js` | create | Fetch agents + summaries, render rows, 10s polling loop, error/empty states |

**Code patterns to copy exactly:**
```javascript
// frontend/pp-portal/pages/fleet.js
const API_BASE = window.PP_API_BASE || '';
let refreshTimer = null;

function renderFleetAgentRow(agent, summary) {
  const errorRate = summary.total > 0
    ? ((summary.failed / summary.total) * 100).toFixed(1)
    : '0.0';
  const barWidth = (count, total) => total > 0 ? Math.round((count / total) * 100) : 0;
  return `
<div class="fleet-row" data-agent-id="${agent.id}">
  <div class="fleet-row__name">${agent.name}</div>
  <div class="fleet-row__instances">${agent.instance_count ?? 0} instances</div>
  <div class="fleet-row__bars">
    <div class="fleet-bar fleet-bar--green" style="width:${barWidth(summary.completed, summary.total)}%"
         title="${summary.completed} completed"></div>
    <div class="fleet-bar fleet-bar--yellow" style="width:${barWidth(summary.running, summary.total)}%"
         title="${summary.running} running"></div>
    <div class="fleet-bar fleet-bar--red" style="width:${barWidth(summary.failed, summary.total)}%"
         title="${summary.failed} failed"></div>
  </div>
  <div class="fleet-row__error-rate ${parseFloat(errorRate) > 10 ? 'fleet-row__error-rate--high' : ''}">
    ${errorRate}% err
  </div>
  <a href="/pp/agent/${agent.id}" class="btn btn--outline fleet-row__drill">Details →</a>
</div>`;
}

async function loadFleet() {
  const agentsRes = await fetch(`${API_BASE}/v1/agents`);
  if (!agentsRes.ok) throw new Error('Failed to load agents');
  const agents = await agentsRes.json();
  const summaries = await Promise.all(
    agents.map(a => fetch(`${API_BASE}/v1/component-runs/summary?agent_id=${a.id}`)
      .then(r => r.ok ? r.json() : { total: 0, running: 0, completed: 0, failed: 0 })
    )
  );
  const grid = document.getElementById('fleet-grid');
  if (!agents.length) { grid.innerHTML = '<p class="empty-state">No agents deployed yet.</p>'; return; }
  grid.innerHTML = agents.map((a, i) => renderFleetAgentRow(a, summaries[i])).join('');
}

function startPolling() {
  loadFleet().catch(err => { document.getElementById('fleet-grid').innerHTML = `<p class="error">${err.message}</p>`; });
  refreshTimer = setInterval(() => loadFleet().catch(console.error), 10000);
}

document.addEventListener('DOMContentLoaded', startPolling);
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E12-S1-T1 | `frontend/tests/pp-portal/test_fleet.spec.js` | Mock agents returns 2; summaries return `{total:10,running:2,completed:7,failed:1}` | Two `fleet-row` elements rendered; error rate shows `10.0%` |
| E12-S1-T2 | same | Error rate > 10 % | `fleet-row__error-rate--high` class present |
| E12-S1-T3 | same | Mock `GET /v1/agents` returns empty array | Empty-state message rendered |
| E12-S1-T4 | same | Mock `GET /v1/agents` returns HTTP 500 | Error message displayed in fleet grid |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/pp-portal/test_fleet.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E12-S1 — PP fleet dashboard with agent health map`

**Done signal:**
`"E12-S1 done. Changed: frontend/pp-portal/pages/fleet.html, fleet.js. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

**Epic E12 complete ✅** — run Docker integration test (Rule 5) before starting E13.

---

### Epic E13: Partner drills into a single agent to diagnose component failures

**Branch:** `feat/EXEC-ENGINE-001-it6-e13`
**User story:** As a partner, I can click on any agent in the Fleet dashboard and see a detailed per-agent page with recent flow runs, each step's duration and error message, so that I can diagnose why a specific component is failing.

---

#### Story E13-S1: Per-agent health drill-in with `ComponentRunRow` component

**BLOCKED UNTIL:** E12-S1 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it6-e13`
**CP BackEnd pattern:** N/A — PP portal wires Plant Gateway directly; calls `GET /v1/flow-runs?agent_id={id}` and `GET /v1/component-runs?flow_run_id={id}`

**What to do:**
Create `frontend/pp-portal/pages/agent-detail.html`, `frontend/pp-portal/pages/agent-detail.js`, and `frontend/pp-portal/components/ComponentRunRow.js`. Agent detail page loads `GET /v1/flow-runs?agent_id={id}` (most recent 10), renders each as a collapsible row with `ComponentRunRow` sub-rows for each step — showing step name, status badge, `duration_ms`, and truncated `error_message`. Expand/collapse on click without full page reload.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `frontend/components/FlowRunTimeline.js` | 1–25 | Step status icon map to reuse consistently |
| `frontend/pp-portal/pages/fleet.js` | 1–20 | `API_BASE` convention and fetch pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/pp-portal/components/ComponentRunRow.js` | create | Full component as per code pattern below |
| `frontend/pp-portal/pages/agent-detail.html` | create | Agent name header, back link to fleet, flow run list container |
| `frontend/pp-portal/pages/agent-detail.js` | create | Load flow runs, render expandable rows with `ComponentRunRow` sub-rows |

**Code patterns to copy exactly:**
```javascript
// frontend/pp-portal/components/ComponentRunRow.js
const STATUS_ICONS = { completed: '✓', running: '⏳', failed: '✗', pending: '⏸' };
const STATUS_CLASSES = { completed: 'success', running: 'running', failed: 'error', pending: 'pending' };

export function renderComponentRunRow(cr) {
  const icon = STATUS_ICONS[cr.status] || '•';
  const cls = STATUS_CLASSES[cr.status] || 'pending';
  const errMsg = cr.error_message
    ? `<span class="cr-row__error" title="${cr.error_message}">${cr.error_message.slice(0, 80)}…</span>`
    : '';
  return `
<div class="cr-row cr-row--${cls}">
  <span class="cr-row__icon">${icon}</span>
  <span class="cr-row__step">${cr.step_name}</span>
  ${cr.duration_ms ? `<span class="cr-row__dur">${cr.duration_ms}ms</span>` : ''}
  ${errMsg}
</div>`;
}

// frontend/pp-portal/pages/agent-detail.js
import { renderComponentRunRow } from '../components/ComponentRunRow.js';
const API_BASE = window.PP_API_BASE || '';

async function loadAgentDetail(agentId) {
  const runsRes = await fetch(`${API_BASE}/v1/flow-runs?agent_id=${agentId}&limit=10`);
  if (!runsRes.ok) throw new Error('Failed to load flow runs');
  const flowRuns = await runsRes.json();
  const list = document.getElementById('flow-run-list');
  if (!flowRuns.length) { list.innerHTML = '<p class="empty-state">No runs yet for this agent.</p>'; return; }
  list.innerHTML = flowRuns.map(fr => `
<details class="flow-run-item">
  <summary class="flow-run-item__summary">
    <span class="flow-run-item__status flow-run-item__status--${fr.status}">${fr.status}</span>
    <time>${new Date(fr.created_at).toLocaleString()}</time>
  </summary>
  <div class="flow-run-item__steps" data-flow-run-id="${fr.id}">Loading steps…</div>
</details>`).join('');

  list.addEventListener('toggle', async (e) => {
    const details = e.target.closest('details');
    if (!details || !e.target.open) return;
    const flowRunId = details.querySelector('[data-flow-run-id]')?.dataset?.flowRunId;
    if (!flowRunId) return;
    const crRes = await fetch(`${API_BASE}/v1/component-runs?flow_run_id=${flowRunId}`);
    const componentRuns = crRes.ok ? await crRes.json() : [];
    details.querySelector('.flow-run-item__steps').innerHTML =
      componentRuns.map(renderComponentRunRow).join('') || '<em>No steps recorded.</em>';
  }, true);
}

const agentId = new URLSearchParams(window.location.search).get('id');
document.addEventListener('DOMContentLoaded', () => agentId && loadAgentDetail(agentId)
  .catch(err => { document.getElementById('flow-run-list').innerHTML = `<p class="error">${err.message}</p>`; }));
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E13-S1-T1 | `frontend/tests/pp-portal/test_agent_detail.spec.js` | Mock `GET /v1/flow-runs?agent_id=X` returns 2 runs | Two `flow-run-item` details elements rendered |
| E13-S1-T2 | same | Expand first item; mock `GET /v1/component-runs?flow_run_id=X` returns 2 steps | Two `cr-row` elements rendered inside the expanded `details` |
| E13-S1-T3 | `frontend/tests/pp-portal/test_component_run_row.spec.js` | Render with `status="failed"` and `error_message="Timeout after 30s"` | `cr-row--error` class; error message text present |
| E13-S1-T4 | same | `error_message` longer than 80 chars | Displayed text truncated with `…` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/pp-portal/test_agent_detail.spec.js frontend/tests/pp-portal/test_component_run_row.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E13-S1 — PP per-agent health drill-in with ComponentRunRow`

**Done signal:**
`"E13-S1 done. Changed: frontend/pp-portal/components/ComponentRunRow.js, pp-portal/pages/agent-detail.html, agent-detail.js. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

**Epic E13 complete ✅** — run Docker integration test (Rule 5) before starting E14.

---

### Epic E14: Partner manages the Dead Letter Queue; Customer Portal wires live execution data

**Branch:** `feat/EXEC-ENGINE-001-it6-e14`
**User story (partner):** As a partner, I can view all failed tasks in the DLQ, requeue a task for retry, or skip it permanently — so that I can recover from transient failures without code deployments.
**User story (customer — enabled by E14-S2):** As a CP customer with an agent hired, I can see live flow run timelines and approve/reject output because CP now proxies the necessary Plant Gateway routes.

---

#### Story E14-S2: CP proxy routes for flow-runs + component-runs

> **⚠️ Start with E14-S2 — merge it to `main` before E14-S1** so Iteration 5 E11-S1/E11-S2 customer stories unblock.

**BLOCKED UNTIL:** Iteration 5 PR merged to `main`
**Estimated time:** 30 min
**Branch:** `feat/EXEC-ENGINE-001-it6-e14`
**CP BackEnd pattern:** Pattern A — thin proxy via `gatewayRequestJson()`; routes go in a new file `src/CP/BackEnd/api/cp_flow_runs.py`; all 5 routes use `waooaw_router()`; GET routes use `get_read_db_session()`; `X-Correlation-ID` forwarded automatically by `get_correlation_id` global dep

**What to do:**
Create `src/CP/BackEnd/api/cp_flow_runs.py` with 5 routes that proxy Plant Gateway: `GET /cp/flow-runs`, `GET /cp/flow-runs/{flow_run_id}`, `POST /cp/approvals/{flow_run_id}/approve`, `POST /cp/approvals/{flow_run_id}/reject`, `GET /cp/component-runs`. Register the router in `src/CP/BackEnd/main.py`. All routes validate the authenticated customer owns the requested resource before proxying (call `GET /v1/flow-runs/{id}` and check `customer_id` field).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/api/cp_deliverables.py` | 1–60 | Canonical Pattern A thin proxy — copy `waooaw_router()`, `gatewayRequestJson`, auth, `get_read_db_session` usage exactly |
| `src/CP/BackEnd/main.py` | 1–40 | How routers are registered — find the `app.include_router(...)` block |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/api/cp_flow_runs.py` | create | 5 proxy routes as per code pattern below |
| `src/CP/BackEnd/main.py` | modify | Add `from api.cp_flow_runs import router as flow_runs_router` and `app.include_router(flow_runs_router)` |

**Code patterns to copy exactly:**
```python
# src/CP/BackEnd/api/cp_flow_runs.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.routing import waooaw_router
from core.database import get_read_db_session
from core.gateway import gatewayRequestJson
from dependencies.auth import get_current_customer

router = waooaw_router(prefix="/cp", tags=["flow-runs"])


@router.get("/flow-runs")
async def list_flow_runs(
    hired_instance_id: str | None = None,
    flow_status: str | None = None,
    customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_read_db_session),
):
    params = {"customer_id": customer.id}
    if hired_instance_id:
        params["hired_instance_id"] = hired_instance_id
    if flow_status:
        params["status"] = flow_status
    return await gatewayRequestJson("GET", "/v1/flow-runs", params=params)


@router.get("/flow-runs/{flow_run_id}")
async def get_flow_run(
    flow_run_id: str,
    customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_read_db_session),
):
    data = await gatewayRequestJson("GET", f"/v1/flow-runs/{flow_run_id}")
    if data.get("customer_id") != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return data


@router.post("/approvals/{flow_run_id}/approve")
async def approve_flow_run(
    flow_run_id: str,
    customer=Depends(get_current_customer),
):
    data = await gatewayRequestJson("GET", f"/v1/flow-runs/{flow_run_id}")
    if data.get("customer_id") != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await gatewayRequestJson("POST", f"/v1/approvals/{flow_run_id}/approve")


@router.post("/approvals/{flow_run_id}/reject")
async def reject_flow_run(
    flow_run_id: str,
    customer=Depends(get_current_customer),
):
    data = await gatewayRequestJson("GET", f"/v1/flow-runs/{flow_run_id}")
    if data.get("customer_id") != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await gatewayRequestJson("POST", f"/v1/approvals/{flow_run_id}/reject")


@router.get("/component-runs")
async def list_component_runs(
    flow_run_id: str,
    customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_read_db_session),
):
    # Ownership verified via parent flow_run
    fr = await gatewayRequestJson("GET", f"/v1/flow-runs/{flow_run_id}")
    if fr.get("customer_id") != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await gatewayRequestJson("GET", "/v1/component-runs", params={"flow_run_id": flow_run_id})
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E14-S2-T1 | `src/CP/BackEnd/tests/api/test_cp_flow_runs.py` | Authenticated; mock Gateway `GET /v1/flow-runs` 200 | CP returns 200 with flow runs list |
| E14-S2-T2 | same | `GET /cp/flow-runs/{id}` where `customer_id` ≠ token | 403 Forbidden |
| E14-S2-T3 | same | `POST /cp/approvals/{id}/approve` where `customer_id` ≠ token | 403 Forbidden |
| E14-S2-T4 | same | Unauthenticated request to any route | 401 Unauthorized |
| E14-S2-T5 | same | `GET /cp/component-runs?flow_run_id=X` — customer owns the flow run | Proxied list returned |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-test pytest src/CP/BackEnd/tests/api/test_cp_flow_runs.py -v --cov=src/CP/BackEnd/api/cp_flow_runs --cov-fail-under=80
```

**Commit message:** `feat(EXEC-ENGINE-001): E14-S2 — CP proxy routes for flow-runs and approvals`

**Done signal:**
`"E14-S2 done. Changed: src/CP/BackEnd/api/cp_flow_runs.py, main.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅ Coverage ≥ 80% ✅"`

> **⚠️ Merge E14-S2 to `main` NOW** (open PR `feat/EXEC-ENGINE-001-it6-e14 → main`, get it merged). Only then start E14-S1 DLQ panel.

---

#### Story E14-S1: PP DLQ panel — view, requeue, skip

**BLOCKED UNTIL:** E14-S2 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/EXEC-ENGINE-001-it6-e14`
**CP BackEnd pattern:** N/A — PP portal wires Plant Gateway directly; calls `GET /v1/dlq`, `POST /v1/dlq/{task_id}/requeue`, `POST /v1/dlq/{task_id}/skip`

**What to do:**
Create `frontend/pp-portal/pages/dlq.html` and `frontend/pp-portal/pages/dlq.js`. Render DLQ tasks as a list: task ID, agent name, step name, failure count, last error message, and action buttons (Requeue / Skip). Requeue is optimistic (disables buttons immediately). Skip requires a `confirm()` dialog. Auto-refresh badge count in PP nav. Empty DLQ shows a "Queue is clear" celebration message. Paginate at 50 items.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `frontend/pp-portal/components/ComponentRunRow.js` | 1–20 | Status class naming convention to be consistent |
| `frontend/pp-portal/pages/fleet.js` | 1–10 | `PP_API_BASE` convention |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `frontend/pp-portal/pages/dlq.html` | create | PP nav with DLQ badge, task list container, empty state, dark theme |
| `frontend/pp-portal/pages/dlq.js` | create | Fetch + render + requeue/skip actions as per code pattern below |

**Code patterns to copy exactly:**
```javascript
// frontend/pp-portal/pages/dlq.js
const API_BASE = window.PP_API_BASE || '';

function renderDlqItem(task) {
  const errMsg = task.last_error ? task.last_error.slice(0, 100) : 'No error detail';
  return `
<div class="dlq-item" data-task-id="${task.id}">
  <div class="dlq-item__info">
    <span class="dlq-item__id">#${task.id.slice(0, 8)}</span>
    <span class="dlq-item__agent">${task.agent_name}</span>
    <span class="dlq-item__step">${task.step_name}</span>
    <span class="dlq-item__failures">${task.failure_count}× failed</span>
    <p class="dlq-item__error" title="${task.last_error || ''}">${errMsg}…</p>
  </div>
  <div class="dlq-item__actions">
    <button class="btn btn--cyan" onclick="requeueTask('${task.id}', this)">Requeue</button>
    <button class="btn btn--red" onclick="skipTask('${task.id}')">Skip</button>
  </div>
</div>`;
}

async function loadDlq() {
  const res = await fetch(`${API_BASE}/v1/dlq?limit=50`);
  if (!res.ok) throw new Error('Failed to load DLQ');
  const tasks = await res.json();
  const container = document.getElementById('dlq-list');
  if (!tasks.length) {
    container.innerHTML = '<div class="empty-state empty-state--celebrate">🎉 Queue is clear — all agents running smoothly!</div>';
    return;
  }
  container.innerHTML = tasks.map(renderDlqItem).join('');
  updateNavBadge(tasks.length);
}

async function requeueTask(taskId, btn) {
  btn.disabled = true;
  btn.nextElementSibling.disabled = true;
  const res = await fetch(`${API_BASE}/v1/dlq/${taskId}/requeue`, { method: 'POST' });
  if (!res.ok) { btn.disabled = false; btn.nextElementSibling.disabled = false; alert('Requeue failed'); return; }
  document.querySelector(`[data-task-id="${taskId}"]`)?.remove();
}

async function skipTask(taskId) {
  if (!confirm('Skip this task permanently? It will not be retried.')) return;
  await fetch(`${API_BASE}/v1/dlq/${taskId}/skip`, { method: 'POST' });
  document.querySelector(`[data-task-id="${taskId}"]`)?.remove();
}

function updateNavBadge(count) {
  const badge = document.getElementById('dlq-badge');
  if (badge) { badge.textContent = count; badge.hidden = count === 0; }
}

document.addEventListener('DOMContentLoaded', () =>
  loadDlq().catch(err => { document.getElementById('dlq-list').innerHTML = `<p class="error">${err.message}</p>`; })
);
```

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E14-S1-T1 | `frontend/tests/pp-portal/test_dlq.spec.js` | Mock `GET /v1/dlq` returns 2 tasks | Two `dlq-item` elements rendered |
| E14-S1-T2 | same | Mock `POST /v1/dlq/{id}/requeue` returns 200, click Requeue | Buttons disabled immediately; item removed from DOM |
| E14-S1-T3 | same | `confirm()` returns false, click Skip | Item NOT removed; no API call made |
| E14-S1-T4 | same | Mock `GET /v1/dlq` returns empty array | "Queue is clear" celebration message displayed |
| E14-S1-T5 | same | Mock `GET /v1/dlq` returns HTTP 500 | Error message displayed in DLQ container |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-frontend-test npx jest frontend/tests/pp-portal/test_dlq.spec.js --forceExit
```

**Commit message:** `feat(EXEC-ENGINE-001): E14-S1 — PP DLQ panel view requeue skip`

**Done signal:**
`"E14-S1 done. Changed: frontend/pp-portal/pages/dlq.html, dlq.js. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅"`

**Epic E14 complete ✅** — run Docker integration test (Rule 5) before opening iteration PR.

---

### Iteration 6 — Completion Checkpoint

After ALL E12, E13, and E14 epics complete and Docker integration test passes:

```bash
git checkout main && git pull
git checkout -b feat/EXEC-ENGINE-001-it6
git merge --no-ff feat/EXEC-ENGINE-001-it6-e12 feat/EXEC-ENGINE-001-it6-e13 feat/EXEC-ENGINE-001-it6-e14
git push origin feat/EXEC-ENGINE-001-it6

gh pr create \
  --base main \
  --head feat/EXEC-ENGINE-001-it6 \
  --title "feat(EXEC-ENGINE-001): iteration 6 — PP portal UI + CP proxy routes" \
  --body "## EXEC-ENGINE-001 Iteration 6

### Stories completed
| E12-S1 | PP fleet dashboard with agent health map | 🟢 Done |
| E13-S1 | Per-agent health drill-in with ComponentRunRow | 🟢 Done |
| E14-S2 | CP proxy routes for flow-runs + approvals | 🟢 Done |
| E14-S1 | PP DLQ panel: view, requeue, skip | 🟢 Done |

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() on all new CP routes — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] 403 ownership check on all CP proxy routes before proxying
- [ ] Dark theme on PP portal pages
- [ ] Loading + error + empty states on all data-fetching screens
- [ ] Optimistic UI on Requeue (disables immediately)
- [ ] Skip requires confirm() guard"
```

Post PR URL. **EXEC-ENGINE-001 all 6 iterations complete — plan is fully implemented.**

---



---

## PM Review Checklist

- [x] Zero placeholders in published plan
- [x] Every story is self-contained (no "see above", exact file paths given)
- [x] NFR patterns embedded inline in relevant stories
- [x] Story size: all ≤ 90 min
- [x] Max 6 stories per iteration
- [x] Backend story precedes frontend counterpart in iteration ordering
- [x] UI stories specify component names, design tokens, data fields
- [x] Reusable components named and catalogued in summary table
- [x] P0 gaps closed by end of Iteration 2
- [x] P1 gaps closed by end of Iteration 2
- [x] P2 gaps closed by end of Iteration 4
- [x] Data persistence: every story that touches data includes Alembic migration or DB write as acceptance criterion
- [x] Approval gate: located in FlowDef, not AgentType or Goal (constitutional invariant)
- [x] Fan-out: parallel_steps in FlowDef, PARTIAL_FAILURE status in flow_run
- [x] `definition_version_id` pin on HiredAgent in Iteration 1
- [x] No in-memory stubs — all state in Postgres
- [x] CHECKPOINT RULE embedded in Agent Execution Rules
