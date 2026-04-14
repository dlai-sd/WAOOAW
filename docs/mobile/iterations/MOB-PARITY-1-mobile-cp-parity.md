# MOB-PARITY-1 — Mobile CP Feature Parity Iteration Plan

> **Objective alignment:** DMA enablement — ensures the mobile app can serve DMA customers
> end-to-end (approve content, review analytics, manage YouTube connections, monitor deliverables,
> handle billing) directly from mobile, driving trial-to-paid conversion for the first commercial
> agent priority.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | MOB-PARITY-1 |
| Feature area | Mobile App — CP Feature Parity |
| Created | 2026-04-14 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §23 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 6 |
| Total stories | 6 |

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

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list based on the tech stack that iteration uses (React Native/TypeScript/Expo)
- [x] Epic titles name customer outcomes, not technical actions ("Customer sees X" not "Add X to API")
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C — N/A (no CP BackEnd changes — mobile talks to Plant Gateway directly)
- [x] Every new backend route story embeds the `waooaw_router()` snippet — N/A (no backend changes)
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()` — N/A (no backend changes)
- [x] Every story that adds env vars lists the exact Terraform file paths to update — N/A (no env var changes)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2) — N/A (pure mobile/frontend iteration)
- [x] Iteration count minimized for PR-only delivery (1 iteration)
- [x] Related backend/frontend work kept in the same iteration — all in one iteration
- [x] No placeholders remain

---

## Drift Prevention Contract

> **Purpose:** This plan includes explicit anti-drift mechanisms to ensure the mobile app
> stays functionally aligned with CP Frontend. Test coverage serves as the corrective measure.

| Drift vector | Prevention mechanism | Detection |
|---|---|---|
| API contract mismatch | Mobile services use same Plant Gateway endpoints as CP FE services — types match Plant response schemas | TypeScript strict mode catches type drift; Jest tests mock responses matching Plant schemas |
| Screen parity regression | Each story acceptance criteria references the equivalent CP page — functionality must match | Jest snapshot + behaviour tests confirm identical data flow paths |
| Navigation inconsistency | Navigation types (`types.ts`) updated atomically with screen additions | Navigation test suite validates all routes are reachable |
| Voice/text input drift | Voice chat is an input mode toggle, not a separate flow — same service calls underneath | Tests cover both voice-initiated and text-initiated paths |
| Component reuse erosion | Shared components (`EmptyState`, `ErrorView`, `LoadingSpinner`) must be used — no inline alternatives | Test assertions verify component render in loading/error/empty states |
| Coverage regression | Every story mandates ≥80% coverage on new files; CI blocks PRs below threshold | `jest --coverage` in test command for each story |

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — Wire existing Plant Gateway APIs into new mobile screens/services with voice command overlay, achieving full CP feature parity | 6 | 6 | 6h | 2026-04-14 21:00 UTC |

**Estimate basis:** Each story = new screen + service + hook + tests ≈ 60 min average. Add 20% buffer for zero-cost model context loading. Total = 6 × 60 min = 6h.

### PR-Overhead Optimization Rules

- Single iteration — one merge to `main` unlocks full mobile CP parity.
- All 6 stories are independent vertical slices (each delivers one complete screen).
- No cross-story blocking dependencies — agent can execute in order without merge gates.

---

## How to Launch Each Iteration

> Instructions for running the development agent from the GitHub repository Agents tab.
> These plans are written for GitHub-hosted agents, where shell, git, gh, and docker tools may be unavailable.
> Do not make terminal access a prerequisite to start the iteration.

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
7. Go away. Come back at: **2026-04-14 21:00 UTC**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer + Senior mobile UX/accessibility engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-PARITY-1-mobile-cp-parity.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3, E4, E5, E6. This is a single-iteration plan.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify this execution surface allows repository writes on the current task branch.
3. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
5. Execute Epics in this order: E1 → E2 → E3 → E4 → E5 → E6
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required `Prerequisite evidence` block for this iteration is complete and not marked pending.
- The GitHub execution surface lets you save repository changes on the current task branch.
- The GitHub execution surface lets you open or update a PR to `main`, or you can explicitly report that PR controls are unavailable.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

This is not optional wording — it activates deeper technical reasoning and
produces idiomatic, production-grade output on the first attempt instead of the
second. Relevant persona table (scan and claim):

| Technology area | Expert persona to activate |
|---|---|
| `src/mobile/` | Senior React Native / Expo / TypeScript engineer |
| `src/mobile/src/services/` | Senior API integration / TypeScript engineer |
| `src/mobile/src/components/` | Senior mobile UX / accessibility engineer |
| `src/mobile/__tests__/` | Senior Jest / React Native Testing Library engineer |

---

### Rule 0 — Use the GitHub task branch and open the iteration PR early

GitHub-hosted agents usually start on a task-specific branch. Keep the entire iteration on that branch.

- If the execution surface already created a branch for this run, keep using it.
- If the UI lets you choose a branch name, prefer: `feat/MOB-PARITY-1-it1-mobile-cp-parity`.
- Open a draft PR to `main` as soon as PR controls are available and keep updating that same PR through the iteration.
- If draft PR creation is not available early, continue working and open the iteration PR before HALT.
- Use the Tracking Table in this plan as the source of truth for story status updates.

---

### Rule 1 — Branch discipline
One iteration = one GitHub task branch and one PR.
Treat every `Branch:` value in story cards as a logical label only; on the GitHub Agents tab, keep the full iteration on the single branch created for the run.
Never push or merge directly to `main`.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table. Do not edit any other file — not Dockerfiles, not CI workflows, not other services — even if you see an obvious improvement. Record it as a PR description note instead.

**Missing iteration HALT rule**: Before writing any code, verify your assigned iteration section exists in the plan file.
If the section is missing, post: "Iteration N not found in [plan file]. Cannot proceed." and HALT.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.
If this execution surface exposes test execution, run the story's listed command or the narrowest equivalent.
If not, add the tests anyway and note that execution is deferred to CI or local follow-up.

### Rule 4 — Save progress after every story
- Update this plan file's Tracking Table: change the story status to Done or Blocked.
- Save code and plan updates to the GitHub task branch for this run.
- If the PR already exists, add a concise progress update in the PR description or comments with files changed, tests added/run, and the next story.

### Rule 5 — Validate after every epic
- Prefer the narrowest relevant automated validation for the files you changed.
- If GitHub Agents exposes execution tools, run the relevant test command and record the result.
- If execution tools are unavailable, state clearly that validation is deferred to CI or local follow-up and continue.
- After validation, add `**Epic complete ✅**` under the epic heading if the epic is complete.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
- Mark the blocked story as `🚫 Blocked` in the Tracking Table.
- Open or update a draft PR titled `WIP: [story-id] — blocked` if PR controls are available.
- Include the exact blocker, the exact error message, and 1-2 attempted fixes.
- Post the PR URL if available. Otherwise post the blocker in the GitHub agent thread. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
- Use the same GitHub task branch for the final iteration PR to `main`.
- Title format: `feat(MOB-PARITY-1): iteration 1 — mobile CP feature parity`.
- PR body must include: completed stories for this iteration, validation status or deferral note, and the NFR checklist.
- Post the PR URL in the task thread. **HALT — do not start the next iteration.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(MOB-PARITY-1): [epic-id] — [epic title]" && git push origin HEAD
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## NFR Quick Reference

> Mobile-specific NFR rules for this iteration. All patterns are embedded inline in each story card.

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | Every data-fetching screen must have loading + error + empty states | Silent failures / broken UX |
| 2 | Use shared components (`LoadingSpinner`, `ErrorView`, `EmptyState`) — no inline alternatives | Component reuse erosion |
| 3 | Every API service must include `X-Correlation-ID` header (via `apiClient.ts` interceptor) | Trace broken |
| 4 | Use `useTheme()` for all colors/spacing — no hardcoded values | Theme drift |
| 5 | All new screens must include `testID` props on interactive elements | Accessibility / E2E failures |
| 6 | React Query hooks for server state — Zustand for client state only | State management drift |
| 7 | Tests ≥ 80% coverage on all new files | PR blocked by CI |
| 8 | Voice input toggle must use existing `useSpeechToText` + `useTextToSpeech` hooks | Voice infrastructure fragmentation |
| 9 | TypeScript strict mode — no `any` types, no `@ts-ignore` | Type safety regression |
| 10 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 11 | `@shopify/flash-list` for long lists (not `FlatList`) | Performance regression on large datasets |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer reviews and approves deliverables from mobile | Deliverables & Inbox screen with voice-enabled approval actions | 🔴 Not Started | — |
| E2-S1 | 1 | Customer views usage, invoices, and receipts on mobile | Usage & Billing screen with invoice/receipt download | 🔴 Not Started | — |
| E3-S1 | 1 | Customer sees DMA content performance insights on mobile | Content Analytics dashboard with recommendations | 🔴 Not Started | — |
| E4-S1 | 1 | Customer manages YouTube and platform connections on mobile | Platform Connections setup and management screen | 🔴 Not Started | — |
| E5-S1 | 1 | Customer uses voice or text to interact with agent screens | Voice command layer integrated into agent interaction surfaces | 🔴 Not Started | — |
| E6-S1 | 1 | Drift prevention: parity test suite validates mobile matches CP | Parity test suite covering all new screens + navigation | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Mobile CP Feature Parity with Voice Chat

**Scope:** Customer can perform all CP Frontend operations from the mobile app — review deliverables, manage billing, view analytics, manage platform connections, and use voice commands for hands-free operation — with ≥80% test coverage and drift-prevention parity tests.
**Lane:** A (wire existing Plant Gateway APIs only — no backend changes)
**⏱ Estimated:** 6h | **Come back:** 2026-04-14 21:00 UTC
**Epics:** E1, E2, E3, E4, E5, E6
**Objective alignment:** DMA enablement — mobile parity ensures DMA customers can approve content, review analytics, manage YouTube connections, and monitor deliverables from mobile with voice command support, directly enabling trial-to-paid conversion.

### Dependency Map (Iteration 1)

```
E1-S1 (Deliverables & Inbox)     — independent
E2-S1 (Usage & Billing)          — independent
E3-S1 (Content Analytics)        — independent
E4-S1 (Platform Connections)     — independent
E5-S1 (Voice Command Overlay)    — soft dependency on E1, E3 (modifies their screens to add VoiceFAB)
E6-S1 (Parity Test Suite)        — depends on E1–E5 (runs last)
```

All stories E1–E4 are independent vertical slices. E5 modifies screens from E1 and E3 (adding voice FAB). E6 (parity tests) runs last as it validates all preceding screens. Recommended execution order: E1 → E2 → E3 → E4 → E5 → E6.

---

### Epic E1: Customer reviews and approves deliverables from mobile

**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**User story:** As a customer, I can view all my agent deliverables in a dedicated Inbox screen on mobile, filter by status (pending/approved/rejected), and approve or reject them with voice or tap, so that I never miss an approval action while away from my desktop.

---

#### Story E1-S1: Deliverables & Inbox screen with voice-enabled approval actions

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**CP BackEnd pattern:** N/A — mobile calls Plant Gateway directly via `cpApiClient`
**Objective alignment:** DMA value — customers approve DMA content drafts from mobile, unblocking the publish pipeline

**What to do (self-contained — read this card, then act):**
> The mobile app currently shows deliverables only inside `AgentOperationsScreen.tsx` in a collapsed section. There is no standalone Inbox/Deliverables screen. The CP Frontend has `Inbox.tsx` (approval queue with pending/approved/rejected counts) and `Deliverables.tsx` (deliverable list with review status, preview, approval workflow).
>
> Create a new `InboxScreen.tsx` in `src/mobile/src/screens/agents/` that shows all deliverables across all hired agents. Use the existing `useApprovalQueue` hook (in `src/mobile/src/hooks/useApprovalQueue.ts`) as the data source for per-agent queues. Create a new `useAllDeliverables` hook that aggregates deliverables from all hired agents (fetch hired agents list first via `hiredAgents.service.ts`, then fetch approval queue for each). Add a status filter bar (All / Pending / Approved / Rejected). Add a voice input toggle — tapping the mic icon lets the customer say "approve" or "reject" followed by the deliverable title, parsed via the existing `useSpeechToText` hook. Register the new screen in `MyAgentsStackParamList` in `types.ts` and add it to `MyAgentsNavigator` in `MainNavigator.tsx`. Add a tab-bar badge on "Ops" tab showing pending count (already partially implemented — enhance with inbox count).

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/hooks/useApprovalQueue.ts` | 1–100 | `DeliverableItem` interface, `fetchApprovalQueue`, `approveDeliverable`, `rejectDeliverable` functions |
| `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` | 1–80 | `getHiredAgents()` or equivalent function to list all hired agents for the customer |
| `src/mobile/src/hooks/useSpeechToText.ts` | 1–30 | `UseSpeechToTextResult` interface: `start`, `stop`, `transcript`, `isListening` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/agents/InboxScreen.tsx` | create | New screen: FlashList of `DeliverableItem` cards, status filter chips (All/Pending/Approved/Rejected), approve/reject swipe or button actions, voice mic FAB using `useSpeechToText`, loading/error/empty states via shared components. Use `useTheme()` for all colors. Dark theme `#0a0a0a` background. Each card shows: title, type badge, content preview (truncated), created_at, approve/reject buttons. Voice command parsing: when transcript contains "approve" + deliverable title fragment → auto-select and approve; when "reject" → auto-select and reject. |
| `src/mobile/src/hooks/useAllDeliverables.ts` | create | New hook: calls `hiredAgentsService.getHiredAgents()` to get all hired agent IDs, then fetches `cpApiClient.get(/cp/hired-agents/{id}/approval-queue)` for each. Returns `{ deliverables: DeliverableItem[], isLoading, error, approve, reject, refetch }`. Uses React Query `useQueries` for parallel fetching. Merges results into single sorted array (newest first). Adds `status` field derived from deliverable state. |
| `src/mobile/src/navigation/types.ts` | modify | Add `Inbox: undefined` to `MyAgentsStackParamList` type |
| `src/mobile/src/navigation/MainNavigator.tsx` | modify | Import `InboxScreen` and add `<MyAgentsStack.Screen name="Inbox" component={InboxScreen} />` inside `MyAgentsNavigator`. Add an "Inbox" button/link in the MyAgents tab header or as a FAB on MyAgentsScreen. |
| `src/mobile/src/screens/agents/index.ts` | modify | Export `InboxScreen` from the barrel file |

