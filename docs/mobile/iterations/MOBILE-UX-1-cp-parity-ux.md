# MOBILE-UX-1 — Mobile UX Parity + CP Wiring Iteration Plan

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | MOBILE-UX-1 |
| Feature area | Mobile App UX + CP Frontend Wiring — Make the product worth paying for |
| Created | 2026-03-10 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/mobile/iterations/MOBILE-UX-1-cp-parity-assessment.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 10 |

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

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list based on the tech stack that iteration uses
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2)
- [x] Iteration count minimized for PR-only delivery (default 1-2)
- [x] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [x] No placeholders remain

---

## Vision Intake

### What service/area?
CP FrontEnd + Mobile app (cross-cutting UX fix)

### What user outcome?
After this plan: (1) CP Deliverables page shows REAL agent output from the API instead of placeholder healthcare examples, (2) CP Command Centre dashboard shows live agent status instead of hardcoded "Today's Flight Plan", (3) DMA Wizard stops asking fields already in customer profile, (4) Mobile app has professional vector icons + functional search/filter + a Deliverables screen. The customer can now SEE their agent working and decide to pay.

### What is OUT of scope?
- New backend endpoints (all APIs already exist — this is pure Lane A wiring)
- DMA Wizard step restructuring (only deduplicating fields and showing draft before blind approval)
- Mobile payment integration (Razorpay)
- Mobile push notifications
- New agent types or industries

### Lane?
Lane A — wire existing APIs. No new backend endpoints required.

### Timeline constraint?
2 iterations. Each iteration ≤ 6 stories, ≤ 6 hours agent work.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | CP FrontEnd: Wire Deliverables + Command Centre to real APIs, deduplicate DMA wizard fields | 2 | 5 | 5h | +6h from launch |
| 2 | Mobile: Vector icons, functional search/filter, Deliverables screen | 2 | 5 | 5h | +6h from launch |

