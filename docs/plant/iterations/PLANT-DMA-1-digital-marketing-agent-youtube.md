# PLANT-DMA-1 — Digital Marketing Agent MVP (Theme Discovery, Content Creation, Approved YouTube Publishing)

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-DMA-1` |
| Feature area | Cross-surface Digital Marketing Agent MVP across Plant, CP, PP, and mobile |
| Created | 2026-03-11 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §1, §4.6, §5.1, §5.3, §11, §26 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` |
| Total iterations | 3 |
| Total epics | 6 |
| Total stories | 12 |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained and names exact file paths |
| No working memory across files | Each backend story embeds the relevant route and dependency patterns inline |
| No planning ability | Stories are atomic and sequenced backend first, then customer surfaces, then PP and hardening |
| Token cost per file read | Max 3 files in each story card's `Files to read first` section |
| Binary inference only | Acceptance criteria are written as pass/fail behavioural outcomes |

> Agent: execute exactly one story at a time. Read only the story card you were assigned and the files listed in that card.

---

## PM Review Checklist

- [x] Epic titles name customer or operator outcomes
- [x] Every story has an exact branch name
- [x] Every story card will embed relevant NFR snippets inline
- [x] Every story card will keep `Files to read first` to 3 or fewer files
- [x] CP BackEnd stories follow thin-proxy discipline
- [x] New backend route stories use `waooaw_router()`
- [x] GET route stories call out `get_read_db_session()`
- [x] Stories involving secrets name the exact credential and adapter surfaces
- [x] Every story has `BLOCKED UNTIL` or `none`
- [x] Each iteration has an estimate and come-back time
- [x] STUCK PROTOCOL is included in Agent Execution Rules
- [x] Backend stories come before frontend/mobile stories that depend on them
- [x] Iteration count is justified by cross-surface scope and approval-publish governance requirements
- [x] No placeholders remain in the skeleton

---

## Vision Intake (confirmed)

1. **Area:** Plant runtime and agent mould first, then CP, PP, and mobile operating surfaces for the first sellable Digital Marketing Agent.
2. **User outcome:** A customer hires a Digital Marketing Agent, completes a guided Theme Discovery conversation, receives channel-ready content drafts, explicitly approves each deliverable, and only then allows YouTube publication through a governed scheduler flow.
3. **Out of scope:** Multi-channel live publishing beyond YouTube, image/video generation, auto-publish without customer approval, performance optimization loops, ads management, and broad analytics automation.
4. **Lane choice:** Mixed. Lane B first for new Plant and proxy routes, then Lane A for CP, PP, and mobile wiring onto the new contracts.
5. **Timeline constraint:** Not explicitly fixed by the user; optimize for a mergeable MVP plan that can drive immediate execution after review.

---

## Architecture Decisions (read before coding)

### Product shape

The first sellable Digital Marketing Agent exposes three customer-visible skills:

1. `Theme Discovery`
2. `Content Creation`
3. `Content Publishing`

`Theme Discovery` is not a plain text field. It is a guided conversation skill that produces a structured marketing brief. `Content Creation` consumes that brief and generates customer-reviewable deliverables. `Content Publishing` is a governed publish skill that remains hard-blocked until the customer approves the exact deliverable.

The Theme Discovery output must also capture the campaign goal and success signal for the hired agent. For MVP planning, that means the brief includes at minimum: business objective, target audience, locality, profession/persona, offer, tone, YouTube intent, posting frequency, and a small set of customer-readable success metrics or expected outcomes.

### Approval invariant

No external platform handshake, upload, schedule execution, or publish submit is allowed before customer approval of the exact deliverable. For this MVP, that invariant applies to YouTube first and must be enforced in Plant runtime state and scheduler logic, not only in CP/mobile UI.

For YouTube specifically, the plan must distinguish `approved for upload` from `approved for public release`. MVP default should be fail-safe: if the workflow supports non-public YouTube visibility (`private` or `unlisted`), any later move to `public` is a second explicit customer action, never an automatic side effect.

### Channel scope

Iteration 1 channel scope is YouTube only. The model, stateless components, and destination abstractions must still be designed so Facebook, LinkedIn, X, Instagram, and future channels can be added later without redesigning customer or operator flows.

### Shared component principle

Common product components must be stateless and reusable across CP, PP, and mobile. Shared UI and runtime concepts include:

- Theme brief summary
- Objective and audience cards
- Channel selection and credential status
- Draft approval cards
- Publish cadence and schedule state
- Skill progress and run history
- Deliverable status timeline

### Runtime rule