**Code patterns to copy exactly** (no other file reads needed for these):

```typescript
// React Native screen with 3-state data fetching (mandatory pattern):
import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useTheme } from '../../hooks/useTheme';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorView } from '../../components/ErrorView';
import { EmptyState } from '../../components/EmptyState';

export const InboxScreen = () => {
  const { colors, spacing } = useTheme();
  const { deliverables, isLoading, error, approve, reject, refetch } = useAllDeliverables();
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorView message="Failed to load deliverables" onRetry={refetch} />;
  if (!deliverables?.length) return <EmptyState message="No deliverables yet" icon="📭" />;

  const filtered = filter === 'all' ? deliverables : deliverables.filter(d => d.status === filter);

  return (
    <View style={{ flex: 1, backgroundColor: colors.black }} testID="inbox-screen">
      {/* Filter chips + FlashList + Voice FAB */}
    </View>
  );
};
```

```typescript
// Voice-enabled approval pattern (use existing hooks):
import { useSpeechToText } from '../../hooks/useSpeechToText';

// Inside component:
const { isListening, transcript, start, stop, isAvailable } = useSpeechToText();

// Parse voice command from transcript:
const parseVoiceApproval = (text: string): { action: 'approve' | 'reject'; query: string } | null => {
  const lower = text.toLowerCase().trim();
  if (lower.startsWith('approve')) return { action: 'approve', query: lower.replace('approve', '').trim() };
  if (lower.startsWith('reject')) return { action: 'reject', query: lower.replace('reject', '').trim() };
  return null;
};
```

