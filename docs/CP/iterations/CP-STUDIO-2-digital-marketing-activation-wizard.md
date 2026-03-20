# CP-STUDIO-2 — Digital Marketing Activation Wizard Iteration Plan

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | CP-STUDIO-2 |
| Feature area | Customer Portal + Plant BackEnd — Digital Marketing activation wizard in My Agents |
| Created | 2026-03-18 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | docs/PP/AGENT-CONSTRUCT-DESIGN.md |
| Platform index | docs/CONTEXT_AND_INDEX.md (file map §13) |
| Total iterations | 2 |
| Total epics | 2 |
| Total stories | 10 |

## Vision Intake

- Area: CP FrontEnd My Agents wizard for Digital Marketing hires, with CP BackEnd as thin proxy and Plant BackEnd owning business logic and persistence.
- Outcome: A customer selects an already-hired Digital Marketing agent, completes induction and platform preparation, generates a master theme plus derived themes, confirms schedule, and leaves the hire runtime-ready with persisted state.
- Out of scope: Share Trader activation, generic multi-agent studio abstraction, unrelated payments/catalog redesign, and non-Digital-Marketing runtime behavior changes.
- Lane: Lane B first, because Plant needs new persisted activation state and wizard/theme endpoints; CP BackEnd remains proxy-only.
- Timeline: Two iterations sized for end-to-end delivery, with backend-first ordering and direct Cloud SQL demo DDL during story execution instead of Alembic authoring.

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story is self-contained, names exact files, and embeds the only patterns needed |
| No working memory across files | Files to read first are capped at 3 and story cards repeat the key runtime assumptions |
| Weak mid-flight planning | Stories are linear, atomic, and branch-scoped inside one epic per iteration |
| Token cost per read | Existing reusable files are named explicitly; no “find the file that does X” instructions |
| Binary success bias | Acceptance criteria and tests are observable pass/fail behaviors only |

## PM Review Checklist (tick every box before publishing)

- [x] EXPERT PERSONAS filled
- [x] Epic title names a customer outcome, not a technical action
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant code snippets inline
- [x] Every story card has max 3 files in Files to read first
- [x] Every CP story states the exact pattern: A, B, C, or N/A
- [x] Every new backend route story embeds waooaw_router when needed
- [x] Every GET route story says get_read_db_session when needed
- [x] Every story that adds env vars lists exact Terraform file paths to update when needed
- [x] Every story has BLOCKED UNTIL or none
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Stories are sequenced so dependencies stay on the same branch
- [x] Iteration count minimized for PR-only delivery
- [x] Related activation, theme generation, and schedule confirmation work kept in one plan
- [x] No placeholders remain

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Persist Digital Marketing activation state and deliver the hire-first Induct Agent + Prepare Agent wizard inside My Agents | 1 | 5 | 8h | 2026-03-19 02:00 UTC |
| 2 | Generate master and derived themes through Grok, confirm schedule, and prove the full runtime-ready journey | 1 | 5 | 8h | 2026-03-20 02:00 UTC |

**Estimate basis:** Plant DB/API story = 90 min | CP proxy story = 45 min | CP FE studio story = 60–90 min | regression story = 60 min | 20% buffer included.

### PR-Overhead Optimization Rules

- One epic per iteration keeps branch and review overhead low while preserving a real user-visible checkpoint.
- Backend-first work stays in the same iteration branch so the frontend agent is not blocked on a separate planning round.
- Direct Cloud SQL demo DDL is bundled inside the backend persistence story, then validated again in the regression story.

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show the plan file on disk and no unexpected merge-conflict state.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel and select Agent mode
4. Click `+` to start a new agent session
5. Type `@` and select `platform-engineer`
6. Paste the block below and press Enter
7. Go away and come back at 2026-03-19 02:00 UTC

**Iteration 1 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite engineer + Senior FastAPI / SQLAlchemy / PostgreSQL engineer + Senior product UX engineer
Activate these personas NOW. Begin the epic with:
  "Acting as a senior React, FastAPI, and UX engineer, I will implement CP-STUDIO-2 Iteration 1 exactly as written and validate each story with its listed tests before moving on."

PLAN FILE: docs/CP/iterations/CP-STUDIO-2-digital-marketing-activation-wizard.md
YOUR SCOPE: Iteration 1 only — Epic E1. Do not invent more epics or stories.
TIME BUDGET: 8h. If you reach 9h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
2. Read the Agent Execution Rules section in this plan file.
3. Read the Iteration 1 section in this plan file.
4. Read nothing else before starting.
5. Execute stories in this order: E1-S1 -> E1-S2 -> E1-S3 -> E1-S4 -> E1-S5.
6. When all story tests pass, open the iteration PR, post the PR URL, and HALT.
```

### Iteration 2

**Pre-flight check (run in terminal before launching):**
```bash
git fetch origin
git show origin/main:docs/CP/iterations/CP-STUDIO-2-digital-marketing-activation-wizard.md | grep "## Iteration 2"
# Must return the Iteration 2 heading from main before launching.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel and select Agent mode
4. Click `+` to start a new agent session
5. Type `@` and select `platform-engineer`
6. Paste the block below and press Enter
7. Go away and come back at 2026-03-20 02:00 UTC

**Iteration 2 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite engineer + Senior FastAPI / SQLAlchemy / PostgreSQL engineer + Senior AI integration engineer
Activate these personas NOW. Begin the epic with:
  "Acting as a senior React, FastAPI, and AI integration engineer, I will implement CP-STUDIO-2 Iteration 2 exactly as written and validate each story with its listed tests before moving on."