Plant remains the source of truth for hired-agent state, skill config, deliverables, approval state, scheduler eligibility, publish receipts, and observability. CP and mobile are customer operating surfaces. PP is the operator and governance surface.

Mobile should follow the platform default: use Plant Gateway-backed routes directly unless a capability is genuinely CP-only. Do not route mobile through CP BackEnd by habit.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Agent contract, Theme Discovery brief model, approval-gated YouTube runtime and proxy layer | E1, E2 | 4 | 6h | 2026-03-12 06:00 UTC |
| 2 | Customer workflow on CP and mobile for Theme Discovery, review, approval, and publish readiness | E3, E4 | 4 | 6h | 2026-03-12 14:00 UTC |
| 3 | PP governance workflow, monitoring, scheduler hardening, and release regression | E5, E6 | 4 | 5h | 2026-03-12 20:00 UTC |

**Estimate basis:** new Plant model/runtime story = 90 min, new proxy/API story = 45 min, cross-surface customer story = 60–90 min, PP governance story = 60 min, regression/hardening story = 45–60 min.

---

## Agent Execution Rules

1. Start from `main` with a clean tree.
2. Execute only one story at a time.
3. Read only the files listed in the story card before editing.
4. Keep CP BackEnd and PP BackEnd as thin proxies only.
5. Plant owns publish eligibility, approval state, scheduler gating, and destination execution truth.
6. All external publish flows must fail closed if approval is absent, expired, revoked, or the platform credential reference is missing.
7. Mobile uses Plant Gateway-backed contracts by default; only use CP BackEnd if the capability is truly CP-only.
8. Every story ends with the exact validation command written in its card.
9. **CHECKPOINT RULE**: After completing each epic (all tests passing), run:

```bash
git add -A && git commit -m "feat([plan-id]): [epic-id] — [epic title]" && git push
```

Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

10. **STUCK PROTOCOL**: if blocked for more than 20 minutes on one story, open a draft PR titled `WIP: PLANT-DMA-1 [story-id] — [blocker]`, post the blocker, and halt.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check:**

```bash
git status && git log --oneline -3
# Must show: clean tree on main.
```

**Agent task:**

```text
You are executing Iteration 1 of PLANT-DMA-1.

EXPERT PERSONAS: Senior Python/FastAPI engineer + Senior platform runtime engineer + Senior scheduler/secrets integration engineer.
PLAN FILE: docs/plant/iterations/PLANT-DMA-1-digital-marketing-agent-youtube.md
YOUR SCOPE: Iteration 1 only — Epics E1 and E2.

EXECUTION ORDER:
1. Confirm clean tree on main.
2. Read Agent Execution Rules.
3. Read Iteration 1 only.
4. Execute E1 then E2.
5. Docker-test each story as written.
6. Open the iteration PR and stop.
```

### Iteration 2

**Pre-flight check:** Iteration 1 must already be merged to `main`.

**Agent task:**

```text
You are executing Iteration 2 of PLANT-DMA-1.

EXPERT PERSONAS: Senior React/TypeScript engineer + Senior React Native/Expo engineer + Senior customer workflow designer.
PLAN FILE: docs/plant/iterations/PLANT-DMA-1-digital-marketing-agent-youtube.md
YOUR SCOPE: Iteration 2 only — Epics E3 and E4.

EXECUTION ORDER:
1. Confirm clean tree on main and verify Iteration 1 merge.
2. Read Agent Execution Rules.
3. Read Iteration 2 only.
4. Execute E3 then E4.
5. Run the listed CP and mobile tests.
6. Open the iteration PR and stop.
```

### Iteration 3

**Pre-flight check:** Iteration 2 must already be merged to `main`.

**Agent task:**

```text
You are executing Iteration 3 of PLANT-DMA-1.

EXPERT PERSONAS: Senior PP operations workflow engineer + Senior observability engineer + Senior release-hardening engineer.
PLAN FILE: docs/plant/iterations/PLANT-DMA-1-digital-marketing-agent-youtube.md
YOUR SCOPE: Iteration 3 only — Epics E5 and E6.

EXECUTION ORDER:
1. Confirm clean tree on main and verify Iteration 2 merge.
2. Read Agent Execution Rules.
3. Read Iteration 3 only.
4. Execute E5 then E6.
5. Run the listed PP, backend, mobile, and regression checks.
6. Open the iteration PR and stop.
```

---

## Iteration Details

## Iteration 1 — Runtime Contract And Approval-Gated YouTube Foundation

**Goal:** Make the Digital Marketing Agent real in Plant runtime with visible skills, a structured Theme Discovery brief, explicit approval-gated publish semantics, and customer-side proxy routes ready for CP.