**Acceptance criteria (binary pass/fail only):**
1. New `InboxScreen` renders with a FlashList of deliverable cards from all hired agents
2. Status filter chips (All/Pending/Approved/Rejected) filter the displayed list
3. Tapping "Approve" on a deliverable card calls the approve API and removes it from pending
4. Tapping "Reject" on a deliverable card calls the reject API and removes it from pending
5. Voice mic FAB is visible (if speech recognition available); tapping it starts listening; saying "approve [title]" triggers approval
6. Loading state shows `LoadingSpinner`, error state shows `ErrorView` with retry, empty state shows `EmptyState`
7. Screen is navigable from the MyAgents/Ops tab
8. All interactive elements have `testID` props

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/mobile/__tests__/InboxScreen.test.tsx` | Mock `useAllDeliverables` returns 3 deliverables (1 pending, 1 approved, 1 rejected) | All 3 cards rendered; filter "Pending" shows 1 card |
| E1-S1-T2 | same | Mock `useAllDeliverables` returns empty array | `EmptyState` component rendered with "No deliverables yet" |
| E1-S1-T3 | same | Mock `useAllDeliverables` returns loading=true | `LoadingSpinner` component rendered |
| E1-S1-T4 | same | Mock `useAllDeliverables` returns error | `ErrorView` component rendered with retry button |
| E1-S1-T5 | same | Mock approve mutation, press "Approve" on a pending card | `approve` function called with correct deliverable ID |
| E1-S1-T6 | `src/mobile/__tests__/useAllDeliverables.test.ts` | Mock cpApiClient to return deliverables for 2 agents | Hook returns merged, sorted array of all deliverables |
| E1-S1-T7 | same | Mock cpApiClient to reject for one agent | Hook returns partial results + error state |

**Test command:**
```bash
cd src/mobile && npx jest __tests__/InboxScreen.test.tsx __tests__/useAllDeliverables.test.ts --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

---

### Epic E2: Customer views usage, invoices, and receipts on mobile

**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**User story:** As a customer, I can view my subscription usage, download invoices, and view receipts on mobile, so that I have full billing transparency without needing the desktop portal.

---

#### Story E2-S1: Usage & Billing screen with invoice/receipt download

**BLOCKED UNTIL:** none
**Estimated time:** 60 min
**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**CP BackEnd pattern:** N/A — mobile calls Plant Gateway directly
**Objective alignment:** DMA enablement — billing transparency drives trial-to-paid conversion and retention for DMA customers

**What to do (self-contained — read this card, then act):**
> The mobile app has `SubscriptionManagementScreen.tsx` and `PaymentMethodsScreen.tsx` in the Profile stack, but neither shows invoices, receipts, or usage history. The CP Frontend has `UsageBilling.tsx` which shows subscriptions, invoices (with download), receipts (with download), and next billing date.
>
> Create a new `UsageBillingScreen.tsx` in `src/mobile/src/screens/profile/` that shows: (a) active subscriptions summary (reuse data from existing `SubscriptionManagementScreen`), (b) invoices list with "Download" button that opens the invoice HTML in the device browser, (c) receipts list with "Download" button. Create two new service files: `invoices.service.ts` and `receipts.service.ts` in `src/mobile/src/services/` that call the Plant Gateway endpoints (same as CP Frontend's invoice/receipt services). Create a `useInvoices` and `useReceipts` hook or combine into `useBillingData`. Register the screen in `ProfileStackParamList` and `ProfileNavigator`. Add a "Usage & Billing" menu item in the existing `ProfileScreen`.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/screens/profile/SubscriptionManagementScreen.tsx` | 1–80 | Existing subscription data pattern, how it fetches/renders subscriptions |
| `src/mobile/src/screens/profile/ProfileScreen.tsx` | 1–60 | Menu item pattern — how profile menu items navigate to sub-screens |
| `src/mobile/src/lib/cpApiClient.ts` | 1–40 | Base URL resolution for CP API calls (invoices/receipts use CP backend routes) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/profile/UsageBillingScreen.tsx` | create | New screen with 3 sections: Subscriptions Summary (card with plan name, status, next billing date), Invoices (FlashList of invoice rows: date, amount, status, "Download" button), Receipts (FlashList of receipt rows: date, amount, "View" button). Use `useTheme()` for styling, dark theme. Each section has independent loading state. Download buttons open invoice/receipt HTML URL in device browser via `Linking.openURL()`. |
| `src/mobile/src/services/invoices.service.ts` | create | `listInvoices()` → `cpApiClient.get('/cp/invoices')`, `getInvoiceHtml(invoiceId: string)` → `cpApiClient.get('/cp/invoices/{id}/html')`. Types: `Invoice { id, amount, currency, status, created_at, pdf_url? }`. |
| `src/mobile/src/services/receipts.service.ts` | create | `listReceipts()` → `cpApiClient.get('/cp/receipts')`, `getReceiptHtml(receiptId: string)` → `cpApiClient.get('/cp/receipts/{id}/html')`. Types: `Receipt { id, amount, currency, created_at, order_id }`. |
| `src/mobile/src/hooks/useBillingData.ts` | create | Combines `useQuery` for invoices and receipts. Returns `{ invoices, receipts, isLoading, error, refetch }`. |
| `src/mobile/src/navigation/types.ts` | modify | Add `UsageBilling: undefined` to `ProfileStackParamList` type |
| `src/mobile/src/navigation/MainNavigator.tsx` | modify | Import `UsageBillingScreen` and add `<ProfileStack.Screen name="UsageBilling" component={UsageBillingScreen} />` inside `ProfileNavigator` |
| `src/mobile/src/screens/profile/ProfileScreen.tsx` | modify | Add a "Usage & Billing" menu item that navigates to `UsageBilling` screen (follow same pattern as existing menu items) |
| `src/mobile/src/screens/profile/index.ts` | modify | Export `UsageBillingScreen` from barrel file |

**Code patterns to copy exactly:**

```typescript
// Service file pattern (matches existing mobile services):
import cpApiClient from '../lib/cpApiClient';

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'overdue';
  created_at: string;
  pdf_url?: string;
}

