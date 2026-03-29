# CP-YT-CONN-1 — CP Web YouTube Connection Unblock Iteration Plan

## Objective

Restore a working one-time YouTube connection flow in CP web so a customer can clear Google sign-in, save a reusable YouTube channel connection against their WAOOAW customer profile, attach it to the hired digital-marketing agent, and reuse it later for scheduled publishing without logging in again.

## Defect List

| Defect ID | Root cause | Impact | Best possible solution/fix |
|---|---|---|---|
| DEF-YT-01 | The Google OAuth app is requesting sensitive YouTube scopes, but the Google-side consent configuration is not ready for the current demo flow. | Customers hit the “Google hasn’t verified this app” warning before WAOOAW can finish YouTube sign-in. | Include an operator-gated Google OAuth setup checklist in this iteration, verify redirect URIs and test-user access, and capture proof before merge. |
| DEF-YT-02 | CP BackEnd YouTube proxy still forwards a prefixed customer identifier while Plant stores and queries YouTube credentials by exact customer identifier. | OAuth start/finalize/list/get/attach can drift from the actual customer record and produce broken saved-connection behavior after sign-in. | Normalize the CP YouTube proxy to the raw WAOOAW customer ID and lock it with route tests. |
| DEF-YT-03 | CP web has the pieces for start/finalize/list/attach, but the hire/setup journey still needs explicit closure around callback completion, saved-channel selection, and attach-to-hire continuity. | A customer can begin the flow but not reliably finish with a reusable, attached YouTube channel that is visibly ready for later publishing. | Harden the wizard callback, saved-channel selection, and attach flow so the chosen channel becomes the durable connection of record. |
| DEF-YT-04 | Runtime validation is split across backend, web UI, and Google-side setup with no single iteration-owned verification path. | Regressions can survive until demo deployment, and the team lacks a clean prove-it path for “connect once, publish later.” | Add explicit regression coverage and rollout evidence for Google setup, CP web flow, and attached YouTube readiness. |

## Story Tracker

| Tracking | Story ID | Epic | Customer outcome | Branch |
|---|---|---|---|---|
| Completed | E1-S1 | Customer reaches a trusted Google sign-in screen | Operator has the exact Google OAuth setup checklist and evidence requirements needed to unblock the warning screen. | feat/cp-yt-conn-1-it1-e1 |
| Completed | E1-S2 | Customer reaches a trusted Google sign-in screen | CP sends the same customer identity contract that Plant uses when saving YouTube connections. | feat/cp-yt-conn-1-it1-e1 |
| Completed | E2-S1 | Customer saves one reusable YouTube connection | Hire setup finalizes Google callback state and keeps the chosen YouTube channel selected in the wizard. | feat/cp-yt-conn-1-it1-e2 |
| Completed | E2-S2 | Customer saves one reusable YouTube connection | Saving the wizard attaches the selected YouTube credential to the hired agent so later publishing can reuse it. | feat/cp-yt-conn-1-it1-e2 |
| Completed | E3-S1 | Customer sees reliable YouTube readiness later | My Agents clearly shows not connected, ready to attach, connected, and reconnect-required states with the right next action. | feat/cp-yt-conn-1-it1-e3 |
| Completed | E3-S2 | Customer sees reliable YouTube readiness later | The team has a prove-it regression path and rollout evidence for connect once, publish later. | feat/cp-yt-conn-1-it1-e3 |

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | CP-YT-CONN-1 |
| Feature area | Customer Portal Web — YouTube connection unblock |
| Created | 2026-03-25 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | Copilot chat requirement dated 2026-03-25 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 3 |
| Total stories | 6 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained with exact files and exact acceptance criteria. |
| No working memory across files | Required NFR and proxy/client patterns are embedded inline in each story card. |
| No planning ability | Stories are atomic: one deliverable, one file set, one verification path. |
| Token cost per file read | Each story caps “Files to read first” at 3 files. |
| Binary inference only | Acceptance criteria are pass/fail and customer-visible. |

> Agent: execute exactly one story at a time, update the Story Tracker row when done, push code, then move to the next story in the same epic branch.

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
- [x] Stories sequenced: backend before frontend where required
- [x] Iteration count minimized for PR-only delivery
- [x] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Unblock CP web YouTube sign-in, saved credential attach, customer-visible readiness states, and Google-side setup evidence in one merge. | 3 | 6 | 5.5h | 2026-03-25 22:30 IST |

**Estimate basis:** CP proxy fix = 30 min | CP web wizard flow = 60 min | My Agents readiness UX = 45 min | Google operator checklist + evidence = 30 min | E2E/regression = 60 min | PR/test/update overhead = 75 min.

