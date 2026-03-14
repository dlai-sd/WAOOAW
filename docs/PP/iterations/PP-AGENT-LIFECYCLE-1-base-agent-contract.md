# PP-AGENT-LIFECYCLE-1 — Base Agent Contract Authoring And Approval

> Template version: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PP-AGENT-LIFECYCLE-1` |
| Feature area | PP Base Agent Contract authoring, Plant-backed draft persistence, and PP approval flow |
| Created | 2026-03-13 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/WAOOAW_agents.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` |
| Total iterations | 1 |
| Total epics | 1 |
| Total stories | 4 |

---

## Zero-Cost Agent Constraints

| Constraint | How this plan handles it |
|---|---|
| PP must stay thin | Every durable write goes through Plant-owned APIs into Plant DB |
| No ambiguous storage ownership | Story cards explicitly ban PP-local JSONL, SQLite, or PP-specific DB state |
| Limited context | Each story names exact edit files and keeps the initial read set to 3 files |
| Scope creep risk | Plant runtime build-out is explicitly out of scope; only authoring draft persistence and approval state are included |

---

## Vision Intake

- Area: PP FrontEnd, PP BackEnd thin proxy, and Plant BackEnd persistence for PP-authored agent contract drafts.
- User outcome: a platform contributor can start the Digital Marketing Agent from a Base Agent Contract in PP, save the draft in Plant, get structural guidance, and move it into PP review and approval.
- Out of scope: Plant's internal agent development journey, `src/Plant/BackEnd/agent_mold/` runtime implementation work, component registry work, and CP customer-facing changes.
- Lane: Lane B first for Plant-backed persistence and PP proxy routes, then Lane A for PP authoring and approval UX.
- Timeline: one iteration only.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Plant-backed PP authoring draft lifecycle for the Digital Marketing Agent | 1 | 4 | 6h | 2026-03-14 00:30 UTC |

Estimate basis: new Plant persistence route 90 min, PP proxy 45 min, PP authoring UI 90 min, PP review board 75 min, focused tests and smoke validation 45 min.

---

## How to Launch Iteration 1

Pre-flight check:

```bash
git status && git log --oneline -3
```

Iteration 1 agent task:

```text
You are executing PP-AGENT-LIFECYCLE-1 Iteration 1 on WAOOAW.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior React 18 / TypeScript engineer + Senior product-minded platform engineer
Activate these personas NOW.

PLAN FILE: docs/PP/iterations/PP-AGENT-LIFECYCLE-1-base-agent-contract.md
YOUR SCOPE: Iteration 1 only.
TIME BUDGET: 6h.

EXECUTION ORDER:
1. Run git status && git log --oneline -3
2. Read Agent Execution Rules in this plan.
3. Read Iteration 1 in this plan.
4. Execute stories in order: E1-S1 -> E1-S2 -> E1-S3 -> E1-S4
5. Run the listed focused tests after each story.
6. For persistence stories, validate against the demo Cloud SQL path before closing the story.
7. Open the PR against main and halt.
```

---

## Agent Execution Rules

### Rule 1 — Scope lock

- Do not add a PP-owned database, file store, or local durable draft cache.
- Do not modify `src/Plant/BackEnd/agent_mold/` or implement Plant runtime behavior for the agent.
- Treat the Digital Marketing Agent as the only candidate used for validation in this iteration.

### Rule 2 — Storage ownership

- PP is a thin authoring and approval surface only.
- All durable draft, review, and approval state must be persisted in Plant's database.
- Any PP route added in this iteration must be a thin proxy to Plant with audit logging.

### Rule 3 — Backend before frontend

- Complete Plant persistence and PP proxy routes before changing the PP screens.

### Rule 4 — Persistence validation

- Any story that changes persisted schema or persisted workflow must be smoke-checked against the demo Cloud SQL path, not treated as complete from Docker-only validation.

### Rule 5 — Commit discipline

```bash
git add -A
git commit -m "feat(pp-agent-lifecycle-1): [story title]"
git push
```

### Rule 6 — STUCK PROTOCOL

After 3 failed fix attempts on the same blocker:

```bash
git add -A && git commit -m "WIP(pp-agent-lifecycle-1): [story-id] blocked — [exact error]"
git push
```

Stop and report the exact blocker.

### Rule 7 — PP UX and theme compliance