export async function listInvoices(): Promise<Invoice[]> {
  const response = await cpApiClient.get<Invoice[]>('/cp/invoices');
  return response.data;
}

export async function getInvoiceHtml(invoiceId: string): Promise<string> {
  const response = await cpApiClient.get<string>(`/cp/invoices/${invoiceId}/html`);
  return response.data;
}
```

```typescript
// React Query hook pattern (matches existing hooks):
import { useQuery } from '@tanstack/react-query';
import { listInvoices, Invoice } from '../services/invoices.service';
import { listReceipts, Receipt } from '../services/receipts.service';

export function useBillingData() {
  const invoicesQuery = useQuery<Invoice[]>({ queryKey: ['invoices'], queryFn: listInvoices });
  const receiptsQuery = useQuery<Receipt[]>({ queryKey: ['receipts'], queryFn: listReceipts });

  return {
    invoices: invoicesQuery.data ?? [],
    receipts: receiptsQuery.data ?? [],
    isLoading: invoicesQuery.isLoading || receiptsQuery.isLoading,
    error: invoicesQuery.error || receiptsQuery.error,
    refetch: () => { invoicesQuery.refetch(); receiptsQuery.refetch(); },
  };
}
```

**Acceptance criteria (binary pass/fail only):**
1. `UsageBillingScreen` renders with sections for Subscriptions, Invoices, and Receipts
2. Invoices list shows date, amount, status, and a "Download" button per row
3. Receipts list shows date, amount, and a "View" button per row
4. Tapping "Download" on an invoice opens the invoice URL in device browser
5. Loading state shows `LoadingSpinner`, error shows `ErrorView`, empty shows `EmptyState`
6. Screen is navigable from Profile menu
7. All interactive elements have `testID` props

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/mobile/__tests__/UsageBillingScreen.test.tsx` | Mock `useBillingData` returns 2 invoices, 1 receipt | Invoice rows and receipt rows rendered correctly |
| E2-S1-T2 | same | Mock `useBillingData` returns empty arrays | `EmptyState` shown for invoices and receipts sections |
| E2-S1-T3 | same | Mock `useBillingData` returns loading=true | `LoadingSpinner` rendered |
| E2-S1-T4 | same | Mock `useBillingData` returns error | `ErrorView` rendered with retry |
| E2-S1-T5 | `src/mobile/__tests__/billingServices.test.ts` | Mock cpApiClient to return invoice list | `listInvoices()` returns correct typed data |
| E2-S1-T6 | same | Mock cpApiClient to return receipts | `listReceipts()` returns correct typed data |

**Test command:**
```bash
cd src/mobile && npx jest __tests__/UsageBillingScreen.test.tsx __tests__/billingServices.test.ts --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

---

### Epic E3: Customer sees DMA content performance insights on mobile

**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**User story:** As a DMA customer, I can view content performance analytics and AI-generated improvement recommendations on my phone, so that I can make data-driven decisions about my marketing content anywhere.

---

#### Story E3-S1: Content Analytics dashboard with recommendations

**BLOCKED UNTIL:** none
**Estimated time:** 60 min
**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**CP BackEnd pattern:** N/A — mobile calls Plant Gateway directly
**Objective alignment:** DMA value — content analytics enable customers to see ROI from agent work, directly driving retention and trial-to-paid conversion

**What to do (self-contained — read this card, then act):**
> The CP Frontend has `contentAnalytics.service.ts` which calls `getContentRecommendations()` and displays performance insights for DMA agents. The mobile app has no equivalent.
>
> Create a new `ContentAnalyticsScreen.tsx` in `src/mobile/src/screens/agents/` that shows: (a) performance summary cards (views, engagement rate, top-performing content type), (b) AI-generated recommendations list (each recommendation has title, description, confidence score), (c) time period selector (7d / 30d / 90d). Create a `contentAnalytics.service.ts` calling the Plant Gateway endpoint for content recommendations. Create a `useContentAnalytics` hook. Register the screen in `MyAgentsStackParamList` and add it as a navigation option from `AgentOperationsScreen` (in the performance section). Include voice readout — customer can tap a "Read insights" button that uses `useTextToSpeech` to speak the top recommendations aloud.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | 1–80 | How the screen is structured with collapsible sections; where to add "View Analytics" navigation |
| `src/mobile/src/hooks/useTextToSpeech.ts` | 1–40 | `UseTextToSpeechResult` interface: `speak`, `isSpeaking`, `stop` |
| `src/mobile/src/lib/cpApiClient.ts` | 1–20 | Import pattern and base URL for CP API calls |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/agents/ContentAnalyticsScreen.tsx` | create | New screen: performance summary cards at top (4 stat cards: total posts analyzed, avg engagement rate %, top dimensions, best posting hours), recommendations text block with AI-generated improvement advice. "Read Insights" FAB uses `useTextToSpeech` to speak the recommendation text aloud. Loading/error/empty states. Dark theme. All elements with `testID`. |
| `src/mobile/src/services/contentAnalytics.service.ts` | create | `getContentRecommendations(hiredAgentId: string)` → `cpApiClient.get('/cp/content-recommendations/{hiredAgentId}')`. Types: `ContentRecommendation { top_dimensions: string[], best_posting_hours: number[], avg_engagement_rate: number, total_posts_analyzed: number, recommendation_text: string }`. **Endpoint**: `/cp/content-recommendations/${hiredAgentId}` — matches CP FE's `contentAnalytics.service.ts`. |
| `src/mobile/src/hooks/useContentAnalytics.ts` | create | React Query hook wrapping `getContentRecommendations`. Accepts `hiredAgentId` param. Returns `{ data, isLoading, error, refetch }`. |
| `src/mobile/src/navigation/types.ts` | modify | Add `ContentAnalytics: { hiredAgentId: string }` to `MyAgentsStackParamList` |
| `src/mobile/src/navigation/MainNavigator.tsx` | modify | Import `ContentAnalyticsScreen` and add to `MyAgentsNavigator` stack |
| `src/mobile/src/screens/agents/index.ts` | modify | Export `ContentAnalyticsScreen` |

**Code patterns to copy exactly:**

```typescript
// Content analytics service pattern (matches CP FE contentAnalytics.service.ts):
import cpApiClient from '../lib/cpApiClient';

export interface ContentRecommendation {
  top_dimensions: string[];
  best_posting_hours: number[];
  avg_engagement_rate: number;
  total_posts_analyzed: number;
  recommendation_text: string;
}

export async function getContentRecommendations(
  hiredAgentId: string
): Promise<ContentRecommendation> {
  const response = await cpApiClient.get<ContentRecommendation>(
    `/cp/content-recommendations/${hiredAgentId}`
  );
  return response.data;
}
```

```typescript
// Voice readout pattern (use existing TTS infrastructure):
import { useTextToSpeech } from '../../hooks/useTextToSpeech';

// Inside component:
const { speak, isSpeaking, stop } = useTextToSpeech();

const readInsights = async () => {
  if (isSpeaking) { await stop(); return; }
  const script = data
    ? `You have ${data.total_posts_analyzed} posts analyzed with ${data.avg_engagement_rate.toFixed(1)} percent average engagement. Top dimensions are ${data.top_dimensions.join(', ')}. Recommendation: ${data.recommendation_text}`
    : 'No insights available yet.';
  await speak(script);
};
```