**Estimate basis:** FE wiring = 30 min | Data-fetching component = 45 min | Complex refactor = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

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
7. Go away. Come back at: **+6h from launch**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React/TypeScript/Fluent UI engineer + Senior FastAPI/Python engineer (thin proxy patterns only)
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2. Do not touch Iteration 2 content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git checkout main && git pull origin main
   (GitHub cloud agents start on a copilot/* branch — this is normal. Always checkout main first.)
2. Run: git status && git log --oneline -3
   Confirm: clean tree on main. If untracked/modified files exist, stash them.
3. Read the "Agent Execution Rules" section in this plan file.
4. Read the "Iteration 1" section in this plan file.
5. Read nothing else before starting.
6. Execute Epics in this order: E1 → E2
7. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(mobile-ux-1): iteration 1 — CP wiring
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4. Do not touch Iteration 1.
TIME BUDGET: 5h.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(mobile-ux-1): iteration 1 — CP wiring
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** +6h from launch

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/FrontEnd/` | Senior React / TypeScript / Fluent UI engineer |
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `src/mobile/` | Senior React Native / Expo / TypeScript engineer |

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
git checkout main && git pull
git checkout -b feat/mobile-ux-1-it1-e1

git commit --allow-empty -m "chore(mobile-ux-1): start iteration 1"
git push origin feat/mobile-ux-1-it1-e1

gh pr create \
  --base main \
  --head feat/mobile-ux-1-it1-e1 \
  --draft \
  --title "tracking: MOBILE-UX-1 Iteration 1 — in progress" \
  --body "## tracking: MOBILE-UX-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Wire Deliverables page to listHiredAgentDeliverables API
- [ ] [E1-S2] Add deliverable review actions (approve/reject)
- [ ] [E1-S3] Wire Command Centre to live agent summary data
- [ ] [E2-S1] Deduplicate DMA Wizard fields — pull from customer profile
- [ ] [E2-S2] Show draft preview before strategy approval gate

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/mobile-ux-1-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

**Missing iteration HALT rule**: Before writing any code, verify your assigned iteration section exists:
```bash
grep -n "## Iteration N" docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
```
If the section is missing, do not create story cards. HALT.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.
Run the test command listed in the story card — not a generic command.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(mobile-ux-1): [story title]"
git push origin feat/mobile-ux-1-itN-eN

git add docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
git commit -m "docs(mobile-ux-1): mark [story-id] done"
git push origin feat/mobile-ux-1-itN-eN

gh pr comment \
  $(gh pr list --head feat/mobile-ux-1-it1-e1 --json number -q '.[0].number') \
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
Non-zero → fix on same branch, retry. Max 3 attempts. Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/mobile-ux-1-itN-eN
gh pr create \
  --base main \
  --head feat/mobile-ux-1-itN-eN \
  --title "WIP: [story-id] — blocked" \
  --draft \
  --body "Blocked on: [test name]
Error: [exact error message]
Attempted fixes:
1. [what I tried]
2. [what I tried]"
```
Post the draft PR URL. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
```bash
git checkout main && git pull
git checkout -b feat/mobile-ux-1-itN
git merge --no-ff feat/mobile-ux-1-itN-e1 feat/mobile-ux-1-itN-e2
git push origin feat/mobile-ux-1-itN

gh pr create \
  --base main \
  --head feat/mobile-ux-1-itN \
  --title "feat(mobile-ux-1): iteration N — [summary]" \
  --body "## MOBILE-UX-1 Iteration N

### Stories completed
[paste tracking table rows]

### NFR checklist
- [ ] FE: loading + error + empty states on all data-fetching components
- [ ] No env-specific values in code
- [ ] Tests pass"
```
Post PR URL. **HALT — do not start the next iteration.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(mobile-ux-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 7 | Loading + error + empty states on every FE data-fetching component | Silent failures |
| 11 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 13 | CP BackEnd is a thin proxy only — no business logic | Architecture violation |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer sees real deliverables | Wire Deliverables page to listHiredAgentDeliverables API | 🔴 Not Started | — |
| E1-S2 | 1 | Customer sees real deliverables | Add deliverable review actions (approve/reject) | 🔴 Not Started | — |
| E1-S3 | 1 | Customer sees real deliverables | Wire Command Centre to live agent summary data | 🔴 Not Started | — |
| E2-S1 | 1 | DMA Wizard stops wasting time | Deduplicate DMA Wizard fields — pull from customer profile | 🔴 Not Started | — |
| E2-S2 | 1 | DMA Wizard stops wasting time | Show draft preview before strategy approval gate | 🔴 Not Started | — |
| E3-S1 | 2 | Mobile feels professional | Replace emoji tab icons with vector icons | 🔴 Not Started | — |
| E3-S2 | 2 | Mobile feels professional | Wire SearchResults + FilterAgents to API | 🔴 Not Started | — |
| E3-S3 | 2 | Mobile feels professional | Add tab badge counts for pending actions | 🔴 Not Started | — |
| E4-S1 | 2 | Mobile shows agent output | Create mobile Deliverables screen | 🔴 Not Started | — |
| E4-S2 | 2 | Mobile shows agent output | Wire SubscriptionManagement to real billing data | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — CP Frontend: Customer Sees Real Data, Not Placeholders

**Scope:** Wire Deliverables and Command Centre to real APIs; deduplicate DMA wizard identity fields; show strategy content before approval gate.
**Lane:** A — wire existing APIs only. No new backend endpoints.
**⏱ Estimated:** 5h | **Come back:** +6h from launch
**Epics:** E1, E2

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2    (same branch, S2 adds review actions on top of S1's wired page)
   └────► E1-S3    (S3 is Command Centre, same branch, uses same getMyAgentsSummary service)
E2-S1 ──► E2-S2    (same branch, S1 pre-fills fields, S2 shows strategy preview)
```

---

### Epic E1: Customer sees real deliverables and live dashboard

**Branch:** `feat/mobile-ux-1-it1-e1`
**User story:** As a customer, I can see the actual deliverables my hired agents have produced and my real dashboard status, so that I know my agents are working and I'm getting value for money.

---

#### Story E1-S1: Wire Deliverables page to listHiredAgentDeliverables API

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/mobile-ux-1-it1-e1`
**CP BackEnd pattern:** C — existing `/v1/hired-agents/*/deliverables` Plant endpoint. CP FE calls via `gatewayRequestJson` through existing service. No new BE file.

**What to do (self-contained — read this card, then act):**
> `src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx` (47 lines) contains a hardcoded `placeholders` array (lines 4-8) with fake healthcare examples. Replace the entire component with a data-fetching version that:
> 1. Calls `getMyAgentsSummary()` on mount to get all hired instances
> 2. For each instance with a `hired_instance_id`, calls `listHiredAgentDeliverables(hiredInstanceId)`
> 3. Aggregates all deliverables into a single list sorted by `created_at` descending
> 4. Shows loading spinner, error banner, or empty state as appropriate
> 5. Renders each real deliverable in a Card with: title, review_status badge (pending_review=yellow, approved=green, rejected=red), created_at formatted date, and a preview of payload (use the first non-empty value from payload.summary, payload.text_preview, payload.preview, or payload.content — truncated to 120 chars)

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx` | 1–47 | Current placeholder implementation to replace entirely |
| `src/CP/FrontEnd/src/services/hiredAgentDeliverables.service.ts` | 1–60, 155–170 | `Deliverable` type definition (lines 3-20), `listHiredAgentDeliverables` function signature (line 155) |
| `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` | 1–35 | `MyAgentInstanceSummary` type (lines 3-29), `getMyAgentsSummary()` signature (line 30) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx` | modify | Replace entire file content. Keep `Card` import from `@fluentui/react-components`. Add `Badge`, `Spinner` imports. Import `getMyAgentsSummary` and `listHiredAgentDeliverables`, `type Deliverable`. Add useState for deliverables/loading/error. Add useEffect to fetch. Render 3-state UI. |

**Code patterns to copy exactly:**

```typescript
// 3-state data fetching — mandatory pattern for every data-fetching component:
import { useEffect, useState } from 'react'
import { Card, Badge, Spinner } from '@fluentui/react-components'
import { getMyAgentsSummary } from '../../services/myAgentsSummary.service'
import { listHiredAgentDeliverables, type Deliverable } from '../../services/hiredAgentDeliverables.service'

export default function Deliverables() {
  const [deliverables, setDeliverables] = useState<Deliverable[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const summary = await getMyAgentsSummary()
        const instances = (summary?.instances || []).filter(
          (i) => String(i.hired_instance_id || '').trim()
        )
        if (!instances.length) {
          if (!cancelled) setDeliverables([])
          return
        }
        const results = await Promise.allSettled(
          instances.map((i) =>
            listHiredAgentDeliverables(String(i.hired_instance_id))
          )
        )
        const all: Deliverable[] = []
        for (const r of results) {
          if (r.status === 'fulfilled' && r.value?.deliverables) {
            all.push(...r.value.deliverables)
          }
        }
        all.sort((a, b) =>
          (b.created_at || '').localeCompare(a.created_at || '')
        )
        if (!cancelled) setDeliverables(all)
      } catch {
        if (!cancelled) setError('Failed to load deliverables. Please try again.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center' }}><Spinner label="Loading deliverables..." /></div>
  if (error) return <div className="error-banner" style={{ padding: '1rem', color: '#ef4444' }}>{error}</div>
  if (!deliverables.length) return (
    <div className="deliverables-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h1>Deliverables</h1>
      </div>
      <Card style={{ padding: '2rem', textAlign: 'center', opacity: 0.7 }}>
        No deliverables yet. Once your agents start working, their output will appear here.
      </Card>
    </div>
  )
  // ...render real deliverables
}
```

**Acceptance criteria (binary pass/fail only):**
1. Visiting /deliverables when user has hired agents shows deliverable cards with titles from the API, not hardcoded "5 Ways to Manage Diabetes"
2. Each deliverable card shows a `review_status` badge: yellow for `pending_review`, green for `approved`, red for `rejected`
3. When API returns error, "Failed to load deliverables" message appears in DOM
4. When loading, Spinner component with "Loading deliverables..." text is rendered
5. When user has no hired agents, empty state "No deliverables yet" message appears

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/CP/FrontEnd/src/__tests__/Deliverables.test.tsx` | Mock `getMyAgentsSummary` returns 1 instance, mock `listHiredAgentDeliverables` returns 2 deliverables | Both deliverable titles in DOM |
| E1-S1-T2 | same | Mock `getMyAgentsSummary` rejects | Error text "Failed to load" in DOM |
| E1-S1-T3 | same | Mock `getMyAgentsSummary` returns empty instances | Empty state text in DOM |
| E1-S1-T4 | same | Mock returns deliverable with `review_status: 'approved'` | Green badge or "approved" text in DOM |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/__tests__/Deliverables.test.tsx --no-coverage
```

**Commit message:** `feat(mobile-ux-1): wire deliverables page to real API`

**Done signal:** `"E1-S1 done. Changed: Deliverables.tsx, Deliverables.test.tsx. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S2: Add deliverable review actions (approve/reject)

**BLOCKED UNTIL:** E1-S1 committed to `feat/mobile-ux-1-it1-e1`
**Estimated time:** 30 min
**Branch:** `feat/mobile-ux-1-it1-e1` (same branch, continue from E1-S1)
**CP BackEnd pattern:** C — existing `/v1/hired-agents/*/deliverables/*/review` Plant endpoint. Called via `reviewHiredAgentDeliverable` in existing service. No new BE file.

**What to do:**
> In the `Deliverables.tsx` modified by E1-S1, add approve/reject buttons to each deliverable card where `review_status === 'pending_review'`. Import `reviewHiredAgentDeliverable` from the existing `hiredAgentDeliverables.service.ts` (line 160). When clicked, call the service with `{ decision: 'approved' }` or `{ decision: 'rejected' }` and update the local deliverables state to reflect the new review_status. Show a loading state on the button during the API call. For rejected items, show a simple text input for rejection notes before confirming.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx` | 1–80 | Current state after E1-S1 — the deliverables rendering, state variables |
| `src/CP/FrontEnd/src/services/hiredAgentDeliverables.service.ts` | 55–70, 160–170 | `ReviewDeliverableInput` type (decision + notes), `reviewHiredAgentDeliverable` function |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx` | modify | Import `reviewHiredAgentDeliverable`. Add `reviewLoading` state (Record<string, boolean>). For deliverables with `review_status === 'pending_review'`, add Approve button (calls service with `{decision:'approved'}`), Reject button (shows notes input then calls service). On success, update deliverable's review_status in state. |

**Code patterns to copy exactly:**

```typescript
import { reviewHiredAgentDeliverable } from '../../services/hiredAgentDeliverables.service'

// Inside component:
const [reviewLoading, setReviewLoading] = useState<Record<string, boolean>>({})

async function handleReview(deliverableId: string, decision: 'approved' | 'rejected', notes?: string) {
  setReviewLoading((prev) => ({ ...prev, [deliverableId]: true }))
  try {
    await reviewHiredAgentDeliverable(deliverableId, { decision, notes })
    setDeliverables((prev) =>
      prev.map((d) =>
        d.deliverable_id === deliverableId
          ? { ...d, review_status: decision }
          : d
      )
    )
  } catch {
    // Show inline error — do not crash
  } finally {
    setReviewLoading((prev) => ({ ...prev, [deliverableId]: false }))
  }
}
```

**Acceptance criteria:**
1. Deliverables with `review_status === 'pending_review'` show Approve and Reject buttons
2. Deliverables with `review_status === 'approved'` or `'rejected'` do NOT show action buttons
3. Clicking Approve calls `reviewHiredAgentDeliverable` with `{decision: 'approved'}` and updates the badge to green
4. Clicking Reject shows a notes input; submitting calls service with `{decision: 'rejected', notes}` and updates badge to red

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/CP/FrontEnd/src/__tests__/Deliverables.test.tsx` | Render with `pending_review` deliverable | Approve + Reject buttons visible |
| E1-S2-T2 | same | Render with `approved` deliverable | No action buttons in DOM |
| E1-S2-T3 | same | Click Approve, mock `reviewHiredAgentDeliverable` resolves | Badge changes to approved/green |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/__tests__/Deliverables.test.tsx --no-coverage
```

**Commit message:** `feat(mobile-ux-1): add deliverable review actions`

**Done signal:** `"E1-S2 done. Changed: Deliverables.tsx, Deliverables.test.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E1-S3: Wire Command Centre to live agent summary data

**BLOCKED UNTIL:** E1-S1 committed (shares service import knowledge, but technically independent — same branch for simplicity)
**Estimated time:** 45 min
**Branch:** `feat/mobile-ux-1-it1-e1`
**CP BackEnd pattern:** C — existing `/cp/my-agents-summary` called via `getMyAgentsSummary`. No new BE file.

**What to do:**
> `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx` (104 lines) has hardcoded `readinessCards` array (lines 10-14) with static emoji values, hardcoded `priorities` array (lines 16-20), and hardcoded numbers (lines 75-79: "Pinned alerts: 0", "Billing area: 1", "Suggested actions: 3"). Replace with real data from `getMyAgentsSummary()`. Show: (1) total hired agents count, (2) agents in trial count, (3) agents needing setup count, (4) configured agents count. Replace priorities with context-aware suggestions based on actual agent state. Replace workspace overview with real counts. Add loading/error/empty states.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx` | 1–104 | Full file — hardcoded arrays, readinessCards, priorities, workspace overview numbers |
| `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` | 1–35 | `MyAgentInstanceSummary` type with `configured`, `goals_completed`, `trial_status`, `status` fields |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx` | modify | Import `getMyAgentsSummary`, `type MyAgentInstanceSummary`. Add `useState`/`useEffect`. Replace hardcoded `readinessCards` with computed values from API. Replace `priorities` with dynamic suggestions. Replace workspace overview numbers with real counts. Add Spinner for loading, error banner for errors. |

**Code patterns to copy exactly:**

```typescript
import { useEffect, useState } from 'react'
import { getMyAgentsSummary, type MyAgentInstanceSummary } from '../../services/myAgentsSummary.service'

// Inside component — compute dashboard stats from real data:
const [instances, setInstances] = useState<MyAgentInstanceSummary[]>([])
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  getMyAgentsSummary()
    .then((resp) => setInstances(resp?.instances || []))
    .catch(() => setError('Failed to load dashboard data.'))
    .finally(() => setLoading(false))
}, [])

