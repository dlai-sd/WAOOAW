# MOB-DMA-1 — Mobile DMA Chat, Content Viewing & YouTube DB Persistence

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `MOB-DMA-1` |
| Feature area | Mobile — Digital Marketing Agent chat, content artifact viewer, YouTube DB credential persistence |
| Created | 2026-04-15 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `.github/copilot-instructions.md` §DMA priority; `docs/CONTEXT_AND_INDEX.md` §1, §3, §13 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 5 |
| Total stories | 9 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | All service types and API paths are embedded inline — agent never reads a separate NFR file |
| No planning ability | Stories are atomic — one screen or one service file per story |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist

- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant code patterns inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] CP BackEnd pattern: N/A — this plan is mobile-only (Lane A)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: services (S1) before screens (S2+)
- [x] Iteration count minimized — 2 iterations, each unlocks a meaningful product slice
- [x] No placeholders remain

---

## Objective Alignment

**This plan advances: DMA value.**

A mobile customer can manage the full Digital Marketing Agent lifecycle from their phone: activate the DMA via the strategy workshop chat that already powers CP, view themed content batches with table/image/mp4 artifacts, approve or reject individual posts, and manage the YouTube credential from the database-backed `CustomerPlatformCredential`. This removes mobile as a blocker to DMA trial-to-paid conversion.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — DMA services + DMAConversationScreen + artifact renderer + voice wiring | E1, E2, E3 | 5 | 5h | +5h from start |
| 2 | Lane A — Staged DMA workflow + YouTube DB persistence + strip placeholder sections + BDD parity tests | E4, E5 | 4 | 4h | +4h after Iteration 1 merged |

**Estimate basis:** Service file = 45 min | New screen = 90 min | Component = 30 min | Navigation wiring = 20 min | Tests = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
7. Go away. Come back in **~5 hours**.

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React Native / Expo / TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-DMA-1-dma-chat-content.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the Iteration 1 section exists.
2. Verify this execution surface allows repository writes on the current task branch.
3. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run.
5. Execute Epics in this order: E1 → E2 → E3
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Prerequisite evidence:**
- Iteration 1 merge status: `[PENDING HUMAN UPDATE BEFORE LAUNCH]`
- Iteration 1 PR: `[PR URL or #NUMBER]`
- Merge commit on `main`: `[FULL SHA]`
- Merged at: `[UTC TIMESTAMP]`

**Verify merge first:** use the Prerequisite evidence block above as the source of truth. If it is still marked pending or missing a merged PR number and merge commit, do not launch Iteration 2.

**Steps to launch:** same as Iteration 1 (GitHub repository → Agents tab)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React Native / Expo / TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-DMA-1-dma-chat-content.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch Iteration 1 content.
TIME BUDGET: 4h.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

PREREQUISITE CHECK (do before anything else):
  Read the "Prerequisite evidence" block under Iteration 2 in this plan file.
  Treat Iteration 2 as unlaunchable only if that block is still marked pending or does not include both a merged PR reference and a merge commit on `main`.
  If the block is still pending or incomplete: post "Blocked: Iteration 1 merge evidence has not been recorded in the plan." and HALT.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the Iteration 2 section exists.
2. Verify the Prerequisite evidence block for Iteration 2 is complete and not pending.
3. Verify this execution surface allows repository writes on the current task branch.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
2. Execute Epics in this order: E4 → E5
3. Add or update the tests listed in each story before moving on.
4. Open or update the iteration PR to `main`, post URL, and HALT.
```

**Come back at:** +4 hours after Iteration 2 launch.

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required `Prerequisite evidence` block for this iteration is complete and not marked pending.
- The GitHub execution surface lets you save repository changes on the current task branch.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from your task. Activate each now.
For every epic you execute, open with one line:

> *"Acting as a Senior React Native / Expo / TypeScript engineer, I will [what] by [approach]."*

### Rule 0 — Use the GitHub task branch and open the iteration PR early

GitHub-hosted agents usually start on a task-specific branch. Keep the entire iteration on that branch.

- If the execution surface already created a branch for this run, keep using it.
- Open a draft PR to `main` as soon as PR controls are available.

### Rule 1 — Branch discipline
One iteration = one GitHub task branch and one PR.
Never push or merge directly to `main`.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.

### Rule 4 — Save progress after every story
Update this plan file's Tracking Table. Save code and plan updates to the GitHub task branch.

### Rule 5 — Validate after every epic
If GitHub Agents exposes execution tools, run the relevant test command.
If not, state clearly that validation is deferred to CI and continue.
After validation, add `**Epic complete ✅**` under the epic heading.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
- Mark the blocked story as `🚫 Blocked` in the Tracking Table.
- Open or update a draft PR titled `WIP: [story-id] — blocked`.
- Include the exact blocker, the exact error message, and 1-2 attempted fixes.
- Post the PR URL. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
- Title: `feat(MOB-DMA-1): iteration N — [one-line summary]`.
- PR body: completed stories, validation status, NFR checklist.
- Post the PR URL in the task thread. **HALT.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(MOB-DMA-1): [epic-id] — [epic title]" && git push origin HEAD
```
Do this BEFORE starting the next epic.