**Acceptance criteria (binary pass/fail only):**
1. `ContentAnalyticsScreen` renders 4 summary stat cards (total posts analyzed, avg engagement rate, top dimensions, best posting hours)
2. Recommendation text block shows AI-generated advice from `recommendation_text`
3. "Read Insights" button uses TTS to speak the summary and recommendation aloud
4. Loading/error/empty states use shared components
5. Screen is navigable from `AgentOperationsScreen` performance section
6. All interactive elements have `testID` props

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/mobile/__tests__/ContentAnalyticsScreen.test.tsx` | Mock `useContentAnalytics` returns `ContentRecommendation` with 5 top_dimensions, 3 posting hours, 42 posts, 7.2% engagement | Summary cards rendered: total posts, engagement rate, dimensions, posting hours |
| E3-S1-T2 | same | Mock returns null data | `EmptyState` component shown |
| E3-S1-T3 | same | Mock loading=true | `LoadingSpinner` shown |
| E3-S1-T4 | same | Mock error | `ErrorView` shown with retry |
| E3-S1-T5 | same | Press "Read Insights" button | `speak` function called with summary + recommendation text |
| E3-S1-T6 | `src/mobile/__tests__/contentAnalytics.service.test.ts` | Mock cpApiClient returns analytics data | Service function returns typed `ContentRecommendation` object |

**Test command:**
```bash
cd src/mobile && npx jest __tests__/ContentAnalyticsScreen.test.tsx __tests__/contentAnalytics.service.test.ts --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

---

### Epic E4: Customer manages YouTube and platform connections on mobile

**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**User story:** As a DMA customer, I can set up, view, and manage my YouTube and social platform connections on mobile, so that the marketing agent can publish approved content without me needing to use the desktop portal.

---

#### Story E4-S1: Platform Connections setup and management screen

**BLOCKED UNTIL:** none
**Estimated time:** 60 min
**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**CP BackEnd pattern:** N/A — mobile calls Plant Gateway directly
**Objective alignment:** DMA enablement — YouTube/platform connections are a prerequisite for DMA content publish pipeline; without mobile setup, customers are blocked from activating their DMA agent on-the-go

**What to do (self-contained — read this card, then act):**
> The mobile app currently shows YouTube publish status inside `MyAgentsScreen` but has no dedicated screen for connecting or managing platform connections. The CP Frontend has `platformConnections.service.ts` (credential-based connections: YouTube, Instagram, Facebook, LinkedIn, X, etc.) and `youtubeConnections.service.ts` (YouTube-specific OAuth flow).
>
> Create a new `PlatformConnectionsScreen.tsx` in `src/mobile/src/screens/agents/` that shows: (a) connected platforms list with status badges (Connected ✅ / Disconnected ❌ / Pending ⚠️), (b) "Connect" button for each platform that opens a credentials input form (matching `CreateConnectionBody` from CP FE: `skill_id`, `platform_key`, `credentials`), (c) YouTube-specific "Connect" button that triggers OAuth via `/cp/youtube-connections/connect/start` and opens the returned URL in device browser via `WebBrowser.openBrowserAsync()`, (d) connection health check — shows `last_verified_at` date. Create `platformConnections.service.ts` in services using the **actual CP FE endpoints**: GET/POST/DELETE on `/cp/hired-agents/{id}/platform-connections`. Register the screen in navigation.
>
> **IMPORTANT**: The platform connections API does NOT have a per-platform OAuth URL endpoint. Connections are created by POSTing `{ skill_id, platform_key, credentials }` to `/cp/hired-agents/{id}/platform-connections`. YouTube is the only platform with OAuth (via a separate `/cp/youtube-connections/connect/start` endpoint). Other platforms require manual credential input.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | 1–60 | Where platform status is shown; where to add "Manage Connections" link |
| `src/mobile/src/lib/cpApiClient.ts` | 1–20 | Import pattern for service files |
| `src/mobile/src/components/ConnectorSetupCard.tsx` | 1–60 | Existing card pattern for connector/platform setup display |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/agents/PlatformConnectionsScreen.tsx` | create | New screen: list of platforms rendered as cards showing: platform icon/name, connection status badge (Connected/Disconnected/Pending), `last_verified_at` timestamp, action button based on state. For YouTube: "Connect via Google" opens OAuth flow. For other platforms: "Connect" opens a credentials form (platform_key, credentials dict). Connected platforms show "Disconnect" button. Summary header: "X of Y platforms connected". Loading/error/empty states. Dark theme, `testID` on all interactive elements. |
| `src/mobile/src/services/platformConnections.service.ts` | create | `listPlatformConnections(hiredAgentId: string)` → `cpApiClient.get('/cp/hired-agents/{id}/platform-connections')`. `createPlatformConnection(hiredAgentId: string, body: CreateConnectionBody)` → `cpApiClient.post('/cp/hired-agents/{id}/platform-connections', body)` where `CreateConnectionBody = { skill_id: string, platform_key: string, credentials?: Record<string, unknown> }`. `deletePlatformConnection(hiredAgentId: string, connectionId: string)` → `cpApiClient.delete('/cp/hired-agents/{id}/platform-connections/{connectionId}')`. `startYouTubeOAuth(redirectUri: string)` → `cpApiClient.post('/cp/youtube-connections/connect/start', { redirect_uri: redirectUri })` returns `{ authorization_url: string }`. Types: `PlatformConnection { id, hired_instance_id, skill_id, platform_key, status, connected_at, last_verified_at, created_at, updated_at }`. |
| `src/mobile/src/hooks/usePlatformConnections.ts` | create | React Query hook wrapping `listPlatformConnections`. Returns `{ connections, isLoading, error, refetch, connect, disconnect }`. `connect` is a `useMutation` wrapping `createPlatformConnection` (or `startYouTubeOAuth` for YouTube). `disconnect` wraps `deletePlatformConnection`. Both invalidate the query on success. |
| `src/mobile/src/navigation/types.ts` | modify | Add `PlatformConnections: { hiredAgentId: string }` to `MyAgentsStackParamList` |
| `src/mobile/src/navigation/MainNavigator.tsx` | modify | Import `PlatformConnectionsScreen` and add to `MyAgentsNavigator` stack |
| `src/mobile/src/screens/agents/index.ts` | modify | Export `PlatformConnectionsScreen` |

**Code patterns to copy exactly:**

```typescript
// Platform connections service pattern (matches CP FE platformConnections.service.ts):
import cpApiClient from '../lib/cpApiClient';

export interface PlatformConnection {
  id: string;
  hired_instance_id: string;
  skill_id: string;
  customer_platform_credential_id?: string | null;
  platform_key: string; // e.g. 'youtube', 'instagram', 'facebook', 'linkedin', 'x'
  status?: string; // 'connected' | 'active' | 'pending' | 'disconnected'
  connected_at?: string | null;
  last_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateConnectionBody {
  skill_id: string;
  platform_key: string;
  credentials?: Record<string, unknown>;
}

export async function listPlatformConnections(hiredAgentId: string): Promise<PlatformConnection[]> {
  const response = await cpApiClient.get<PlatformConnection[]>(
    `/cp/hired-agents/${hiredAgentId}/platform-connections`
  );
  // Handle both array and { connections: [...] } response shapes
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as any)?.connections)) return (data as any).connections;
  return [];
}