const totalAgents = instances.length
const inTrial = instances.filter((i) => i.trial_status === 'active').length
const needsSetup = instances.filter((i) => !i.configured || !i.goals_completed).length
const configured = instances.filter((i) => i.configured).length

const readinessCards = [
  { label: 'Total agents', sublabel: 'Hired agents in your workspace', value: String(totalAgents) },
  { label: 'In trial', sublabel: 'Agents in their 7-day trial period', value: String(inTrial) },
  { label: 'Need setup', sublabel: 'Agents waiting for configuration', value: String(needsSetup) },
  { label: 'Configured', sublabel: 'Agents ready and producing output', value: String(configured) },
]

// Dynamic priorities based on actual state:
const priorities: string[] = []
if (needsSetup > 0) priorities.push(`${needsSetup} agent${needsSetup > 1 ? 's' : ''} need${needsSetup === 1 ? 's' : ''} setup — open My Agents to configure.`)
if (inTrial > 0) priorities.push(`${inTrial} agent${inTrial > 1 ? 's' : ''} in trial — review output before trial ends.`)
if (totalAgents === 0) priorities.push('Hire your first agent from Discover to get started.')
if (priorities.length === 0) priorities.push('All agents are set up and running. Check Deliverables for latest output.')
```

**Acceptance criteria:**
1. Command Centre shows "Total agents" card with the real count from API (not hardcoded ⏳)
2. "Need setup" card shows count of agents where `configured === false` or `goals_completed === false`
3. Priorities section shows context-aware text like "2 agents need setup" instead of static text
4. When API errors, "Failed to load dashboard data" text appears
5. When loading, Spinner component is rendered
6. Workspace overview section shows real counts instead of hardcoded 0/1/3

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S3-T1 | `src/CP/FrontEnd/src/__tests__/CommandCentre.test.tsx` | Mock `getMyAgentsSummary` returns 3 instances (1 trial, 1 needs setup, 1 configured) | "3" in total agents card, "1" in trial card, "1" in needs setup card |
| E1-S3-T2 | same | Mock rejects | Error text in DOM |
| E1-S3-T3 | same | Mock returns 0 instances | "Hire your first agent" text in priorities |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/__tests__/CommandCentre.test.tsx --no-coverage
```

