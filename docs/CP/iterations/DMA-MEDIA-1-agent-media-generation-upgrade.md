# DMA-MEDIA-1 — DMA Agent Media Generation Upgrade

**Objective**
This plan upgrades the Digital Marketing Agent from a text-only strategy and draft generator into an artifact-capable agent that can produce customer-requested tables, images, audio, video, and combined video+audio without breaking the current architectural guardrails.
The upgrade must preserve the existing strengths of the platform: CP BackEnd stays a thin proxy, Plant BackEnd owns business logic, approvals remain mandatory before publication, and all new media handling remains provider-agnostic and promotion-safe.
The first release bias is DMA value: customers should be able to ask for richer deliverables, review them safely, and use the same approval flow instead of learning a separate media subsystem.
If a story does not improve DMA value delivery, DMA enablement, or runtime safety for this path, cut it.

> **Template version**: 2.0 adapted for a durable branch-first execution workflow on 2026-04-10.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `DMA-MEDIA-1` |
| Feature area | Customer Portal + Plant BackEnd — DMA artifact and media generation |
| Created | 2026-04-10 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 7 |
| Total stories | 10 |

---

## Vision Intake

- Area: Plant BackEnd is the primary implementation owner for media generation, artifact typing, storage, and publish contracts; CP FrontEnd and CP BackEnd changes exist to let customers request, review, and approve those artifacts without violating the thin-proxy pattern.
- Outcome: A DMA customer can explicitly request a table, image, audio clip, video, or video+audio deliverable from the DMA workflow and receive a typed artifact they can preview, approve, and later publish through the existing channel flow.
- Out of scope: Generic SaaS media studio work, non-DMA agent lanes, billing changes, mobile app work, fully autonomous publish-without-approval behavior, and provider-specific lock-in in business logic.
- Lane: Lane B first because new Plant backend capabilities are required before CP can wire a usable customer experience. Lane A follows only after the backend contract is stable.
- Timeline constraint: Durable execution only. Commit and push the plan skeleton first, then commit and push each completed iteration section so disconnection cannot lose plan state.
- Objective alignment: DMA value and DMA enablement. This closes the current blocker where DMA can discuss rich outputs but cannot actually generate, store, route, or render them as first-class artifacts.

---

## Architecture Guardrails

| Guardrail | Required behavior |
|---|---|
| CP BackEnd role | Thin proxy only. No business logic, no media processing, no provider SDK coupling. |
| Plant ownership | Artifact contracts, routing, generation orchestration, storage metadata, review state, and publish readiness stay in Plant BackEnd. |
| Approval safety | Customer approval remains required before any external publish action. Media generation may be async, but publish stays gated. |
| Cloud portability | Media storage and generation providers must sit behind adapters. No provider SDK in business logic. |
| Image promotion | No environment-specific URIs or credentials baked into code or Dockerfiles. |
| Observability | New generation jobs and storage calls must be traceable with correlation IDs, structured logs, and metrics. |
| DMA-first scope | Build the minimal platform shape that unlocks DMA artifacts now; defer generalized marketplace-wide media tooling. |

---

## Target State Definition

The DMA workflow accepts a typed artifact request instead of treating every prompt as plain text strategy. Plant translates that request into a stable artifact contract, routes it to the right generation path, stores metadata and asset references, and returns draft artifacts that CP can preview in the normal review flow. The customer sees clear generation state, previews for each artifact type, and the next required approval action. Publishing stays separate from generation: a generated asset becomes publishable only after review, channel validation, and explicit approval.

### Target-state acceptance criteria

1. DMA can represent artifact intent explicitly as `table`, `image`, `audio`, `video`, or `video_audio` instead of collapsing all outputs into text.
2. Plant stores draft artifact metadata and binary asset references in a durable, provider-agnostic way.
3. Async generation exists for binary artifacts so long-running media work does not block the request-response path.
4. CP can request artifact types, poll or display job state, and preview returned artifacts inside the DMA operating surface.
5. Existing approval and publish flows continue to work, with richer readiness and validation states for media artifacts.
6. Docker-based validation exists for the new backend and frontend contract paths at the end of execution.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B foundation — define typed artifact contracts, persistence, adapter seams, and async job lifecycle for DMA media generation | 3 | 4 | 5.5h | 2026-04-10 18:30 UTC |
| 2 | Lane B execution — wire media generation providers, storage, artifact routing, review-state integration, and publish-ready backend responses | 2 | 3 | 5.0h | 2026-04-11 12:30 UTC |
| 3 | Lane A integration — proxy CP safely, render artifact previews in DMA UI, and complete Docker validation for the end-to-end contract | 2 | 3 | 4.5h | 2026-04-11 18:30 UTC |