PLAN FILE: docs/CP/iterations/CP-STUDIO-2-digital-marketing-activation-wizard.md
YOUR SCOPE: Iteration 2 only — Epic E2. Do not invent more epics or stories.
TIME BUDGET: 8h. If you reach 9h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
2. Read the Agent Execution Rules section in this plan file.
3. Read the Iteration 2 section in this plan file.
4. Read nothing else before starting.
5. Execute stories in this order: E2-S1 -> E2-S2 -> E2-S3 -> E2-S4 -> E2-S5.
6. When all story tests pass, open the iteration PR, post the PR URL, and HALT.
```

## Agent Execution Rules

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the EXPERT PERSONAS field from the task and activate them before any code changes.

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
git checkout -b feat/cp-studio-2-it[1-or-2]-e[1-or-2]
git commit --allow-empty -m "chore(cp-studio-2): start iteration [1-or-2]"
git push origin feat/cp-studio-2-it[1-or-2]-e[1-or-2]

gh pr create \
  --base main \
  --head feat/cp-studio-2-it[1-or-2]-e[1-or-2] \
  --draft \
  --title "tracking: CP-STUDIO-2 Iteration [1-or-2] — in progress" \
  --body "## tracking: CP-STUDIO-2 Iteration [1-or-2]

### Stories
- [ ] Story 1
- [ ] Story 2
- [ ] Story 3
- [ ] Story 4
- [ ] Story 5

_Live updates posted as comments below._"
```

### Rule 1 — Branch discipline

One iteration equals one branch. All five stories in that iteration commit sequentially to the same branch.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card. Do not refactor unrelated CP pages, Plant runtime code, or generic marketplace screens.

### Rule 3 — Tests before the next story

Write every test in the story card before moving to the next story. Run the exact command listed in the story card.

### Rule 4 — Commit + push + notify after every story

```bash
git add -A
git commit -m "feat(cp-studio-2): complete current story"
git push origin $(git branch --show-current)

gh pr comment \
  $(gh pr list --head $(git branch --show-current) --json number -q '.[0].number') \
  --body "✅ Current story done — $(git rev-parse --short HEAD)
Files changed: see commit diff
Tests: current story test command passed
Next: proceed to the next story in plan order"
```

### Rule 5 — Docker integration test after every epic

```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest src/Plant/BackEnd/tests/unit -q --maxfail=1 --no-cov
docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest src/CP/BackEnd/tests -q --maxfail=1 --no-cov
```

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)

If the same story fails three times, stop immediately. Post the blocker, exact failing command, and the smallest missing decision needed from a human.

### Rule 7 — Iteration PR (after ALL stories complete)

Open or update the PR only after every story in that iteration passes its listed tests and the Cloud SQL demo smoke query succeeds.

### CHECKPOINT RULE

> **CHECKPOINT RULE**: After completing each epic (all tests passing), run:
> ```bash
> git add -A && git commit -m "feat([plan-id]): [epic-id] — [epic title]" && git push
> ```
> Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

## NFR Quick Reference

| Rule | Exact requirement |
|---|---|
| Router | Use `waooaw_router()` for every new Plant or CP API file |
| GET DB access | Use `get_read_db_session()` for GET routes in Plant |
| Logging | Add `PiiMaskingFilter` / `PiiMaskingFilter()` and never log raw brand/customer data or credentials |
| Correlation | Preserve `X-Correlation-ID` through CP FE -> CP BE -> Plant |
| Secrets | Store raw platform or AI secrets in GCP Secret Manager only; DB stores opaque refs only |
| Persistence truth | Apply DDL against demo Cloud SQL through the Auth Proxy, then smoke-check with `psql`; Docker Postgres is regression-only |
| CP boundary | CP BackEnd stays thin proxy only; Plant owns business logic and persistence |
| Promotion | Do not hardcode environment-specific config in code or Dockerfiles |

## Tracking Table

| Story | Branch | Status | Notes |
|---|---|---|---|
| E1-S1 | `feat/cp-studio-2-it1-e1` | Planned | Plant persistence + direct demo SQL |
| E1-S2 | `feat/cp-studio-2-it1-e1` | Planned | Plant APIs + CP thin proxies |
| E1-S3 | `feat/cp-studio-2-it1-e1` | Planned | CP FE service layer |
| E1-S4 | `feat/cp-studio-2-it1-e1` | Planned | Hire-first shell + help toggle + induction |
| E1-S5 | `feat/cp-studio-2-it1-e1` | Planned | Prepare Agent step + save/resume |
| E2-S1 | `feat/cp-studio-2-it2-e2` | Planned | Campaign persistence reuse for theme plans |
| E2-S2 | `feat/cp-studio-2-it2-e2` | Planned | Grok generation APIs + CP thin proxies |
| E2-S3 | `feat/cp-studio-2-it2-e2` | Planned | Master theme + derived theme UI |
| E2-S4 | `feat/cp-studio-2-it2-e2` | Planned | Schedule confirmation + runtime handoff |
| E2-S5 | `feat/cp-studio-2-it2-e2` | Planned | Full regression + demo DB smoke + browser verification |

## Iteration 1 — Hire-First Activation Foundations

**Scope:** Persist the Digital Marketing wizard state and let the customer finish Induct Agent and Prepare Agent inside My Agents without losing progress.
**Lane:** B
**⏱ Estimated:** 8h | **Come back:** 2026-03-19 02:00 UTC
**Epics:** E1

### Dependency Map (Iteration 1)

```text
E1-S1 -> E1-S2 -> E1-S3 -> E1-S4 -> E1-S5
```

---

### Epic E1: Customer can reopen a Digital Marketing activation draft and finish induction/platform readiness without losing progress

**Branch:** `feat/cp-studio-2-it1-e1`
**User story:** As a customer with a hired Digital Marketing agent, I can reopen my setup draft in My Agents and complete induction plus platform readiness in a single flow, so that I never lose setup progress.

---