### PR-Overhead Optimization Rules

- This is a single-iteration plan by request.
- Backend and frontend changes stay in one iteration so one merge unlocks a working customer path.
- No separate deployment iteration is added; deployment validation happens after merge through the standard `waooaw deploy` workflow if needed.

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
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` in the message box → select **platform-engineer** from the dropdown
6. Copy the block below and paste into the message box → press **Enter**
7. Go away. Come back at: **2026-03-25 22:30 IST**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Fluent UI engineer + Senior Python 3.11 / FastAPI engineer + Google OAuth rollout operator for customer-facing integrations.
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-YT-CONN-1-youtube-connection-unblock.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3.
TIME BUDGET: 5.5h. If you reach 6.5h without finishing, follow STUCK PROTOCOL now.

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
git checkout -b feat/cp-yt-conn-1-it1-e1
git commit --allow-empty -m "chore(cp-yt-conn-1): start iteration 1"
git push origin feat/cp-yt-conn-1-it1-e1

gh pr create \
  --base main \
  --head feat/cp-yt-conn-1-it1-e1 \
  --draft \
  --title "tracking: CP-YT-CONN-1 Iteration 1 — in progress" \
  --body "## tracking: CP-YT-CONN-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Google OAuth operator checklist and evidence pack
- [ ] [E1-S2] CP YouTube proxy uses Plant customer ID contract
- [ ] [E2-S1] Hire setup finalizes saved YouTube channel selection
- [ ] [E2-S2] Hire setup attaches saved YouTube credential to the hire
- [ ] [E3-S1] My Agents shows reliable YouTube readiness states
- [ ] [E3-S2] Regression and rollout evidence prove connect once publish later

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline

One epic = one branch: `feat/cp-yt-conn-1-it1-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code.
Do not refactor outside listed files.

### Rule 3 — Tracker discipline

After each story is complete:
1. Update that Story Tracker row from `Not started` to `Completed` in this plan file.
2. If the next story has started, mark it `In progress`.
3. Commit that tracker update with the story code changes.

### Rule 4 — Test-plan discipline

Each story must either add tests, update existing tests, or explicitly state why no test changed.
If rollout or operator validation is part of the story, update an existing test-plan or testing asset file rather than creating a new document.

### Rule 5 — Google operator gate

Google OAuth consent-screen or test-user changes are outside repo code. For the Google setup story, the agent must:
1. Prepare the exact checklist and evidence requirements in the files named by the story card.
2. Post the manual actions clearly in the PR description or PR comment.
3. Mark the story complete only after the repo-side checklist and captured validation evidence are present.

### Rule 6 — STUCK PROTOCOL

If blocked for more than 20 minutes on one story:
1. Post the blocker in the tracking PR.
2. Commit any safe partial progress.
3. Stop only if the blocker is external and cannot be reduced further.

### CHECKPOINT RULE