### Story Table

| Story | Title | Surface | Status | Dependency |
|---|---|---|---|---|
| I1-S1 | Register the Digital Marketing Agent and its three visible skills | Plant BackEnd | Completed | none |
| I1-S2 | Persist the Theme Discovery brief and draft workflow as first-class runtime state | Plant BackEnd | Completed | I1-S1 |
| I1-S3 | Enforce approval-gated YouTube publish eligibility and credential execution | Plant BackEnd | Completed | I1-S2 |
| I1-S4 | Expose thin CP proxy routes for the new digital marketing runtime | CP BackEnd | Completed | I1-S2 and I1-S3 |

### E1 — Customer-visible digital marketing runtime exists

#### I1-S1 — Register the Digital Marketing Agent and its three visible skills

**Branch:** `feat/plant-dma-1-it1-s1-agent-contract`  
**BLOCKED UNTIL:** none

**Outcome**  
The platform can hire a first-class `Digital Marketing Agent` whose visible skills are `Theme Discovery`, `Content Creation`, and `Content Publishing`, with YouTube represented as the first live destination.

**Files to read first**

1. `src/Plant/BackEnd/agent_mold/reference_agents.py`
2. `src/Plant/BackEnd/agent_mold/spec.py`
3. `src/Plant/BackEnd/api/v1/reference_agents.py`

**Files to create / modify**

- `src/Plant/BackEnd/agent_mold/reference_agents.py`
- `src/Plant/BackEnd/agent_mold/skills/content_models.py`
- `src/Plant/BackEnd/api/v1/reference_agents.py`
- `src/Plant/BackEnd/tests/unit/test_reference_agents_api.py`
- `src/Plant/BackEnd/tests/unit/test_agent_spec_v2.py`

**Implementation**

- Add or evolve the reference agent definition so `Digital Marketing Agent` is a first-class mould entry instead of a generic content helper.
- Model the three visible skills explicitly and ensure their runtime vocabulary matches the platform hierarchy: skill config, skill run, deliverable, approval, and publish outcome.
- Extend the content models so the structured Theme Discovery brief includes business background, objective, industry, locality, target audience, profession/persona, tone, offer, channel intent, posting cadence, and customer-facing success metrics.
- Keep the destination abstraction open-ended while marking YouTube as the only supported live destination in this MVP.

**Code patterns to copy exactly**

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/reference-agents", tags=["reference-agents"])
```

**Acceptance criteria**

- The Plant reference-agent catalogue exposes a named `Digital Marketing Agent` suitable for hiring.
- The visible skills listed for this agent are exactly Theme Discovery, Content Creation, and Content Publishing.
- Theme Discovery brief fields are structured enough to drive downstream content and publishing work without a one-line free-text dependency.
- Existing content-agent capabilities are not broken for other reference agents.

**Validation**

```bash
cd src/Plant/BackEnd && pytest tests -k "reference_agents or content_models" -x -v
```

#### I1-S2 — Persist the Theme Discovery brief and draft workflow as first-class runtime state

**Branch:** `feat/plant-dma-1-it1-s2-theme-brief-runtime`  
**BLOCKED UNTIL:** I1-S1 merged

**Outcome**  
Plant treats Theme Discovery, content draft generation, and approval staging as real campaign runtime state rather than loose text blobs or ad hoc draft batches.

**Files to read first**

1. `src/Plant/BackEnd/api/v1/campaigns.py`
2. `src/Plant/BackEnd/models/campaign.py`
3. `src/Plant/BackEnd/api/v1/marketing_drafts.py`

**Files to create / modify**

- `src/Plant/BackEnd/api/v1/campaigns.py`
- `src/Plant/BackEnd/models/campaign.py`
- `src/Plant/BackEnd/repositories/campaign_repository.py`
- `src/Plant/BackEnd/services/draft_batches.py`
- `src/Plant/BackEnd/tests/unit/test_campaign_repository.py`
- `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py`

**Implementation**

- Extend campaign runtime state so one hired instance can store a structured Theme Discovery brief, a generated brief summary, draft deliverables, and approval state.
- Keep the existing campaign and draft flow where it helps, but converge on one truthful model for digital-marketing runtime instead of parallel temporary storage.
- Add explicit state transitions for `brief_captured`, `draft_ready_for_review`, `awaiting_customer_approval`, and `approved_for_upload` so customer and operator surfaces can render truthful progress.
- Make sure deliverables remain reviewable before any external publish action is even considered.

**Code patterns to copy exactly**

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_read_db_session, get_db_session
from core.routing import waooaw_router

router = waooaw_router(prefix="/campaigns", tags=["campaigns"])

@router.get("/{campaign_id}")
async def get_campaign(
	campaign_id: str,
	db: AsyncSession = Depends(get_read_db_session),
):
	...
```