#### Story E1-S1: Persist the activation workspace in existing Plant hired-agent records

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-2-it1-e1`
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> Reuse existing persistence instead of inventing new tables. `src/Plant/BackEnd/models/hired_agent.py` lines 17–58 already provide the JSONB `config` column, and `src/Plant/BackEnd/repositories/hired_agent_repository.py` lines 49–145 already upsert that payload. Add a canonical `digital_marketing_activation` object inside `config` with these keys: `selected_hire`, `help_visible`, `current_step`, `induct_agent`, `prepare_agent`, `campaign_setup`, and `last_completed_step`; add repository helpers that read and patch that envelope without overwriting unrelated config, then prove the exact row shape against demo Cloud SQL through the Auth Proxy before and after the code change.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/models/hired_agent.py` | 17–117 | Existing `config` JSONB field and hired-agent model shape |
| `src/Plant/BackEnd/repositories/hired_agent_repository.py` | 49–145 | Existing `draft_upsert()` update path that writes `config` |
| `docs/CONTEXT_AND_INDEX.md` | 1054–1172 | Cloud SQL Auth Proxy workflow and direct `psql` migration/query rules |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/repositories/hired_agent_repository.py` | modify | Add `get_activation_workspace()` and `update_activation_workspace()` helpers that read/write only `config.digital_marketing_activation` and preserve existing config keys |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | modify | Add pure helper functions that normalize the activation workspace payload and reuse them later from the new activation API file |
| `src/Plant/BackEnd/tests/integration/test_hired_agent_repository.py` | modify | Add repository coverage proving activation workspace patching is idempotent and does not erase unrelated config |
| `src/Plant/BackEnd/tests/unit/test_digital_marketing_activation_workspace.py` | create | Add normalization and merge tests for the new workspace helper functions |

**Code patterns to copy exactly** (no other file reads needed for these):

```python
# Merge a JSONB workspace without dropping unrelated config keys.
def merge_activation_workspace(
    config: dict[str, Any] | None,
    workspace_patch: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(config or {})
    current = dict(merged.get("digital_marketing_activation") or {})
    current.update(workspace_patch)
    merged["digital_marketing_activation"] = current
    return merged
```

```bash
# Mandatory live DB truth check before and after repository changes.
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh
source /root/.env.db && psql -c "SELECT hired_instance_id, jsonb_typeof(config), config->'digital_marketing_activation' FROM hired_agents LIMIT 5;"
```

**Acceptance criteria (binary pass/fail only):**
1. A hired-agent record can persist `config.digital_marketing_activation` without changing unrelated config keys.
2. Re-saving only `prepare_agent` state does not erase `induct_agent` or `campaign_setup` state.
3. The repository integration test passes against Docker Postgres, and the live demo `psql` smoke query shows the persisted JSON object for a real hired instance.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/unit/test_digital_marketing_activation_workspace.py` | Existing config includes unrelated keys plus a partial workspace | Merge keeps unrelated keys and updates only the workspace subtree |
| E1-S1-T2 | same | Reapply the same patch twice | Output is stable and idempotent |
| E1-S1-T3 | `src/Plant/BackEnd/tests/integration/test_hired_agent_repository.py` | Upsert hired agent, then patch activation workspace | Reloaded row contains the expected JSON subtree |
| E1-S1-T4 | live demo DB smoke | Query a real hired-agent row through `psql` | `config->'digital_marketing_activation'` returns JSON, not null, after save |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test \
  pytest src/Plant/BackEnd/tests/unit/test_digital_marketing_activation_workspace.py \
         src/Plant/BackEnd/tests/integration/test_hired_agent_repository.py -v --no-cov
```

**Commit message:** `feat(cp-studio-2): persist dma activation workspace`

**Done signal (post as a comment then continue to E1-S2):**
`"E1-S1 done. Changed: hired_agent_repository + hired_agents_simple workspace helpers + tests. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S2: Expose Plant activation APIs and CP thin-proxy routes for the wizard

**BLOCKED UNTIL:** E1-S1 committed to `feat/cp-studio-2-it1-e1`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-2-it1-e1` (same branch, continue from E1-S1)
**CP BackEnd pattern:** B — create new `api/digital_marketing_activation.py` thin proxy file

**What to do:**
> Create a dedicated Plant API file for the wizard instead of overloading the generic hired-agents routes. `src/Plant/BackEnd/api/v1/hired_agents_simple.py` lines 1–240 already own hired-agent draft persistence, and `src/CP/BackEnd/api/hired_agents_proxy.py` lines 1–240 already show the current proxy style. Add Plant endpoints under `/api/v1/digital-marketing-activation/{hired_instance_id}` for `GET workspace`, `PATCH workspace`, and `POST platform-step/complete`, then add a new CP BackEnd proxy file under `/api/cp/digital-marketing-activation/...` that forwards those routes with correlation ID and auth preserved.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | 1–240 | Existing hired-agent request/response models and DB session patterns |
| `src/CP/BackEnd/api/hired_agents_proxy.py` | 1–240 | Thin proxy pattern, error mapping, correlation forwarding |
| `src/CP/BackEnd/main.py` | 1–114 | Router registration order before the catch-all `/api/{path:path}` proxy |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | create | Add `GET /digital-marketing-activation/{hired_instance_id}`, `PATCH /digital-marketing-activation/{hired_instance_id}`, and `POST /digital-marketing-activation/{hired_instance_id}/platform-steps/{platform_key}/complete` backed by the E1-S1 repository helpers |
| `src/Plant/BackEnd/api/v1/router.py` or relevant registration file | modify | Register the new Plant route so it is reachable through the gateway |
| `src/CP/BackEnd/api/digital_marketing_activation.py` | create | Add CP thin proxy routes mirroring the new Plant endpoints |
| `src/CP/BackEnd/main.py` | modify | Include the new proxy router before the catch-all `/api/{path:path}` route |
| `src/Plant/BackEnd/tests/unit/test_digital_marketing_activation_api.py` | create | Add route coverage for GET/PATCH/complete |
| `src/CP/BackEnd/tests/test_digital_marketing_activation_proxy.py` | create | Add proxy route coverage |

**Code patterns to copy exactly:**

```python
from core.routing import waooaw_router
from core.database import get_read_db_session, get_db_session
from fastapi import Depends

router = waooaw_router(prefix="/digital-marketing-activation", tags=["digital-marketing-activation"])

@router.get("/{hired_instance_id}")
async def get_workspace(hired_instance_id: str, db=Depends(get_read_db_session)):
    ...

@router.patch("/{hired_instance_id}")
async def patch_workspace(hired_instance_id: str, body: WorkspacePatchRequest, db=Depends(get_db_session)):
    ...
```

```python
from core.routing import waooaw_router
from fastapi import Depends, Request

router = waooaw_router(prefix="/cp/digital-marketing-activation", tags=["cp-digital-marketing-activation"])

@router.get("/{hired_instance_id}")
async def get_workspace(hired_instance_id: str, request: Request, current_user=Depends(get_current_user)):
    ...
```

**Acceptance criteria:**
1. Plant `GET /api/v1/digital-marketing-activation/{hired_instance_id}` returns the normalized wizard workspace for a valid hired instance.
2. Plant `PATCH` saves partial workspace updates without erasing existing sections.
3. CP `GET/PATCH` proxy routes return the same shape and preserve `X-Correlation-ID`.
4. Missing hired instance returns 404, and upstream network failure maps to CP 502.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/Plant/BackEnd/tests/unit/test_digital_marketing_activation_api.py` | Seed hired agent with saved workspace | GET returns normalized sections and current step |
| E1-S2-T2 | same | PATCH only `induct_agent.nickname` | Saved workspace still contains existing `prepare_agent` state |
| E1-S2-T3 | `src/CP/BackEnd/tests/test_digital_marketing_activation_proxy.py` | Mock Plant 200 | CP response is 200 and shape matches |
| E1-S2-T4 | same | Mock Plant network error | CP returns 502 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test \
  pytest src/Plant/BackEnd/tests/unit/test_digital_marketing_activation_api.py -v --no-cov

docker compose -f docker-compose.test.yml run --rm cp-backend-test \
  pytest src/CP/BackEnd/tests/test_digital_marketing_activation_proxy.py -v --no-cov
```

**Commit message:** `feat(cp-studio-2): add dma activation apis`

**Done signal:** `"E1-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S3: Add the CP FrontEnd data layer for activation workspace, hire selection, and platform sequencing

**BLOCKED UNTIL:** E1-S2 committed to `feat/cp-studio-2-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/cp-studio-2-it1-e1` (same branch, continue from E1-S2)
**CP BackEnd pattern:** A — call the new `/cp/digital-marketing-activation/*` routes with `gatewayRequestJson`

**What to do:**
> Create one dedicated frontend service instead of pushing wizard fetch logic into `MyAgents.tsx`. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` lines 1–31 already provide the list surface, `src/CP/FrontEnd/src/services/platformConnections.service.ts` lines 1–138 already provide platform connection helpers, and `src/CP/FrontEnd/src/services/agentSkills.service.ts` lines 1–99 already expose the digital-marketing skill helpers. Add `digitalMarketingActivation.service.ts` with typed `getWorkspace`, `patchWorkspace`, and `completePlatformStep` functions, plus selector helpers that combine selected-platform ordering and existing connection state into a one-platform-at-a-time sequence.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` | 1–31 | Existing summary types for hired instances |
| `src/CP/FrontEnd/src/services/platformConnections.service.ts` | 1–138 | Existing platform connection DTOs and summary helpers |
| `src/CP/FrontEnd/src/services/agentSkills.service.ts` | 1–99 | Digital Marketing agent helpers and goal schema types |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | create | Add typed workspace contracts, API calls, and helpers for next pending platform step |
| `src/CP/FrontEnd/src/test/digitalMarketingActivation.service.test.ts` | create | Add service contract and sequencing helper tests |

**Code patterns to copy exactly:**

```typescript
import { gatewayRequestJson } from './gatewayApiClient'

export async function getDigitalMarketingActivationWorkspace(hiredInstanceId: string) {
  return gatewayRequestJson(`/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`)
}

export async function patchDigitalMarketingActivationWorkspace(hiredInstanceId: string, patch: unknown) {
  return gatewayRequestJson(`/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}