**Why 3 iterations are justified:** this upgrade changes the backend domain contract, introduces async binary-artifact infrastructure, and then wires customer review UX on top. Collapsing all three into 2 iterations would either overload a single PR or blur backend-before-frontend merge discipline.

---

## PM Review Checklist

- [x] Expert personas are filled for each iteration task block.
- [x] Epic titles describe customer or platform outcomes, not generic technical chores.
- [x] Every story includes an exact logical branch name.
- [x] Every story embeds relevant code patterns inline.
- [x] Every story limits “Files to read first” to 3 files.
- [x] Every CP BackEnd story states the thin-proxy pattern explicitly.
- [x] Backend work is sequenced before frontend work where there is a dependency.
- [x] Docker-only validation is specified for the final execution slice.
- [x] No placeholder text remains in the published plan.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. Select **platform-engineer** if available
5. Paste the task block below
6. Start the run
7. Come back at **2026-04-10 18:30 UTC**

**Iteration 1 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior platform architecture engineer + Senior async job orchestration engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-MEDIA-1-agent-media-generation-upgrade.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 or 3 content.
TIME BUDGET: 5.5h. If you reach 6.5h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell, git, gh, and docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch and PR flow for this run.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify repository writes are possible on the task branch.
3. Verify a PR to `main` can be opened or updated, or explicitly report that PR controls are unavailable.
4. If any gate fails, post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the Agent Execution Rules section in this plan file.
2. Read the Iteration 1 section in this plan file.
3. Read nothing else before starting.
4. Execute Epics E1 → E2 → E3 in order.
5. Add or update the tests listed in each story before moving on.
6. If tool execution is available, run the narrowest relevant validation and record the result.
7. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

### Iteration 2

> Do not launch until Iteration 1 is merged to `main` and the evidence block below is updated.

**Prerequisite evidence:**
- Iteration 1 merge status: `PENDING HUMAN UPDATE BEFORE LAUNCH`
- Iteration 1 PR: `TBD`
- Merge commit on `main`: `TBD`
- Merged at: `TBD`

**Steps to launch:** same as Iteration 1

**Iteration 2 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior media pipeline engineer + Senior cloud-portable storage adapter engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-MEDIA-1-agent-media-generation-upgrade.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch other iterations.
TIME BUDGET: 5.0h.

PREREQUISITE CHECK:
1. Read the Prerequisite evidence block under Iteration 2.
2. If it is still pending or incomplete, post `Blocked: Iteration 1 merge evidence has not been recorded in the plan.` and HALT.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify repository writes are possible on the task branch.
3. Verify a PR to `main` can be opened or updated, or explicitly report that PR controls are unavailable.
4. If any gate fails, post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read Agent Execution Rules and Iteration 2 only.
2. Execute backend work in the listed order.
3. Add or update the tests listed in each story before moving on.
4. If execution tools are available, run the narrowest relevant validation and record the result.
5. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

### Iteration 3

> Do not launch until Iteration 2 is merged to `main` and the evidence block below is updated.

**Prerequisite evidence:**
- Iteration 2 merge status: `PENDING HUMAN UPDATE BEFORE LAUNCH`
- Iteration 2 PR: `TBD`
- Merge commit on `main`: `TBD`
- Merged at: `TBD`

**Steps to launch:** same as Iteration 1

**Iteration 3 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React / TypeScript / Vite engineer + Senior Python 3.11 / FastAPI engineer + Senior product-minded DMA UX engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-MEDIA-1-agent-media-generation-upgrade.md
YOUR SCOPE: Iteration 3 only — Epics E6, E7. Do not touch earlier iterations.
TIME BUDGET: 4.5h.