After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(cp-yt-conn-1): [epic-id] — [epic title]" && git push
```

Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## Iteration 1

### Dependency Map

| Story | Depends on | Why |
|---|---|---|
| E1-S1 | none | Google-side unblock checklist can be prepared immediately. |
| E1-S2 | E1-S1 | Repo-side proxy fix should use the same validated redirect/OAuth context captured in E1-S1. |
| E2-S1 | E1-S2 | Wizard callback must finalize against the corrected CP customer contract. |
| E2-S2 | E2-S1 | Attach-on-save should use the finalized selected credential flow. |
| E3-S1 | E2-S2 | My Agents readiness states are meaningful only after saved credential and attachment semantics are stable. |
| E3-S2 | E3-S1 | End-to-end proof should cover the finished customer journey, not partial states. |

---

### Epic E1 — Customer reaches a trusted Google sign-in screen

**Outcome:** The team can remove the current Google warning-page blocker and the CP proxy speaks the same customer identity contract as Plant before any web-flow polish starts.

#### Story E1-S1 — Google OAuth operator checklist and evidence pack

| Field | Value |
|---|---|
| Story ID | E1-S1 |
| Branch | feat/cp-yt-conn-1-it1-e1 |
| Estimate | 30 min |
| BLOCKED UNTIL | none |
| Files to read first | `src/Plant/BackEnd/services/youtube_connection_service.py` · `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` · `docs/testing/ExistingTestAssets.md` |
| Files to create / modify | `docs/testing/ExistingTestAssets.md` |
| CP pattern | none — operational checklist and test-asset update only |

**Context**

The current customer failure happens before WAOOAW completes OAuth: Google shows the unverified-app warning page because the requested YouTube scopes are sensitive and the demo OAuth setup is not fully ready. This story makes that external dependency explicit inside the iteration, so the code PR has a matching Google-side checklist instead of treating the warning as a mysterious runtime bug.

**Tasks**

1. Add a CP web YouTube OAuth validation entry to `docs/testing/ExistingTestAssets.md` that lists the exact demo checks: OAuth app name/support email present, demo redirect URI registered, required YouTube scopes present, test users added, and evidence to capture after sign-in.
2. State clearly that Google Console changes are manual/operator work, not repo code, and include the exact evidence required after completion: screenshot-free textual checklist, confirmed client ID, redirect URI used, and whether the warning screen disappeared.
3. In the iteration PR body or first comment, instruct the operator to perform the checklist before final merge validation.

**Code patterns to copy exactly**

```python
scopes = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
```

```tsx
function buildRedirectUri(searchParams: URLSearchParams): string {
  if (typeof window === 'undefined') return ''
  const nextParams = new URLSearchParams(searchParams)
  nextParams.delete('code')
  nextParams.delete('state')
  nextParams.delete('scope')
  nextParams.delete('error')
  const query = nextParams.toString()
  return `${window.location.origin}${window.location.pathname}${query ? `?${query}` : ''}`
}
```

**Acceptance criteria**

- Existing testing assets contain a dedicated CP web YouTube OAuth validation entry with operator steps and required evidence.
- The story explicitly distinguishes manual Google Console actions from repo code changes.
- The PR contains a clear operator checklist for removing the warning-screen blocker.

**Verification**

- No automated command required for this story.
- Confirm the updated testing asset names the exact redirect-uri source and the exact YouTube scopes in use.

#### Story E1-S2 — CP YouTube proxy uses Plant customer ID contract

| Field | Value |
|---|---|
| Story ID | E1-S2 |
| Branch | feat/cp-yt-conn-1-it1-e1 |
| Estimate | 35 min |
| BLOCKED UNTIL | E1-S1 completed |
| Files to read first | `src/CP/BackEnd/api/cp_youtube_connections.py` · `src/CP/BackEnd/tests/test_cp_youtube_connections_routes.py` · `src/CP/BackEnd/api/digital_marketing_activation.py` |
| Files to create / modify | `src/CP/BackEnd/api/cp_youtube_connections.py` · `src/CP/BackEnd/tests/test_cp_youtube_connections_routes.py` |
| CP pattern | Pattern A — existing `/cp/youtube-connections` route proxies to Plant using `PlantGatewayClient`; no business logic belongs in CP |

**Context**

Plant stores and queries saved YouTube credentials by exact `customer_id`, but the CP YouTube proxy still manufactures a `CUST-` prefix. This is the same class of defect already fixed in digital marketing activation, so this story closes the YouTube path with matching behavior and tests.

**Tasks**

1. Change `_customer_id_from_user()` in `cp_youtube_connections.py` to return `str(user.id)`.
2. Update route tests so start/finalize/list/get/attach assertions lock the raw customer ID contract instead of allowing the prefixed value.
3. Ensure the route keeps its thin-proxy behavior and does not add any Plant business logic to CP.

**Code patterns to copy exactly**

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/cp/youtube-connections", tags=["cp-youtube-connections"])


def _customer_id_from_user(user: User) -> str:
    return str(user.id)
```

```python
resp = await plant.request_json(
    method="POST",
    path="api/v1/customer-platform-connections/youtube/connect/start",
    headers=_forward_headers(request),
    json_body={
        "customer_id": _customer_id_from_user(current_user),
        "redirect_uri": body.redirect_uri,
    },
)
```

**Acceptance criteria**

- CP start/finalize/list/get/attach all forward the raw WAOOAW customer ID.
- CP route tests fail if the prefixed contract returns.
- No new route or CP-side business logic is introduced.

**Verification**

```bash
docker-compose -f docker-compose.test.yml run cp-test pytest tests/test_cp_youtube_connections_routes.py -q
```

---

### Epic E2 — Customer saves one reusable YouTube connection

**Outcome:** A CP web customer can complete Google callback handling once, keep the chosen YouTube channel selected, and save the hire with an attached reusable credential for later publishing.

#### Story E2-S1 — Hire setup finalizes saved YouTube channel selection

| Field | Value |
|---|---|
| Story ID | E2-S1 |
| Branch | feat/cp-yt-conn-1-it1-e2 |
| Estimate | 55 min |
| BLOCKED UNTIL | E1-S2 completed |
| Files to read first | `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` · `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` · `src/CP/FrontEnd/src/test/HireSetupWizard.test.tsx` |
| Files to create / modify | `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` · `src/CP/FrontEnd/src/test/HireSetupWizard.test.tsx` |
| CP pattern | none — existing CP FrontEnd calls existing CP BackEnd route via `gatewayRequestJson` |