export async function createPlatformConnection(
  hiredAgentId: string,
  body: CreateConnectionBody
): Promise<PlatformConnection> {
  const response = await cpApiClient.post<PlatformConnection>(
    `/cp/hired-agents/${hiredAgentId}/platform-connections`,
    body
  );
  return response.data;
}

export async function deletePlatformConnection(
  hiredAgentId: string,
  connectionId: string
): Promise<void> {
  await cpApiClient.delete(
    `/cp/hired-agents/${hiredAgentId}/platform-connections/${connectionId}`
  );
}

// YouTube-specific OAuth (separate endpoint from general platform connections):
export async function startYouTubeOAuth(redirectUri: string): Promise<{ authorization_url: string }> {
  const response = await cpApiClient.post<{ authorization_url: string }>(
    '/cp/youtube-connections/connect/start',
    { redirect_uri: redirectUri }
  );
  return response.data;
}
```

```typescript
// YouTube OAuth flow on mobile — open in system browser:
import * as WebBrowser from 'expo-web-browser';

const handleConnectYouTube = async () => {
  const { authorization_url } = await startYouTubeOAuth(Linking.createURL('/youtube-callback'));
  await WebBrowser.openBrowserAsync(authorization_url);
  // After OAuth completes, deep link returns to app — refetch connections
  refetch();
};

// Non-OAuth platform connection — credential form submit:
const handleConnectPlatform = async (skillId: string, platformKey: string, credentials: Record<string, unknown>) => {
  await createPlatformConnection(hiredAgentId, { skill_id: skillId, platform_key: platformKey, credentials });
  refetch();
};
```

**Acceptance criteria (binary pass/fail only):**
1. `PlatformConnectionsScreen` renders a list of platform cards with status badges
2. Summary header shows "X of Y platforms connected"
3. Tapping "Connect via Google" on YouTube calls `startYouTubeOAuth` and opens browser with `authorization_url`
4. Tapping "Connect" on non-YouTube platforms opens a credentials input form; submitting calls `createPlatformConnection` with `{ skill_id, platform_key, credentials }`
5. Connected platforms show "Disconnect" button; tapping it calls `deletePlatformConnection` API
6. Loading/error/empty states use shared components
7. Screen is navigable from `AgentOperationsScreen`
8. All interactive elements have `testID` props

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/mobile/__tests__/PlatformConnectionsScreen.test.tsx` | Mock `usePlatformConnections` returns 3 connections (1 connected, 1 disconnected, 1 pending) | 3 cards rendered with correct status badges; summary shows "1 of 3" |
| E4-S1-T2 | same | Mock returns empty array | `EmptyState` shown |
| E4-S1-T3 | same | Mock loading=true | `LoadingSpinner` shown |
| E4-S1-T4 | same | Press "Connect" on YouTube platform | `startYouTubeOAuth` called, `WebBrowser.openBrowserAsync` called with `authorization_url` |
| E4-S1-T5 | same | Press "Connect" on non-YouTube platform, submit credentials | `createPlatformConnection` called with correct `CreateConnectionBody` |
| E4-S1-T6 | `src/mobile/__tests__/platformConnections.service.test.ts` | Mock cpApiClient returns connections | `listPlatformConnections` returns typed array |
| E4-S1-T7 | same | Mock cpApiClient for YouTube OAuth start | `startYouTubeOAuth` returns `{ authorization_url }` |
| E4-S1-T8 | same | Mock cpApiClient for create connection | `createPlatformConnection` returns typed `PlatformConnection` |

**Test command:**
```bash
cd src/mobile && npx jest __tests__/PlatformConnectionsScreen.test.tsx __tests__/platformConnections.service.test.ts --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

---

### Epic E5: Customer uses voice or text to interact with agent screens

**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**User story:** As a customer, I can toggle between voice and text input across all agent screens, so that I can approve deliverables hands-free, request analytics readback, and navigate between operations without typing.

---

#### Story E5-S1: Voice command layer integrated into agent interaction surfaces

**BLOCKED UNTIL:** none
**Estimated time:** 60 min
**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**CP BackEnd pattern:** N/A — voice is a client-side input mode; no backend changes
**Objective alignment:** DMA enablement — voice commands let DMA customers approve content, hear analytics, and navigate agent operations hands-free, reducing friction and increasing engagement

> **NOTE — Chat endpoint deferred:** The CP Frontend does not currently have a chat/messaging
> service. A standalone agent chat screen would require a new backend endpoint (Lane B). This
> story instead delivers voice input as a **command overlay** across the E1–E4 screens, which is
> Lane A work (purely client-side, no new backend). A future iteration can add the chat endpoint
> and build a dedicated `VoiceChatScreen` on top of it.

**What to do (self-contained — read this card, then act):**
> The mobile app has full voice infrastructure: `useSpeechToText` hook (speech-to-text), `useTextToSpeech` hook (text-to-speech), `useVoiceCommands` hook (command parsing), `VoiceFAB` component (floating mic button), and `VoiceControl` component. However, these are not wired into any agent operation surface yet.
>
> Create a `useAgentVoiceOverlay` hook in `src/mobile/src/hooks/` that provides a reusable voice command layer for any agent screen. Features: (a) activates STT when user taps the mic FAB, (b) parses transcript for known commands: "approve [title]", "reject [title]", "read insights", "go to inbox", "go to billing", "go to connections", (c) executes the matched command callback, (d) provides TTS feedback on command execution ("Approved: [title]"). Wire this hook into `InboxScreen` (E1), `ContentAnalyticsScreen` (E3), and update `AgentOperationsScreen` to use voice navigation. Add the `VoiceFAB` component as a floating button on each of these screens. Default input mode is text; voice activates on FAB tap. Persist voice preference in Zustand `uiStore`.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/hooks/useVoiceCommands.ts` | 1–60 | Full voice command flow: STT → parse → TTS feedback. `UseVoiceCommandsResult` interface |
| `src/mobile/src/components/voice/VoiceFAB.tsx` | 1–40 | Existing FAB component: props, pulsing animation, haptic feedback pattern |
| `src/mobile/src/hooks/useSpeechToText.ts` | 1–30 | `start`, `stop`, `transcript`, `isListening` — how to capture voice input |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/hooks/useAgentVoiceOverlay.ts` | create | New hook: combines `useSpeechToText` + `useTextToSpeech` into a command-parsing layer. Accepts a `commands` map: `Record<string, (args: string) => void | Promise<void>>`. When `isListening` goes false and `transcript` is non-empty, match transcript against command map keys (case-insensitive prefix match). If match found, call the handler with the rest of the transcript as args, then TTS confirm: "Done: [command]". If no match, TTS: "Command not recognized. Try: [list available commands]." Returns `{ isListening, toggle, lastCommand, isAvailable }`. Persist `voiceEnabled` preference in Zustand (add to existing auth/ui store). |
| `src/mobile/src/screens/agents/InboxScreen.tsx` | modify | Wire `useAgentVoiceOverlay` with commands `{ approve: (title) => matchAndApprove(title), reject: (title) => matchAndReject(title) }`. Add `VoiceFAB` positioned bottom-right, `onPress={toggle}`. |
| `src/mobile/src/screens/agents/ContentAnalyticsScreen.tsx` | modify | Wire `useAgentVoiceOverlay` with command `{ "read insights": () => readInsights() }`. Add `VoiceFAB` positioned bottom-right. |
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | modify | Wire `useAgentVoiceOverlay` with navigation commands: `{ "go to inbox": () => navigate('Inbox'), "go to analytics": (id) => navigate('ContentAnalytics', { hiredAgentId }), "go to connections": (id) => navigate('PlatformConnections', { hiredAgentId }) }`. Add `VoiceFAB`. |

**Code patterns to copy exactly:**

```typescript
// Voice command overlay hook pattern:
import { useEffect, useCallback, useRef } from 'react';
import { useSpeechToText } from './useSpeechToText';
import { useTextToSpeech } from './useTextToSpeech';