PREREQUISITE CHECK:
1. Read the Prerequisite evidence block under Iteration 3.
2. If it is still pending or incomplete, post `Blocked: Iteration 2 merge evidence has not been recorded in the plan.` and HALT.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify repository writes are possible on the task branch.
3. Verify a PR to `main` can be opened or updated, or explicitly report that PR controls are unavailable.
4. If any gate fails, post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read Agent Execution Rules and Iteration 3 only.
2. Respect backend-before-frontend sequencing inside the iteration.
3. Add or update the tests listed in each story before moving on.
4. Run Docker-only validation if execution tools are available; do not use virtual environments.
5. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

---

## Agent Execution Rules

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required prerequisite-evidence block for the iteration is complete and not marked pending.
- The execution surface allows repository writes on the current task branch.
- The execution surface allows opening or updating a PR to `main`, or you can explicitly report that PR controls are unavailable.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona immediately. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

### Rule 0 — Use the GitHub task branch and open the iteration PR early

- One iteration = one GitHub task branch and one PR.
- If the execution surface already created a branch, keep using it.
- If the UI lets you choose a branch name, prefer `feat/dma-media-1-itN-short-scope-runid`.
- Open a draft PR to `main` as soon as PR controls are available and keep updating that same PR.
- Use the Tracking Table in this plan as the source of truth for story status updates.

### Rule 1 — Scope lock

- Implement exactly the acceptance criteria in the story card.
- Do not refactor unrelated code.
- Do not edit files outside the story card’s allowed file list.
- If you discover out-of-scope issues, note them and move on.

### Rule 2 — Tests before the next story

- Add every listed test before moving to the next story.
- If test execution is available, run the narrowest relevant command.
- If execution tooling is unavailable, add the tests and record that execution is deferred.
- Final validation for this plan must use Docker only. Do not use a virtual environment.

### Rule 3 — Save progress after every story

- Update the Tracking Table status.
- Save code and plan updates to the iteration branch.
- If a PR already exists, add a concise progress update with changed files, tests, and next story.

### Rule 4 — Validate after every epic

- Prefer the narrowest relevant automated validation for the changed files.
- If execution tools are available, run the command and record the result.
- If not, state clearly that validation is deferred.
- After validation, add `**Epic complete ✅**` under the epic heading.

### Rule 5 — STUCK PROTOCOL

- After 3 failed implementation attempts on the same blocker, mark the story as `🚫 Blocked`.
- Open or update a draft PR titled `WIP: dma-media-blocked-story — blocked` if PR controls are available.
- Include the exact blocker, the exact error, and 1-2 attempted fixes.
- Post the PR URL if available, otherwise post the blocker in the thread, then HALT.

### Rule 6 — Iteration PR

- Use the same task branch for the final iteration PR to `main`.
- PR title format: `feat(DMA-MEDIA-1): iteration N — one-line summary`.
- PR body must include completed stories, validation status or deferral, and the NFR checklist.
- Post the PR URL in the task thread and HALT.

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:

```bash
git add -A && git commit -m "feat(DMA-MEDIA-1): [epic-id] — [epic title]" && git push
```

Do this before starting the next epic. If interrupted, completed work is already saved.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | DMA speaks a typed artifact language | Extend the Plant artifact contract beyond text-only outputs | 🔴 Not Started | — |
| E1-S2 | 1 | DMA speaks a typed artifact language | Persist draft artifact metadata with a first-class schema | 🔴 Not Started | — |
| E2-S1 | 1 | DMA stores and names media safely | Introduce a provider-agnostic media artifact store service | 🔴 Not Started | — |
| E3-S1 | 1 | DMA generation jobs run asynchronously | Add async media job state to the draft-batch generation path | 🔴 Not Started | — |
| E4-S1 | 2 | DMA routes typed artifacts through provider-safe backend paths | Teach content generation to honor artifact requests | 🔴 Not Started | — |
| E4-S2 | 2 | DMA routes typed artifacts through provider-safe backend paths | Route generated artifacts into channel-compatible variants | 🔴 Not Started | — |
| E5-S1 | 2 | DMA returns review-ready artifact payloads and typed publish receipts | Expose artifact status, previews, and publish-ready media receipts through Plant APIs | 🔴 Not Started | — |
| E6-S1 | 3 | CP stays a thin proxy while exposing the richer contract | Extend CP proxy and frontend service types for typed artifacts | 🔴 Not Started | — |
| E7-S1 | 3 | DMA customers can request, preview, and approve richer artifacts | Add artifact request controls and preview renderers to the DMA UI | 🔴 Not Started | — |
| E7-S2 | 3 | DMA customers can request, preview, and approve richer artifacts | Lock the upgrade with Docker-only backend and frontend validation | 🔴 Not Started | — |

