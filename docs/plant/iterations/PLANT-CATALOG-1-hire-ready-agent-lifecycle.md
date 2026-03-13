# PLANT-CATALOG-1 — Hire-Ready Agent Lifecycle And PP Design Board Iteration Plan

> Template version: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-CATALOG-1` |
| Feature area | Plant-owned hire-ready agent lifecycle, PP design-board approval flow, and CP lifecycle visibility |
| Created | 2026-03-13 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/WAOOAW_agents.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 1 |
| Total stories | 4 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is structured for one autonomous implementation pass with minimal cross-file hunting.

| Constraint | How this plan handles it |
|---|---|
| Cross-service scope | Stories are ordered Plant → PP → CP so public lifecycle state exists before UI wiring |
| Limited context | Each story names exact files and keeps the read set to 3 files |
| No implicit design leaps | The Digital Marketing Agent is the first release target; generic component CRUD is explicitly out of scope |
| Binary completion | Acceptance criteria are pass/fail and tied to concrete route or UI outcomes |

---

## Vision Intake (locked for this plan)

- Area: Plant catalog lifecycle plus PP design-board approval flow for hireable agents, with CP consuming the approved lifecycle surface.
- User outcome: a platform contributor can approve a Digital Marketing Agent release for CP hiring, and customers can see lifecycle/version truth before and after hire.
- Out of scope: generic no-code component creation, multi-agent families beyond the Digital Marketing Agent first slice, and infra/deployment redesign.
- Lane: mixed Lane B then Lane A. Plant lifecycle and PP proxy work must land before CP discovery and lifecycle UI.
- Timeline: one iteration only.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Plant lifecycle model + PP design board + CP lifecycle visibility for the Digital Marketing Agent | 1 | 4 | 7h | 2026-03-14 01:00 UTC |

Estimate basis: Plant model plus route work 90 min per backend story, PP workflow 60 min, CP lifecycle UI 60 min, focused tests 30 min, Docker validation 15 min.

---

## How to Launch Iteration 1

Pre-flight check:

```bash
git status && git log --oneline -3
```

Launch task for the platform engineer agent:

```text
You are executing PLANT-CATALOG-1 Iteration 1 on WAOOAW.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior React 18 / TypeScript / Vite engineer + Senior product-minded platform engineer
Activate these personas NOW.

PLAN FILE: docs/plant/iterations/PLANT-CATALOG-1-hire-ready-agent-lifecycle.md
YOUR SCOPE: Iteration 1 only.
TIME BUDGET: 7h.

EXECUTION ORDER:
1. Run git status && git log --oneline -3
2. Read Agent Execution Rules in this plan.
3. Read Iteration 1 in this plan.
4. Execute stories in order: E1-S1 → E1-S2 → E1-S3 → E1-S4
5. Run the listed focused tests after each story.
6. Run the Docker validation command after the final story.
7. Open the PR against main and halt.
```

---

## Agent Execution Rules

### Rule 1 — Scope lock

- Treat the Digital Marketing Agent as the only release target for this iteration.
- Do not build a generic component builder in PP.
- Do not add business logic to CP or PP backends; Plant remains the source of lifecycle truth.

### Rule 2 — Backend before frontend

- Complete Plant lifecycle persistence and PP proxy surfaces before any CP discovery change.
- Complete PP design-board controls before CP lifecycle UI.

### Rule 3 — Tests before the next story

- Run the exact focused test command listed in the story card before moving on.

### Rule 4 — Commit discipline

```bash
git add -A
git commit -m "feat(plant-catalog-1): [story title]"
git push
```

### Rule 5 — Docker validation after the final story

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```

### Rule 6 — STUCK PROTOCOL

After 3 failed fix attempts on the same blocker:

```bash
git add -A && git commit -m "WIP(plant-catalog-1): [story-id] blocked — [exact error]"
git push
```

Stop and report the exact blocker.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status |
|---|---|---|---|---|
| E1-S1 | 1 | Hire-ready Digital Marketing Agent lifecycle | Plant owns catalog lifecycle and release snapshots | 🟢 Completed |
| E1-S2 | 1 | Hire-ready Digital Marketing Agent lifecycle | PP design board exposes recommended release fields and approval flow | 🟢 Completed |
| E1-S3 | 1 | Hire-ready Digital Marketing Agent lifecycle | CP discovery and hire setup consume approved lifecycle truth | 🔴 Not Started |
| E1-S4 | 1 | Hire-ready Digital Marketing Agent lifecycle | Existing hires show lifecycle continuity and version truth | 🔴 Not Started |

---

## Iteration 1 — Hire-ready Digital Marketing Agent lifecycle

Scope: introduce a Plant-owned lifecycle gate for the Digital Marketing Agent, let PP review and approve the release fields, and show lifecycle/version truth in CP for both new hires and existing customers.

Dependency map:

```text
E1-S1 → E1-S2 → E1-S3 → E1-S4
```