**Acceptance criteria**

- Theme Discovery brief data is stored as structured campaign state attached to the hired agent.
- Draft generation and review-ready deliverables are represented in one runtime model that CP, PP, and mobile can all consume.
- No route in this story performs a publish action.
- Read-only routes use `get_read_db_session()` and write routes use `get_db_session()`.

**Validation**

```bash
cd src/Plant/BackEnd && pytest tests -k "campaign or marketing_drafts" -x -v
```

### E2 — Approval gate and customer proxy layer exist

#### I1-S3 — Enforce approval-gated YouTube publish eligibility and credential execution

**Branch:** `feat/plant-dma-1-it1-s3-youtube-approval-gate`  
**BLOCKED UNTIL:** I1-S2 merged

**Outcome**  
Plant refuses to handshake or publish to YouTube until the exact deliverable is customer-approved and a valid YouTube platform credential reference exists.

**Files to read first**

1. `src/Plant/BackEnd/api/v1/platform_connections.py`
2. `src/Plant/BackEnd/models/platform_connection.py`
3. `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py`

**Files to create / modify**

- `src/Plant/BackEnd/api/v1/platform_connections.py`
- `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py`
- `src/Plant/BackEnd/services/marketing_scheduler.py`
- `src/Plant/BackEnd/tests/unit/test_platform_connections_api.py`
- `src/Plant/BackEnd/tests/unit/test_marketing_scheduled_posting.py`
- `src/Plant/BackEnd/tests/unit/test_youtube_publisher.py`

**Implementation**

- Add YouTube as the first supported destination in the publisher engine and keep the abstraction open for later channels.
- Enforce a hard runtime rule: approval state plus YouTube credential reference plus channel selection must all be valid before scheduling or publishing proceeds.
- If the YouTube workflow supports `private` or `unlisted` upload, require a second explicit customer release action before any move to `public` visibility.
- Make scheduler execution fail closed if approval is missing, revoked, stale, or not tied to the exact deliverable.
- Ensure publish receipts and failure reasons are recorded so CP and PP can expose truthful state.

**Code patterns to copy exactly**

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/platform-connections", tags=["platform-connections"])
```

**Acceptance criteria**

- No YouTube publish path can execute without customer approval of the exact deliverable.
- Public YouTube release cannot happen as an automatic side effect of approval or upload.
- The scheduler rejects ineligible publish jobs instead of attempting external execution.
- Publish failures and denials are persisted in a way PP can diagnose later.
- The platform-connection model still stores only secret references, never raw secrets.

**Validation**

```bash
cd src/Plant/BackEnd && pytest tests -k "platform_connection or publisher_engine or marketing_scheduler" -x -v
```

#### I1-S4 — Expose thin CP proxy routes for the new digital marketing runtime

**Branch:** `feat/plant-dma-1-it1-s4-cp-proxy-runtime`  
**BLOCKED UNTIL:** I1-S2 and I1-S3 merged

**Outcome**  
CP BackEnd exposes the Theme Discovery, draft review, approval, and YouTube connection routes needed for customer surfaces without owning business logic.

**Files to read first**

1. `src/CP/BackEnd/api/campaigns.py`
2. `src/CP/BackEnd/api/marketing_review.py`
3. `src/CP/BackEnd/api/platform_credentials.py`

**Files to create / modify**

- `src/CP/BackEnd/api/campaigns.py`
- `src/CP/BackEnd/api/marketing_review.py`
- `src/CP/BackEnd/api/platform_credentials.py`
- `src/CP/BackEnd/tests/test_campaigns_proxy.py`
- `src/CP/BackEnd/tests/test_marketing_review_routes.py`
- `src/CP/BackEnd/tests/test_platform_credentials_routes.py`

**Implementation**

- Keep CP BackEnd as a thin proxy and response-mapping layer only.
- Add or extend the proxy routes so CP can create or update Theme Discovery briefs, fetch reviewable deliverables, submit approvals, request upload eligibility, and store YouTube credential refs.
- Preserve correlation ID propagation and audit dependency patterns already used in CP.
- Do not add customer-side business logic, scheduler logic, or external publish logic in CP BackEnd.

**Code patterns to copy exactly**

```python
from fastapi import Depends
from core.routing import waooaw_router
from services.audit_dependency import AuditLogger, get_audit_logger