---

## Iteration 1 — Typed Artifact Contract + Persistence Foundation

**Outcome**
Plant can represent media-generation intent as a typed DMA artifact request, persist artifact metadata beside draft posts, and launch async generation work without blocking the customer-facing request path.

### Dependency Map

| Story | Depends on | Enables |
|---|---|---|
| E1-S1 | none | E1-S2, E2-S1, E3-S1 |
| E1-S2 | E1-S1 | E3-S1, E4-S1 |
| E2-S1 | E1-S1 | E3-S1, E4-S1 |
| E3-S1 | E1-S1, E1-S2, E2-S1 | Iteration 2 |

### E1 — DMA speaks a typed artifact language

#### Story E1-S1 — Extend the Plant artifact contract beyond text-only outputs

| Field | Value |
|---|---|
| Story ID | `E1-S1` |
| Branch | `feat/dma-media-1-it1-artifact-contract` |
| Estimate | 45 min |
| BLOCKED UNTIL | none |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/Plant/BackEnd/agent_mold/skills/playbook.py`
2. `src/Plant/BackEnd/agent_mold/skills/executor.py`
3. `src/Plant/BackEnd/tests/test_content_creator.py`

**Files to create / modify**
- `src/Plant/BackEnd/agent_mold/skills/playbook.py`
- `src/Plant/BackEnd/agent_mold/skills/executor.py`
- `src/Plant/BackEnd/tests/test_content_creator.py`

**Context**
Today the canonical DMA contract only knows how to return a text canonical message plus per-channel text variants. That forces every downstream path to treat user requests for tables, images, audio, or video as plain text, which is the root reason artifact generation cannot be routed safely.

**Code patterns to copy exactly**
```python
from pydantic import BaseModel, Field

class CanonicalMessage(BaseModel):
  schema_version: Literal["1.0"] = Field(default="1.0")
```

```python
# Cloud-portable rule: store typed metadata, not provider SDK objects.
class ArtifactRequest(BaseModel):
  artifact_type: Literal["table", "image", "audio", "video", "video_audio"]
  prompt: str = Field(..., min_length=1)
  metadata: dict[str, Any] = Field(default_factory=dict)
```

**Acceptance criteria**
1. Add typed Pydantic contracts in `playbook.py` for requested artifacts and generated artifact references.
2. Extend `CanonicalMessage`, `ChannelVariant`, `MarketingMultiChannelOutput`, and `SkillExecutionInput` so later stories can carry artifact intent and artifact metadata without breaking existing text behavior.
3. Keep deterministic execution backward-compatible: text-only DMA requests still work when no artifact request is supplied.
4. Add unit coverage proving typed artifact contracts validate accepted values and reject unsupported artifact types.

**Tests to add / update**
- `src/Plant/BackEnd/tests/test_content_creator.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/test_content_creator.py
```

#### Story E1-S2 — Persist draft artifact metadata with a first-class schema

| Field | Value |
|---|---|
| Story ID | `E1-S2` |
| Branch | `feat/dma-media-1-it1-draft-artifact-persistence` |
| Estimate | 60 min |
| BLOCKED UNTIL | `E1-S1` merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/Plant/BackEnd/models/marketing_draft.py`
2. `src/Plant/BackEnd/services/draft_batches.py`
3. `src/Plant/BackEnd/database/migrations/versions/031_dma_iteration1_persistence.py`

**Files to create / modify**
- `src/Plant/BackEnd/models/marketing_draft.py`
- `src/Plant/BackEnd/services/draft_batches.py`
- `src/Plant/BackEnd/database/migrations/versions/033_dma_media_artifact_persistence.py`
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`

**Context**
Draft posts currently persist text, hashtags, review state, and provider posting fields only. If DMA generates an image, audio clip, or video, there is nowhere durable to record the artifact type, storage location, preview URL, or generation status, so later review and publish steps cannot behave deterministically.

**Code patterns to copy exactly**
```python
from sqlalchemy.dialects.postgresql import JSONB

