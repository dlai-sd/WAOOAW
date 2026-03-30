# CP-STUDIO-5 — DMA YouTube Post-Connect Vertical Slice

## Problem Statement

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| The DMA wizard currently stops at a generic connected state and does not surface the exact linked YouTube channel as the durable channel of record. | A customer can connect YouTube but still cannot confidently tell which channel will be used for draft generation and later posting. | Reuse the existing YouTube connection records and activation workspace bindings to show the linked channel, verification state, and reconnect path directly inside the DMA journey. |
| CP marketing review routes still derive `customer_id` with a `CUST-` prefix and do not expose create-draft or execute-now proxy routes. | Draft list, create, and execute semantics can drift away from the raw customer identity used by the now-working YouTube OAuth flow. | Normalize CP marketing routes to the raw WAOOAW customer ID and add the missing thin-proxy routes for create-draft and execute-now. |
| Plant draft execution currently stops at policy approval, while scheduled posting uses mocked providers for all channels. | “Publish now” and “queue” look available in code but do not provide a real YouTube posting path for the DMA YouTube slice. | Route YouTube draft execution and scheduler dispatch through the existing `integrations/social/youtube_client.py` boundary while leaving other channels mocked in this iteration. |
| Review and publish readiness UI exists mainly in My Agents deliverable flows, not in the DMA wizard itself. | The customer has to leave the activation journey to finish draft review and publish intent, which breaks the product story needed here. | Embed draft generation, review, approve, publish-now, and queue actions into the DMA wizard while keeping deliverable-centric flows unchanged. |

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-STUDIO-5` |
| Feature area | Customer Portal — DMA YouTube post-connect flow |
| Created | 2026-03-30 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | Copilot chat requirement dated 2026-03-30 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 3 |
| Total stories | 6 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained with exact files, exact contracts, and exact acceptance criteria. |
| No working memory across files | NFR and proxy patterns are embedded inline in each story card. |
| No planning ability | Stories are atomic and sequenced by dependency. |
| Token cost per file read | Every story caps “Files to read first” at 3 files. |
| Binary inference only | Acceptance criteria are pass/fail and customer-visible. |

> Agent: execute exactly one story at a time. Read only the files named in your story card before you begin coding.

---

## PM Review Checklist (tick every box before publishing)

- [x] EXPERT PERSONAS filled
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in “Files to read first”
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or `none`)
- [x] Iteration has a time estimate and come-back datetime
- [x] Iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend before frontend
- [x] Iteration count minimized for PR-only delivery
- [x] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [x] No placeholders remain

---

## Story Tracker

| Tracking | Story ID | Epic | Customer outcome | Branch |
|---|---|---|---|---|
| Not started | E1-S1 | E1 | Connected YouTube identity and draft routes use one customer contract. | feat/cp-studio-5-it1-e1 |
| Not started | E1-S2 | E1 | Approved YouTube draft can publish now or queue through the real YouTube boundary. | feat/cp-studio-5-it1-e1 |
| Not started | E2-S1 | E2 | Frontend has one typed service surface for linked channel, draft create, draft review, and execute. | feat/cp-studio-5-it1-e2 |
| Not started | E2-S2 | E2 | DMA wizard shows the linked channel and can generate the first YouTube draft inline. | feat/cp-studio-5-it1-e2 |
| Not started | E3-S1 | E3 | Customer can approve, publish now, or queue from the same DMA journey. | feat/cp-studio-5-it1-e3 |
| Not started | E3-S2 | E3 | Team has prove-it regression coverage for the full one-iteration slice. | feat/cp-studio-5-it1-e3 |

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | One vertical slice: linked YouTube channel, draft generation, review/approve, publish now, and queue for DMA YouTube only. | 3 | 6 | 7h | 2026-03-30 22:30 IST |

**Estimate basis:** CP thin-proxy route change = 45 min | Plant publish boundary change = 90 min | FE service layer = 30 min | DMA wizard UI change = 90 min | inline review/publish UI = 60 min | regression = 75 min.

### PR-Overhead Optimization Rules

- This is a single-iteration plan by user request.
- Scope is limited to YouTube and DMA agents only.
- Multi-platform support, non-DMA agents, and full scheduler hardening remain out of scope.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` on Linux/Windows or `Cmd+Alt+I` on Mac
3. Click the model dropdown → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` and select **platform-engineer**
6. Paste the block below and press Enter
7. Go away. Come back at: **2026-03-30 22:30 IST**

**Iteration 1 agent task** (paste verbatim):

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior React 18 / TypeScript / Fluent UI engineer + Senior YouTube OAuth/publishing integration engineer.
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-STUDIO-5-dma-youtube-post-connect.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3.
TIME BUDGET: 7h. If you reach 8h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: E1 → E2 → E3
6. Update the Story Tracker row after each story, push the epic branch, and continue.
7. When all epics are tested and the iteration PR is open, post the PR URL. HALT.
```

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/cp-studio-5-it1-e1
git commit --allow-empty -m "chore(cp-studio-5): start iteration 1"
git push origin feat/cp-studio-5-it1-e1