```

**Acceptance criteria:**
1. The service can fetch and patch the activation workspace with typed contracts.
2. The sequencing helper returns the next selected platform that is not yet complete.
3. The helper treats an already connected platform as ready only when the workspace marks the step complete.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S3-T1 | `src/CP/FrontEnd/src/test/digitalMarketingActivation.service.test.ts` | Mock `gatewayRequestJson` for GET | Workspace call hits the expected CP route |
| E1-S3-T2 | same | Mock PATCH payload | Body contains only the partial workspace patch |
| E1-S3-T3 | same | Selected platforms `[youtube, instagram]`, youtube complete | Helper returns instagram as next step |

**Test command:**
```bash
docker run --rm -v "$PWD/src/CP/FrontEnd:/app" -w /app node:20-bookworm \
  sh -lc "npm ci && npm run test:run -- src/test/digitalMarketingActivation.service.test.ts"
```

**Commit message:** `feat(cp-studio-2): add dma activation frontend service`

**Done signal:** `"E1-S3 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E1-S4: Build the hire-first wizard shell with header help toggle and Induct Agent step

**BLOCKED UNTIL:** E1-S3 committed to `feat/cp-studio-2-it1-e1`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-2-it1-e1` (same branch, continue from E1-S3)
**CP BackEnd pattern:** A — consume the activation workspace service created in E1-S3

**What to do:**
> Convert the Digital Marketing path in `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` from the current generic configure panel into a hire-first wizard shell. The current file lines 1–260 already import most of the data services and establish the page-level state; use that file to add a Digital Marketing-specific wizard entry that requires selecting the hired instance first, persists `help_visible`, and renders the two red-box help zones from the user’s spec only when the header control says `Show Help`. The Induct Agent step must save nickname, theme, primary language, timezone, brand name, offerings/services, and location into the activation workspace, not into transient component-only state.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1–260 | Current page imports, page state, and configure panel scaffolding |
| `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | 1–240 | Existing render harness and navigation mocking pattern |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | 1–220 | New workspace contract from E1-S3 |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Add a Digital Marketing wizard path with hire selector, milestone header, `Show Help/Hide Help` toggle, and the full Induct Agent form bound to workspace state |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | create | Extract the Digital Marketing-specific step shell and form sections out of `MyAgents.tsx` once the page wiring exists |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | create | Add component-level coverage for help toggle, hire-first gating, and persisted induction field hydration |