- Preserve the current PP dark-theme visual language, Fluent UI component usage, and existing PP page, card, table, and board patterns.
- Reframe authoring as a guided operator workflow, not a raw technical configuration form.
- Every PP screen added or modified in this iteration must define loading, empty, success, error, and recovery states.
- Every authoring and review step must make the next step explicit after save, submit, approval, or changes requested.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status |
|---|---|---|---|---|
| E1-S1 | 1 | Base Agent Contract lifecycle | Plant persists PP-authored base contract drafts in GCP SQL | Completed |
| E1-S2 | 1 | Base Agent Contract lifecycle | PP BackEnd proxies draft and approval actions to Plant | Completed |
| E1-S3 | 1 | Base Agent Contract lifecycle | PP authoring screen guides mandatory and optional contract sections | Completed |
| E1-S4 | 1 | Base Agent Contract lifecycle | PP review board submits and approves the Digital Marketing Agent contract | Not Started |

---

## Iteration 1 — Base Agent Contract lifecycle

Scope: create a Plant-backed authoring lifecycle for the Digital Marketing Agent so PP users can sketch from a fixed Base Agent Contract, save drafts durably in Plant's GCP SQL database, and move the contract through PP review and approval without any PP-local persistence.

Dependency map:

```text
E1-S1 -> E1-S2 -> E1-S3 -> E1-S4
```

### Epic E1: Base Agent Contract lifecycle

Branch: `feat/pp-agent-lifecycle-1-it1-e1`

---

#### Story E1-S1: Plant persists PP-authored base contract drafts in GCP SQL

BLOCKED UNTIL: none
Estimated time: 90 min
Branch: `feat/pp-agent-lifecycle-1-it1-e1`
CP BackEnd pattern: N/A — Plant BackEnd only.

What to do:

> Add a Plant-owned persistence model for PP-authored Base Agent Contract drafts. The draft must store the contract sections, draft lifecycle state, reviewer metadata, and a Digital Marketing Agent seed candidate, and it must live in Plant's shared GCP SQL database rather than anywhere in PP.

Files to read first:

| File | What to look for |
|---|---|
| `src/Plant/BackEnd/models/agent_type.py` | Existing pattern for Plant-owned authoring metadata and payload persistence |
| `src/Plant/BackEnd/api/v1/agent_types_db.py` | Existing DB-backed route style for authored agent-type data |
| `src/Plant/BackEnd/repositories/agent_type_repository.py` | Repository conventions for persisted authoring payloads |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/agent_authoring_draft.py` | add | Create the Plant model for Base Agent Contract drafts with fields for draft id, candidate agent type, contract payload, status, reviewer fields, and timestamps. |
| `src/Plant/BackEnd/repositories/agent_authoring_draft_repository.py` | add | Add repository methods for create, update, list, get by id, submit for review, send to changes requested with reviewer comments, and approve. |
| `src/Plant/BackEnd/api/v1/agent_authoring.py` | add | Add Plant routes for listing drafts, fetching one draft, saving a draft, submitting for review, sending to changes requested, approving, and patching constraint policy on a draft. |
| `src/Plant/BackEnd/api/v1/router.py` | modify | Register the new Plant authoring router. |
| `src/Plant/BackEnd/database/migrations/versions/034_pp_agent_authoring_drafts.py` | add | Add the migration for the new draft table in Plant's DB. |

Code patterns to copy exactly:

```python
from fastapi import Depends
from core.routing import waooaw_router
from core.database import get_db_session, get_read_db_session

router = waooaw_router(prefix="/pp-agent-authoring", tags=["pp-agent-authoring"])

@router.get("/drafts")
async def list_drafts(db = Depends(get_read_db_session)):
    ...

@router.post("/drafts")
async def save_draft(db = Depends(get_db_session)):
    ...