gh pr create \
  --base main \
  --head feat/cp-studio-5-it1-e1 \
  --draft \
  --title "tracking: CP-STUDIO-5 Iteration 1 — in progress" \
  --body "## tracking: CP-STUDIO-5 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] CP marketing proxy uses the same customer contract as YouTube OAuth
- [ ] [E1-S2] Plant YouTube draft execute and scheduler use the real publish boundary
- [ ] [E2-S1] CP frontend service layer exposes draft create and execute
- [ ] [E2-S2] DMA wizard shows linked channel and generates draft inline
- [ ] [E3-S1] DMA wizard supports approve, publish now, and queue
- [ ] [E3-S2] Regression coverage proves the full slice

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline

One epic = one branch: `feat/cp-studio-5-it1-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card.
Do not refactor unrelated flows.
Do not touch non-DMA, non-YouTube behavior unless a listed acceptance criterion requires it.

### Rule 3 — CP BackEnd thin-proxy rule

CP BackEnd is a thin proxy, not a business-logic layer.
For any `/api/cp/...` addition in this plan, keep logic to: authenticate user, derive raw customer ID, forward headers, call Plant, translate upstream errors, and return the response.

### Rule 4 — Test discipline

Run the narrowest useful checks after each epic, then run the full iteration checks before opening the PR.

**Per-epic checks:**
```bash
docker compose -f docker-compose.test.yml run --rm cp-backend-test src/CP/BackEnd/tests/test_marketing_review_routes.py -q
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py src/Plant/BackEnd/tests/unit/test_marketing_scheduled_posting.py -q
cd src/CP/FrontEnd && npm run test -- --run src/__tests__/digitalMarketingActivation.service.test.ts src/__tests__/MyAgents.test.tsx
```

**Final iteration checks:**
```bash
docker compose -f docker-compose.test.yml run --rm cp-backend-test src/CP/BackEnd/tests/test_marketing_review_routes.py -q
docker compose -f docker-compose.test.yml run --rm plant-backend-test src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py src/Plant/BackEnd/tests/unit/test_marketing_scheduled_posting.py src/Plant/BackEnd/tests/e2e/test_e2e_marketing_workflow.py -q
cd src/CP/FrontEnd && npm run test -- --run src/__tests__/digitalMarketingActivation.service.test.ts src/__tests__/MyAgents.test.tsx
cd src/CP/FrontEnd && npm run build
```

### Rule 5 — STUCK PROTOCOL

If blocked for more than 20 minutes on one story:
1. Post the blocker in the tracking PR.
2. Commit any safe partial progress.
3. Stop only if the blocker is external and cannot be reduced further.

### CHECKPOINT RULE

After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat([plan-id]): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

### Rule 6 — Image promotion and runtime config

Do not hardcode any environment-specific hostname, redirect URI, customer identifier prefix, or scheduler toggle into code.
Use existing runtime config and current window location patterns only.

---

## Iteration 1

### Dependency Map

| Story | Depends on | Why |
|---|---|---|
| E1-S1 | none | CP proxy contract and missing routes are the first blocker for draft continuity. |
| E1-S2 | E1-S1 | Publish-now and queue semantics should use the same draft and customer contract fixed in E1-S1. |
| E2-S1 | E1-S1 | FE service additions depend on CP create/execute routes existing. |
| E2-S2 | E2-S1 | Wizard UI needs the typed FE service surface before wiring generation and linked-channel display. |
| E3-S1 | E1-S2, E2-S2 | Inline publish controls depend on both the real publish boundary and the wizard draft state. |
| E3-S2 | E1-S1, E1-S2, E2-S1, E2-S2, E3-S1 | Regression coverage belongs on the finished slice. |

---

### Epic E1 — Connected YouTube identity and draft routes become one source of truth

**Outcome:** The same raw customer identity and the same YouTube credential now carry all the way from OAuth connection into draft creation, review, execute-now, and queue.

#### Story E1-S1 — CP marketing proxy uses the same customer contract as YouTube OAuth

| Field | Value |
|---|---|
| Story ID | E1-S1 |
| Branch | feat/cp-studio-5-it1-e1 |
| Estimate | 45 min |
| BLOCKED UNTIL | none |
| Files to read first | `src/CP/BackEnd/api/marketing_review.py` · `src/CP/BackEnd/tests/test_marketing_review_routes.py` · `src/CP/BackEnd/api/cp_youtube_connections.py` |
| Files to create / modify | `src/CP/BackEnd/api/marketing_review.py` · `src/CP/BackEnd/tests/test_marketing_review_routes.py` |
| CP pattern | Pattern B — missing `/cp/*` routes are added in CP BackEnd, but CP remains a thin proxy to existing Plant routes. |

**Context**

`marketing_review.py` still derives `customer_id` as `CUST-{user.id}` while the fixed YouTube connection flow now uses raw `str(user.id)`. The same file also lacks `POST /api/cp/marketing/draft-batches` and `POST /api/cp/marketing/draft-posts/execute`, which means the frontend cannot create a YouTube draft batch or request publish-now through CP.

**Required change**

Normalize `marketing_review.py` to raw `str(user.id)` and add two thin-proxy routes:
- `POST /api/cp/marketing/draft-batches`
- `POST /api/cp/marketing/draft-posts/execute`

Both routes must forward `Authorization` and `X-Correlation-ID`, inject the raw customer ID, and pass through Plant errors without adding business logic.

**Code patterns to copy exactly**

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/cp/marketing", tags=["cp-marketing"])

def _customer_id_from_user(user: User) -> str:
    return str(user.id)
```

```python
resp = await plant.request_json(
    method="POST",
    path="api/v1/marketing/draft-batches",
    headers=_forward_headers(request),
    json_body={**payload, "customer_id": _customer_id_from_user(current_user)},
)
```

**Acceptance criteria**

- `list_draft_batches()` and all new create/execute paths use raw `str(user.id)`.
- New CP create route forwards to Plant `POST /api/v1/marketing/draft-batches`.
- New CP execute route forwards to Plant `POST /api/v1/marketing/draft-posts/{post_id}/execute`.
- Existing list, approve, reject, and schedule behavior remains unchanged except for the corrected customer contract.
- `test_marketing_review_routes.py` proves raw-customer-id forwarding plus the new create and execute proxy routes.

---

#### Story E1-S2 — Plant YouTube draft execute and scheduler use the real publish boundary

| Field | Value |
|---|---|
| Story ID | E1-S2 |
| Branch | feat/cp-studio-5-it1-e1 |
| Estimate | 90 min |
| BLOCKED UNTIL | E1-S1 complete |
| Files to read first | `src/Plant/BackEnd/api/v1/marketing_drafts.py` · `src/Plant/BackEnd/services/marketing_scheduler.py` · `src/Plant/BackEnd/integrations/social/youtube_client.py` |
| Files to create / modify | `src/Plant/BackEnd/api/v1/marketing_drafts.py` · `src/Plant/BackEnd/services/marketing_providers.py` · `src/Plant/BackEnd/services/marketing_scheduler.py` · `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py` · `src/Plant/BackEnd/tests/unit/test_marketing_scheduled_posting.py` |
| CP pattern | none — Plant BackEnd business logic only |

**Context**

`execute_draft_post()` currently stops after policy approval and uses `get_read_db_session()`, so it never writes publish results and never posts to YouTube. `marketing_scheduler.py` does update post status, but `default_social_provider()` is still all-mock, so queueing a YouTube post cannot use the real OAuth-backed client.

**Required change**

Make YouTube-only publish execution real in this slice:
- `execute_draft_post()` becomes a write path using `get_db_session()`.
- Approved YouTube posts with `credential_ref` publish through `integrations/social/youtube_client.py` and persist `provider_post_id`, `provider_post_url`, and posted execution status.
- Scheduler passes `credential_ref` through and uses the same YouTube boundary for queued YouTube posts.
- Non-YouTube channels stay mock-backed in this iteration.

**Code patterns to copy exactly**

```python
@router.post("/draft-posts/{post_id}/execute", response_model=ExecuteDraftPostResponse)
async def execute_draft_post(
    post_id: str,
    body: ExecuteDraftPostRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    policy_audit: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
) -> ExecuteDraftPostResponse:
    ...
```

```python
client = YouTubeClient(customer_id=batch.customer_id)
result = await client.post_text(
    credential_ref=post.credential_ref,
    text=post.text,
)
```

**Acceptance criteria**

- Immediate execute refuses unknown, unapproved, or credential-less YouTube posts with the existing policy-style errors.
- Immediate execute writes posted status and provider receipt fields when YouTube publish succeeds.
- Scheduler uses the same credential-aware publish path for queued YouTube posts.
- `marketing_providers.py` remains mock for non-YouTube channels.
- Plant tests mock the YouTube client and prove zero real network access.

---

### Epic E2 — Customer can generate and review the first YouTube draft without leaving the DMA wizard

**Outcome:** After connecting YouTube, the DMA customer sees the exact linked channel and can generate the first draft batch inline from the same wizard.

#### Story E2-S1 — CP frontend service layer exposes draft create and execute

| Field | Value |
|---|---|
| Story ID | E2-S1 |
| Branch | feat/cp-studio-5-it1-e2 |
| Estimate | 30 min |
| BLOCKED UNTIL | E1-S1 complete |
| Files to read first | `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` · `src/CP/FrontEnd/src/services/marketingReview.service.ts` · `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` |
| Files to create / modify | `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` · `src/CP/FrontEnd/src/services/marketingReview.service.ts` · `src/CP/FrontEnd/src/__tests__/digitalMarketingActivation.service.test.ts` |
| CP pattern | Pattern A — CP FrontEnd calls existing `/api/cp/*` routes through typed service helpers only. |

**Context**

The frontend already knows how to read the activation workspace and YouTube connection state, but it does not expose typed helpers for create-draft or execute-now. That forces any new wizard UI to either duplicate request shapes or bypass the intended CP service layer.

**Required change**

Add typed helpers and request/response models for:
- create draft batch
- execute draft post now
- list batches filtered to the active hired instance on the client side when needed

Keep all browser calls on `/api/cp/...` through `gatewayRequestJson()`; no direct `/api/v1/...` calls from the browser.

**Code patterns to copy exactly**

```typescript
return gatewayRequestJson<T>(`/cp/marketing/...`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(input),
})
```

**Acceptance criteria**

- Service layer exports typed `createDraftBatch()` and `executeDraftPost()` helpers.
- Types include the YouTube-specific fields already supported by Plant: `youtube_credential_ref`, `youtube_visibility`, and `public_release_requested`.
- Existing list, approve, reject, and schedule helpers keep their current signatures unless a typed improvement is required for this slice.
- Service tests cover the new request shapes and endpoints.

---

#### Story E2-S2 — DMA wizard shows linked channel and generates draft inline

| Field | Value |
|---|---|
| Story ID | E2-S2 |
| Branch | feat/cp-studio-5-it1-e2 |
| Estimate | 90 min |
| BLOCKED UNTIL | E2-S1 complete |
| Files to read first | `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` · `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` · `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` |
| Files to create / modify | `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` · `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx` |
| CP pattern | Pattern A — frontend-only wiring against existing CP services |

**Context**

The wizard already knows the selected platforms and the YouTube connection APIs, but the current UX stops at a generic connected state. The customer still cannot see the exact linked channel or press one clear CTA to generate the first YouTube draft.

**Required change**

Update `DigitalMarketingActivationWizard.tsx` so the YouTube connection section shows:
- linked channel display name
- verification or reconnect-needed state
- credential attachment status for the active hired instance
- one “Generate YouTube Draft” CTA once the theme plan and YouTube binding are both ready

The CTA should create a draft batch from the active workspace and render the returned posts inline in the wizard.

**Acceptance criteria**

- The wizard shows the exact linked YouTube channel name rather than only a generic connected badge.
- If the connection exists but is not attached or not verified, the wizard shows the next action clearly.
- “Generate YouTube Draft” is disabled until YouTube is selected, attached, and the brief/theme state is complete.
- Clicking the CTA creates a draft batch and renders returned draft posts without navigating away from the wizard.
- Existing YouTube OAuth connect and reconnect behavior keeps working.

---

### Epic E3 — Customer can approve, publish now, or queue from the same DMA journey

**Outcome:** The DMA customer finishes the full YouTube slice in one place: review the generated draft, approve it, publish immediately, or queue it for later.

#### Story E3-S1 — DMA wizard supports approve, publish now, and queue

| Field | Value |
|---|---|
| Story ID | E3-S1 |
| Branch | feat/cp-studio-5-it1-e3 |
| Estimate | 60 min |
| BLOCKED UNTIL | E1-S2 and E2-S2 complete |
| Files to read first | `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` · `src/CP/FrontEnd/src/services/marketingReview.service.ts` · `src/CP/FrontEnd/src/services/hiredAgentDeliverables.service.ts` |
| Files to create / modify | `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` · `src/CP/FrontEnd/src/services/marketingReview.service.ts` · `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx` |
| CP pattern | Pattern A — frontend-only wiring against the CP review routes created earlier |

**Context**

The existing review UI in My Agents is deliverable-centric, while the DMA wizard has no inline draft review or publish controls. The service layer already supports approve, reject, and schedule; this iteration adds execute-now and then wires the wizard to all four actions.

**Required change**

Render inline per-post actions in the wizard:
- Approve
- Reject
- Publish now
- Queue for later

Reuse the current customer-facing readiness language wherever practical, but do not refactor deliverable flows in this iteration.

**Acceptance criteria**

- Publish-now is unavailable until the post is approved and the YouTube binding is attached.
- Queue action captures a schedule timestamp and calls the CP schedule route.
- Publish-now calls the new CP execute route and updates the post state inline.
- When Plant returns `provider_post_url`, the wizard surfaces it as the publish receipt.
- Reject keeps the post out of follow-on publish actions in the same wizard session.

---

#### Story E3-S2 — Regression coverage proves the full slice

| Field | Value |
|---|---|
| Story ID | E3-S2 |
| Branch | feat/cp-studio-5-it1-e3 |
| Estimate | 75 min |
| BLOCKED UNTIL | E1-S1, E1-S2, E2-S1, E2-S2, E3-S1 complete |
| Files to read first | `src/CP/BackEnd/tests/test_marketing_review_routes.py` · `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py` · `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx` |
| Files to create / modify | `src/CP/BackEnd/tests/test_marketing_review_routes.py` · `src/Plant/BackEnd/tests/unit/test_marketing_draft_batch_api.py` · `src/Plant/BackEnd/tests/unit/test_marketing_scheduled_posting.py` · `src/CP/FrontEnd/src/__tests__/digitalMarketingActivation.service.test.ts` · `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx` |
| CP pattern | none — regression only |

**Context**

This slice crosses CP proxying, Plant business logic, and CP frontend wizard behavior. Without explicit regression coverage, the next YouTube or DMA change will likely break one of the transitions that now matter for the product story.

**Required change**

Add or update tests so the full slice is provable:
- CP backend tests prove raw-customer-id forwarding plus create and execute proxy coverage.
- Plant tests prove execute-now persists posted state and scheduler reuses the credential-aware publish path.
- Frontend tests prove linked-channel rendering, generate-draft CTA enablement, approve/publish-now/queue actions, and inline state updates.

**Acceptance criteria**

- No new story ships without updated automated coverage.
- Plant publish tests use mocks or monkeypatching only; zero live Google calls.
- Frontend tests assert customer-visible labels and CTA enable/disable rules, not just internal callbacks.
- The final iteration commands in Agent Execution Rules pass before the PR is opened.

---

## Out of Scope

| Area | Why it is out of scope in CP-STUDIO-5 |
|---|---|
| Multi-platform publish beyond YouTube | User explicitly constrained this slice to YouTube only. |
| Non-DMA agents such as Share Trader | This plan is for the DMA YouTube journey only. |
| Full scheduler hardening, retries, and operations dashboards | Current goal is customer-visible publish-now and queue for one verified YouTube path, not full production scheduler maturity. |
| Deliverable-flow refactor in My Agents | Existing deliverable review surfaces remain as-is; this iteration only reuses language and proven patterns. |