**Commit message:** `feat(mobile-ux-1): wire command centre to live agent data`

**Done signal:** `"E1-S3 done. Changed: CommandCentre.tsx, CommandCentre.test.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

### Epic E2: DMA Wizard stops wasting customer time

**Branch:** `feat/mobile-ux-1-it1-e2`
**User story:** As a customer, I don't have to re-enter my business name, location, and timezone in the DMA wizard because the agent already knows them from my profile, and I can see what strategy the agent produced before I'm asked to approve it.

---

#### Story E2-S1: Pre-fill DMA Wizard identity fields from customer profile

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/mobile-ux-1-it1-e2`
**CP BackEnd pattern:** C — existing `/cp/profile` called via `getProfile()` in `profile.service.ts`. No new BE file.

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` initializes `brandName`, `location`, `timezone` as empty strings (lines 315, 317, 319). When the activation workspace data loads (lines 534-536), it populates these from `nextActivation?.workspace.*`. But on FIRST activation (when workspace is empty/new), these remain blank and the user must type everything from scratch. Fix: after loading the activation workspace, if `brandName` is still empty, fall back to `getProfile()` and use `business_name` as the default. The profile service already exists at `src/CP/FrontEnd/src/services/profile.service.ts` with `getProfile(): Promise<ProfileData>` returning `business_name` and `industry` fields.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 310–340, 520–555 | State variables (lines 315-319), loadState function that populates from workspace (lines 534-536) |
| `src/CP/FrontEnd/src/services/profile.service.ts` | 1–36 | `ProfileData` type with `business_name`, `industry` fields; `getProfile()` function |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Import `getProfile` from `../../services/profile.service`. In the `loadState` async function, AFTER the existing `setBrandName(normalizeText(...))` call at line 534, add a fallback: if `normalizeText(nextActivation?.workspace.brand_name)` is empty, call `getProfile()` and use `response.business_name` as the default for `setBrandName`. This is a single conditional block — no restructuring. |

**Code patterns to copy exactly:**

```typescript
// In loadState function, after line 536 (setTimezone(...)):
// Fallback: pre-fill from customer profile if activation workspace is empty
const wsName = normalizeText(nextActivation?.workspace.brand_name)
if (!wsName) {
  try {
    const profile = await getProfile()
    if (profile.business_name && !normalizeText(nextActivation?.workspace.brand_name)) {
      setBrandName(profile.business_name)
    }
  } catch {
    // Profile fallback is best-effort — don't block wizard
  }
}
```

**Acceptance criteria:**
1. When DMA wizard opens for a NEW activation (empty workspace), `brandName` field is pre-filled with `business_name` from customer profile
2. When DMA wizard opens for an EXISTING activation with workspace data, the workspace value takes priority over profile
3. If `getProfile()` fails, wizard continues without error — fields remain empty for manual entry
4. No new API call is made if the workspace already has a `brand_name` value

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Mock activation workspace with empty `brand_name`, mock `getProfile` returns `{business_name: 'TestCo'}` | Input with `aria-label="Brand name"` has value "TestCo" |
| E2-S1-T2 | same | Mock activation workspace with `brand_name: 'ExistingBrand'` | Input value is "ExistingBrand" (not profile fallback) |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx --no-coverage
```