---

## NFR Quick Reference (mobile-only)

| # | Rule | Applies to |
|---|---|---|
| 1 | Every data-fetching component must render loading → error → empty → data states | All new screens/components |
| 2 | `X-Correlation-ID` header on every outgoing HTTP call | All new service files |
| 3 | No email/phone/name in logs or console.log — use stripped dev logging | All new code |
| 4 | Retry 429/5xx/network-drop with exponential backoff (3×, 1s/2s/4s+jitter) | Service layer |
| 5 | All new navigation routes must be in `MyAgentsStackParamList` in `types.ts` | Navigation |
| 6 | Jest tests ≥ 80% coverage on new service files | Tests |
| 7 | Voice input is an optional toggle — never the only input path | DMAConversationScreen |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | DMA services | Mirror DMA activation service | 🔴 Not Started | — |
| E1-S2 | 1 | DMA services | Mirror marketing review service | 🔴 Not Started | — |
| E2-S1 | 1 | Customer sees DMA chat | DMAConversationScreen + navigation wiring | 🔴 Not Started | — |
| E2-S2 | 1 | Customer sees DMA chat | ArtifactRenderer component (table/image/mp4) | 🔴 Not Started | — |
| E3-S1 | 1 | Voice as alt input | Wire voice toggle into DMAConversationScreen | 🔴 Not Started | — |
| E4-S1 | 2 | Staged DMA workflow | Theme-to-content batch staging in DMAConversationScreen | 🔴 Not Started | — |
| E4-S2 | 2 | Staged DMA workflow | YouTube credential ref passed to createContentBatch | 🔴 Not Started | — |
| E5-S1 | 2 | Clean mobile ops hub | Strip placeholder sections in AgentOperationsScreen | 🔴 Not Started | — |
| E5-S2 | 2 | DMA parity tests | BDD parity test suite | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---


## Iteration 1 — DMA Services + Conversation Screen + Artifact Renderer

**Scope:** Customer can open DMAConversationScreen, run the DMA strategy workshop conversation, and view content artifacts (table/image/mp4) returned by the agent — all calling the same Plant Gateway routes that CP web uses.
**Lane:** A — all Plant Gateway routes exist; this is mobile service wiring + new React Native screens.
**⏱ Estimated:** 5h | **Come back:** +5h from launch
**Epics:** E1, E2, E3

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2 ──► E2-S1 ──► E2-S2 ──► E3-S1
(services first, then screen, then component, then voice wire)
```

---

### Epic E1: DMA services are in mobile — customer requests reach Plant Gateway

**Branch:** `feat/MOB-DMA-1-it1-e1`

---

#### Story E1-S1: Mirror the DMA activation service in mobile

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/MOB-DMA-1-it1-e1`
**CP BackEnd pattern:** N/A — mobile calls Plant Gateway directly via cpApiClient

**What to do (self-contained — read this card, then act):**
> `src/mobile/src/services/` currently has no `digitalMarketingActivation.service.ts`. Create it by mirroring the same API calls that `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` makes via `gatewayRequestJson`, but using mobile's `import cpApiClient from '@/lib/cpApiClient'`. The CP service uses `gatewayRequestJson('/cp/digital-marketing-activation/{id}', ...)` — the mobile file must call `cpApiClient.get/put/patch/post` to the same paths. Export all types (copy verbatim from lines 1–160 of the CP service) and the four async functions listed below. Add `X-Correlation-ID` header with `uuidv4()` on every write call.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | 1–240 | All exported types and function signatures; exact URL paths |
| `src/mobile/src/lib/cpApiClient.ts` | 1–60 | How cpApiClient is imported and used (axios instance) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/services/digitalMarketingActivation.service.ts` | create | New file — copy all type exports from CP service, then implement four functions below |

**Code patterns to copy exactly:**

```typescript
// src/mobile/src/services/digitalMarketingActivation.service.ts
import cpApiClient from '@/lib/cpApiClient'
import { v4 as uuidv4 } from 'uuid'

// STEP 1: Copy ALL type exports verbatim from
//   src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts lines 1-160
// (DigitalMarketingPlatformBinding, DigitalMarketingDerivedTheme,
//  DigitalMarketingStrategyWorkshopMessage, DigitalMarketingStrategyWorkshop,
//  DigitalMarketingCampaignSetup, DigitalMarketingActivationWorkspace,
//  DigitalMarketingActivationReadiness, DigitalMarketingActivationResponse,
//  DigitalMarketingLegacyWorkspace, DigitalMarketingThemePlanResponse,
//  UpsertDigitalMarketingActivationInput)

// STEP 2: Implement functions:

export async function getDigitalMarketingActivationWorkspace(
  hiredInstanceId: string
): Promise<DigitalMarketingActivationResponse> {
  const resp = await cpApiClient.get(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`
  )
  return resp.data
}

export async function upsertDigitalMarketingActivationWorkspace(
  hiredInstanceId: string,
  input: UpsertDigitalMarketingActivationInput
): Promise<DigitalMarketingActivationResponse> {
  const resp = await cpApiClient.put(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`,
    input,
    { headers: { 'X-Correlation-ID': uuidv4(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}

export async function patchDigitalMarketingActivationWorkspace(
  hiredInstanceId: string,
  patch: Record<string, unknown>
): Promise<DigitalMarketingActivationResponse> {
  const resp = await cpApiClient.patch(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}`,
    patch,
    { headers: { 'X-Correlation-ID': uuidv4(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}

export async function generateDigitalMarketingThemePlan(
  hiredInstanceId: string,
  patch: Record<string, unknown> = {}
): Promise<DigitalMarketingThemePlanResponse> {
  const resp = await cpApiClient.post(
    `/cp/digital-marketing-activation/${encodeURIComponent(hiredInstanceId)}/generate-theme-plan`,
    patch,
    { headers: { 'X-Correlation-ID': uuidv4(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}
```

**Acceptance criteria (binary pass/fail only):**
1. File exports `getDigitalMarketingActivationWorkspace`, `upsertDigitalMarketingActivationWorkspace`, `patchDigitalMarketingActivationWorkspace`, `generateDigitalMarketingThemePlan`.
2. All four functions call `/cp/digital-marketing-activation/${hiredInstanceId}` (or `.../${hiredInstanceId}/generate-theme-plan`).
3. Write calls include `X-Correlation-ID` header.
4. TypeScript compiles without errors.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/mobile/src/__tests__/services/digitalMarketingActivation.service.test.ts` | Mock `cpApiClient.get` returns `{ data: { hired_instance_id: 'x', workspace: {}, readiness: {} } }` | `getDigitalMarketingActivationWorkspace('x')` resolves with `hired_instance_id === 'x'` |
| E1-S1-T2 | same | Mock `cpApiClient.put` returns mock | `upsertDigitalMarketingActivationWorkspace('x', {...})` calls `cpApiClient.put` with path containing `/x` |
| E1-S1-T3 | same | Mock `cpApiClient.post` returns mock | `generateDigitalMarketingThemePlan('x')` calls path ending in `/generate-theme-plan` |

**Test command:**
```bash
cd src/mobile && node_modules/.bin/jest src/__tests__/services/digitalMarketingActivation.service.test.ts --no-coverage
```

**Commit message:** `feat(MOB-DMA-1): E1-S1 — mobile digitalMarketingActivation service`

**Done signal:** `"E1-S1 done. Created: digitalMarketingActivation.service.ts. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E1-S2: Mirror the marketing review service in mobile

**BLOCKED UNTIL:** E1-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/MOB-DMA-1-it1-e1` (same branch, continue from E1-S1)
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> `src/mobile/src/services/` has no `marketingReview.service.ts`. Create it by mirroring `src/CP/FrontEnd/src/services/marketingReview.service.ts`. Copy all type exports verbatim (lines 1–60 of CP service: `DraftArtifactType`, `DraftArtifactRequest`, `GeneratedArtifact`, `DraftPost`, `DraftBatch`, `CreateDraftBatchInput`, `CreateContentFromThemeInput`, `ArtifactStatus`). Implement seven async functions using `cpApiClient`: `listCustomerDraftBatches`, `createDraftBatch`, `approveDraftPost`, `rejectDraftPost`, `pollDraftPostArtifactStatus`, `createContentBatchFromTheme`. Routes are identical to CP: `/cp/marketing/draft-batches`, `/cp/marketing/draft-posts/approve`, etc. Add `X-Correlation-ID` header on all write calls.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/marketingReview.service.ts` | 1–200 | All type exports and function signatures; exact URL paths |
| `src/mobile/src/services/digitalMarketingActivation.service.ts` | 1–20 | Import pattern to stay consistent |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/services/marketingReview.service.ts` | create | New file — copy types from CP service, implement functions below |

**Code patterns to copy exactly:**

```typescript
// src/mobile/src/services/marketingReview.service.ts
import cpApiClient from '@/lib/cpApiClient'
import { v4 as uuidv4 } from 'uuid'

// STEP 1: Copy all type exports from
//   src/CP/FrontEnd/src/services/marketingReview.service.ts lines 1-80
// (DraftArtifactType, DraftArtifactRequest, GeneratedArtifact, DraftPost,
//  DraftBatch, CreateDraftBatchInput, CreateContentFromThemeInput, ArtifactStatus)

export async function listCustomerDraftBatches(): Promise<DraftBatch[]> {
  const resp = await cpApiClient.get('/cp/marketing/draft-batches')
  return resp.data
}

export async function createDraftBatch(input: CreateDraftBatchInput): Promise<DraftBatch> {
  const resp = await cpApiClient.post('/cp/marketing/draft-batches', input, {
    headers: { 'X-Correlation-ID': uuidv4(), 'Content-Type': 'application/json' }
  })
  return resp.data
}

export async function approveDraftPost(
  postId: string
): Promise<{ post_id: string; review_status: string; approval_id: string }> {
  const resp = await cpApiClient.post('/cp/marketing/draft-posts/approve', { post_id: postId }, {
    headers: { 'X-Correlation-ID': uuidv4(), 'Content-Type': 'application/json' }
  })
  return resp.data
}

export async function rejectDraftPost(
  postId: string, reason?: string
): Promise<{ post_id: string; decision: string }> {
  const resp = await cpApiClient.post('/cp/marketing/draft-posts/reject',
    { post_id: postId, reason }, {
    headers: { 'X-Correlation-ID': uuidv4(), 'Content-Type': 'application/json' }
  })
  return resp.data
}

export async function pollDraftPostArtifactStatus(postId: string): Promise<ArtifactStatus> {
  const resp = await cpApiClient.get(`/cp/marketing/draft-posts/${postId}/artifact-status`)
  return resp.data
}

export async function createContentBatchFromTheme(
  themeBatchId: string,
  input: CreateContentFromThemeInput
): Promise<DraftBatch> {
  const resp = await cpApiClient.post(
    `/cp/marketing/draft-batches/${themeBatchId}/create-content-batch`,
    input,
    { headers: { 'X-Correlation-ID': uuidv4(), 'Content-Type': 'application/json' } }
  )
  return resp.data
}
```

**Acceptance criteria:**
1. File exports `listCustomerDraftBatches`, `createDraftBatch`, `approveDraftPost`, `rejectDraftPost`, `pollDraftPostArtifactStatus`, `createContentBatchFromTheme`.
2. `listCustomerDraftBatches` calls `cpApiClient.get('/cp/marketing/draft-batches')`.
3. `createContentBatchFromTheme('b1', {})` calls URL containing `b1/create-content-batch`.
4. TypeScript compiles without errors.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/mobile/src/__tests__/services/marketingReview.service.test.ts` | Mock `cpApiClient.get` returns `{ data: [] }` | `listCustomerDraftBatches()` resolves with `[]` |
| E1-S2-T2 | same | Mock `cpApiClient.post('/cp/marketing/draft-posts/approve', ...)` returns `{ data: { post_id: 'p1', review_status: 'approved', approval_id: 'a1' } }` | `approveDraftPost('p1')` resolves with `review_status === 'approved'` |
| E1-S2-T3 | same | Mock `cpApiClient.post` for createContentBatch | `createContentBatchFromTheme('b1', {})` calls URL containing `b1/create-content-batch` |

**Test command:**
```bash
cd src/mobile && node_modules/.bin/jest src/__tests__/services/marketingReview.service.test.ts --no-coverage
```

**Commit message:** `feat(MOB-DMA-1): E1-S2 — mobile marketingReview service`

**Done signal:** `"E1-S2 done. Created: marketingReview.service.ts. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

### Epic E2: Customer can run DMA strategy workshop and view content artifacts on mobile

**Branch:** `feat/MOB-DMA-1-it1-e2`

---

#### Story E2-S1: Create DMAConversationScreen and wire navigation

**BLOCKED UNTIL:** E1-S1 and E1-S2 committed
**Estimated time:** 90 min
**Branch:** `feat/MOB-DMA-1-it1-e2`
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> There is no `DMAConversationScreen` in `src/mobile/src/screens/agents/`. Create it. The screen receives `hiredAgentId: string` as a navigation param. On mount it calls `getDigitalMarketingActivationWorkspace(hiredAgentId)` and reads `workspace.campaign_setup?.strategy_workshop?.messages ?? []` into a `messages` state array. It renders the conversation as a scrollable list of bubbles (user = right-aligned purple `#667eea22`; assistant = left-aligned dark `#18181b`). A `TextInput` + "Send" button forms the input bar. On Send, append the user message, call `patchDigitalMarketingActivationWorkspace(hiredAgentId, { campaign_setup: { strategy_workshop: { messages: [...current, newMsg] } } })`, then update messages from the response. Render all three states: loading (ActivityIndicator), error (red banner), and the chat UI.
>
> After creating the screen: (1) add `DMAConversation: { hiredAgentId: string }` to `MyAgentsStackParamList` in `types.ts`; (2) register it in `MyAgentsNavigator` in `MainNavigator.tsx`; (3) in `AgentOperationsScreen.tsx` inside the `goals` section block (around line 695, after the `DigitalMarketingBriefSummaryCard` closing tag), add a "Chat with Agent" `TouchableOpacity` that calls `navigation.navigate('DMAConversation', { hiredAgentId })` — only shown when `isDigitalMarketing` is true.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/navigation/types.ts` | 95–130 | `MyAgentsStackParamList` exact shape — find the line to add `DMAConversation` |
| `src/mobile/src/navigation/MainNavigator.tsx` | 82–120 | `MyAgentsNavigator` — find PlatformConnections Screen line to insert after |
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | 680–720 | Goals section render — find `DigitalMarketingBriefSummaryCard` closing tag to insert after |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/agents/DMAConversationScreen.tsx` | create | New file — see code pattern below |
| `src/mobile/src/navigation/types.ts` | modify | Add `DMAConversation: { hiredAgentId: string }` inside `MyAgentsStackParamList` after the `PlatformConnections` entry |
| `src/mobile/src/navigation/MainNavigator.tsx` | modify | Import `DMAConversationScreen`; add `<MyAgentsStack.Screen name="DMAConversation" component={DMAConversationScreen} />` after `PlatformConnections` Screen |
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | modify | After `DigitalMarketingBriefSummaryCard` closing tag in the goals section, add the "Chat with Agent" button (only when `isDigitalMarketing`) — see snippet below |

**Code patterns to copy exactly:**

```typescript
// src/mobile/src/screens/agents/DMAConversationScreen.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  SafeAreaView, View, Text, TextInput, TouchableOpacity,
  ScrollView, ActivityIndicator, StyleSheet, KeyboardAvoidingView, Platform,
} from 'react-native'
import { useTheme } from '@/hooks/useTheme'
import {
  getDigitalMarketingActivationWorkspace,
  patchDigitalMarketingActivationWorkspace,
  type DigitalMarketingStrategyWorkshopMessage,
} from '@/services/digitalMarketingActivation.service'
import type { MyAgentsStackScreenProps } from '@/navigation/types'

type Props = MyAgentsStackScreenProps<'DMAConversation'>

export const DMAConversationScreen = ({ navigation, route }: Props) => {
  const { hiredAgentId } = route.params
  const { colors, spacing, typography } = useTheme()
  const scrollRef = useRef<ScrollView>(null)

  const [messages, setMessages] = useState<DigitalMarketingStrategyWorkshopMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    getDigitalMarketingActivationWorkspace(hiredAgentId)
      .then((resp) => {
        setMessages(resp.workspace?.campaign_setup?.strategy_workshop?.messages ?? [])
      })
      .catch(() => setError('Failed to load conversation. Please try again.'))
      .finally(() => setLoading(false))
  }, [hiredAgentId])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || sending) return
    const userMsg: DigitalMarketingStrategyWorkshopMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInputText('')
    setSending(true)
    try {
      const resp = await patchDigitalMarketingActivationWorkspace(hiredAgentId, {
        campaign_setup: { strategy_workshop: { messages: [...messages, userMsg] } },
      })
      setMessages(resp.workspace?.campaign_setup?.strategy_workshop?.messages ?? [])
    } catch {
      setError('Failed to send message. Please try again.')
    } finally {
      setSending(false)
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100)
    }
  }, [hiredAgentId, inputText, messages, sending])

  if (loading) {
    return (
      <SafeAreaView style={[s.root, { backgroundColor: colors.black }]}>
        <ActivityIndicator color={colors.neonCyan} style={{ flex: 1 }} />
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={[s.root, { backgroundColor: colors.black }]} testID="dma-conversation-screen">
      <View style={[s.header, { borderBottomColor: colors.textSecondary + '20' }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={{ color: colors.neonCyan, fontSize: 14 }}>← Back</Text>
        </TouchableOpacity>
        <Text style={[s.title, { color: colors.textPrimary, fontFamily: typography.fontFamily.display }]}>
          Strategy Workshop
        </Text>
      </View>

      {error ? (
        <View style={[s.errorBanner, { backgroundColor: '#ef444418', borderColor: '#ef444455' }]}>
          <Text style={{ color: '#ef4444' }}>{error}</Text>
        </View>
      ) : null}

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={80}>
        <ScrollView ref={scrollRef} contentContainerStyle={{ padding: 16, gap: 12 }}
          onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: false })}>
          {messages.length === 0 ? (
            <Text style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 40 }}>
              Start the strategy workshop — describe your business, audience, and goals.
            </Text>
          ) : (
            messages.map((msg, i) => (
              <View key={i} style={[s.bubble,
                msg.role === 'user'
                  ? { alignSelf: 'flex-end', backgroundColor: '#667eea22', borderColor: '#667eea55' }
                  : { alignSelf: 'flex-start', backgroundColor: '#18181b', borderColor: colors.textSecondary + '30' }
              ]}>
                <Text style={{ color: colors.textPrimary, fontSize: 14 }}>{msg.content}</Text>
              </View>
            ))
          )}
          {sending ? <ActivityIndicator color={colors.neonCyan} style={{ alignSelf: 'flex-start', marginLeft: 16 }} /> : null}
        </ScrollView>

        <View style={[s.inputBar, { borderTopColor: colors.textSecondary + '20', backgroundColor: colors.black }]}>
          <TextInput style={[s.textInput, { color: colors.textPrimary, borderColor: colors.textSecondary + '40' }]}
            value={inputText} onChangeText={setInputText}
            placeholder="Type your message…" placeholderTextColor={colors.textSecondary}
            multiline editable={!sending} testID="dma-chat-input" />
          <TouchableOpacity
            style={[s.sendBtn, { backgroundColor: sending || !inputText.trim() ? colors.textSecondary + '40' : colors.neonCyan }]}
            onPress={handleSend} disabled={sending || !inputText.trim()} testID="dma-chat-send">
            <Text style={{ color: '#0a0a0a', fontWeight: '700', fontSize: 13 }}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 16, borderBottomWidth: 1 },
  title: { flex: 1, fontSize: 18, fontWeight: 'bold' },
  errorBanner: { margin: 12, padding: 12, borderRadius: 8, borderWidth: 1 },
  bubble: { maxWidth: '80%', borderRadius: 12, borderWidth: 1, padding: 12 },
  inputBar: { flexDirection: 'row', alignItems: 'flex-end', gap: 10, padding: 12, borderTopWidth: 1 },
  textInput: { flex: 1, borderWidth: 1, borderRadius: 10, padding: 10, minHeight: 40, maxHeight: 120, fontSize: 14 },
  sendBtn: { borderRadius: 8, paddingHorizontal: 16, paddingVertical: 10, alignItems: 'center', justifyContent: 'center' },
})
```

```typescript
// AgentOperationsScreen.tsx — "Chat with Agent" button snippet (add after DigitalMarketingBriefSummaryCard):
<TouchableOpacity
  style={[styles.actionBtn, { backgroundColor: colors.neonCyan + '22', marginTop: 12 }]}
  onPress={() => navigation.navigate('DMAConversation', { hiredAgentId })}
  testID="chat-with-agent-btn"
  accessibilityLabel="Chat with Agent"
>
  <Text style={{ color: colors.neonCyan, fontSize: 14, fontWeight: '600' }}>
    💬 Chat with Agent
  </Text>
</TouchableOpacity>
```

**Acceptance criteria:**
1. `DMAConversation: { hiredAgentId: string }` is in `MyAgentsStackParamList` in `types.ts`.
2. `DMAConversationScreen` is registered in `MyAgentsNavigator` in `MainNavigator.tsx`.
3. Rendering `DMAConversationScreen` with mocked workspace (2 messages) shows both bubbles.
4. Loading state shows `ActivityIndicator`.
5. Error state shows red error banner text.
6. `testID="chat-with-agent-btn"` appears in `AgentOperationsScreen` goals section when `isDigitalMarketing` is true.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/mobile/src/__tests__/screens/DMAConversationScreen.test.tsx` | Mock `getDigitalMarketingActivationWorkspace` returns workspace with 2 messages | Both message texts in rendered output |
| E2-S1-T2 | same | Mock throws error | Error banner text visible |
| E2-S1-T3 | same | User types "hello" + taps Send; mock `patchDigitalMarketingActivationWorkspace` resolves | Patch called with messages containing `{ role: 'user', content: 'hello' }` |
| E2-S1-T4 | same | Workspace with empty messages | Empty-state hint text visible |

**Test command:**
```bash
cd src/mobile && node_modules/.bin/jest src/__tests__/screens/DMAConversationScreen.test.tsx --no-coverage
```

**Commit message:** `feat(MOB-DMA-1): E2-S1 — DMAConversationScreen + navigation wiring`

**Done signal:** `"E2-S1 done. Created: DMAConversationScreen.tsx. Modified: types.ts, MainNavigator.tsx, AgentOperationsScreen.tsx. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E2-S2: Create ArtifactRenderer component for table / image / mp4

**BLOCKED UNTIL:** E2-S1 committed
**Estimated time:** 60 min
**Branch:** `feat/MOB-DMA-1-it1-e2` (same branch)
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> `DraftPost` objects returned by `listCustomerDraftBatches()` can have `artifact_type` of `'table'` | `'image'` | `'video'` | `'video_audio'` and an `artifact_uri`. Create `src/mobile/src/components/dma/ArtifactRenderer.tsx` that accepts a `DraftPost` prop and renders:
> - **image**: React Native `Image` full-width 200 px height, `source={{ uri: artifact_uri }}`, `testID="artifact-image"`.
> - **video / video_audio**: `TouchableOpacity` "▶ Play video" that calls `Linking.openURL(artifact_uri)`, `testID="artifact-video"`. If `artifact_preview_uri` exists show it as a 100 px thumbnail `Image`.
> - **table**: Parse `artifact_uri` as JSON array; render header row (gray) + data rows with `FlatList`, `testID="artifact-table"`. On parse failure show amber banner "Table data could not be parsed".
> - **queued / running status**: `ActivityIndicator` + "Generating artifact…"
> - **failed status**: red banner "Artifact generation failed"
> - **text / undefined / no URI**: return null (render nothing).
>
> After creating the component, import it in `DMAConversationScreen.tsx` and render it after the last assistant message bubble when the message list is non-empty (as a preview of the latest content batch; pass a mock `DraftPost` stub as `post` until E4-S1 wires real batch data).

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/services/marketingReview.service.ts` | 1–60 | `DraftPost` type fields: `artifact_type`, `artifact_uri`, `artifact_preview_uri`, `artifact_generation_status` |
| `src/mobile/src/screens/agents/DMAConversationScreen.tsx` | 1–40 | Import list and ScrollView children area |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/components/dma/ArtifactRenderer.tsx` | create | New file — see code pattern below |
| `src/mobile/src/screens/agents/DMAConversationScreen.tsx` | modify | Import `ArtifactRenderer`; add `<ArtifactRenderer post={mockPost} />` after the messages list inside ScrollView when `messages.length > 0`. Define `mockPost` as `const mockPost = { artifact_type: undefined } as any` as a placeholder until E4-S1. |

**Code patterns to copy exactly:**

```typescript
// src/mobile/src/components/dma/ArtifactRenderer.tsx
import React from 'react'
import { View, Text, Image, TouchableOpacity, FlatList, ActivityIndicator, Linking, StyleSheet } from 'react-native'
import { useTheme } from '@/hooks/useTheme'
import type { DraftPost } from '@/services/marketingReview.service'

interface Props { post: DraftPost }

export const ArtifactRenderer = ({ post }: Props) => {
  const { colors, typography } = useTheme()
  const status = post.artifact_generation_status
  if (status === 'queued' || status === 'running') {
    return (
      <View style={s.row}>
        <ActivityIndicator color={colors.neonCyan} size="small" />
        <Text style={{ color: colors.textSecondary, marginLeft: 8 }}>Generating artifact…</Text>
      </View>
    )
  }
  if (status === 'failed') {
    return (
      <View style={[s.banner, { borderColor: '#ef444455', backgroundColor: '#ef444418' }]}>
        <Text style={{ color: '#ef4444' }}>Artifact generation failed</Text>
      </View>
    )
  }
  const type = post.artifact_type
  const uri = post.artifact_uri
  if (!type || type === 'text' || !uri) return null

  if (type === 'image') {
    return <Image source={{ uri }} style={s.img} resizeMode="cover" testID="artifact-image" accessibilityLabel="Content image" />
  }
  if (type === 'video' || type === 'video_audio') {
    return (
      <TouchableOpacity style={[s.videoCard, { borderColor: colors.textSecondary + '30', backgroundColor: '#18181b' }]}
        onPress={() => Linking.openURL(uri)} testID="artifact-video" accessibilityLabel="Play video">
        {post.artifact_preview_uri ? <Image source={{ uri: post.artifact_preview_uri }} style={s.thumb} resizeMode="cover" /> : null}
        <Text style={{ color: colors.neonCyan, fontWeight: '700', marginTop: 8 }}>▶ Play video</Text>
      </TouchableOpacity>
    )
  }
  if (type === 'table') {
    let rows: Record<string, string>[] = []
    let headers: string[] = []
    try {
      const parsed = JSON.parse(uri)
      if (Array.isArray(parsed) && parsed.length > 0) { headers = Object.keys(parsed[0]); rows = parsed }
    } catch {
      return (
        <View style={[s.banner, { borderColor: '#f59e0b55', backgroundColor: '#f59e0b18' }]}>
          <Text style={{ color: '#f59e0b' }}>Table data could not be parsed</Text>
        </View>
      )
    }
    return (
      <View style={[s.table, { borderColor: colors.textSecondary + '30' }]}>
        <View style={[s.trow, { backgroundColor: '#27272a' }]}>
          {headers.map((h) => <Text key={h} style={[s.th, { color: colors.textPrimary }]}>{h}</Text>)}
        </View>
        <FlatList data={rows} keyExtractor={(_, i) => String(i)} scrollEnabled={false} testID="artifact-table"
          renderItem={({ item, index }) => (
            <View style={[s.trow, { backgroundColor: index % 2 === 0 ? '#18181b' : '#1c1c1f' }]}>
              {headers.map((h) => <Text key={h} style={[s.td, { color: colors.textSecondary }]}>{String(item[h] ?? '')}</Text>)}
            </View>
          )} />
      </View>
    )
  }
  return null
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', padding: 8 },
  banner: { borderWidth: 1, borderRadius: 8, padding: 10, marginVertical: 4 },
  img: { width: '100%', height: 200, borderRadius: 10, marginVertical: 4 },
  videoCard: { borderWidth: 1, borderRadius: 10, padding: 12, alignItems: 'center', marginVertical: 4 },
  thumb: { width: '100%', height: 100, borderRadius: 8 },
  table: { borderWidth: 1, borderRadius: 8, overflow: 'hidden', marginVertical: 4 },
  trow: { flexDirection: 'row' },
  th: { flex: 1, padding: 8, fontSize: 12, fontWeight: '700' },
  td: { flex: 1, padding: 8, fontSize: 12 },
})
```

**Acceptance criteria:**
1. `ArtifactRenderer` exists and is exported from `src/mobile/src/components/dma/ArtifactRenderer.tsx`.
2. `artifact_type: 'image'` → `testID="artifact-image"` rendered.
3. `artifact_type: 'video'` → `testID="artifact-video"` rendered with "▶ Play video".
4. `artifact_type: 'table'` with valid JSON → `testID="artifact-table"` rendered.
5. `artifact_generation_status: 'running'` → "Generating artifact…" visible.
6. `artifact_generation_status: 'failed'` → "Artifact generation failed" visible.
7. `artifact_type: 'text'` → returns null (nothing in rendered output).

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/mobile/src/__tests__/components/ArtifactRenderer.test.tsx` | `artifact_type: 'image', artifact_uri: 'https://img.jpg'` | `testID="artifact-image"` in output |
| E2-S2-T2 | same | `artifact_type: 'video', artifact_uri: 'https://vid.mp4'` | `testID="artifact-video"` and "▶ Play video" in output |
| E2-S2-T3 | same | `artifact_type: 'table', artifact_uri: '[{"col":"val"}]'` | `testID="artifact-table"` in output |
| E2-S2-T4 | same | `artifact_generation_status: 'running'` | "Generating artifact…" in output |
| E2-S2-T5 | same | `artifact_generation_status: 'failed'` | "Artifact generation failed" in output |
| E2-S2-T6 | same | `artifact_type: 'text'` | Rendered output is null / empty |

**Test command:**
```bash
cd src/mobile && node_modules/.bin/jest src/__tests__/components/ArtifactRenderer.test.tsx --no-coverage
```

**Commit message:** `feat(MOB-DMA-1): E2-S2 — ArtifactRenderer (table/image/mp4)`

**Done signal:** `"E2-S2 done. Created: ArtifactRenderer.tsx. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅ T6 ✅"`

---

### Epic E3: Voice input is a customer choice — not the only input path

**Branch:** `feat/MOB-DMA-1-it1-e3`

---

#### Story E3-S1: Wire existing VoiceFAB into DMAConversationScreen as optional toggle

**BLOCKED UNTIL:** E2-S1 committed
**Estimated time:** 30 min
**Branch:** `feat/MOB-DMA-1-it1-e3`
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> `AgentOperationsScreen.tsx` already wires `VoiceFAB` and `useAgentVoiceOverlay`. Add the same to `DMAConversationScreen.tsx`. Import `VoiceFAB` from `@/components/voice/VoiceFAB` and `useAgentVoiceOverlay` from `@/hooks/useAgentVoiceOverlay`. Add the hook inside the component with command `'send message': handleSend`. Render `<VoiceFAB isListening={voiceListening} onPress={voiceToggle} testID="voice-fab-dma" position="bottom-left" />` inside `SafeAreaView` after `</KeyboardAvoidingView>`, gated by `voiceAvailable`. The text input and Send button must remain fully functional when voice is unavailable — do not remove or disable them.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | 345–375 | Exact `useAgentVoiceOverlay` call pattern and `VoiceFAB` render |
| `src/mobile/src/screens/agents/DMAConversationScreen.tsx` | 1–55 | Current imports and handleSend declaration — where to add hook |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/agents/DMAConversationScreen.tsx` | modify | Add VoiceFAB import, useAgentVoiceOverlay import, hook call (after handleSend), and conditional FAB inside SafeAreaView after </KeyboardAvoidingView> |

**Code patterns to copy exactly:**

```typescript
// Add these two imports at top of DMAConversationScreen.tsx:
import { VoiceFAB } from '@/components/voice/VoiceFAB'
import { useAgentVoiceOverlay } from '@/hooks/useAgentVoiceOverlay'

// Add hook call inside component after handleSend useCallback:
const { isListening: voiceListening, toggle: voiceToggle, isAvailable: voiceAvailable } =
  useAgentVoiceOverlay({ 'send message': handleSend })

// Add inside return's SafeAreaView, after </KeyboardAvoidingView>:
{voiceAvailable && (
  <VoiceFAB
    isListening={voiceListening}
    onPress={voiceToggle}
    testID="voice-fab-dma"
    position="bottom-left"
  />
)}
```

**Acceptance criteria:**
1. `DMAConversationScreen` renders `testID="voice-fab-dma"` when `useAgentVoiceOverlay` returns `isAvailable: true`.
2. `testID="voice-fab-dma"` NOT rendered when `isAvailable: false`.
3. Text input (`testID="dma-chat-input"`) and Send button (`testID="dma-chat-send"`) are present regardless of voice availability.
4. Speaking "send message" invokes `handleSend`.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/mobile/src/__tests__/screens/DMAConversationScreen.test.tsx` | Mock `useAgentVoiceOverlay` returns `{ isAvailable: true, isListening: false, toggle: jest.fn() }` | `testID="voice-fab-dma"` in output |
| E3-S1-T2 | same | Mock `useAgentVoiceOverlay` returns `{ isAvailable: false, isListening: false, toggle: jest.fn() }` | `testID="voice-fab-dma"` NOT in output; `testID="dma-chat-input"` still present |

**Test command:**
```bash
cd src/mobile && node_modules/.bin/jest src/__tests__/screens/DMAConversationScreen.test.tsx --no-coverage
```

**Commit message:** `feat(MOB-DMA-1): E3-S1 — voice toggle wired into DMAConversationScreen`

**Done signal:** `"E3-S1 done. Modified: DMAConversationScreen.tsx. Tests: T1 ✅ T2 ✅"`

---