artifact_metadata = Column(JSONB, nullable=False, default=dict)
```

```python
# Persist provider-neutral asset references only.
artifact_uri = Column(Text, nullable=True)
artifact_type = Column(String(32), nullable=False, index=True)
```

**Acceptance criteria**
1. Extend the draft-post persistence model to store artifact metadata and zero-or-more media assets per post.
2. Add an Alembic migration that creates the new persistence surface without rewriting unrelated draft-batch tables.
3. Extend `DraftPostRecord` and `DraftBatchRecord` to serialize and deserialize the new artifact metadata cleanly.
4. Add unit coverage proving a stored batch round-trips typed artifact metadata.

**Tests to add / update**
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py
```

---

## Iteration 3 — CP Thin Proxy + DMA Artifact Review UX + Docker Validation

**Outcome**
CP can request and display typed DMA artifacts without owning media logic, and the full upgraded path has a Docker-only validation recipe covering Plant, CP BackEnd, and CP FrontEnd.

### Dependency Map

| Story | Depends on | Enables |
|---|---|---|
| E6-S1 | Iteration 2 merged | E7-S1, E7-S2 |
| E7-S1 | E6-S1 | E7-S2 |
| E7-S2 | E6-S1, E7-S1 | Final PR |

### E6 — CP stays a thin proxy while exposing the richer contract

#### Story E6-S1 — Extend CP proxy and frontend service types for typed artifacts

| Field | Value |
|---|---|
| Story ID | `E6-S1` |
| Branch | `feat/dma-media-1-it3-cp-proxy-and-types` |
| Estimate | 60 min |
| BLOCKED UNTIL | Iteration 2 merged |
| CP BackEnd pattern | `Pattern A` — extend the existing `/cp/marketing/*` route file `src/CP/BackEnd/api/marketing_review.py`; keep it as a pure forwarding layer |

**Files to read first**
1. `src/CP/BackEnd/api/marketing_review.py`
2. `src/CP/FrontEnd/src/services/marketingReview.service.ts`
3. `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts`

**Files to create / modify**
- `src/CP/BackEnd/api/marketing_review.py`
- `src/CP/FrontEnd/src/services/marketingReview.service.ts`
- `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts`
- `src/CP/BackEnd/tests/test_marketing_review_proxy.py`

**Context**
By the time this iteration starts, Plant should already expose typed artifact payloads and media-ready draft metadata. CP’s job is only to pass that contract through cleanly, inject the customer scope, and present accurate TypeScript types so the UI can render previews without inventing business logic locally.

**Code patterns to copy exactly**
```python
router = waooaw_router(prefix="/cp/marketing", tags=["cp-marketing"])
```

```python
def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    correlation = request.headers.get("x-correlation-id")
    if correlation:
        headers["X-Correlation-ID"] = correlation
    return headers
```

**Acceptance criteria**
1. Extend CP request and response types so artifact requests, artifact status, preview URIs, and typed media metadata pass through intact.
2. Keep `marketing_review.py` as a pure proxy: no provider branching, no media orchestration, no data reshaping beyond customer scoping and HTTP forwarding.
3. Add a CP backend test proving the proxy forwards the richer contract unchanged.
4. Add TypeScript types that let the frontend distinguish `table`, `image`, `audio`, `video`, and `video_audio` safely.

**Tests to add / update**
- `src/CP/BackEnd/tests/test_marketing_review_proxy.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm cp-backend-test src/CP/BackEnd/tests/test_marketing_review_proxy.py
```

### E7 — DMA customers can request, preview, and approve richer artifacts

#### Story E7-S1 — Add artifact request controls and preview renderers to the DMA UI