**Context**

The wizard already has start/finalize/list primitives, but the customer outcome depends on callback closure: after Google returns with `code` and `state`, the chosen channel must become the selected saved credential in the wizard, independent of whether the Google account matches the CP login account. This story makes the saved channel the durable unit of selection, not the login identity.

**Tasks**

1. Harden the callback-finalize flow so it sets the selected YouTube credential from the finalized response, refreshes the saved connection list, and clears transient query parameters after success.
2. Keep the selected channel anchored on the credential record and displayed `display_name`, not on any assumption about the CP login email.
3. Add or extend wizard tests for finalize success, query cleanup, and connected-channel selection after callback.

**Code patterns to copy exactly**

```ts
export async function finalizeYouTubeConnection(
  input: FinalizeYouTubeConnectionInput
): Promise<YouTubeConnection> {
  return gatewayRequestJson<YouTubeConnection>('/cp/youtube-connections/connect/finalize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}
```

```tsx
const credential = await finalizeYouTubeConnection({
  state: stateParam,
  code,
  redirect_uri: redirectUri,
})
setSelectedYouTubeConnectionId(credential.id)
setMarketingPlatforms((prev) =>
  upsertMarketingPlatformConfig(prev, {
    platform: 'youtube',
    customer_platform_credential_id: credential.id,
    display_name: credential.display_name || 'YouTube Channel',
    posting_identity: credential.display_name || null,
  })
)
```

**Acceptance criteria**

- Returning from Google with `code` and `state` results in one selected saved YouTube credential inside the wizard.
- The selected channel is represented by the saved credential ID and channel display name, not the CP login identity.
- Query parameters used for callback handling are removed after successful finalize.

**Verification**

```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/HireSetupWizard.test.tsx
```

#### Story E2-S2 — Hire setup attaches saved YouTube credential to the hire

| Field | Value |
|---|---|
| Story ID | E2-S2 |
| Branch | feat/cp-yt-conn-1-it1-e2 |
| Estimate | 45 min |
| BLOCKED UNTIL | E2-S1 completed |
| Files to read first | `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` · `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` · `src/CP/FrontEnd/src/test/HireSetupWizard.test.tsx` |
| Files to create / modify | `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` · `src/CP/FrontEnd/src/test/HireSetupWizard.test.tsx` |
| CP pattern | none — existing CP FrontEnd uses existing `/cp/youtube-connections/{credential_id}/attach` route |

**Context**

Saving the wizard is the moment when “saved in customer account” becomes “attached to this hired agent.” Without this step, later scheduled publishing still lacks the agent-scoped connection even if the customer successfully signed in once.

**Tasks**

1. Keep attach-on-save explicit for marketing hires: if a connected YouTube credential is selected, save the wizard config and then attach that exact credential to the hired agent using the marketing skill ID.
2. Ensure the saved config carries `customer_platform_credential_id` and display name for the selected YouTube channel.
3. Add or extend tests proving continue/activate paths call attach only when a valid connected credential is selected.

**Code patterns to copy exactly**

```ts
export async function attachYouTubeConnection(
  credentialId: string,
  input: AttachYouTubeConnectionInput
): Promise<Record<string, unknown>> {
  return gatewayRequestJson<Record<string, unknown>>(
    `/cp/youtube-connections/${encodeURIComponent(credentialId)}/attach`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hired_instance_id: input.hired_instance_id,
        skill_id: input.skill_id,
        platform_key: input.platform_key || 'youtube',
      }),
    }
  )
}
```

```tsx
if (isMarketingAgent && selectedYouTubeConnectionId.trim()) {
  await attachYouTubeConnection(selectedYouTubeConnectionId, {
    hired_instance_id: next.hired_instance_id,
    skill_id: getMarketingSkillId(),
    platform_key: 'youtube',
  })
}
```

**Acceptance criteria**

- Saving or activating a marketing hire attaches the exact selected YouTube credential to that hire.
- The saved wizard config contains the chosen credential ID and display name.
- Continue/activate remains blocked when the selected YouTube credential is no longer connected.

**Verification**

```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/HireSetupWizard.test.tsx
```

---

### Epic E3 — Customer sees reliable YouTube readiness later

**Outcome:** Once the YouTube connection is saved and attached, CP web clearly tells the customer whether the agent is blocked, ready, or needs reconnect, and the team has a regression path that proves the one-time connection can be reused later.