router = waooaw_router(prefix="/cp/campaigns", tags=["cp-campaigns"])

@router.post("/{hired_instance_id}/approve")
async def approve_campaign_item(
	hired_instance_id: str,
	audit: AuditLogger = Depends(get_audit_logger),
):
	...
```

**Acceptance criteria**

- CP has proxy coverage for Theme Discovery brief CRUD, draft review list, approval submission, and YouTube credential-ref storage.
- Audit dependency is used on the customer approval and credential-write paths.
- No CP route contains business logic that belongs in Plant.

**Validation**

```bash
cd src/CP/BackEnd && pytest tests -k "campaigns or marketing_review or platform_credentials" -x -v
```

## Iteration 2 — Customer Workflow On CP And Mobile

**Goal:** Let the customer use the Digital Marketing Agent end-to-end on web and mobile: guided Theme Discovery, content review, approval, and publish readiness tracking.

### Story Table

| Story | Title | Surface | Status | Dependency |
|---|---|---|---|---|
| I2-S1 | Build the CP Theme Discovery conversation and brief summary workflow | CP FrontEnd | Planned | Iteration 1 |
| I2-S2 | Build the CP content review, approval, and YouTube readiness workflow | CP FrontEnd | Planned | I2-S1 |
| I2-S3 | Bring Theme Discovery and brief review to mobile | mobile | Planned | Iteration 1 |
| I2-S4 | Bring approval, publish readiness, and progress state to mobile | mobile | Planned | I2-S3 |

### E3 — Customer can create a useful marketing brief

#### I2-S1 — Build the CP Theme Discovery conversation and brief summary workflow

**Branch:** `feat/plant-dma-1-it2-s1-cp-theme-discovery`  
**BLOCKED UNTIL:** Iteration 1 merged

**Outcome**  
CP gives the customer a guided conversational Theme Discovery experience that leads them toward a precise brief instead of a one-line theme box.

**Files to read first**

1. `src/CP/FrontEnd/src/services/agentSkills.service.ts`
2. `src/CP/FrontEnd/src/services/gatewayApiClient.ts`
3. `src/CP/FrontEnd/src/pages/authenticated/GoalsSetup.tsx`

**Files to create / modify**

- `src/CP/FrontEnd/src/pages/authenticated/GoalsSetup.tsx`
- `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx`
- `src/CP/FrontEnd/src/services/agentSkills.service.ts`
- `src/CP/FrontEnd/src/components/DigitalMarketingBriefStepCard.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingBriefSummaryCard.tsx`
- `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx`

**Implementation**

- Design Theme Discovery as a guided multi-step or chat-like conversation that asks for business background, objective, locality, target audience, profession/persona, tone, offer, YouTube intent, posting cadence, and expected success signal.
- Render a structured brief summary so the customer can verify what the system understood before drafts are created.
- Keep shared components stateless so the same cards and summary sections can be reused later in PP and mobile.
- Make the UI feel like the first impression of a sellable agent, not an admin form.

**Acceptance criteria**

- Customers cannot mistake Theme Discovery for a one-line input field.
- The output is a structured brief summary, not just preserved chat text.
- Shared stateless components are used for brief capture and summary rendering.
- CP tests cover at least one brief-completion happy path.

**Validation**

```bash
cd src/CP/FrontEnd && npm run build && npx vitest run src/__tests__/GoalsSetup.test.tsx src/__tests__/AuthenticatedPortal.test.tsx src/__tests__/agentSkills.service.test.ts
```

#### I2-S2 — Build the CP content review, approval, and YouTube readiness workflow

**Branch:** `feat/plant-dma-1-it2-s2-cp-review-approval`  
**BLOCKED UNTIL:** I2-S1 merged

**Outcome**  
Customers can review drafts, approve exact deliverables, connect or verify the target YouTube channel, and see that nothing will publish before approval.

**Files to read first**

1. `src/CP/FrontEnd/src/services/platformConnections.service.ts`
2. `src/CP/FrontEnd/src/services/hiredAgentDeliverables.service.ts`
3. `src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx`

**Files to create / modify**

- `src/CP/FrontEnd/src/services/platformConnections.service.ts`
- `src/CP/FrontEnd/src/services/hiredAgentDeliverables.service.ts`
- `src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx`
- `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingApprovalCard.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingPublishReadinessCard.tsx`

**Implementation**

- Reuse stateless approval and status components to show draft content, exact approval action, YouTube channel state, and publish readiness.
- Make the approval copy explicit that approval precedes any external posting.
- Show schedule and publish readiness truthfully: ready for upload, blocked by missing approval, blocked by missing YouTube connection, uploaded as non-public, ready for public release, or already published.
- Feed the same state into My Agents or portal progress surfaces so the customer can monitor the agent after setup.

**Acceptance criteria**

- Customers can approve or reject exact deliverables from CP.
- The UI clearly distinguishes review-ready from publish-ready.
- YouTube connection or readiness state is visible before any publish action.
- CP tests cover approval gating states.

**Validation**

```bash
cd src/CP/FrontEnd && npm run build && npx vitest run src/__tests__/MyAgents.test.tsx src/__tests__/AuthenticatedPortal.test.tsx src/__tests__/platformCredentials.service.test.ts
```

### E4 — Customer can operate the same agent from mobile

#### I2-S3 — Bring Theme Discovery and brief review to mobile

**Branch:** `feat/plant-dma-1-it2-s3-mobile-theme-discovery`  
**BLOCKED UNTIL:** Iteration 1 merged

**Outcome**  
Mobile customers can complete or continue Theme Discovery and review the resulting structured brief without losing context from CP.

**Files to read first**

1. `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`
2. `src/mobile/src/navigation/MainNavigator.tsx`
3. `src/mobile/src/lib/apiClient.ts`

**Files to create / modify**

- `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`
- `src/mobile/src/navigation/MainNavigator.tsx`
- `src/mobile/src/components/DigitalMarketingBriefSummaryCard.tsx`
- `src/mobile/src/components/DigitalMarketingBriefStepCard.tsx`
- `src/mobile/__tests__/AgentOperationsScreen.test.tsx`
- `src/mobile/__tests__/MyAgentsScreen.test.tsx`

**Implementation**

- Add a mobile-friendly Theme Discovery continuation flow rather than trying to mirror the full CP layout.
- Use Gateway-backed contracts by default; do not add a CP-specific mobile dependency unless a CP-only route is required.
- Reuse the same stateless brief-summary concepts so CP and mobile stay semantically aligned.
- Ensure the customer can resume where they left off and review the structured brief before draft generation.
- Keep mobile navigation precise so notifications or agent-entry routes can land on the correct digital-marketing view.

**Acceptance criteria**

- Mobile can show and update the Theme Discovery brief for the hired Digital Marketing Agent.
- Brief-summary components are reused rather than rebuilt as a separate model.
- The customer can resume Theme Discovery context from agent operations.

**Validation**

```bash
cd src/mobile && npm test -- --runTestsByPath __tests__/AgentOperationsScreen.test.tsx __tests__/MyAgentsScreen.test.tsx --maxWorkers=2
```

#### I2-S4 — Bring approval, publish readiness, and progress state to mobile

**Branch:** `feat/plant-dma-1-it2-s4-mobile-approval-status`  
**BLOCKED UNTIL:** I2-S3 merged

**Outcome**  
Mobile customers can approve deliverables, confirm YouTube publish readiness, and monitor the agent’s progress from the same runtime surface.

**Files to read first**

1. `src/mobile/src/components/ContentDraftApprovalCard.tsx`
2. `src/mobile/src/screens/agents/MyAgentsScreen.tsx`
3. `src/mobile/src/screens/profile/NotificationsScreen.tsx`

**Files to create / modify**

- `src/mobile/src/components/ContentDraftApprovalCard.tsx`
- `src/mobile/src/screens/agents/MyAgentsScreen.tsx`
- `src/mobile/src/screens/profile/NotificationsScreen.tsx`
- `src/mobile/src/services/hiredAgents/hiredAgents.service.ts`
- `src/mobile/__tests__/NotificationsScreen.test.tsx`

**Implementation**

- Extend the existing approval-card pattern to represent digital-marketing deliverables, explicit approval, and YouTube readiness.
- Surface blocked-vs-ready-vs-uploaded-vs-public states in My Agents so the customer sees truthful progress.
- Route notification taps into the right approval or publish-readiness screen.
- Keep approval exact and explicit: no mobile action should imply publish without approval.

**Acceptance criteria**

- Mobile customers can approve or reject exact digital-marketing deliverables.
- My Agents shows progress and blocked states for the Digital Marketing Agent.
- Notification-driven re-entry lands on the correct approval or status surface.

**Validation**

```bash
cd src/mobile && npm run typecheck && npm test -- --runTestsByPath __tests__/MyAgentsScreen.test.tsx __tests__/NotificationsScreen.test.tsx --maxWorkers=2
```

## Iteration 3 — PP Governance, Monitoring, And Release Hardening

**Goal:** Give PP users full operator visibility into the Digital Marketing Agent and make the runtime safe to ship with observability, scheduler hardening, and regression coverage.

### Story Table

| Story | Title | Surface | Status | Dependency |
|---|---|---|---|---|
| I3-S1 | Build PP oversight for briefs, approvals, and YouTube publish state | PP FrontEnd and PP BackEnd | Planned | Iterations 1 and 2 |
| I3-S2 | Build PP diagnostics for blocked publish, credentials, and scheduler traces | PP FrontEnd and PP BackEnd | Planned | I3-S1 |
| I3-S3 | Add audit, metrics, and run-history alignment for the agent lifecycle | Plant, CP, PP, mobile | Planned | I3-S1 |
| I3-S4 | Add regression coverage and release-closeout for the first sellable agent | cross-surface | Planned | I3-S2 and I3-S3 |

### E5 — PP can support and govern the agent

#### I3-S1 — Build PP oversight for briefs, approvals, and YouTube publish state

**Branch:** `feat/plant-dma-1-it3-s1-pp-oversight`  
**BLOCKED UNTIL:** Iterations 1 and 2 merged

**Outcome**  
PP users can inspect the customer’s marketing brief, approval queue, YouTube readiness, and publish state without guessing how the Digital Marketing Agent is operating.

**Files to read first**

1. `src/PP/BackEnd/api/ops_hired_agents.py`
2. `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx`
3. `src/PP/FrontEnd/src/pages/ReviewQueue.tsx`

**Files to create / modify**

- `src/PP/BackEnd/api/ops_hired_agents.py`
- `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx`
- `src/PP/FrontEnd/src/pages/ReviewQueue.tsx`
- `src/PP/BackEnd/tests/test_ops_hired_agents.py`
- `src/PP/FrontEnd/src/__tests__/HiredAgentsOps.test.tsx`
- `src/PP/FrontEnd/src/pages/ReviewQueue.test.tsx`

**Implementation**

- Extend PP runtime views so the Digital Marketing Agent surfaces the brief summary, approval queue state, channel readiness, and publish outcomes in one coherent workflow.
- Reuse the same stateless summary concepts from customer surfaces where practical, but with operator-focused labels and diagnostics.
- Make clear whether a deliverable is waiting on customer approval, waiting on YouTube credentials, uploaded in non-public visibility, waiting on public release, published, or failed.

**Code patterns to copy exactly**

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/ops/hired-agents", tags=["ops-hired-agents"])
```