**Code patterns to copy exactly:**

```typescript
const [workspace, setWorkspace] = useState<DigitalMarketingActivationWorkspace | null>(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  if (!selectedHiredInstanceId) return
  getDigitalMarketingActivationWorkspace(selectedHiredInstanceId)
    .then(setWorkspace)
    .catch(() => setError('Failed to load activation workspace.'))
    .finally(() => setLoading(false))
}, [selectedHiredInstanceId])
```

**Acceptance criteria:**
1. No Digital Marketing setup form appears until the user selects a hired instance.
2. Clicking `Show Help` reveals both help areas; clicking `Hide Help` hides both areas.
3. Refreshing after saving induction data reloads the same values from the workspace API.
4. The milestone labels are exactly `Induct Agent`, `Prepare Agent`, `Master Theme`, and `Confirm Schedule`.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S4-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Render Digital Marketing hire with no selected instance | Form is gated behind hire selection |
| E1-S4-T2 | same | Toggle help button twice | Both help panels appear then disappear |
| E1-S4-T3 | same | Mock workspace load with saved induction data | Inputs hydrate with saved values |
| E1-S4-T4 | same | Inspect milestone header | Labels match the exact required text |

**Test command:**
```bash
docker run --rm -v "$PWD/src/CP/FrontEnd:/app" -w /app node:20-bookworm \
  sh -lc "npm ci && npm run test:run -- src/test/MyAgentsDigitalMarketingWizard.test.tsx src/test/MyAgents.test.tsx"
```

**Commit message:** `feat(cp-studio-2): add dma induct agent step`

**Done signal:** `"E1-S4 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S5: Build the Prepare Agent step with selected-platform sequencing and save/resume proof

**BLOCKED UNTIL:** E1-S4 committed to `feat/cp-studio-2-it1-e1`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-2-it1-e1` (same branch, continue from E1-S4)
**CP BackEnd pattern:** A — reuse the activation workspace service and existing platform connection routes

**What to do:**
> Extend the Digital Marketing wizard to drive the `Prepare Agent` milestone one selected platform at a time. `src/CP/FrontEnd/src/services/platformConnections.service.ts` lines 1–138 already expose connection state, and `src/Plant/BackEnd/api/v1/platform_connections.py` lines 1–300 already support secret-ref/customer-credential-backed connections. Use the selected platform list saved in the workspace to render one step per platform, mark a platform complete only after the relevant connection action succeeds, and allow the user to leave and resume with the next incomplete platform highlighted.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/platformConnections.service.ts` | 1–138 | Existing create/list/delete helpers and readiness summaries |
| `src/Plant/BackEnd/api/v1/platform_connections.py` | 1–300 | Supported connection models and YouTube attach flow |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1–260 | Existing page state you extended in E1-S4 |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Add platform checklist cards, one-platform-at-a-time navigation, and completion actions |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Add step-completion and resume coverage |
| `src/CP/FrontEnd/e2e/digital-marketing-activation.spec.ts` | create | Add browser flow covering hire select -> help toggle -> induction save -> platform step resume |

**Code patterns to copy exactly:**

```typescript
const nextPlatform = getNextPendingPlatform(workspace.prepare_agent.selected_platforms, workspace.prepare_agent.platform_steps)

if (!nextPlatform) {
  return <div>All selected platforms are prepared.</div>
}
```

**Acceptance criteria:**
1. The wizard shows platform steps only for the platforms the user selected during induction.
2. Completing one platform advances the wizard to the next incomplete selected platform.
3. Reloading the page restores completed platform steps and focuses the next incomplete platform.
4. YouTube can use the existing connection/attach flow, while non-OAuth platforms save through the generic connection route without storing raw secrets in the frontend.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S5-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Workspace selected platforms are youtube + instagram | Only those two steps render |
| E1-S5-T2 | same | First step completes | Second selected platform becomes active |
| E1-S5-T3 | same | Reload with first platform complete | Wizard resumes on the second platform |
| E1-S5-T4 | `src/CP/FrontEnd/e2e/digital-marketing-activation.spec.ts` | Browser journey with mocked API | Save/resume works end to end |

**Test command:**
```bash
docker run --rm -v "$PWD/src/CP/FrontEnd:/work" -w /work mcr.microsoft.com/playwright:v1.57.0-noble \
  sh -lc "npm ci && npm run test:run -- src/test/MyAgentsDigitalMarketingWizard.test.tsx && npm run test:e2e -- e2e/digital-marketing-activation.spec.ts"
```

**Commit message:** `feat(cp-studio-2): add dma prepare agent step`

**Done signal:** `"E1-S5 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

## Iteration 2 — Theme Generation And Schedule Confirmation

**Scope:** Reuse the Plant campaign runtime to generate a master theme, persist derived themes, confirm schedule, and leave the hire runtime-ready.
**Lane:** B
**⏱ Estimated:** 8h | **Come back:** 2026-03-20 02:00 UTC
**Prerequisite:** Iteration 1 merged to `main`
**Epics:** E2

### Dependency Map (Iteration 2)

```text
E2-S1 -> E2-S2 -> E2-S3 -> E2-S4 -> E2-S5
```

---

### Epic E2: Customer can generate a master theme, review derived themes, confirm schedule, and leave the agent runtime-ready

**Branch:** `feat/cp-studio-2-it2-e2`
**User story:** As a customer with a prepared Digital Marketing hire, I can generate a master theme, inspect the derived plan, confirm cadence, and finish setup with a runtime-ready campaign.

---