**Commit message:** `feat(mobile-ux-1): pre-fill DMA wizard fields from customer profile`

**Done signal:** `"E2-S1 done. Changed: DigitalMarketingActivationWizard.tsx, test file. Tests: T1 ✅ T2 ✅"`

---

#### Story E2-S2: Show strategy content before approval gate

**BLOCKED UNTIL:** E2-S1 committed to `feat/mobile-ux-1-it1-e2`
**Estimated time:** 45 min
**Branch:** `feat/mobile-ux-1-it1-e2`
**CP BackEnd pattern:** N/A — pure frontend display change, no API calls needed

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` line 951 shows a disabled message "Approve the master theme strategy below before generating a YouTube draft" when `isThemeApproved` is false (line 468: `const isThemeApproved = strategyWorkshop.status === 'approved'`). The customer complaint is BLIND APPROVAL — they can't see what they're approving. Fix: in the step where the user sees this gate message, render a read-only preview of the `strategyWorkshop` content (master theme, derived themes, summary) ABOVE the approval message. The `strategyWorkshop` state variable (line 325) already contains `master_theme`, `derived_themes[]`, and `summary` fields. Show this as a styled read-only card so the customer can see exactly what they're approving.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 325–327, 460–475, 940–960 | `strategyWorkshop` state (line 325), `isThemeApproved` derivation (line 468), gate message rendering (line 951) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Around line 951, BEFORE the "Approve the master theme strategy" disabled message, add a Card block that renders: (1) `masterTheme` as a heading, (2) `derivedThemes` as a bulleted list showing each theme's `label` and `description`, (3) `strategySummary` object's key fields. Only show this preview if `masterTheme` or `derivedThemes.length > 0`. Wrap in a Card with `background: 'var(--colorNeutralBackground3)'` and `padding: '1rem'`. |

**Code patterns to copy exactly:**

```typescript
// Strategy preview card — insert before the approval gate message:
{(masterTheme || derivedThemes.length > 0) && !isThemeApproved && (
  <Card style={{ padding: '1rem', marginBottom: '1rem', background: 'var(--colorNeutralBackground3)' }}>
    <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em', opacity: 0.7, marginBottom: '0.5rem' }}>
      Strategy Preview — review before approving
    </div>
    {masterTheme && (
      <div style={{ fontWeight: 600, fontSize: '1.05rem', marginBottom: '0.5rem' }}>
        Master Theme: {masterTheme}
      </div>
    )}
    {derivedThemes.length > 0 && (
      <div style={{ marginBottom: '0.5rem' }}>
        <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>Derived Themes:</div>
        <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
          {derivedThemes.map((dt, i) => (
            <li key={i} style={{ marginBottom: '0.25rem' }}>
              <strong>{dt.label}</strong>{dt.description ? ` — ${dt.description}` : ''}
            </li>
          ))}
        </ul>
      </div>
    )}
  </Card>
)}
```

**Acceptance criteria:**
1. When `isThemeApproved` is `false` and `masterTheme` has a value, a "Strategy Preview" card appears above the approval gate message
2. The preview card shows the master theme text and a list of derived themes with labels
3. When `masterTheme` is empty and `derivedThemes` is empty, no preview card is shown (just the existing gate message)
4. The preview card has a "Strategy Preview — review before approving" label

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Mock strategyWorkshop with `status: 'pending'`, master_theme = "Growth content" | Text "Strategy Preview" and "Growth content" in DOM |
| E2-S2-T2 | same | Mock strategyWorkshop with `status: 'approved'` | "Strategy Preview" NOT in DOM (already approved) |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx --no-coverage
```

**Commit message:** `feat(mobile-ux-1): show strategy preview before approval gate`

**Done signal:** `"E2-S2 done. Changed: DigitalMarketingActivationWizard.tsx, test file. Tests: T1 ✅ T2 ✅"`

---

## Iteration 2 — Mobile: Professional Polish + Functional Search

**Scope:** Replace emoji tab icons with vector icons, add tab badge counts, wire SearchResults to API, add Apply button to FilterAgents, add pull-to-refresh.
**Lane:** A — wire existing hooks/APIs only. No new backend endpoints.
**⏱ Estimated:** 5h | **Come back:** +6h from launch
**Epics:** E3, E4

### Dependency Map (Iteration 2)

```
E3-S1 ──► E3-S2    (same branch — S1 changes icon rendering, S2 adds badges on same Tab.Screen components)
   └────► E3-S3    (same branch — FilterAgents apply button, same navigation stack)
E4-S1              (independent branch — SearchResults wiring)
E4-S2              (independent branch — pull-to-refresh, but keep on same E4 branch for simplicity)
```

---

### Epic E3: Mobile navigation feels professional