**Acceptance criteria**

- PP can inspect brief, approval, and publish state for the Digital Marketing Agent from one operator context.
- Operator screens distinguish customer-blocked from platform-blocked publish states.
- PP remains a support and governance surface, not a second customer workflow.

**Validation**

```bash
cd src/PP/BackEnd && pytest tests -k "ops_hired_agents" -x -v
cd /workspaces/WAOOAW/src/PP/FrontEnd && npm run build && npx vitest run src/__tests__/HiredAgentsOps.test.tsx src/pages/ReviewQueue.test.tsx
```

#### I3-S2 — Build PP diagnostics for blocked publish, credentials, and scheduler traces

**Branch:** `feat/plant-dma-1-it3-s2-pp-diagnostics`  
**BLOCKED UNTIL:** I3-S1 merged

**Outcome**  
PP can diagnose why a YouTube publish did not happen and whether the blocker was approval, credentials, scheduler state, or external publish failure.

**Files to read first**

1. `src/PP/FrontEnd/src/components/SchedulerDiagnosticsPanel.tsx`
2. `src/PP/FrontEnd/src/components/HookTracePanel.tsx`
3. `src/PP/BackEnd/api/approvals.py`

**Files to create / modify**

- `src/PP/FrontEnd/src/components/SchedulerDiagnosticsPanel.tsx`
- `src/PP/FrontEnd/src/components/HookTracePanel.tsx`
- `src/PP/BackEnd/api/approvals.py`
- `src/PP/BackEnd/tests/test_approval_routes.py`
- `src/PP/FrontEnd/src/__tests__/SchedulerDiagnosticsPanel.test.tsx`
- `src/PP/FrontEnd/src/__tests__/HookTracePanel.test.tsx`