#### Story E2-S1: Reuse the existing Plant campaign runtime to persist master-theme and derived-theme setup

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-2-it2-e2`
**CP BackEnd pattern:** N/A

**What to do:**
> Do not invent a second theme system. `src/Plant/BackEnd/agent_mold/skills/content_models.py` lines 90–184 already define `CampaignBrief`, `ThemeDiscoveryBrief`, cadence, approval mode, and destination data; `src/Plant/BackEnd/models/campaign.py` lines 1–120 already persist the campaign brief and runtime summary; and `src/Plant/BackEnd/repositories/campaign_repository.py` lines 1–140 already create/update campaigns. Extend the existing campaign brief mapping so the activation wizard can persist the master theme into `brief.theme`, the derived themes into `daily_theme_items`, and the customer’s cadence/schedule preferences into `brief.theme_discovery.posting_cadence` and `brief.schedule`, with one draft campaign per hired instance during setup.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | 90–184 | Existing `CampaignBrief`, `PostingSchedule`, and `ThemeDiscoveryBrief` contracts |
| `src/Plant/BackEnd/models/campaign.py` | 1–120 | Existing persisted campaign, theme item, and runtime summary fields |
| `src/Plant/BackEnd/repositories/campaign_repository.py` | 1–140 | Existing create/update campaign repository methods |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/repositories/campaign_repository.py` | modify | Add helper methods to find the active draft campaign by `hired_instance_id`, replace its theme items, and update the brief summary in one transaction |
| `src/Plant/BackEnd/api/v1/campaigns.py` | modify | Add internal helper functions that map activation wizard fields into the existing campaign brief model |
| `src/Plant/BackEnd/tests/unit/test_campaign_repository.py` | modify | Add repository coverage for “one draft campaign per hired instance” and theme-item replacement |
| `src/Plant/BackEnd/tests/test_campaigns_api_db.py` | modify | Add DB-backed coverage for the new mapping helpers |

**Code patterns to copy exactly:**

```python
campaign = await repo.create_campaign(
    hired_instance_id=hired_instance_id,
    customer_id=customer_id,
    brief=brief.model_dump(mode="json"),
    cost_estimate=estimate_cost(brief).model_dump(mode="json"),
)
```

**Acceptance criteria:**
1. A Digital Marketing hire can have exactly one draft setup campaign reused across repeated theme-generation edits.
2. Saving a new master theme replaces the draft campaign’s theme items instead of creating duplicate draft campaigns.
3. The persisted campaign brief stores cadence and schedule fields needed for the final confirmation step.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/Plant/BackEnd/tests/unit/test_campaign_repository.py` | Create two draft updates for the same hired instance | Repository returns a single draft campaign id |
| E2-S1-T2 | same | Replace theme items for an existing draft | Old theme items are removed and new ones persist |
| E2-S1-T3 | `src/Plant/BackEnd/tests/test_campaigns_api_db.py` | Build campaign brief from activation payload | Persisted brief contains theme, cadence, and destination data |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test \
  pytest src/Plant/BackEnd/tests/unit/test_campaign_repository.py \
         src/Plant/BackEnd/tests/test_campaigns_api_db.py -v --no-cov
```

**Commit message:** `feat(cp-studio-2): reuse campaign runtime for dma setup`

**Done signal:** `"E2-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E2-S2: Add Grok-backed theme-generation APIs in Plant and thin proxies in CP

**BLOCKED UNTIL:** E2-S1 committed to `feat/cp-studio-2-it2-e2`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-2-it2-e2` (same branch, continue from E2-S1)
**CP BackEnd pattern:** B — create a new CP proxy file for the theme-generation surface

**What to do:**
> Add a dedicated activation-generation API instead of forcing the frontend to compose multiple campaign endpoints. `src/Plant/BackEnd/agent_mold/skills/grok_client.py` lines 1–29 already provide the Grok client using `XAI_API_KEY`, and `src/Plant/BackEnd/api/v1/campaigns.py` lines 1–260 already own campaign orchestration. Create Plant routes for `POST /digital-marketing-activation/{hired_instance_id}/generate-theme-plan` and `PATCH /digital-marketing-activation/{hired_instance_id}/theme-plan`, where the first call uses Grok to propose one master theme plus derived themes based on the saved induction/platform data, then persists the result into the reused campaign draft from E2-S1. Add CP proxy routes under `/api/cp/digital-marketing-activation/...` for those endpoints, and only touch Terraform secret wiring if demo/uat/prod do not already inject `XAI_API_KEY`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/grok_client.py` | 1–29 | Existing Grok client contract and `XAI_API_KEY` handling |
| `src/Plant/BackEnd/api/v1/campaigns.py` | 1–260 | Existing campaign creation and runtime enrichment flow |
| `src/CP/BackEnd/api/campaigns.py` | 1–220 | Existing CP campaign proxy patterns |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | Add `generate-theme-plan` and `theme-plan` update routes on top of the workspace API created in Iteration 1 |
| `src/Plant/BackEnd/tests/unit/test_digital_marketing_theme_generation_api.py` | create | Mock Grok and verify persistence mapping |
| `src/CP/BackEnd/api/digital_marketing_activation.py` | modify | Add matching CP thin proxy routes |
| `src/CP/BackEnd/tests/test_digital_marketing_activation_proxy.py` | modify | Add proxy tests for the generation endpoints |
| `cloud/terraform/stacks/plant/main.tf` | modify only if required | If `XAI_API_KEY` is missing from runtime env injection, wire it from Secret Manager here |
| `cloud/terraform/stacks/plant/variables.tf` | modify only if required | Add only the minimal variable needed for `XAI_API_KEY` pass-through |
| `cloud/terraform/stacks/plant/environments/demo.tfvars` | modify only if required | Add only the demo secret binding if absent |

**Code patterns to copy exactly:**

```python
client = get_grok_client()
proposal = grok_complete(
    client,
    system="You are a digital marketing strategist creating one master theme and a short list of derived campaign themes.",
    user=prompt_text,
    model="grok-3-latest",
    temperature=0.7,
)
```

```python
logger.addFilter(PiiMaskingFilter())
# Never log raw prompt bodies containing brand or platform credential details.
```

**Acceptance criteria:**
1. Plant can generate a theme plan from saved induction/workspace data with Grok mocked in tests.
2. The generated master theme and derived themes persist into the reused campaign draft.
3. CP proxy routes expose the same response shape and preserve correlation IDs.
4. No raw secret values are written to logs, frontend state snapshots, or database rows.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/Plant/BackEnd/tests/unit/test_digital_marketing_theme_generation_api.py` | Mock Grok returns a master theme + 3 derived themes | Response contains master theme and three persisted derived themes |
| E2-S2-T2 | same | Existing draft campaign already exists | Endpoint updates the draft instead of creating a second draft |
| E2-S2-T3 | `src/CP/BackEnd/tests/test_digital_marketing_activation_proxy.py` | Mock Plant 200 for generation route | CP returns 200 with identical payload |
| E2-S2-T4 | same | Mock missing `XAI_API_KEY` path or upstream failure | CP returns surfaced error without leaking secret values |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test \
  pytest src/Plant/BackEnd/tests/unit/test_digital_marketing_theme_generation_api.py -v --no-cov