**Branch:** `feat/mobile-ux-1-it2-e3`
**User story:** As a mobile user, I see professional vector icons in the bottom navigation (not emojis), I can see badge counts for pending actions, and I can apply filters and navigate back with results.

---

#### Story E3-S1: Replace emoji tab icons with Ionicons

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/mobile-ux-1-it2-e3`
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> `src/mobile/src/navigation/MainNavigator.tsx` uses emoji characters (🏠🔍🤖👤) inside `<Text>` components for tab bar icons (lines 165, 186, 198, 210). Replace these with proper `Ionicons` from `@expo/vector-icons` (already installed as an Expo transitive dependency — `node_modules/@expo/vector-icons/Ionicons.js` exists). For each tab, replace the `<View><Text>{emoji}</Text></View>` block with `<Ionicons name={iconName} size={size} color={color} />`. Icon mapping: HomeTab → `home`, DiscoverTab → `search`, MyAgentsTab → `grid` (operations), ProfileTab → `person`. Remove the wrapping `<View>` and `<Text>` — just return the Ionicons component directly.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/navigation/MainNavigator.tsx` | 140–215 | Four `Tab.Screen` definitions with emoji icon rendering blocks at lines 158-166 (🏠), 178-187 (🔍), 190-199 (🤖), 202-211 (👤) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/navigation/MainNavigator.tsx` | modify | Add import: `import { Ionicons } from '@expo/vector-icons'` at top. For each of the 4 `tabBarIcon` callbacks, replace the `<View>...<Text>{emoji}</Text></View>` block with a single `<Ionicons name={name} size={size} color={color} />`. Icon names: HomeTab→`"home"`, DiscoverTab→`"search"`, MyAgentsTab→`"grid"`, ProfileTab→`"person"`. |

**Code patterns to copy exactly:**

```typescript
import { Ionicons } from '@expo/vector-icons';

// For each Tab.Screen, the tabBarIcon prop becomes simply:
tabBarIcon: ({ color, size }) => (
  <Ionicons name="home" size={size} color={color} />
),
// Replace "home" with the correct icon name for each tab:
// HomeTab: "home"
// DiscoverTab: "search"
// MyAgentsTab: "grid"
// ProfileTab: "person"
```

**Acceptance criteria (binary pass/fail only):**
1. All 4 bottom tabs show Ionicons vector icons, not emoji characters
2. Icons use the tab's `color` prop (cyan when active, gray when inactive)
3. No `<Text>` elements with emoji characters remain in the tab bar
4. App compiles without errors: `cd src/mobile && npx expo export --platform web` exits 0

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/mobile/src/navigation/__tests__/MainNavigator.test.tsx` | Render MainNavigator in test | No emoji strings (🏠🔍🤖👤) in rendered output |
| E3-S1-T2 | same | Render MainNavigator | Ionicons components present in tree (mock @expo/vector-icons if needed) |

**Test command:**
```bash
cd src/mobile && npx jest src/navigation/__tests__/MainNavigator.test.tsx --no-coverage --forceExit
```

**Commit message:** `feat(mobile-ux-1): replace emoji tab icons with Ionicons`

**Done signal:** `"E3-S1 done. Changed: MainNavigator.tsx, MainNavigator.test.tsx. Tests: T1 ✅ T2 ✅"`

---

#### Story E3-S2: Add tab badge counts for pending actions

**BLOCKED UNTIL:** E3-S1 committed to `feat/mobile-ux-1-it2-e3`
**Estimated time:** 45 min
**Branch:** `feat/mobile-ux-1-it2-e3` (same branch)
**CP BackEnd pattern:** N/A

**What to do:**
> In `src/mobile/src/navigation/MainNavigator.tsx`, add badge counts on the Ops tab (MyAgentsTab) to show how many agents need setup. Use the existing `useAgentsNeedingSetup()` hook from `src/mobile/src/hooks/useHiredAgents.ts` (line 200). In the `MainNavigator` component (which wraps the Tab.Navigator), call `useAgentsNeedingSetup()` and pass the count to the `tabBarBadge` prop on the MyAgentsTab `Tab.Screen`. React Navigation's `tabBarBadge` prop natively supports this — pass a number and it shows a red badge. Only show the badge if count > 0 (pass `undefined` when 0).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/navigation/MainNavigator.tsx` | 130–145, 190–200 | MainNavigator component function, MyAgentsTab Tab.Screen definition |
| `src/mobile/src/hooks/useHiredAgents.ts` | 195–215 | `useAgentsNeedingSetup()` hook — returns `UseQueryResult<MyAgentInstanceSummary[], Error>` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/navigation/MainNavigator.tsx` | modify | Import `useAgentsNeedingSetup` from hooks. Call it inside `MainNavigator` component. On the MyAgentsTab `Tab.Screen`, add `tabBarBadge` prop: `tabBarBadge={needsSetupCount > 0 ? needsSetupCount : undefined}`. Also add `tabBarBadgeStyle` with small font and neon-red background. |

**Code patterns to copy exactly:**

```typescript
import { useAgentsNeedingSetup } from '../hooks/useHiredAgents';

// Inside MainNavigator component, before the return:
const { data: agentsNeedingSetup } = useAgentsNeedingSetup();
const needsSetupCount = agentsNeedingSetup?.length ?? 0;

// On the MyAgentsTab Tab.Screen options:
tabBarBadge: needsSetupCount > 0 ? needsSetupCount : undefined,
tabBarBadgeStyle: { backgroundColor: '#ef4444', fontSize: 10, fontWeight: '700' },
```

**Acceptance criteria:**
1. When there are agents needing setup, Ops tab shows a red badge with the count
2. When all agents are configured, no badge is shown (badge is `undefined`)
3. Badge updates when agent setup status changes (on refocus via React Query refetchOnWindowFocus)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/mobile/src/navigation/__tests__/MainNavigator.test.tsx` | Mock `useAgentsNeedingSetup` returns 2 items | Badge with "2" visible |
| E3-S2-T2 | same | Mock `useAgentsNeedingSetup` returns empty array | No badge in DOM |