### Epic E1: Hire-ready Digital Marketing Agent lifecycle

Branch: `feat/plant-catalog-1-it1-e1`

---

#### Story E1-S1: Plant owns catalog lifecycle and release snapshots

BLOCKED UNTIL: none
Estimated time: 90 min
Branch: `feat/plant-catalog-1-it1-e1`
CP BackEnd pattern: N/A — Plant BackEnd and Plant Gateway public catalog surface only.

What to do:

> Add a Plant-owned catalog-release concept for hireable agents so CP no longer treats every active `Agent` as market-ready. Persist lifecycle state and both internal and external version identifiers, and snapshot the approved release metadata onto hired instances at hire/finalize time so retired catalog entries do not break active customers.

Files to read first:

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/agents.py` | 1–260 | current public catalog listing and response metadata |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | 1–320 | hire draft/finalize path and existing `agent_type_id` / `definition_version_id` handling |
| `src/Plant/BackEnd/models/hired_agent.py` | 1–220 | current hired-agent lifecycle fields and snapshot slots |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/hired_agent.py` | modify | Add fields for catalog lifecycle snapshot such as `catalog_release_id`, `internal_definition_version_id`, `external_catalog_version`, and `catalog_status_at_hire`. |
| `src/Plant/BackEnd/api/v1/agents.py` | modify | Stop exposing the raw active-agent list as the only CP-ready catalog surface; add a release-aware list path that returns only approved-for-catalog agents with lifecycle metadata. |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | modify | Persist the approved release snapshot at draft/finalize time and preserve servicing continuity when a catalog release is later retired. |
| `src/Plant/BackEnd/database/migrations/versions/` | add | Add one migration for the new hired-agent snapshot columns and any release table or release fields required by the story. |

Code patterns to copy exactly:

```python
from fastapi import Depends
from core.routing import waooaw_router
from core.database import get_db_session, get_read_db_session

router = waooaw_router(prefix="/catalog", tags=["catalog"])

@router.get("/agents")
async def list_catalog_agents(db = Depends(get_read_db_session)):
    ...

@router.post("/agents/{agent_id}/approve")
async def approve_catalog_agent(db = Depends(get_db_session)):
    ...
```

Acceptance criteria:

- Plant exposes an approved-for-catalog agent surface distinct from the raw active agent list.
- Hired instances keep the release/version snapshot they were sold against.
- Retiring a catalog release removes it from new-hire discovery without invalidating active hired instances.

Test command:

```bash
docker compose -f docker-compose.test.yml run plant-backend-test pytest src/Plant/BackEnd/tests -k "agent or hired"
```

Execution notes:

- Completed on 2026-03-13 on branch `feat/plant-catalog-1-it1-e1`.
- Focused Docker validation passed for the new lifecycle path, hired-agent snapshot persistence, Alembic migration checks, and API/repository tests.
- Demo Cloud SQL was migrated to `033_agent_catalog_lifecycle` through the repo Cloud SQL proxy flow and a one-off Docker migration container.
- The broader plan command remains blocked by an unrelated pre-existing repo issue: `tests/bdd/test_trial_lifecycle.py` references a missing feature file `tests/bdd/features/trial_lifecycle.feature`, which interrupts collection before this story slice can finish the full filtered run.

---

#### Story E1-S2: PP design board exposes recommended release fields and approval flow

BLOCKED UNTIL: E1-S1 merged on the branch
Estimated time: 75 min
Branch: `feat/plant-catalog-1-it1-e1`
CP BackEnd pattern: N/A — PP thin proxy to Plant.

What to do:

> Turn Agent Management into a Digital Marketing Agent release board for this slice. The PP user should see recommended hire-ready fields, edit the publishable values, review lifecycle state, and explicitly approve or retire the catalog release instead of editing raw JSON with no release gate.

Files to read first:

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/pages/AgentManagement.tsx` | 1–280 | current agent list and raw agent type editor |
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | 1–320 | existing PP proxy calls and naming style |
| `src/PP/BackEnd/api/agent_types.py` | 1–220 | PP thin-proxy pattern and audit dependency usage |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/pages/AgentManagement.tsx` | modify | Add a Digital Marketing Agent release board that captures public name, short description, industry, monthly price, trial days, allowed durations, approval mode, supported channels, and catalog status. |
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | modify | Add PP client methods for listing, approving, and retiring catalog releases. |
| `src/PP/BackEnd/api/agent_catalog.py` | add | Add PP thin-proxy routes to forward catalog release CRUD/approve/retire actions to Plant with audit logging. |
| `src/PP/BackEnd/clients/plant_client.py` | modify | Add upstream client calls for the new Plant catalog-release endpoints with existing circuit-breaker behavior. |

Code patterns to copy exactly:

```python
from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router
from services.audit_dependency import AuditLogger, get_audit_logger

router = waooaw_router(prefix="/agent-catalog", tags=["agent-catalog"])

@router.post("/{release_id}/approve")
async def approve_release(
    request: Request,
    audit: AuditLogger = Depends(get_audit_logger),
):
    ...
```