docker compose -f docker-compose.test.yml run --rm cp-backend-test \
  pytest src/CP/BackEnd/tests/test_digital_marketing_activation_proxy.py -v --no-cov
```

**Commit message:** `feat(cp-studio-2): add dma grok theme generation`

**Done signal:** `"E2-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E2-S3: Build the Master Theme step with derived-theme review and revision loop

**BLOCKED UNTIL:** E2-S2 committed to `feat/cp-studio-2-it2-e2`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-2-it2-e2` (same branch, continue from E2-S2)
**CP BackEnd pattern:** A — consume the activation and generation routes from the frontend service layer

**What to do:**
> Add the `Master Theme` milestone UI to the Digital Marketing wizard. The step must collect or display the AI-suggested master theme, render the derived themes/frequency breakdown from the persisted draft campaign, allow the customer to regenerate or manually revise, and keep the header help-toggle behavior consistent with Iteration 1. Do not build a disconnected local-only editor; every accepted change must round-trip through the activation/generation APIs and reload the persisted state.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1–260 | The wizard shell introduced in Iteration 1 |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1–260 | The current wizard step rendering from E1-S4/E1-S5 |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | 1–220 | Theme-generation and workspace contracts |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Add the `Master Theme` step with generate, regenerate, edit, approve, and derived-theme list rendering |
| `src/CP/FrontEnd/src/components/DigitalMarketingThemePlanCard.tsx` | create | Extract the theme plan summary rendering and revision actions |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Add generation and revision-loop coverage |

**Code patterns to copy exactly:**

```typescript
if (loading) return <LoadingIndicator message="Generating theme plan..." size="small" />
if (error) return <FeedbackMessage intent="error" title="Theme plan unavailable" message={error} />
```

**Acceptance criteria:**
1. The `Master Theme` step can generate a plan from persisted induction/workspace data.
2. The step renders one master theme plus the persisted list of derived themes.
3. Regenerating or manually revising the plan updates the persisted backend state and survives refresh.
4. The help toggle still controls both help panels in this step.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S3-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Mock generate API success | Master theme and derived themes render |
| E2-S3-T2 | same | Mock manual edit save | Refresh reads the edited theme back |
| E2-S3-T3 | same | Toggle help in Master Theme step | Both help panels respond to the toggle |

**Test command:**
```bash
docker run --rm -v "$PWD/src/CP/FrontEnd:/app" -w /app node:20-bookworm \
  sh -lc "npm ci && npm run test:run -- src/test/MyAgentsDigitalMarketingWizard.test.tsx"
```

**Commit message:** `feat(cp-studio-2): add dma master theme step`

**Done signal:** `"E2-S3 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E2-S4: Build the Confirm Schedule step and final runtime handoff in My Agents

**BLOCKED UNTIL:** E2-S3 committed to `feat/cp-studio-2-it2-e2`
**Estimated time:** 60 min
**Branch:** `feat/cp-studio-2-it2-e2` (same branch, continue from E2-S3)
**CP BackEnd pattern:** A — reuse the activation workspace and campaign draft routes

**What to do:**
> Add the final `Confirm Schedule` milestone to capture start date, posts-per-week / preferred times, and the explicit confirmation that setup is complete. Map the confirmation step into the persisted campaign brief and activation workspace so that My Agents can immediately render the hire as runtime-ready after completion. The confirmation view must show the selected platforms, master theme, derived themes, and cadence in one summary block before the user finishes.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | 40–184 | `PostingSchedule`, `PostingCadence`, and approval-mode fields |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1–320 | Current step flow from Iteration 2 |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | 1–220 | Existing workspace + theme-plan save helpers |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Add final confirmation summary, schedule controls, and finish action |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | After completion, surface the hire as ready and link the saved campaign/setup summary into the page |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Add final confirmation coverage |

**Code patterns to copy exactly:**

```typescript
const canFinish = Boolean(workspace?.campaign_setup?.master_theme) &&
  Boolean(workspace?.campaign_setup?.schedule?.start_date) &&
  Boolean(workspace?.prepare_agent?.all_selected_platforms_completed)
```

**Acceptance criteria:**
1. The confirmation step shows a single summary of platforms, master theme, derived themes, and cadence.
2. The user cannot finish until platform preparation and theme setup are complete.
3. Finishing marks the activation workspace complete and leaves My Agents showing the hire as runtime-ready.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S4-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Complete workspace except schedule | Finish button stays disabled |
| E2-S4-T2 | same | Complete schedule + setup | Finish button enables and success state renders |
| E2-S4-T3 | same | Open final summary | Platforms, master theme, derived themes, and cadence all render |

**Test command:**
```bash
docker run --rm -v "$PWD/src/CP/FrontEnd:/app" -w /app node:20-bookworm \
  sh -lc "npm ci && npm run test:run -- src/test/MyAgentsDigitalMarketingWizard.test.tsx src/test/MyAgents.test.tsx"
```

**Commit message:** `feat(cp-studio-2): add dma schedule confirmation`

## CP Demo Defect Tracker