| Field | Value |
|---|---|
| Story ID | `E7-S1` |
| Branch | `feat/dma-media-1-it3-dma-artifact-ui` |
| Estimate | 90 min |
| BLOCKED UNTIL | `E6-S1` merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx`
2. `src/CP/FrontEnd/src/components/DigitalMarketingThemePlanCard.tsx`
3. `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx`

**Files to create / modify**
- `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingThemePlanCard.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingArtifactPreviewCard.tsx`
- `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx`
- `src/CP/FrontEnd/src/__tests__/WizardPlatforms.test.tsx`

**Context**
The current DMA UI can capture strategy and show theme plans, but it has no first-class way to ask for or preview typed artifacts. This story adds just enough UI to request media intentionally, display generation state, and preview returned assets inside the existing activation and review flow instead of creating a parallel media studio.

**Code patterns to copy exactly**
```tsx
type DraftPost = {
  post_id: string
  channel: string
  text: string
}
```

```tsx
{loading ? <Spinner size="tiny" /> : null}
```

**Acceptance criteria**
1. Add customer controls to request one or more artifact types from the DMA workflow.
2. Render preview states for tables, images, audio, video, and video+audio, including queued, running, ready, and failed statuses.
3. Keep approval behavior explicit: the UI may preview and schedule, but it must not imply auto-publish.
4. Add frontend test coverage for artifact selection and at least one preview state per artifact family.

**Tests to add / update**
- `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx`
- `src/CP/FrontEnd/src/__tests__/WizardPlatforms.test.tsx`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm cp-frontend-test
```

#### Story E7-S2 — Lock the upgrade with Docker-only backend and frontend validation

| Field | Value |
|---|---|
| Story ID | `E7-S2` |
| Branch | `feat/dma-media-1-it3-docker-validation` |
| Estimate | 45 min |
| BLOCKED UNTIL | `E6-S1` and `E7-S1` merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `docker-compose.test.yml`
2. `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`
3. `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx`

**Files to create / modify**
- `docs/CP/iterations/DMA-MEDIA-1-agent-media-generation-upgrade.md`
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`
- `src/CP/BackEnd/tests/test_marketing_review_proxy.py`
- `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx`

**Context**
The user explicitly asked that testing happen at the end using Docker only and without a virtual environment. This story makes that operational rule part of the implementation slice so the finishing agent cannot silently switch to local Python or ad hoc frontend commands.

**Code patterns to copy exactly**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py
docker compose -f docker-compose.test.yml run --rm cp-backend-test src/CP/BackEnd/tests/test_marketing_review_proxy.py
docker compose -f docker-compose.test.yml run --rm cp-frontend-test
```

**Acceptance criteria**
1. Add or update the narrowest backend and frontend tests needed for the DMA media contract.
2. Record the exact Docker-only validation commands in the iteration PR description and in this plan’s Tracking Table update when executed.
3. Do not use a virtual environment or non-Docker local test shortcut.
4. Mark the iteration complete only after all three Docker commands succeed or a blocking failure is reported through STUCK PROTOCOL.

**Tests to add / update**
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`
- `src/CP/BackEnd/tests/test_marketing_review_proxy.py`
- `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py
docker compose -f docker-compose.test.yml run --rm cp-backend-test src/CP/BackEnd/tests/test_marketing_review_proxy.py
docker compose -f docker-compose.test.yml run --rm cp-frontend-test
```

---

## Iteration 2 — Media Generation Execution + Review-Ready Backend Responses

**Outcome**
Plant can generate or prepare typed media artifacts through provider-safe adapters, route them into channel-compatible variants, and expose review-ready artifact payloads and publish receipts to upstream callers.

### Dependency Map

| Story | Depends on | Enables |
|---|---|---|
| E4-S1 | Iteration 1 merged | E4-S2, E5-S1 |
| E4-S2 | E4-S1 | E5-S1 |
| E5-S1 | E4-S1, E4-S2 | Iteration 3 |

### E4 — DMA routes typed artifacts through provider-safe backend paths

#### Story E4-S1 — Teach content generation to honor artifact requests

| Field | Value |
|---|---|
| Story ID | `E4-S1` |
| Branch | `feat/dma-media-1-it2-content-generation` |
| Estimate | 90 min |
| BLOCKED UNTIL | Iteration 1 merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/Plant/BackEnd/agent_mold/skills/content_creator.py`
2. `src/Plant/BackEnd/agent_mold/skills/grok_client.py`
3. `src/Plant/BackEnd/services/media_artifact_store.py`

**Files to create / modify**
- `src/Plant/BackEnd/agent_mold/skills/content_creator.py`
- `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py`
- `src/Plant/BackEnd/tests/test_content_creator.py`

**Context**
The current DMA generator can create themes and post copy, but it cannot translate a typed request like “make a table and an image” into backend work. This story makes the generator artifact-aware while keeping media provider specifics outside the main skill logic.