```

Acceptance criteria:

- Base Agent Contract drafts are persisted only in Plant.
- The persisted draft includes enough data to reopen the Digital Marketing Agent authoring flow in PP.
- The persisted draft includes section-level completeness state and reviewer comment fields needed to reopen a returned draft without losing review context.
- Status transitions at minimum support `draft`, `in_review`, `changes_requested`, and `approved`.
- No change is made to `src/Plant/BackEnd/agent_mold/` in this story.

Validation:

```bash
docker compose -f docker-compose.test.yml run plant-backend-test pytest src/Plant/BackEnd/tests -k "agent_authoring or agent_type"
```

```bash
# After running the repo's Cloud SQL demo auth-proxy flow, smoke-check the new table exists
psql "$DATABASE_URL" -c "\d agent_authoring_drafts"
```

---

#### Story E1-S2: PP BackEnd proxies draft and approval actions to Plant

BLOCKED UNTIL: E1-S1 pushed
Estimated time: 45 min
Branch: `feat/pp-agent-lifecycle-1-it1-e1`
CP BackEnd pattern: N/A — PP thin proxy only.

What to do:

> Add PP thin-proxy routes for the new Base Agent Contract draft flow. PP must not persist anything locally; it must forward save, list, fetch-by-id, submit, send-to-changes-requested, approve, and constraint-policy patch actions to Plant and record audit events.

Files to read first:

| File | What to look for |
|---|---|
| `src/PP/BackEnd/api/agent_types.py` | Thin-proxy route style and auth handling |
| `src/PP/BackEnd/clients/plant_client.py` | Existing Plant client method pattern |
| `src/PP/BackEnd/main_proxy.py` | Router registration and prefix conventions |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/api/agent_authoring.py` | add | Add PP routes for list drafts, fetch draft by id, save draft, submit review, send to changes requested with comments, approve draft, and patch draft constraint policy. |
| `src/PP/BackEnd/clients/plant_client.py` | modify | Add Plant client methods for the new authoring draft routes, including comment-carrying review actions. |
| `src/PP/BackEnd/main_proxy.py` | modify | Register the new PP authoring router. |
| `src/PP/BackEnd/tests/test_agent_authoring_routes.py` | add | Add focused PP proxy tests for list, get, save, submit, changes requested, and approve routes. |

Code patterns to copy exactly:

```python
from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router
from services.audit_dependency import AuditLogger, get_audit_logger

router = waooaw_router(prefix="/agent-authoring", tags=["agent-authoring"])

@router.post("/drafts/{draft_id}/approve")
async def approve_draft(
    request: Request,
    audit: AuditLogger = Depends(get_audit_logger),
):
    ...
```

Acceptance criteria:

- PP has no local file or DB writes for agent authoring.
- Every durable authoring action goes to Plant through a thin proxy.
- Submit, changes requested, and approve actions emit PP audit logs.
- PP exposes enough proxy surface for the frontend to reopen a returned draft with comments and resume authoring without client-side reconstruction hacks.

Test command:

```bash
docker compose -f docker-compose.test.yml run --rm pp-backend-test pytest src/PP/BackEnd/tests/test_agent_authoring_routes.py -v
```

---

#### Story E1-S3: PP authoring screen guides mandatory and optional contract sections

BLOCKED UNTIL: E1-S2 pushed
Estimated time: 90 min
Branch: `feat/pp-agent-lifecycle-1-it1-e1`
CP BackEnd pattern: N/A — PP FrontEnd only.

What to do:

> Turn the current Agent Type Setup screen into a Base Agent Contract authoring workflow. It must clearly separate mandatory sections from optional extensions, preload a Digital Marketing Agent candidate, save the contract draft through the new Plant-backed PP routes, and feel like a guided PP operator journey rather than a raw configuration form.

Mandatory contract sections for this story:

- Agent identity: candidate agent type id, display name, and one-sentence purpose.
- Operating contract: required skills, approval mode, and execution guardrails.
- Deliverable contract: expected outputs, review checkpoints, and success criteria.
- Optional extensions: hooks, connector-specific notes, and future runtime hints.

Files to read first:

| File | What to look for |
|---|---|
| `src/PP/FrontEnd/src/pages/AgentTypeSetupScreen.tsx` | Current authoring sections and validation flow |
| `src/PP/FrontEnd/src/services/useAgentTypeSetup.ts` | Current save flow and payload shape |
| `src/PP/FrontEnd/src/__tests__/AgentTypeSetupScreen.test.tsx` | Existing screen test style |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/pages/AgentTypeSetupScreen.tsx` | modify | Reframe the screen as Base Agent Contract authoring with explicit mandatory versus optional guidance, Digital Marketing Agent defaults, visible contract status, readiness summary, and step-by-step workflow framing using current PP visual patterns. |
| `src/PP/FrontEnd/src/services/useAgentTypeSetup.ts` | modify | Save and load through the new PP authoring draft routes rather than any PP-local setup path, and surface autosave or save-status information needed by the screen. |
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | modify | Add typed client methods for the new PP authoring draft routes. |
| `src/PP/FrontEnd/src/__tests__/AgentTypeSetupScreen.test.tsx` | modify | Cover workflow framing, mandatory guidance, DMA defaults, draft save behavior, save-state messaging, and unsaved-change protection. |

Code patterns to copy exactly:

```typescript
const result = await gatewayRequestJson<unknown>('/pp/agent-authoring/drafts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
})
```

Acceptance criteria:

- The screen starts from a Base Agent Contract view, not a blank technical form.
- The screen is organized into clear workflow stages such as define agent, set operating contract, review deliverables, and submit for review.
- Mandatory sections are visibly distinct from optional extensions.
- Each mandatory section exposes a per-section state of `missing`, `ready`, or `needs_review` based on field completeness and inline validation.
- The screen includes a compact readiness summary showing what is complete, what is missing, and what blocks submission.
- The overall draft cannot be submitted for review while any mandatory section remains `missing`.
- The Digital Marketing Agent is available as the default candidate for validation.
- Saving a draft uses the Plant-backed PP authoring route.
- The author sees clear confidence states: saving, saved, unsaved changes, and save failed.
- Leaving the screen with unsaved edits shows a warning before navigation.
- If save fails, the user remains on the screen with their entered data intact and a plain-language recovery message.
- The screen preserves the current PP theme and component language rather than introducing a visually separate authoring style.

Test command:

```bash
cd src/PP/FrontEnd && npm run test -- --run src/__tests__/AgentTypeSetupScreen.test.tsx
```

---

#### Story E1-S4: PP review board submits and approves the Digital Marketing Agent contract

BLOCKED UNTIL: E1-S3 pushed
Estimated time: 75 min
Branch: `feat/pp-agent-lifecycle-1-it1-e1`
CP BackEnd pattern: N/A — PP review and approval only.

What to do:

> Add a PP review board for the Base Agent Contract draft lifecycle. The reviewer must be able to see the Digital Marketing Agent contract status, inspect mandatory section completion, submit the draft for review, send it back with actionable comments, and approve it without triggering any Plant runtime build workflow in this iteration.

Review-state model for this story:

- `draft`: author is still editing or mandatory sections are incomplete.
- `in_review`: author submitted a reviewable draft and reviewers can inspect section readiness.
- `changes_requested`: reviewer rejected the current draft with explicit comments; draft returns to the authoring queue without Plant runtime build-out.
- `approved`: reviewer accepted the draft for catalog/governed lifecycle continuation.

Files to read first:

| File | What to look for |
|---|---|
| `src/PP/FrontEnd/src/pages/AgentManagement.tsx` | Existing review board and card layout patterns |
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | Existing PP approval action methods |
| `src/PP/FrontEnd/src/pages/AgentManagement.test.tsx` | Current page test style |

Files to create / modify:

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/FrontEnd/src/pages/AgentManagement.tsx` | modify | Add a Base Agent Contract review board showing draft status, contract completeness, submit-for-review, changes-requested with comments, approve actions, and clear next-step messaging for the Digital Marketing Agent using existing PP board patterns. |
| `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | modify | Add client methods for submit, changes requested, and approve draft actions if not already added in E1-S3. |
| `src/PP/FrontEnd/src/pages/AgentManagement.test.tsx` | modify | Add tests for submit, changes requested, approve, and next-step messaging flows. |

Code patterns to copy exactly:

```typescript
await gatewayRequestJson(`/pp/agent-authoring/drafts/${encodeURIComponent(draftId)}/submit-review`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({}),
})
```

Acceptance criteria:

- PP reviewers can move the Digital Marketing Agent contract from `draft` to `in_review`, from `in_review` to `changes_requested`, and from `in_review` to `approved`.
- The review board shows whether mandatory contract sections are complete.
- The review board captures reviewer comments when a draft is sent to `changes_requested`, and those comments are visible when the author reopens the draft.
- Reviewer feedback is presented as actionable fix items tied to sections, not as an unstructured comment blob only.
- After approval, the UI shows a clear next-step state such as ready for catalog preparation or awaiting next owner, so the operator understands what approval unlocked.
- After changes requested, the UI makes the return path explicit so the author knows exactly where to continue editing.
- The review board preserves the current PP visual language instead of introducing a separate one-off moderation UI.
- No UI for Plant runtime build-out is added in this iteration.

Test command:

```bash
cd src/PP/FrontEnd && npm run test -- --run src/pages/AgentManagement.test.tsx
```

---

## Final validation for the iteration

```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest src/Plant/BackEnd/tests -k "agent_authoring or agent_type"
docker compose -f docker-compose.test.yml run --rm pp-backend-test pytest src/PP/BackEnd/tests/test_agent_authoring_routes.py -v
cd src/PP/FrontEnd && npm run test -- --run src/__tests__/AgentTypeSetupScreen.test.tsx src/pages/AgentManagement.test.tsx
```

Cloud SQL persistence smoke-check requirement:

```bash
# Use the repo's existing demo Cloud SQL proxy flow, then verify the draft row exists
psql "$DATABASE_URL" -c "select draft_id, candidate_agent_type, status from agent_authoring_drafts order by updated_at desc limit 5;"
```