Acceptance criteria:

- PP exposes a release board for the Digital Marketing Agent with explicit recommended values.
- Approve and retire actions map to Plant lifecycle truth instead of local PP-only state.
- Audit logging is emitted for approval and retirement actions.

Test command:

```bash
cd src/PP/FrontEnd && npm run test -- --run src/pages/AgentManagement.test.tsx
```

Execution notes:

- Completed on 2026-03-13 on branch `feat/plant-catalog-1-it1-e1`.
- PP now exposes thin-proxy catalog release routes for list, upsert, approve, and retire actions backed by Plant lifecycle truth.
- `AgentManagement` now includes a Digital Marketing Agent release board with recommended hire-ready fields and explicit approve/retire controls.
- Docker validation passed for the focused PP frontend story test and the focused PP backend route tests.
- The PP backend focused route tests require `--cov-fail-under=0` when run alone because the repo-level coverage threshold is global and not meaningful for a four-test slice.

---

#### Story E1-S3: CP discovery and hire setup consume approved lifecycle truth

BLOCKED UNTIL: E1-S2 committed and pushed
Estimated time: 75 min
Branch: `feat/plant-catalog-1-it1-e1`
CP BackEnd pattern: existing `/v1/*` pass-through only; no new CP business logic.

What to do:

> Change CP discovery and hire setup so they consume the approved catalog-release surface and explicit `agent_type_id` / version metadata. Stop relying on the raw active agent catalog as the only market-ready signal, and stop depending on AGT-MKT / AGT-TRD naming heuristics where an explicit type is available from Plant.

Files to read first:

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/AgentDiscovery.tsx` | 1–260 | current catalog loading and filter flow |
| `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` | 1–220 | current `inferAgentTypeId()` shortcut and agent-type branching |
| `src/CP/FrontEnd/src/services/plant.service.ts` | 1–240 | current catalog client methods |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/services/plant.service.ts` | modify | Add a release-aware catalog method and propagate returned `agent_type_id`, `external_catalog_version`, and lifecycle state. |
| `src/CP/FrontEnd/src/pages/AgentDiscovery.tsx` | modify | Load only approved catalog releases and surface lifecycle metadata relevant to new hires. |
| `src/CP/FrontEnd/src/components/AgentCard.tsx` | modify | Render lifecycle/version labels without diluting the marketplace CTA. |
| `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` | modify | Prefer explicit `agent_type_id` and version metadata from the selected catalog item over ID-prefix inference. |

Code patterns to copy exactly:

```typescript
return gatewayRequestJson<ResourceData>('/v1/catalog/agents', { method: 'GET' })
```

Acceptance criteria:

- CP discovery lists only approved-for-catalog agents.
- Hire setup receives explicit `agent_type_id` and version data from the selected catalog agent.
- Customer-facing copy can distinguish ready-to-hire from retired or servicing-only lifecycle states.

Test command:

```bash
cd src/CP/FrontEnd && npm run test -- --run src/test/App.test.tsx src/__tests__/AuthenticatedPortal.test.tsx
```

---

#### Story E1-S4: Existing hires show lifecycle continuity and version truth

BLOCKED UNTIL: E1-S3 committed and pushed
Estimated time: 60 min
Branch: `feat/plant-catalog-1-it1-e1`
CP BackEnd pattern: existing `/cp/hire/wizard` and `/v1/hired-agents/*` routes only.

What to do:

> Show the customer that a retired catalog entry does not end service for an already hired agent. Surface lifecycle truth and version identifiers inside hired-agent views so customers and support can see whether the agent is live for new hires, retired from catalog, or servicing-only under an active contract.

Files to read first:

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1–260 | current hired-agent summary rendering |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | 120–560 | portal shell and entry-state copy |
| `src/CP/FrontEnd/src/services/hireWizard.service.ts` | 1–120 | hire draft/finalize response shape |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/services/hireWizard.service.ts` | modify | Extend the TS response shape with lifecycle and version snapshot fields. |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Show lifecycle continuity copy and version badges for hired agents. |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | modify | Use truthful lifecycle messaging in banner or summary copy when an agent is servicing-only or retired from new hire. |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | modify | Add assertions for lifecycle/version messaging where appropriate. |

Code patterns to copy exactly:

```text
Customer continuity rule:
- retiring from catalog hides the agent from new-hire discovery only
- active hired instances continue to operate
- lifecycle messaging must distinguish “not available for new hire” from “service stopped”
```

Acceptance criteria:

- Existing customers can see lifecycle truth for their hired agent instances.
- A retired catalog agent still appears as serviceable to customers who already hired it.
- Lifecycle/version messaging is covered by focused CP tests.

Test command:

```bash
cd src/CP/FrontEnd && npm run test -- --run src/test/MyAgents.test.tsx src/__tests__/AuthenticatedPortal.test.tsx
```