**Code patterns to copy exactly**
```python
from agent_mold.skills.grok_client import get_grok_client, grok_complete
client = get_grok_client()
```

```python
@circuit_breaker(service="media_generation_provider")
async def generate_artifact(...):
  ...
```

**Acceptance criteria**
1. Extend content generation input handling so artifact requests and prompt hints are carried into Grok-backed or deterministic generation paths.
2. For binary artifacts, queue worker-side generation rather than trying to finish every asset inline.
3. Keep text-only output paths unchanged when no artifact request is present.
4. Add unit tests for mixed requests such as text+table and text+image, including fallback behavior when provider generation is unavailable.

**Tests to add / update**
- `src/Plant/BackEnd/tests/test_content_creator.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/test_content_creator.py
```

#### Story E4-S2 — Route generated artifacts into channel-compatible variants

| Field | Value |
|---|---|
| Story ID | `E4-S2` |
| Branch | `feat/dma-media-1-it2-artifact-routing` |
| Estimate | 90 min |
| BLOCKED UNTIL | `E4-S1` merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/Plant/BackEnd/agent_mold/skills/adapters.py`
2. `src/Plant/BackEnd/agent_mold/skills/executor.py`
3. `src/Plant/BackEnd/agent_mold/skills/playbook.py`

**Files to create / modify**
- `src/Plant/BackEnd/agent_mold/skills/adapters.py`
- `src/Plant/BackEnd/agent_mold/skills/executor.py`
- `src/Plant/BackEnd/agent_mold/skills/artifact_routing.py`
- `src/Plant/BackEnd/tests/unit/test_artifact_routing.py`

**Context**
Once Plant can generate artifacts, it still needs to decide which channel can accept which artifact shape and how to package previewable outputs for review. This is the routing layer that keeps channel compatibility explicit instead of burying it in ad hoc conditionals.

**Code patterns to copy exactly**
```python
def adapt_youtube(canonical: CanonicalMessage, *, constraints: YouTubeConstraints = YouTubeConstraints()) -> ChannelVariant:
  ...
```

```python
# Make compatibility explicit and testable.
ALLOWED_ARTIFACTS = {
  ChannelName.YOUTUBE: {"video", "video_audio", "image", "table"},
}
```

**Acceptance criteria**
1. Add an artifact-routing module that validates channel-to-artifact compatibility before review or publish.
2. Extend the executor and adapters so channel variants can carry artifact references and preview metadata in addition to text.
3. Keep routing failures explicit and testable rather than silently dropping unsupported artifacts.
4. Add unit tests covering at least YouTube, Facebook, and LinkedIn compatibility rules.

**Tests to add / update**
- `src/Plant/BackEnd/tests/unit/test_artifact_routing.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_artifact_routing.py
```

### E5 — DMA returns review-ready artifact payloads and typed publish receipts

#### Story E5-S1 — Expose artifact status, previews, and publish-ready media receipts through Plant APIs

| Field | Value |
|---|---|
| Story ID | `E5-S1` |
| Branch | `feat/dma-media-1-it2-review-and-publish-contract` |
| Estimate | 90 min |
| BLOCKED UNTIL | `E4-S1` and `E4-S2` merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/Plant/BackEnd/api/v1/marketing_drafts.py`
2. `src/Plant/BackEnd/integrations/social/youtube_client.py`
3. `src/Plant/BackEnd/integrations/social/facebook_client.py`

**Files to create / modify**
- `src/Plant/BackEnd/api/v1/marketing_drafts.py`
- `src/Plant/BackEnd/agent_mold/skills/adapters_youtube.py`
- `src/Plant/BackEnd/integrations/social/youtube_client.py`
- `src/Plant/BackEnd/integrations/social/facebook_client.py`
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`

**Context**
Upstream callers need one stable contract that tells them whether an artifact is queued, ready for preview, failed, or publishable. The publish clients already support some media cases, but their contract is still too implicit for DMA to expose typed publish readiness to CP safely.

**Code patterns to copy exactly**
```python
from core.routing import waooaw_router
router = waooaw_router(prefix="/marketing", tags=["marketing"])
```

```python
@router.get("/draft-batches/{batch_id}", response_model=DraftBatchRecord)
async def get_draft_batch(
  batch_id: str,
  db: AsyncSession = Depends(get_read_db_session),
) -> DraftBatchRecord:
  ...