**Test command:**
```bash
cd src/mobile && npx jest src/navigation/__tests__/MainNavigator.test.tsx --no-coverage --forceExit
```

**Commit message:** `feat(mobile-ux-1): add tab badge counts for pending actions`

**Done signal:** `"E3-S2 done. Changed: MainNavigator.tsx, test. Tests: T1 ✅ T2 ✅"`

---

#### Story E3-S3: Add Apply button to FilterAgentsScreen with navigation back

**BLOCKED UNTIL:** E3-S1 committed (same branch, but independent of S2)
**Estimated time:** 30 min
**Branch:** `feat/mobile-ux-1-it2-e3`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/mobile/src/screens/discover/FilterAgentsScreen.tsx` (57 lines) has industry, rating, and price inputs but NO apply button (line 41: `{/* TODO: Add filter action button */}`). Add a "Apply Filters" `TouchableOpacity` button below the inputs. When pressed, navigate back to the Discover screen with the selected filter values. Use `navigation.navigate('Discover', { industry: selectedIndustry, minRating, maxPrice })` to pass filter state back. The DiscoverScreen already reads filter state from its own local state, so the approach is: navigate back and let DiscoverScreen pick up the params. Alternatively, use `navigation.goBack()` after setting params on the parent route.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/screens/discover/FilterAgentsScreen.tsx` | 1–57 | Full file — industry picker, rating/price inputs, TODO at line 41, no submit button |
| `src/mobile/src/navigation/types.ts` | 80–95 | `DiscoverStackParamList` type — `FilterAgents` params definition, `Discover` params (check if it accepts filter params) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/discover/FilterAgentsScreen.tsx` | modify | Add `useNavigation` import. Replace `{/* TODO: Add filter action button */}` with a styled `TouchableOpacity` button labeled "Apply Filters". On press, call `navigation.navigate('Discover', { industry: selectedIndustry, minRating, maxPrice })`. Style the button with neon cyan background (#00f2fe), dark text, border radius 12, padding 14. |
| `src/mobile/src/navigation/types.ts` | modify | If `Discover` route params don't include filter fields, add them as optional: `{ industry?: string; minRating?: number; maxPrice?: number }` |

**Code patterns to copy exactly:**

```typescript
import { TouchableOpacity } from 'react-native';

// Replace the TODO comment with:
<TouchableOpacity
  style={{
    backgroundColor: '#00f2fe',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: spacing.lg,
    width: '100%',
  }}
  onPress={() => navigation.navigate('Discover', {
    industry: selectedIndustry || undefined,
    minRating: minRating || undefined,
    maxPrice: maxPrice || undefined,
  })}
>
  <Text style={{ color: '#0a0a0a', fontWeight: '700', fontSize: 16 }}>Apply Filters</Text>
</TouchableOpacity>
```

**Acceptance criteria:**
1. FilterAgents screen shows an "Apply Filters" button below the price input
2. Pressing Apply navigates back to Discover screen
3. The button has neon cyan (#00f2fe) background with dark text
4. No `TODO` comment remains in the file

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S3-T1 | `src/mobile/src/screens/discover/__tests__/FilterAgentsScreen.test.tsx` | Render FilterAgentsScreen | "Apply Filters" button text in DOM |
| E3-S3-T2 | same | Press Apply button | `navigation.navigate` called with filter params |

**Test command:**
```bash
cd src/mobile && npx jest src/screens/discover/__tests__/FilterAgentsScreen.test.tsx --no-coverage --forceExit
```

**Commit message:** `feat(mobile-ux-1): add apply button to filter agents screen`

**Done signal:** `"E3-S3 done. Changed: FilterAgentsScreen.tsx, types.ts, test. Tests: T1 ✅ T2 ✅"`

---

### Epic E4: Mobile search shows real results

**Branch:** `feat/mobile-ux-1-it2-e4`
**User story:** As a mobile user, when I search for agents from the SearchResults screen, I see real agent cards from the API instead of a TODO placeholder.

---

#### Story E4-S1: Wire SearchResultsScreen to useSearchAgents hook

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/mobile-ux-1-it2-e4`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/mobile/src/screens/discover/SearchResultsScreen.tsx` (24 lines) receives `query` from route params (line 5) but renders only a TODO placeholder (line 18). Replace the placeholder with a real implementation: use the existing `useSearchAgents(query)` hook from `src/mobile/src/hooks/useAgents.ts` (line 45) to fetch matching agents. Render results as a `FlatList` of `AgentCard` components (from `src/mobile/src/components/AgentCard.tsx`). Show loading spinner, error message, and "No agents found" empty state.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/screens/discover/SearchResultsScreen.tsx` | 1–24 | Full file — route.params.query destructuring, TODO placeholder |
| `src/mobile/src/hooks/useAgents.ts` | 45–60 | `useSearchAgents(query, params?)` hook — returns `UseQueryResult<Agent[], Error>` |
| `src/mobile/src/components/AgentCard.tsx` | 1–30 | Import path and `AgentCardProps` interface (needs `agent: Agent` prop) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/discover/SearchResultsScreen.tsx` | modify | Replace entire file content. Import `useSearchAgents` from hooks, `AgentCard` from components, `FlatList`, `ActivityIndicator`. Call `useSearchAgents(query)`. Render loading → error → empty → FlatList of AgentCard. On AgentCard press, navigate to `AgentDetail`. |

**Code patterns to copy exactly:**

```typescript
import React from 'react';
import { View, Text, FlatList, ActivityIndicator, SafeAreaView } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useSearchAgents } from '../../hooks/useAgents';
import AgentCard from '../../components/AgentCard';
import type { DiscoverStackScreenProps } from '../../navigation/types';