type CommandMap = Record<string, (args: string) => void | Promise<void>>;

interface UseAgentVoiceOverlayResult {
  isListening: boolean;
  toggle: () => void;
  lastCommand: string | null;
  isAvailable: boolean;
}

export function useAgentVoiceOverlay(commands: CommandMap): UseAgentVoiceOverlayResult {
  const { isListening, transcript, start, stop, isAvailable } = useSpeechToText();
  const { speak } = useTextToSpeech();
  const [lastCommand, setLastCommand] = useState<string | null>(null);

  const toggle = useCallback(() => {
    if (isListening) { stop(); } else { start({ language: 'en-US' }); }
  }, [isListening, start, stop]);

  useEffect(() => {
    if (!isListening && transcript) {
      const lower = transcript.toLowerCase().trim();
      const match = Object.entries(commands).find(([key]) => lower.startsWith(key.toLowerCase()));
      if (match) {
        const [key, handler] = match;
        const args = lower.slice(key.length).trim();
        setLastCommand(key);
        handler(args);
        speak(`Done: ${key}`);
      } else {
        speak(`Command not recognized. Try: ${Object.keys(commands).join(', ')}`);
      }
    }
  }, [isListening, transcript]);

  return { isListening, toggle, lastCommand, isAvailable };
}
```

```typescript
// Wiring VoiceFAB on a screen:
import { VoiceFAB } from '../../components/voice/VoiceFAB';
import { useAgentVoiceOverlay } from '../../hooks/useAgentVoiceOverlay';

// Inside InboxScreen:
const { isListening, toggle, isAvailable } = useAgentVoiceOverlay({
  approve: (titleFragment) => {
    const match = deliverables.find(d => d.title?.toLowerCase().includes(titleFragment));
    if (match) approve(match.id);
  },
  reject: (titleFragment) => {
    const match = deliverables.find(d => d.title?.toLowerCase().includes(titleFragment));
    if (match) reject(match.id);
  },
});

// In JSX:
{isAvailable && <VoiceFAB isListening={isListening} onPress={toggle} testID="voice-fab" />}
```

**Acceptance criteria (binary pass/fail only):**
1. `useAgentVoiceOverlay` hook exists and parses voice transcript against a command map
2. `InboxScreen` has `VoiceFAB`; saying "approve [title]" triggers the approve API for the matched deliverable
3. `ContentAnalyticsScreen` has `VoiceFAB`; saying "read insights" triggers TTS readback
4. `AgentOperationsScreen` has `VoiceFAB`; saying "go to inbox" navigates to InboxScreen
5. Unrecognized commands produce a TTS error message listing available commands
6. VoiceFAB only renders when speech recognition is available (`isAvailable`)
7. Default input mode is text; voice activates on FAB tap
8. All interactive elements have `testID` props

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S1-T1 | `src/mobile/__tests__/useAgentVoiceOverlay.test.ts` | Mock `useSpeechToText` with transcript "approve monthly report" | Matching command handler called with "monthly report" as args |
| E5-S1-T2 | same | Mock transcript "unknown command" | `speak` called with "Command not recognized" message |
| E5-S1-T3 | same | Call `toggle()` when not listening | `start()` called on STT hook |
| E5-S1-T4 | `src/mobile/__tests__/InboxScreen.test.tsx` | Render InboxScreen with voice mocks | `VoiceFAB` component rendered with `testID="voice-fab"` |
| E5-S1-T5 | `src/mobile/__tests__/ContentAnalyticsScreen.test.tsx` | Render ContentAnalyticsScreen with voice mocks | `VoiceFAB` component rendered |
| E5-S1-T6 | `src/mobile/__tests__/AgentOperationsVoice.test.tsx` | Mock voice command "go to inbox" on AgentOperationsScreen | Navigation `navigate('Inbox')` called |

**Test command:**
```bash
cd src/mobile && npx jest __tests__/useAgentVoiceOverlay.test.ts __tests__/InboxScreen.test.tsx __tests__/ContentAnalyticsScreen.test.tsx __tests__/AgentOperationsVoice.test.ts --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

---

### Epic E6: Drift prevention — parity test suite validates mobile matches CP

**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**User story:** As a platform engineer, I have a parity test suite that verifies mobile screens match CP Frontend functionality, so that future changes to either surface are caught by CI before they drift apart.

---

#### Story E6-S1: Parity test suite covering all new screens and navigation

**BLOCKED UNTIL:** E1-S1, E2-S1, E3-S1, E4-S1, E5-S1 (runs last — validates all preceding screens)
**Estimated time:** 60 min
**Branch:** `feat/MOB-PARITY-1-it1-mobile-cp-parity`
**CP BackEnd pattern:** N/A — test-only story
**Objective alignment:** DMA enablement — drift prevention ensures mobile DMA features remain aligned with CP Frontend as both evolve, preventing customer confusion and support overhead

**What to do (self-contained — read this card, then act):**
> After E1–E5 are complete, the mobile app has 5 new screens. This story creates a dedicated parity test suite that validates: (a) all new screens are registered in navigation and reachable, (b) each screen's data-fetching pattern matches the equivalent CP service call signature, (c) every screen renders loading/error/empty states correctly, (d) voice integration is functional across applicable screens. This test suite runs in CI and serves as a drift-detection gate — if a CP service adds a field that mobile doesn't handle, or mobile drops a screen from navigation, these tests fail.
>
> Create a `mobileCpParity.test.tsx` integration test file that:
> 1. Validates navigation: all 5 new screens are registered in `MyAgentsStackParamList` and `ProfileStackParamList`
> 2. Validates service API contract alignment: each mobile service function signature matches the expected Plant Gateway endpoint path and HTTP method
> 3. Validates shared component usage: each new screen uses `LoadingSpinner`, `ErrorView`, `EmptyState` (not inline alternatives)
> 4. Validates voice integration: screens that support voice have `useSpeechToText` or `useTextToSpeech` wired
> 5. Validates `testID` coverage: every new screen has at least one root `testID` prop
>
> Additionally, update the existing navigation test (`src/mobile/__tests__/navigation.test.ts`) to include the new screens.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/__tests__/navigation.test.ts` | 1–60 | Existing navigation test pattern — how screens are validated as registered |
| `src/mobile/src/navigation/types.ts` | 1–150 | Full param list types — verify all new screens are in their stack types |
| `src/mobile/__tests__/coreScreens.test.tsx` | 1–60 | Existing pattern for testing multiple screens render correctly |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/__tests__/mobileCpParity.test.tsx` | create | Parity test suite with 5 sections: (1) Navigation parity — import `MyAgentsStackParamList` and `ProfileStackParamList` types, assert `Inbox`, `ContentAnalytics`, `PlatformConnections` are keys of `MyAgentsStackParamList` and `UsageBilling` is key of `ProfileStackParamList`. (2) Service contract parity — import each new service file, assert each exported function exists and is callable. (3) Screen render parity — render each new screen with mocked dependencies, assert `LoadingSpinner` renders during loading, `ErrorView` during error, `EmptyState` when empty. (4) Voice integration parity — render `InboxScreen` and `ContentAnalyticsScreen`, assert `useAgentVoiceOverlay` mock was accessed and `VoiceFAB` is rendered. (5) TestID coverage — render each screen, assert `testID` prop exists on root element. |
| `src/mobile/__tests__/navigation.test.ts` | modify | Add test cases for new screens: `Inbox`, `UsageBilling`, `ContentAnalytics`, `PlatformConnections` — validate they are reachable from their parent navigators |