```

**Acceptance criteria**
1. Extend Plant draft-batch responses to include artifact status, preview URIs, mime types, and publish-readiness hints.
2. Expand YouTube and Facebook media-capable methods so the contract distinguishes text-only posts from media-backed posts and returns typed receipt data.
3. Keep publishing separate from generation: this story may expose publish-ready metadata, but it must not bypass approval requirements.
4. Add unit coverage showing media-backed draft responses and typed publish receipt serialization.

**Tests to add / update**
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py
```

### E2 — DMA stores and names media safely

#### Story E2-S1 — Introduce a provider-agnostic media artifact store service

| Field | Value |
|---|---|
| Story ID | `E2-S1` |
| Branch | `feat/dma-media-1-it1-media-store-adapter` |
| Estimate | 60 min |
| BLOCKED UNTIL | `E1-S1` merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/Plant/BackEnd/services/draft_batches.py`
2. `src/Plant/BackEnd/core/config.py`
3. `src/Plant/BackEnd/worker/celery_app.py`

**Files to create / modify**
- `src/Plant/BackEnd/services/media_artifact_store.py`
- `src/Plant/BackEnd/core/config.py`
- `src/Plant/BackEnd/tests/unit/test_media_artifact_store.py`

**Context**
The platform needs a durable place to put generated tables, images, audio, and video without tying Plant business logic to one cloud or media vendor. This service is the portability seam: later provider integrations can upload bytes and return URIs, while the rest of Plant sees only stable metadata.

**Code patterns to copy exactly**
```python
logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())
```

```python
@circuit_breaker(service="media_artifact_store")
async def store_artifact(...):
  ...
```

**Acceptance criteria**
1. Add a `MediaArtifactStore` abstraction with a local-safe implementation and a provider-adapter seam for future cloud storage.
2. Keep storage configuration runtime-driven through env vars or config, not hardcoded URIs.
3. Ensure artifact storage returns provider-neutral metadata: URI, mime type, artifact type, size, and preview capability.
4. Add unit tests for the local-safe implementation and for configuration validation.

**Tests to add / update**
- `src/Plant/BackEnd/tests/unit/test_media_artifact_store.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_media_artifact_store.py
```

### E3 — DMA generation jobs run asynchronously

#### Story E3-S1 — Add async media job state to the draft-batch generation path

| Field | Value |
|---|---|
| Story ID | `E3-S1` |
| Branch | `feat/dma-media-1-it1-async-generation-jobs` |
| Estimate | 90 min |
| BLOCKED UNTIL | `E1-S1`, `E1-S2`, and `E2-S1` merged |
| CP BackEnd pattern | `N/A` |

**Files to read first**
1. `src/Plant/BackEnd/api/v1/marketing_drafts.py`
2. `src/Plant/BackEnd/worker/tasks/component_tasks.py`
3. `src/Plant/BackEnd/services/draft_batches.py`

**Files to create / modify**
- `src/Plant/BackEnd/api/v1/marketing_drafts.py`
- `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py`
- `src/Plant/BackEnd/services/draft_batches.py`
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`

**Context**
Binary media generation cannot run inline inside the existing draft-batch POST handler without creating timeouts and poor user experience. The first async slice should let Plant acknowledge the draft batch quickly, mark requested artifacts as queued or running, and let later workers populate the persisted artifact metadata.

**Code patterns to copy exactly**
```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/marketing", tags=["marketing"])
```

```python
@router.get("/draft-batches", response_model=List[DraftBatchRecord])
async def list_draft_batches(
  db: AsyncSession = Depends(get_read_db_session),
) -> List[DraftBatchRecord]:
  ...
```

**Acceptance criteria**
1. Extend the existing draft-batch creation flow so artifact requests create queued job state instead of pretending binary output is immediately available.
2. Add a worker task file for media generation jobs; job payloads must carry correlation IDs and draft identifiers.
3. Extend draft-batch list and get responses so callers can see artifact generation status and partial completion safely.
4. Add unit coverage proving draft-batch creation remains backward-compatible for text-only requests and marks media requests as queued.

**Tests to add / update**
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`

**Docker validation command**
```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py
```