**Implementation**

- Surface publish-block reasons explicitly: no approval, revoked approval, missing YouTube credential ref, scheduler denial, uploaded non-public and awaiting release, external publish failure.
- Show enough hook and scheduler trace context for PP to support the first sellable agent without direct database inspection.
- Make approval lineage visible so operators can verify which deliverable version the customer approved.

**Acceptance criteria**

- PP diagnostics can explain why a publish job was blocked or failed.
- Approval lineage and scheduler state are visible from operator tooling.
- Operator diagnostics do not require ad hoc DB access to answer first-line support questions.

**Validation**

```bash
cd src/PP/BackEnd && pytest tests -k "approval_routes or ops_diagnostics" -x -v
cd /workspaces/WAOOAW/src/PP/FrontEnd && npm run build && npx vitest run src/__tests__/SchedulerDiagnosticsPanel.test.tsx src/__tests__/HookTracePanel.test.tsx
```

### E6 — The agent is supportable and release-ready

#### I3-S3 — Add audit, metrics, and run-history alignment for the agent lifecycle

**Branch:** `feat/plant-dma-1-it3-s3-observability-audit`  
**BLOCKED UNTIL:** I3-S1 merged

**Outcome**  
The Digital Marketing Agent exposes a complete audit and progress spine for Theme Discovery, draft creation, approval events, scheduler decisions, and YouTube publish attempts.