**Code patterns to copy exactly:**

```typescript
// Navigation parity test pattern:
import type { MyAgentsStackParamList, ProfileStackParamList } from '../src/navigation/types';

describe('Mobile-CP Parity: Navigation', () => {
  it('MyAgents stack includes all parity screens', () => {
    // TypeScript compile-time check — if these types exist, the screens are registered
    const myAgentsScreens: (keyof MyAgentsStackParamList)[] = [
      'MyAgents', 'AgentDetail', 'TrialDashboard', 'ActiveTrialsList',
      'HiredAgentsList', 'AgentOperations',
      // New parity screens:
      'Inbox', 'ContentAnalytics', 'PlatformConnections',
    ];
    expect(myAgentsScreens).toHaveLength(9);
  });

  it('Profile stack includes UsageBilling', () => {
    const profileScreens: (keyof ProfileStackParamList)[] = [
      'Profile', 'EditProfile', 'Settings', 'Notifications',
      'PaymentMethods', 'SubscriptionManagement', 'HelpCenter',
      'PrivacyPolicy', 'TermsOfService',
      // New parity screen:
      'UsageBilling',
    ];
    expect(profileScreens).toHaveLength(10);
  });
});
```

```typescript
// Service contract parity test pattern:
import { listInvoices, getInvoiceHtml } from '../src/services/invoices.service';
import { listReceipts, getReceiptHtml } from '../src/services/receipts.service';
import { getContentRecommendations } from '../src/services/contentAnalytics.service';
import { listPlatformConnections, createPlatformConnection, deletePlatformConnection, startYouTubeOAuth } from '../src/services/platformConnections.service';

describe('Mobile-CP Parity: Service Contracts', () => {
  it('all parity services are importable and callable', () => {
    expect(typeof listInvoices).toBe('function');
    expect(typeof getInvoiceHtml).toBe('function');
    expect(typeof listReceipts).toBe('function');
    expect(typeof getReceiptHtml).toBe('function');
    expect(typeof getContentRecommendations).toBe('function');
    expect(typeof listPlatformConnections).toBe('function');
    expect(typeof createPlatformConnection).toBe('function');
    expect(typeof deletePlatformConnection).toBe('function');
    expect(typeof startYouTubeOAuth).toBe('function');
  });
});
```

```typescript
// Shared component usage parity test pattern:
// For each new screen, render with loading mock and verify LoadingSpinner:
import { render } from '@testing-library/react-native';
import { LoadingSpinner } from '../src/components/LoadingSpinner';

// Mock the hook to return loading state:
jest.mock('../src/hooks/useAllDeliverables', () => ({
  useAllDeliverables: () => ({ deliverables: [], isLoading: true, error: null }),
}));

it('InboxScreen shows LoadingSpinner while loading', () => {
  const { getByTestId } = render(<InboxScreen />);
  // Verify LoadingSpinner is present, not a custom inline spinner
});
```

**Acceptance criteria (binary pass/fail only):**
1. `mobileCpParity.test.tsx` exists and contains 5 test sections (navigation, service contracts, screen render, voice integration, testID coverage)
2. All 5 new screens are validated as registered in their navigation stacks
3. All new service functions are validated as importable and callable
4. Each screen's loading/error/empty state tests pass using shared components
5. Voice integration tests confirm `useSpeechToText`/`useTextToSpeech` are used in applicable screens
6. Navigation test file updated to include new screens
7. Entire parity suite passes: `npx jest __tests__/mobileCpParity.test.tsx` exits 0

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E6-S1-T1 | `src/mobile/__tests__/mobileCpParity.test.tsx` | Import navigation types | All new screen names are keys of correct stack param lists |
| E6-S1-T2 | same | Import service functions | All functions are `typeof 'function'` |
| E6-S1-T3 | same | Render each screen with loading mock | `LoadingSpinner` component present |
| E6-S1-T4 | same | Render each screen with error mock | `ErrorView` component present |
| E6-S1-T5 | same | Render `InboxScreen` with voice mock | `useAgentVoiceOverlay` accessed and `VoiceFAB` rendered |
| E6-S1-T6 | same | Render `ContentAnalyticsScreen` with voice mock | `useAgentVoiceOverlay` accessed and `VoiceFAB` rendered |
| E6-S1-T7 | `src/mobile/__tests__/navigation.test.ts` | Render navigators | New screens navigable from parent stacks |

**Test command:**
```bash
cd src/mobile && npx jest __tests__/mobileCpParity.test.tsx __tests__/navigation.test.ts --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

---

## Full Test Coverage Summary

> CI coverage gate: ≥80% on all new files. The following test commands validate the full iteration.

**Full iteration test command (run after all epics):**
```bash
cd src/mobile && npx jest \
  __tests__/InboxScreen.test.tsx \
  __tests__/useAllDeliverables.test.ts \
  __tests__/UsageBillingScreen.test.tsx \
  __tests__/billingServices.test.ts \
  __tests__/ContentAnalyticsScreen.test.tsx \
  __tests__/contentAnalytics.service.test.ts \
  __tests__/PlatformConnectionsScreen.test.tsx \
  __tests__/platformConnections.service.test.ts \
  __tests__/useAgentVoiceOverlay.test.ts \
  __tests__/AgentOperationsVoice.test.tsx \
  __tests__/mobileCpParity.test.tsx \
  __tests__/navigation.test.ts \
  --coverage \
  --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

**Expected new/modified test files (12 total):**

| File | Covers |
|---|---|
| `__tests__/InboxScreen.test.tsx` | E1 — deliverables screen render + approve/reject + voice |
| `__tests__/useAllDeliverables.test.ts` | E1 — aggregation hook |
| `__tests__/UsageBillingScreen.test.tsx` | E2 — billing screen render + download |
| `__tests__/billingServices.test.ts` | E2 — invoice/receipt services |
| `__tests__/ContentAnalyticsScreen.test.tsx` | E3 — analytics screen render + TTS readout |
| `__tests__/contentAnalytics.service.test.ts` | E3 — analytics service |
| `__tests__/PlatformConnectionsScreen.test.tsx` | E4 — connections screen render + OAuth flow |
| `__tests__/platformConnections.service.test.ts` | E4 — platform connections service |
| `__tests__/useAgentVoiceOverlay.test.ts` | E5 — voice command overlay hook |
| `__tests__/AgentOperationsVoice.test.tsx` | E5 — voice commands on AgentOperationsScreen |
| `__tests__/mobileCpParity.test.tsx` | E6 — navigation, service contract, shared component, voice parity |
| `__tests__/navigation.test.ts` | E6 — updated with new screen reachability |