#### Story E3-S1 — My Agents shows reliable YouTube readiness states

| Field | Value |
|---|---|
| Story ID | E3-S1 |
| Branch | feat/cp-yt-conn-1-it1-e3 |
| Estimate | 45 min |
| BLOCKED UNTIL | E2-S2 completed |
| Files to read first | `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` · `src/CP/FrontEnd/src/test/MyAgents.test.tsx` · `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` |
| Files to create / modify | `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` · `src/CP/FrontEnd/src/test/MyAgents.test.tsx` |
| CP pattern | none — existing CP FrontEnd combines existing platform-connection list and YouTube credential list |

**Context**

The customer’s post-setup trust comes from the runtime view, not the setup screen. My Agents must distinguish four states clearly: no saved connection, saved-but-not-attached, attached-and-ready, and reconnect-required, with the correct next action in each case.

**Tasks**

1. Refine My Agents YouTube summary copy and readiness mapping so saved-but-unattached, connected, and reconnect-required states are all explicit and customer-readable.
2. Keep the “Open YouTube setup” action only where it is the correct next move.
3. Extend tests for not connected, ready-to-attach, connected, and reconnect-required states.

**Code patterns to copy exactly**

```tsx
const attached = connections.find((connection) => String(connection.platform_key || '').trim().toLowerCase() === 'youtube') || null
const attachedCredential = attached?.customer_platform_credential_id
  ? youtubeCredentials.find((connection) => connection.id === attached.customer_platform_credential_id) || null
  : youtubeCredentials.find((connection) => connection.connection_status === 'connected') || null
```

```tsx
if (!attached && attachedCredential) {
  return {
    platformKey: 'youtube',
    label: `${labelPrefix} ready to attach`,
    message: `${labelPrefix} is connected in your account, but this hire is not currently attached to it. Reconnect from setup to restore publish readiness.`,
    tone: 'warning' as const,
    isReady: false,
    connection: null,
  }
}
```

**Acceptance criteria**

- My Agents distinguishes not connected, ready to attach, connected, and reconnect-required without ambiguous language.
- The call to action appears only when the customer actually needs to return to setup.
- Tests cover all four states and fail if the state mapping regresses.

**Verification**

```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/MyAgents.test.tsx
```

#### Story E3-S2 — Regression and rollout evidence prove connect once, publish later

| Field | Value |
|---|---|
| Story ID | E3-S2 |
| Branch | feat/cp-yt-conn-1-it1-e3 |
| Estimate | 70 min |
| BLOCKED UNTIL | E3-S1 completed |
| Files to read first | `src/CP/FrontEnd/e2e/hire-journey.spec.ts` · `docs/testing/ExistingTestAssets.md` · `src/CP/FrontEnd/e2e/digital-marketing-activation.spec.ts` |
| Files to create / modify | `src/CP/FrontEnd/e2e/hire-journey.spec.ts` · `docs/testing/ExistingTestAssets.md` |
| CP pattern | none — regression and rollout validation only |

**Context**

The business promise here is “connect once, publish later.” That promise needs one prove-it path covering Google-side unblock evidence, CP web setup, saved credential attach, and later readiness in the agent runtime.

**Tasks**

1. Extend the CP web end-to-end regression so the hire journey explicitly covers YouTube setup entry, saved credential selection, attach success, and ready-for-upload runtime state.
2. Update `docs/testing/ExistingTestAssets.md` with the final iteration-level regression asset entry for CP web YouTube connect-once reuse validation.
3. In the iteration PR body, record the rollout evidence set the operator must confirm after deployment: Google warning page absent, callback succeeds, saved channel visible, attached state visible in My Agents.

**Code patterns to copy exactly**

```ts
if (path.endsWith('/api/cp/youtube-connections') && method === 'GET') {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([
      {
        id: 'cred-youtube-001',
        platform_key: 'youtube',
        granted_scopes: ['youtube.upload'],
      },
    ]),
  })
}
```

```ts
await expect(page.getByText('YouTube channel status')).toBeVisible()
await expect(page.getByText('Ready for upload')).toBeVisible()
```

**Acceptance criteria**

- E2E coverage proves the CP web path from setup entry to ready-for-upload state.
- Existing testing assets include a final iteration-level validation entry for YouTube connect-once reuse.
- PR rollout evidence explicitly names both Google-side and repo-side validation points.

**Verification**

```bash
cd src/CP/FrontEnd && npm run test:e2e -- hire-journey.spec.ts
```

```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/HireSetupWizard.test.tsx src/test/MyAgents.test.tsx
```