| Defect | Plain-English defect | Evidence | Branch | Status | Notes |
|---|---|---|---|---|---|
| D01 | The Digital Marketing flow in My Agents is still a stacked form, not a horizontal wizard with Back and Continue like PP Agent Studio. | Source review of `DigitalMarketingActivationWizard.tsx` and PP `AgentSetupStudio.tsx` | `feat/PLANT-YT-CONN-1-it1-e1` | Open | Needs a step rail, active-step state, and explicit wizard navigation. |
| D02 | My Agents can trap users on one expired hire because the selector is disabled in retained/read-only states. | Source review of `MyAgents.tsx` selector gating | `feat/PLANT-YT-CONN-1-it1-e1` | Open | Users should still move across hires even when one subscription is read-only. |
| D03 | The View Dashboard and Settings actions in My Agents look live but do nothing. | Source review of `MyAgents.tsx` section actions | `feat/PLANT-YT-CONN-1-it1-e1` | Open | Either wire them to real destinations or remove them. |
| D04 | Digital Marketing save logic guesses agent type from hard-coded agent-id prefixes, so valid hires can miss the right type. | Source review of `agentTypeIdFromAgentId()` usage in `MyAgents.tsx` | `feat/PLANT-YT-CONN-1-it1-e1` | Open | Use the persisted subscription or hired-instance agent type instead of prefix inference. |
| D05 | The activation flow still allows save attempts without a complete business profile, so customers can leave setup half-defined. | Source review of `DigitalMarketingActivationWizard.tsx` required-field handling | `feat/PLANT-YT-CONN-1-it1-e1` | Open | Block finalization until mandatory induction fields are complete. |
| D06 | Authenticated My Agents requests are hitting hired-agent-by-subscription `404`s in live GCP logs, so the runtime can fail after login even when auth itself succeeds. | Latest 10-minute GCP logs from CP and Plant demo services | `feat/PLANT-YT-CONN-1-it1-e1` | Open | Fix the CP to Plant lookup contract or seed the missing hired-agent records. |
| D07 | The top-menu Show/Hide Help control and the extra help-only panels add noise across CP pages. | Source review of `App.tsx`, `Header.tsx`, `AuthenticatedPortal.tsx`, `SignIn.tsx`, `SignUp.tsx`, and `GoalsSetup.tsx` | `feat/PLANT-YT-CONN-1-it1-e1` | Complete | Removed the shared help toggle plumbing and the page help-only panels; validated with updated portal tests. |
| D08 | My Agents still shows the Runtime View promo box instead of focusing the page on real runtime state. | Source review of `AuthenticatedPortal.tsx` page meta for `my-agents` | `feat/PLANT-YT-CONN-1-it1-e1` | Complete | Removed the stale My Agents promo metadata from the portal shell and kept the page focused on the runtime surface only; validated with the portal regression test. |


**Done signal:** `"E2-S4 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E2-S5: Prove the full Digital Marketing wizard journey with regression, demo DB smoke checks, and Codespaces browser verification

**BLOCKED UNTIL:** E2-S4 committed to `feat/cp-studio-2-it2-e2`
**Estimated time:** 60 min
**Branch:** `feat/cp-studio-2-it2-e2` (same branch, continue from E2-S4)
**CP BackEnd pattern:** N/A

**What to do:**
> Add the end-to-end proof. Extend the CP browser journey to cover hire selection, help toggle, induction save, platform step progression, master-theme generation, derived-theme review, schedule confirmation, and the final runtime-ready state. Then run the mandatory live demo DB smoke queries through the Auth Proxy to show both the `hired_agents.config.digital_marketing_activation` object and the reused `campaigns`/`daily_theme_items` rows exist. Finally, serve the CP frontend in Codespaces and verify the browser URL before closing the iteration.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/e2e/hire-journey.spec.ts` | 1–260 | Existing mocked browser-journey style |
| `docs/CONTEXT_AND_INDEX.md` | 1054–1172 | Auth Proxy and `psql` smoke-check rules |
| `src/CP/FrontEnd/package.json` | 1–20 | Build, preview, Vitest, and Playwright scripts |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/e2e/digital-marketing-activation.spec.ts` | modify/create | Cover the full wizard from hire select through final confirmation |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Add any final missing happy-path or error-path coverage |

**Code patterns to copy exactly:**

```bash
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh
source /root/.env.db && psql -c "SELECT hired_instance_id, config->'digital_marketing_activation' FROM hired_agents WHERE hired_instance_id = '[HIRED_INSTANCE_ID]';"
source /root/.env.db && psql -c "SELECT campaign_id, workflow_state FROM campaigns WHERE hired_instance_id = '[HIRED_INSTANCE_ID]';"
source /root/.env.db && psql -c "SELECT COUNT(*) FROM daily_theme_items WHERE campaign_id = '[CAMPAIGN_ID]';"
```

**Acceptance criteria:**
1. Browser automation covers the full Digital Marketing setup path through final confirmation.
2. Demo DB smoke checks prove both activation workspace persistence and campaign/theme-item persistence.
3. The CP frontend is served in Codespaces and the verified browser URL is captured in the PR comment or handoff note.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S5-T1 | `src/CP/FrontEnd/e2e/digital-marketing-activation.spec.ts` | Mock full API journey | User reaches runtime-ready confirmation state |
| E2-S5-T2 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Final smoke test harness | No regression in the wizard happy path |
| E2-S5-T3 | live demo DB smoke | Query hired_agents + campaigns + daily_theme_items | Rows exist for the completed hired instance |

**Test command:**
```bash
docker run --rm -v "$PWD/src/CP/FrontEnd:/work" -w /work mcr.microsoft.com/playwright:v1.57.0-noble \
  sh -lc "npm ci && npm run test:run -- src/test/MyAgentsDigitalMarketingWizard.test.tsx && npm run test:e2e -- e2e/digital-marketing-activation.spec.ts"
```

**Commit message:** `feat(cp-studio-2): prove dma wizard end to end`

**Done signal:** `"E2-S5 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

## Rollback

- Revert the iteration branch if any story breaks My Agents or campaign runtime behavior before merge.
- Drop only the new activation tables/columns from demo Cloud SQL if the merged backend contract cannot be honoured; do not touch existing `campaigns`, `daily_theme_items`, or `content_posts` rows unless the rollback script explicitly scopes them.
- Keep GCP Secret Manager entries created during testing unless they are clearly test-only and tied to rolled-back hired instances.