**Files to read first**

1. `src/Plant/BackEnd/api/v1/flow_runs.py`
2. `src/CP/BackEnd/api/cp_flow_runs.py`
3. `src/Plant/BackEnd/services/audit_service.py`

**Files to create / modify**

- `src/Plant/BackEnd/api/v1/flow_runs.py`
- `src/CP/BackEnd/api/cp_flow_runs.py`
- `src/Plant/BackEnd/core/metrics.py`
- `src/Plant/BackEnd/services/audit_service.py`
- `src/Plant/BackEnd/tests/unit/test_flow_runs_api.py`
- `src/Plant/BackEnd/tests/unit/test_metrics.py`

**Implementation**

- Ensure Theme Discovery, Content Creation, approval, upload, public-release, and publish execution appear coherently in skill-run and component-run history.
- Emit audit and metric coverage for customer approval, scheduler gate decisions, and publish outcomes.
- Keep the naming aligned with the canonical runtime vocabulary so CP, PP, and mobile can all narrate progress consistently.

**Acceptance criteria**

- Run history can show the major lifecycle steps for the Digital Marketing Agent.
- Audit events exist for customer approval and publish-attempt outcomes.
- Metrics and history are sufficient for support and release-readiness monitoring.

**Validation**

```bash
cd src/Plant/BackEnd && pytest tests -k "flow_runs or audit or metrics" -x -v
cd /workspaces/WAOOAW/src/CP/BackEnd && pytest tests -k "cp_flow_runs" -x -v
```

#### I3-S4 — Add regression coverage and release-closeout for the first sellable agent

**Branch:** `feat/plant-dma-1-it3-s4-regression-release`  
**BLOCKED UNTIL:** I3-S2 and I3-S3 merged

**Outcome**  
The first sellable Digital Marketing Agent has enough regression coverage, smoke validation, and release notes to ship confidently as a real marketplace offering.

**Files to read first**

1. `src/CP/FrontEnd/e2e/hire-journey.spec.ts`
2. `src/PP/FrontEnd/e2e/operator-smoke.spec.ts`
3. `scripts/test-web.sh`

**Files to create / modify**

- `src/CP/FrontEnd/e2e/hire-journey.spec.ts`
- `src/PP/FrontEnd/e2e/operator-smoke.spec.ts`
- `src/mobile/__tests__/AgentOperationsScreen.test.tsx`
- `src/mobile/__tests__/MyAgentsScreen.test.tsx`
- `src/mobile/__tests__/NotificationsScreen.test.tsx`
- `scripts/test-web.sh` only if the new web journey must be added to a shared regression entrypoint
- `running_commentary.md` for residual risk notes
- `scripts/test-mobile.sh` only if the new mobile journey must be added to a shared regression entrypoint

**Implementation**

- Add at least one cross-surface regression slice proving Theme Discovery, draft review, approval, and publish-readiness behaviour.
- Validate that YouTube publish remains gated by customer approval in the release candidate path.
- Record any residual v1 limitations clearly, especially that live publishing is YouTube-only and multi-network expansion is future work.

**Acceptance criteria**

- Regression coverage exists for the core sellable Digital Marketing Agent workflow.
- Release notes or commentary record the MVP boundary and known limitations.
- The platform can truthfully present this as the first sellable agent offering.

**Validation**

```bash
bash scripts/test-web.sh --quick
cd src/mobile && npm run typecheck && npm test -- --maxWorkers=2
```

---

## Recommended Merge Order

1. Iteration 1
2. Iteration 2
3. Iteration 3

This order matters because the agent contract and approval-gated runtime must exist before any CP/mobile workflow is built, and customer surfaces must exist before PP support and release hardening become meaningful.