const SearchResultsScreen: React.FC<DiscoverStackScreenProps<'SearchResults'>> = ({ route, navigation }) => {
  const { colors, spacing, typography } = useTheme();
  const { query } = route.params;
  const { data: agents, isLoading, error } = useSearchAgents(query);

  if (isLoading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.black, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={colors.neonCyan} />
        <Text style={{ color: colors.textSecondary, marginTop: spacing.md }}>Searching for "{query}"...</Text>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.black, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: '#ef4444' }}>Failed to search agents. Please try again.</Text>
      </SafeAreaView>
    );
  }

  if (!agents?.length) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.black, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: colors.textSecondary }}>No agents found for "{query}"</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <View style={{ padding: spacing.md }}>
        <Text style={[typography.textVariants.body, { color: colors.white, marginBottom: spacing.md }]}>
          {agents.length} result{agents.length !== 1 ? 's' : ''} for "{query}"
        </Text>
      </View>
      <FlatList
        data={agents}
        keyExtractor={(item) => item.id || item.agent_id}
        renderItem={({ item }) => (
          <AgentCard
            agent={item}
            // onPress={() => navigation.navigate('AgentDetail', { agentId: item.agent_id })}
          />
        )}
        contentContainerStyle={{ paddingHorizontal: spacing.md, paddingBottom: spacing.xl }}
      />
    </SafeAreaView>
  );
};

export default SearchResultsScreen;
```

**Acceptance criteria:**
1. SearchResultsScreen shows agent cards from `useSearchAgents(query)` — not a TODO placeholder
2. Loading state shows ActivityIndicator with "Searching..." text
3. Error state shows "Failed to search agents" text
4. Empty results show "No agents found for [query]" text
5. Results count is displayed above the list

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/mobile/src/screens/discover/__tests__/SearchResultsScreen.test.tsx` | Mock `useSearchAgents` returns 2 agents | Both agent cards rendered |
| E4-S1-T2 | same | Mock `useSearchAgents` returns empty array | "No agents found" text |
| E4-S1-T3 | same | Mock `useSearchAgents` isLoading=true | "Searching" text in DOM |

**Test command:**
```bash
cd src/mobile && npx jest src/screens/discover/__tests__/SearchResultsScreen.test.tsx --no-coverage --forceExit
```

**Commit message:** `feat(mobile-ux-1): wire search results to API`

**Done signal:** `"E4-S1 done. Changed: SearchResultsScreen.tsx, test. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E4-S2: Add pull-to-refresh on DiscoverScreen and MyAgentsScreen

**BLOCKED UNTIL:** none (independent of E4-S1, but same branch for simplicity)
**Estimated time:** 30 min
**Branch:** `feat/mobile-ux-1-it2-e4`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/mobile/src/screens/discover/DiscoverScreen.tsx` and `src/mobile/src/screens/agents/MyAgentsScreen.tsx` fetch data via React Query hooks (`useAgents` and `useHiredAgents`) which expose `refetch` and `isFetching` properties. Add a `RefreshControl` to the main `ScrollView` or `FlatList` in each screen. This is the standard React Native pattern for pull-to-refresh: pass `refreshControl={<RefreshControl refreshing={isFetching} onRefresh={refetch} />}` to the scrollable container. Use the neon cyan color (#00f2fe) for the refresh indicator.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/mobile/src/screens/discover/DiscoverScreen.tsx` | 30–70, 210–260 | Hook call (useAgents) with refetch/isFetching, FlatList or ScrollView rendering |
| `src/mobile/src/screens/agents/MyAgentsScreen.tsx` | 1–50, scrollable container | Hook call (useHiredAgents) with refetch/isFetching, main scrollable component |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/mobile/src/screens/discover/DiscoverScreen.tsx` | modify | Import `RefreshControl` from `react-native`. Add `refreshControl` prop to the main FlatList or ScrollView. |
| `src/mobile/src/screens/agents/MyAgentsScreen.tsx` | modify | Import `RefreshControl` from `react-native`. Add `refreshControl` prop to the main scrollable container. |

**Code patterns to copy exactly:**

```typescript
import { RefreshControl } from 'react-native';

// On the FlatList or ScrollView:
refreshControl={
  <RefreshControl
    refreshing={isFetching && !isLoading}
    onRefresh={refetch}
    tintColor="#00f2fe"
    colors={['#00f2fe']}
  />
}
```

**Acceptance criteria:**
1. Pulling down on DiscoverScreen triggers a data refresh (new API call)
2. Pulling down on MyAgentsScreen triggers a data refresh
3. Refresh spinner uses neon cyan color (#00f2fe)
4. Spinner shows during refetch, disappears when data arrives

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S2-T1 | `src/mobile/src/screens/discover/__tests__/DiscoverScreen.test.tsx` | Render DiscoverScreen | RefreshControl component present in tree |
| E4-S2-T2 | `src/mobile/src/screens/agents/__tests__/MyAgentsScreen.test.tsx` | Render MyAgentsScreen | RefreshControl component present in tree |

**Test command:**
```bash
cd src/mobile && npx jest src/screens/discover/__tests__/DiscoverScreen.test.tsx src/screens/agents/__tests__/MyAgentsScreen.test.tsx --no-coverage --forceExit
```

**Commit message:** `feat(mobile-ux-1): add pull-to-refresh to discover and my agents`

**Done signal:** `"E4-S2 done. Changed: DiscoverScreen.tsx, MyAgentsScreen.tsx, tests. Tests: T1 ✅ T2 ✅"`
