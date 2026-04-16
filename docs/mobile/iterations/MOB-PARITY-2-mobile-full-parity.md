# MOB-PARITY-2 — Mobile Full CP Feature Parity

> **Objective alignment:** DMA value + DMA enablement — closes every gap between the CP web
> app and the mobile app, ensuring customers can run their full WAOOAW workflow — browse,
> hire, approve, manage, and deliver — entirely from mobile.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | MOB-PARITY-2 |
| Feature area | Mobile App — Full CP Feature Parity |
| Created | 2026-04-16 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §23 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 9 |
| Total stories | 14 |

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

## PM Review Checklist

- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] No CP BackEnd changes required — all calls go through Plant Gateway or CP Backend proxy (existing routes)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: tests embedded per story before advancing
- [x] No placeholders remain

---

## Drift Prevention Contract

| Drift vector | Prevention mechanism | Detection |
|---|---|---|
| API contract mismatch | Services use exact CP endpoint paths documented per story | TypeScript strict; Jest mocks use same response shape as CP/Plant Gateway |
| Screen parity regression | Each story references the CP page it mirrors | Acceptance criteria are pass/fail against CP feature list |
| Reject-reason missing | `ContentDraftApprovalCard` gains optional reject-reason text field | Jest tests verify onRejectWithReason callback fires with string |
| Home verbosity regression | Home redesign locked to non-scroll single view | Snapshot test confirms no `ScrollView` at root |
| Scheduled post visibility gap | New `ScheduledPostsSection` component in AgentOperations | Jest tests verify queued/published/failed status chips render |
| Navigation type drift | Navigation types updated atomically with new screens | TypeScript strict; TS compiler catches missing route additions |
| Coverage regression | ≥80% on all new/modified files | `jest --coverage --coverageThreshold` in test command |

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Home redesign (no-scroll dashboard) + Discover completeness (trial button, search quality) | E1, E2 | 4 | 4h | 2026-04-16 22:00 UTC |
| 2 | Hire Wizard receipt flow + My Agents / Ops completeness (pause/resume, scheduled posts section) | E3, E4 | 5 | 5h | 2026-04-17 06:00 UTC |
| 3 | Content Approval (reject-with-reason, scheduled posts list page) + Deliverables/Inbox completeness | E5, E6, E7, E8, E9 | 5 | 5h | 2026-04-17 12:00 UTC |

**Estimate basis:** FE screen = 45 min | Hook/service = 30 min | Test suite = 20 min | PR = 10 min. Add 20% buffer.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task, select **platform-engineer** agent
4. Paste the block below verbatim
5. Come back at: **2026-04-16 22:00 UTC**

**Iteration 1 agent task:**

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer + Senior mobile UX engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-PARITY-2-mobile-full-parity.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2 (Stories E1-S1, E1-S2, E2-S1, E2-S2).

FAIL-FAST VALIDATION GATE (before any code):
1. Verify plan file is readable and "## Iteration 1" section exists.
2. Verify execution surface allows writes on the task branch.
3. If either fails: post "Blocked at validation gate: [reason]" and HALT.

EXECUTION ORDER: E1-S1 → E1-S2 → E2-S1 → E2-S2
After each story: tests written, committed, pushed.
After all stories: open PR titled "feat(MOB-PARITY-2): iteration 1 — home + discover" to main. Post PR URL. HALT.
```

### Iteration 2

**Steps to launch:** (AFTER Iteration 1 PR merged to main)

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer + Senior mobile UX engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-PARITY-2-mobile-full-parity.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4 (Stories E3-S1, E4-S1, E4-S2, E4-S3, E4-S4).

FAIL-FAST VALIDATION GATE (before any code):
1. Verify plan file is readable and "## Iteration 2" section exists.
2. Verify execution surface allows writes on the task branch.
3. If either fails: post "Blocked at validation gate: [reason]" and HALT.

EXECUTION ORDER: E3-S1 → E4-S1 → E4-S2 → E4-S3 → E4-S4
After each story: tests written, committed, pushed.
After all stories: open PR titled "feat(MOB-PARITY-2): iteration 2 — hire + ops" to main. Post PR URL. HALT.
```

### Iteration 3

**Steps to launch:** (AFTER Iteration 2 PR merged to main)

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer + Senior mobile UX engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-PARITY-2-mobile-full-parity.md
YOUR SCOPE: Iteration 3 only — Epics E5–E9 (Stories E5-S1, E6-S1, E7-S1, E8-S1, E9-S1).

FAIL-FAST VALIDATION GATE (before any code):
1. Verify plan file is readable and "## Iteration 3" section exists.
2. Verify execution surface allows writes on the task branch.
3. If either fails: post "Blocked at validation gate: [reason]" and HALT.

EXECUTION ORDER: E5-S1 → E6-S1 → E7-S1 → E8-S1 → E9-S1
After each story: tests written, committed, pushed.
After all stories: open PR titled "feat(MOB-PARITY-2): iteration 3 — approvals + deliverables" to main. Post PR URL. HALT.
```

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -2 — Fail-fast validation gate
Before reading story cards or making any code changes:
- Verify the plan file is readable and your assigned iteration section exists.
- Verify the execution surface lets you save changes on the task branch.
- If any check fails: post `Blocked at validation gate: [exact reason]` and HALT.

### Rule -1 — Activate Expert Personas
Activate: **Senior React Native / Expo / TypeScript engineer** + **Senior mobile UX engineer**.
Open every epic with: *"Acting as a [persona], I will [what] by [approach]."*

| Technology area | Expert persona |
|---|---|
| `src/mobile/src/screens/` | Senior React Native / Expo / TypeScript engineer |
| `src/mobile/src/services/` | Senior API integration / TypeScript engineer |
| `src/mobile/src/components/` | Senior mobile UX / accessibility engineer |
| `src/mobile/__tests__/` | Senior Jest / React Native Testing Library engineer |

### Rule 0 — Branch discipline
- Full iteration = one branch + one PR.
- Branch name: `feat/MOB-PARITY-2-it{N}-{short-desc}` (e.g. `feat/MOB-PARITY-2-it1-home-discover`).
- PR always `--base main`.

### Rule 1 — Scope lock
Implement exactly the acceptance criteria in each story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
**File scope**: only create or modify files listed in the story's "Files to create / modify" table.

### Rule 2 — Tests before the next story
Write every test in the story's test table before advancing.
Run `docker-compose -f docker-compose.test.yml run --rm mobile-test` or equivalent.
If shell is unavailable, add tests anyway and note deferral.

### Rule 3 — Save after every story
Commit + push after each story is complete:
```bash
git add -A && git commit -m "feat(MOB-PARITY-2): [story-id] — [story title]" && git push origin HEAD
```

### Rule 4 — Validate after every epic
Run relevant tests. Record result. Add `**Epic complete ✅**` under the epic heading.

### Rule 5 — STUCK PROTOCOL (3 failures = stop)
- Mark blocked story as `🚫 Blocked` in Tracking Table.
- Open draft PR titled `WIP: [story-id] — blocked` with exact blocker, error, 2 attempted fixes.
- Post PR URL. **HALT.**

### Rule 6 — Iteration PR (after ALL epics complete)
- Title: `feat(MOB-PARITY-2): iteration N — [scope]`
- PR body: completed stories, test result, NFR checklist.
- Post PR URL. **HALT.**

**CHECKPOINT RULE**: After each epic passes tests:
```bash
git add -A && git commit -m "feat(MOB-PARITY-2): [epic-id] — [epic title]" && git push origin HEAD
```

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | Every data-fetching screen: loading + error + empty states | Silent failures |
| 2 | Use `LoadingSpinner`, `ErrorView`, `EmptyState` — no inline alternatives | Component reuse erosion |
| 3 | `X-Correlation-ID` on every API call (via `apiClient`/`cpApiClient` interceptors) | Trace broken |
| 4 | `useTheme()` for all colors/spacing — no hardcoded values | Theme drift |
| 5 | `testID` on all interactive elements | Accessibility / E2E failures |
| 6 | React Query for server state; Zustand for client state only | State management drift |
| 7 | ≥80% coverage on all new/modified files | CI blocks PR |
| 8 | TypeScript strict mode — no `any`, no `@ts-ignore` | Type safety regression |
| 9 | `@shopify/flash-list` for lists > 5 items | Performance regression |
| 10 | PR `--base main` — never target intermediate branch | Work never ships |
| 11 | `cpApiClient` for CP Backend routes (`/cp/*`); `apiClient` for Plant Gateway routes (`/v1/*`) | Wrong auth / wrong base URL |

---

## Tracking Table

| ID | Iter | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Home = single-screen action dashboard | Remove scroll / redesign to fixed-height tiles | � Done | #1071 |
| E1-S2 | 1 | Home = single-screen action dashboard | Pending approvals count tile with deep-link | 🟢 Done | #1071 |
| E2-S1 | 1 | Discover = full-fidelity browse experience | Search debounce + filter persistence | 🟢 Done | #1071 |
| E2-S2 | 1 | Discover = full-fidelity browse experience | Agent Detail shows rating, price, deliver count | 🟢 Done | #1071 |
| E3-S1 | 2 | Hire = end-to-end with receipt | HireConfirmationScreen navigates to MyAgents | � Done | PR #1072 |
| E4-S1 | 2 | My Agents / Ops = live status + controls | Pause / Resume agent controls in Ops screen | � Done | PR #1072 |
| E4-S2 | 2 | My Agents / Ops = live status + controls | Scheduled posts section in Ops (queued / published / failed) | � Done | PR #1072 |
| E4-S3 | 2 | My Agents / Ops = live status + controls | Weekly output count tile in Ops header | � Done | PR #1072 |
| E4-S4 | 2 | My Agents / Ops = live status + controls | Ops parity test suite | � Done | PR #1072 |
| E5-S1 | 3 | Content Approval = reject with reason | ContentDraftApprovalCard gains reject-reason input | 🔴 Not Started | — |
| E6-S1 | 3 | Content Approval = scheduled posts list | ScheduledPostsScreen — full list page | 🔴 Not Started | — |
| E7-S1 | 3 | Deliverables = full content view | DeliverableDetailScreen — read full content | 🔴 Not Started | — |
| E8-S1 | 3 | Inbox = badge count + notification types | Inbox badge on tab + notification type chips | 🔴 Not Started | — |
| E9-S1 | 3 | Parity test suite | All Iteration 3 screens: snapshot + behaviour | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Home Redesign + Discover Completeness

**Scope:** Home becomes a single-screen (no scroll) action dashboard. Discover gains search debounce + filter persistence. Agent Detail shows full data: rating, price, deliverables count, trial button.
**Lane:** A (wire existing APIs — no backend changes)
**⏱ Estimated:** 4h | **Come back:** 2026-04-16 22:00 UTC
**Epics:** E1, E2

### Dependency Map (Iteration 1)
```
E1-S1 (Home no-scroll layout)     — independent
E1-S2 (Home pending approvals tile)  — depends on E1-S1 (same file)
E2-S1 (Discover search debounce)   — independent
E2-S2 (Agent Detail full data)      — independent
```

---

### Epic E1: Customer sees a single-screen action dashboard on Home ✅

**Branch:** `feat/MOB-PARITY-2-it1-home-discover`

---

#### Story E1-S1: Remove scroll — redesign Home to fixed-height tiles

**BLOCKED UNTIL:** none

**Context (2 sentences):**
`HomeScreen.tsx` currently uses a `ScrollView` root with verbose priority text sections. The user says it doesn't fit on screen and is "not a wall of text" — it should be a no-scroll dashboard with stat tiles and action buttons, mirroring the CP "Command Centre" at-a-glance layout.

**User story:** As a customer, when I open the app I see my key numbers (agents working, trials live, billing alerts) in compact stat tiles on a single screen without scrolling, so I can immediately act.

**Files to read first (max 3):**
1. `src/mobile/src/screens/home/HomeScreen.tsx` — current implementation to replace
2. `src/mobile/src/hooks/useHiredAgents.ts` — data source (agents, trial counts)
3. `src/mobile/src/hooks/useTheme.ts` — theme tokens

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/home/HomeScreen.tsx` | Modify — replace ScrollView with fixed-height View; 2×2 stat grid + 2 action buttons |
| `src/mobile/src/__tests__/HomeScreen.test.tsx` | Modify — add test: no ScrollView at root; stat tiles render; action buttons present |

**Acceptance criteria (TDD — write tests first):**

| # | Criterion | Test |
|---|---|---|
| AC1 | Root element is NOT a `ScrollView` | `expect(queryByType(ScrollView)).toBeNull()` at root |
| AC2 | Four stat tiles visible: Agents Active, Trials Live, Pending Approvals (placeholder 0), Billing Alerts | `getByTestId('stat-agents-active')`, `getByTestId('stat-trials-live')`, `getByTestId('stat-pending-approvals')`, `getByTestId('stat-billing-alerts')` |
| AC3 | Two action buttons: "Browse Agents" and "My Agents" | `getByTestId('action-browse-agents')`, `getByTestId('action-my-agents')` |
| AC4 | Loading state renders `LoadingSpinner` | Mock `useHiredAgents` returning `isLoading: true`; assert `LoadingSpinner` rendered |
| AC5 | Error state renders `ErrorView` | Mock returning `error: new Error('x')`; assert `ErrorView` rendered |

**Code patterns to copy exactly:**
```tsx
// NFR: always use useTheme() — no hardcoded colors
const { colors, spacing, typography } = useTheme();

// NFR: testID on every interactive element
<TouchableOpacity testID="action-browse-agents" onPress={() => navigateToTab('DiscoverTab', 'Discover')}>

// NFR: React Query for server state
const { data: hiredAgents, isLoading, error, refetch } = useHiredAgents();

// NFR: shared components for loading/error
if (isLoading) return <LoadingSpinner testID="home-loading" />;
if (error) return <ErrorView message="Could not load your agents" onRetry={refetch} testID="home-error" />;

// NFR: stat tile pattern
<View testID="stat-agents-active" style={styles.statTile}>
  <Text style={[styles.statValue, { color: colors.neonCyan }]}>{activeCount}</Text>
  <Text style={[styles.statLabel, { color: colors.textSecondary }]}>Agents active</Text>
</View>
```

**BDD scenario:**
```
Scenario: Customer sees dashboard on first open
  Given the customer has 2 hired agents and 1 active trial
  When HomeScreen mounts
  Then "2" appears in the Agents Active tile
  And "1" appears in the Trials Live tile
  And no ScrollView exists at the root level
  And "Browse Agents" and "My Agents" buttons are present
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="HomeScreen" --coverage
```

**Definition of done:** All 5 ACs pass. Coverage ≥80% on HomeScreen.tsx.

---

#### Story E1-S2: Pending approvals count tile with deep-link to Inbox

**BLOCKED UNTIL:** E1-S1 complete

**Context (2 sentences):**
The stat-pending-approvals tile from E1-S1 currently shows a hardcoded 0. This story wires it to the real approval queue count (across all hired agents) and makes the tile tappable — navigating to the Inbox tab (MyAgentsTab → Inbox).

**User story:** As a customer, if I have pending content to approve I can see the count on the Home dashboard and tap it to go straight to the Inbox.

**Files to read first (max 3):**
1. `src/mobile/src/screens/home/HomeScreen.tsx` — just modified by E1-S1
2. `src/mobile/src/hooks/useAllDeliverables.ts` — provides deliverable list with status field
3. `src/mobile/src/navigation/types.ts` — navigation type for Inbox deep-link

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/home/HomeScreen.tsx` | Modify — wire stat-pending-approvals to count of pending deliverables; tap navigates to Inbox |
| `src/mobile/src/__tests__/HomeScreen.test.tsx` | Modify — add test: count matches pending deliverables; tap navigates |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Tile shows live count from `useAllDeliverables` filtered to status=pending | Mock `useAllDeliverables` returning 3 pending; tile shows "3" |
| AC2 | Tapping the tile navigates to MyAgentsTab → Inbox | Mock navigation; assert `navigate` called with `{screen:'MyAgentsTab', params:{screen:'Inbox'}}` |
| AC3 | Count "0" shows when no pending items | Mock empty list; tile shows "0" |

**Code patterns to copy exactly:**
```tsx
// Wire pending count
const { data: allDeliverables } = useAllDeliverables();
const pendingCount = (allDeliverables ?? []).filter(d => d.status === 'pending').length;

// Deep-link tap
const handleApprovalsPress = () => {
  navigation.getParent()?.navigate('MyAgentsTab', { screen: 'Inbox' });
};

<TouchableOpacity testID="stat-pending-approvals" onPress={handleApprovalsPress}>
  <Text style={[styles.statValue, {color: pendingCount > 0 ? colors.warning : colors.textSecondary}]}>
    {pendingCount}
  </Text>
  <Text style={[styles.statLabel, {color: colors.textSecondary}]}>Pending approvals</Text>
</TouchableOpacity>
```

**BDD scenario:**
```
Scenario: Customer taps pending approvals tile
  Given 3 deliverables have status "pending"
  When customer taps the pending-approvals tile on Home
  Then navigation navigates to MyAgentsTab → Inbox screen
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="HomeScreen" --coverage
```

**Definition of done:** All 3 ACs pass. Coverage ≥80%.

---

### Epic E2: Customer browses and searches agents with full quality data ✅

**Branch:** `feat/MOB-PARITY-2-it1-home-discover`

---

#### Story E2-S1: Search debounce + filter persistence in Discover

**BLOCKED UNTIL:** none

**Context (2 sentences):**
`DiscoverScreen.tsx` currently fires a search/filter API call on every keystroke, causing too many requests and poor UX. This story adds a 400ms debounce on the search input and persists the active filter chip selection across screen re-mounts using local state.

**User story:** As a customer, when I type in the search box, results update smoothly without lag, and my filter choice (marketing / education / sales) stays selected until I clear it.

**Files to read first (max 3):**
1. `src/mobile/src/screens/discover/DiscoverScreen.tsx` — current search/filter implementation
2. `src/mobile/src/hooks/useAgents.ts` — data hook (accepts params)
3. `src/mobile/src/services/agents/agent.service.ts` — listAgents signature

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/discover/DiscoverScreen.tsx` | Modify — 400ms debounce on search; filter state persists |
| `src/mobile/src/screens/discover/__tests__/DiscoverScreen.test.tsx` | Modify — add debounce test; filter persistence test |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | API is NOT called on each keystroke — fires only after 400ms idle | Mock timer; type 5 chars fast; assert API called once not 5 times |
| AC2 | Selected filter chip remains selected when user returns from AgentDetail | Set filter to "marketing"; simulate screen blur + focus; chip still selected |
| AC3 | Clearing search input resets results to full list | Set query; clear it; assert API called with empty query |
| AC4 | Loading indicator shows while fetching | Assert `LoadingSpinner` visible when `isLoading: true` |

**Code patterns to copy exactly:**
```tsx
// NFR: debounce pattern
const [searchText, setSearchText] = React.useState('');
const [debouncedSearch, setDebouncedSearch] = React.useState('');

React.useEffect(() => {
  const timer = setTimeout(() => setDebouncedSearch(searchText), 400);
  return () => clearTimeout(timer);
}, [searchText]);

// Use debouncedSearch (not searchText) in query params
const { data: agents, isLoading, error } = useAgents({
  q: debouncedSearch || undefined,
  industry: activeFilter || undefined,
});
```

**BDD scenario:**
```
Scenario: Customer types a search query
  Given DiscoverScreen is open
  When customer types "market" (5 chars) in 200ms
  Then the API is called exactly once after 400ms idle
  And results update to matching agents
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="DiscoverScreen" --coverage
```

**Definition of done:** All 4 ACs pass. Coverage ≥80% on DiscoverScreen.tsx.

---

#### Story E2-S2: Agent Detail shows rating, price, deliverables count, and reviews

**BLOCKED UNTIL:** none

**Context (2 sentences):**
`AgentDetailScreen.tsx` has the trial CTA button wired but the data display section is incomplete — it does not show star rating, monthly price, or how many deliverables the agent has produced. The CP web `AgentDetail` page shows all three prominently. This story adds those three data points from the agent object returned by `GET /v1/agents/{id}`.

**User story:** As a customer browsing agents, I can see the agent's star rating, monthly price, and total deliverables produced on the detail screen before deciding to start a trial.

**Files to read first (max 3):**
1. `src/mobile/src/screens/discover/AgentDetailScreen.tsx` — current implementation
2. `src/mobile/src/types/agent.types.ts` — Agent type definition (rating, price fields)
3. `src/mobile/src/screens/discover/__tests__/` — existing test file (or create if absent)

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/discover/AgentDetailScreen.tsx` | Modify — add rating stars row, price badge, deliverables count |
| `src/mobile/src/screens/discover/__tests__/AgentDetailScreen.test.tsx` | Create — tests for rating/price/deliverables display |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Star rating (e.g. "★ 4.8") visible with `testID="agent-detail-rating"` | Mock agent with `rating: 4.8`; assert text contains "4.8" |
| AC2 | Monthly price visible with `testID="agent-detail-price"` | Mock agent with `monthly_price: 12000`; assert text contains "12,000" or "₹12,000" |
| AC3 | Deliverables count visible with `testID="agent-detail-deliverables-count"` | Mock agent with `total_deliverables: 47`; assert text contains "47" |
| AC4 | Trial CTA button still renders with `testID="agent-detail-cta"` (regression guard) | Assert button present |
| AC5 | Gracefully renders when rating/price/deliverables are undefined | Mock agent with those fields undefined; no crash |

**Code patterns to copy exactly:**
```tsx
// NFR: useTheme() for all styles
const { colors, typography } = useTheme();

// Rating row
<View testID="agent-detail-rating" style={styles.ratingRow}>
  <Text style={{color: colors.warning}}>{'★'.repeat(Math.round(agent.rating ?? 0))}</Text>
  <Text style={{color: colors.textSecondary, marginLeft: 6}}>{agent.rating?.toFixed(1) ?? '—'}</Text>
</View>

// Price badge
<View testID="agent-detail-price" style={[styles.priceBadge, {backgroundColor: colors.card}]}>
  <Text style={{color: colors.neonCyan, fontFamily: typography.fontFamily.bodyBold}}>
    {agent.monthly_price ? `₹${agent.monthly_price.toLocaleString('en-IN')}/mo` : 'Free trial'}
  </Text>
</View>

// Deliverables count
<Text testID="agent-detail-deliverables-count" style={{color: colors.textSecondary}}>
  {agent.total_deliverables ?? 0} deliverables produced
</Text>
```

**BDD scenario:**
```
Scenario: Customer opens Agent Detail for the DMA agent
  Given the DMA agent has rating 4.9, price 15000, 128 deliverables
  When AgentDetailScreen renders with that agent
  Then "4.9" is visible in the rating row
  And "₹15,000/mo" is visible in the price badge
  And "128 deliverables produced" is visible
  And the "Start 7-Day Free Trial" CTA button is present
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="AgentDetailScreen" --coverage
```

**Definition of done:** All 5 ACs pass. Coverage ≥80% on AgentDetailScreen.tsx.

---

## Iteration 2 — Hire Receipt Flow + My Agents / Ops Completeness

**Scope:** HireConfirmationScreen navigates to MyAgents after success. Ops screen gains pause/resume controls, scheduled posts section with status chips (queued/published/failed), and weekly output count in the header.
**Lane:** A (wire existing APIs)
**⏱ Estimated:** 5h | **Come back:** 2026-04-17 06:00 UTC
**Epics:** E3, E4

### Dependency Map (Iteration 2)
```
E3-S1 (HireConfirmation → MyAgents nav)  — independent; needs Iteration 1 merged for correct nav types
E4-S1 (Pause/Resume in Ops)              — independent
E4-S2 (Scheduled posts section)          — depends on E4-S1 (same Ops screen file)
E4-S3 (Weekly output count tile)         — depends on E4-S1
E4-S4 (Ops parity test suite)            — depends on E4-S1, E4-S2, E4-S3
```

---

### Epic E3: Customer completes hire flow and lands on My Agents immediately

**Branch:** `feat/MOB-PARITY-2-it2-hire-ops`

---

#### Story E3-S1: HireConfirmationScreen navigates to MyAgents after 3 seconds

**BLOCKED UNTIL:** none (Iteration 1 merged before starting Iteration 2)

**Context (2 sentences):**
`HireConfirmationScreen.tsx` shows a success receipt but has no navigation away — the customer is stranded on the receipt screen. The CP web HireReceipt page redirects to Dashboard after showing a confirmation, then the agent appears in My Agents. Mobile must do the same.

**User story:** As a customer, after hiring an agent I see a clear success confirmation (receipt with agent name, trial dates, plan) and am automatically taken to My Agents after 3 seconds so I can see my new agent immediately.

**Files to read first (max 3):**
1. `src/mobile/src/screens/hire/HireConfirmationScreen.tsx` — current receipt screen
2. `src/mobile/src/navigation/types.ts` — check MyAgentsStackParamList
3. `src/mobile/src/screens/hire/__tests__/` — create if absent

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/hire/HireConfirmationScreen.tsx` | Modify — add 3-second auto-navigate to MyAgentsTab → MyAgents; add "Go to My Agents" manual button |
| `src/mobile/src/screens/hire/__tests__/HireConfirmationScreen.test.tsx` | Create — tests for auto-navigate and manual button |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | After 3000ms, `navigate` is called with `{screen:'MyAgentsTab', params:{screen:'MyAgents'}}` | Fake timers; advance 3000ms; assert navigate called |
| AC2 | "Go to My Agents" button is visible with `testID="hire-confirm-go-my-agents"` | Assert button present on render |
| AC3 | Tapping the button navigates immediately (same destination as auto-navigate) | Tap button; assert navigate called without waiting |
| AC4 | Receipt shows agent name, start date, end date | Mock agent + params; assert name + dates visible |
| AC5 | Countdown text "Taking you to My Agents in 3s..." visible and decrements | At 2000ms: shows "2s"; at 3000ms: navigate fires |

**Code patterns to copy exactly:**
```tsx
// Auto-navigate with countdown
const [countdown, setCountdown] = React.useState(3);
const navigation = useNavigation<any>();

React.useEffect(() => {
  if (countdown <= 0) {
    navigation.getParent()?.navigate('MyAgentsTab', { screen: 'MyAgents' });
    return;
  }
  const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
  return () => clearTimeout(timer);
}, [countdown, navigation]);

// Manual button
<TouchableOpacity
  testID="hire-confirm-go-my-agents"
  onPress={() => navigation.getParent()?.navigate('MyAgentsTab', { screen: 'MyAgents' })}
>
  <Text>Go to My Agents</Text>
</TouchableOpacity>

// Countdown display
<Text testID="hire-confirm-countdown">
  Taking you to My Agents in {countdown}s…
</Text>
```

**BDD scenario:**
```
Scenario: Customer sees receipt and is auto-navigated
  Given HireConfirmationScreen just rendered with agentId and trialData
  When 3 seconds elapse
  Then navigation is called to MyAgentsTab → MyAgents
  And the screen showed "Taking you to My Agents in 3s…" then "2s…" then "1s…"
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="HireConfirmation" --coverage
```

**Definition of done:** All 5 ACs pass. Coverage ≥80% on HireConfirmationScreen.tsx.

---

### Epic E4: Customer sees live agent status and scheduling in Ops

**Branch:** `feat/MOB-PARITY-2-it2-hire-ops`

---

#### Story E4-S1: Pause and Resume agent controls in Ops screen

**BLOCKED UNTIL:** none

**Context (2 sentences):**
`AgentOperationsScreen.tsx` has a `scheduler` section stub but no visible Pause/Resume buttons that call the backend. The CP web Command Centre has prominent Pause/Resume controls in the scheduler panel. Mobile must expose the same.

**User story:** As a customer, I can pause or resume my agent directly from the Ops screen, so I can control its activity without going to the web app.

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` — the scheduler section stub
2. `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` — check for pauseAgent/resumeAgent
3. `src/mobile/src/hooks/useHiredAgents.ts` — check for pause/resume mutations

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | Modify — add Pause/Resume buttons inside scheduler section |
| `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` | Modify — add `pauseAgent(id)` and `resumeAgent(id)` if absent (calls `POST /cp/hired-agents/{id}/pause` and `POST /cp/hired-agents/{id}/resume` via `cpApiClient`) |
| `src/mobile/src/screens/agents/__tests__/AgentOperationsScreen.test.tsx` | Modify or create — add pause/resume tests |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | When agent `status === 'active'`, "Pause Agent" button visible with `testID="ops-pause-btn"` | Mock agent status active; assert button present |
| AC2 | When agent `status === 'paused'`, "Resume Agent" button visible with `testID="ops-resume-btn"` | Mock agent status paused; assert button present |
| AC3 | Tapping Pause calls `POST /cp/hired-agents/{id}/pause` | Mock cpApiClient.post; tap; assert called with correct path |
| AC4 | Tapping Resume calls `POST /cp/hired-agents/{id}/resume` | Same pattern |
| AC5 | Loading spinner shown during API call; buttons disabled while loading | Assert buttons have `disabled` prop during loading state |

**Code patterns to copy exactly:**
```tsx
// In hiredAgents.service.ts
export async function pauseAgent(hiredAgentId: string): Promise<void> {
  await cpApiClient.post(`/cp/hired-agents/${hiredAgentId}/pause`);
}
export async function resumeAgent(hiredAgentId: string): Promise<void> {
  await cpApiClient.post(`/cp/hired-agents/${hiredAgentId}/resume`);
}

// In AgentOperationsScreen.tsx (inside scheduler section)
const [isToggling, setIsToggling] = React.useState(false);
const isActive = agent?.status === 'active';

const handleToggle = async () => {
  setIsToggling(true);
  try {
    if (isActive) {
      await pauseAgent(hiredAgentId);
    } else {
      await resumeAgent(hiredAgentId);
    }
    queryClient.invalidateQueries({ queryKey: ['hiredAgent', hiredAgentId] });
  } finally {
    setIsToggling(false);
  }
};

{isActive
  ? <TouchableOpacity testID="ops-pause-btn" onPress={handleToggle} disabled={isToggling}>
      <Text>Pause Agent</Text>
    </TouchableOpacity>
  : <TouchableOpacity testID="ops-resume-btn" onPress={handleToggle} disabled={isToggling}>
      <Text>Resume Agent</Text>
    </TouchableOpacity>
}
```

**BDD scenario:**
```
Scenario: Customer pauses an active agent
  Given AgentOperationsScreen shows an agent with status "active"
  When customer taps "Pause Agent"
  Then POST /cp/hired-agents/{id}/pause is called
  And buttons are disabled while the call is in-flight
  And after success, agent status refreshes
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="AgentOperations" --coverage
```

**Definition of done:** All 5 ACs pass. Coverage ≥80% on modified files.

---

#### Story E4-S2: Scheduled posts section in Ops (queued / published / failed)

**BLOCKED UNTIL:** E4-S1 complete

**Context (2 sentences):**
The CP Command Centre shows a "Scheduled content" panel listing posts with status chips (queued / published / failed). Mobile Ops screen has no equivalent — customers cannot see what the DMA has scheduled or already published. This story adds a `ScheduledPostsSection` component inside AgentOperationsScreen.

**User story:** As a customer, I can see the posts my DMA has scheduled or already published, with a clear status chip per post, without leaving the mobile app.

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` — file to modify
2. `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` — add `listScheduledPosts` call
3. `src/mobile/src/types/hiredAgents.types.ts` — add ScheduledPost type if absent

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/components/ScheduledPostsSection.tsx` | Create — list of posts with status chip (queued/published/failed) |
| `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` | Modify — add `listScheduledPosts(id): Promise<ScheduledPost[]>` calling `GET /cp/campaigns/{hiredAgentId}/posts` via `cpApiClient` |
| `src/mobile/src/types/hiredAgents.types.ts` | Modify — add `ScheduledPost` type |
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | Modify — add `ScheduledPostsSection` inside existing `scheduler` collapsible section for DMA agents |
| `src/mobile/src/__tests__/ScheduledPostsSection.test.tsx` | Create — tests for render, status chips, empty state |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Queued post shows amber chip "Queued" with `testID="post-status-queued"` | Mock post with status "queued"; assert chip text |
| AC2 | Published post shows green chip "Published" with status "published" | Mock post with status "published"; assert chip |
| AC3 | Failed post shows red chip "Failed" with status "failed" | Mock post with status "failed"; assert chip |
| AC4 | Empty state renders `EmptyState` with message "No scheduled posts yet" | Mock empty array; assert `EmptyState` with correct message |
| AC5 | Loading renders `LoadingSpinner` | Mock isLoading true; assert spinner |
| AC6 | `GET /cp/campaigns/{hiredAgentId}/posts` is called with correct path | Mock cpApiClient.get; assert path |

**Code patterns to copy exactly:**
```tsx
// ScheduledPost type
export interface ScheduledPost {
  id: string;
  title?: string;
  content_preview?: string;
  target_platform?: string;
  status: 'queued' | 'published' | 'failed';
  scheduled_at?: string;
  published_at?: string;
}

// Service call
export async function listScheduledPosts(hiredAgentId: string): Promise<ScheduledPost[]> {
  const response = await cpApiClient.get<ScheduledPost[]>(`/cp/campaigns/${hiredAgentId}/posts`);
  return response.data;
}

// Status chip colors
const STATUS_COLORS = {
  queued:    colors.warning,    // amber
  published: colors.success,    // green
  failed:    colors.error,      // red
} as const;

<View testID={`post-status-${post.status}`}
  style={[styles.chip, {backgroundColor: STATUS_COLORS[post.status] + '22', borderColor: STATUS_COLORS[post.status]}]}>
  <Text style={{color: STATUS_COLORS[post.status], fontSize: 11, fontFamily: typography.fontFamily.bodyBold}}>
    {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
  </Text>
</View>
```

**BDD scenario:**
```
Scenario: DMA agent has 1 queued post and 2 published posts
  Given ScheduledPostsSection receives those 3 posts
  When component renders
  Then 1 amber "Queued" chip is visible
  And 2 green "Published" chips are visible
  And no red chips are visible
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="ScheduledPostsSection|AgentOperations" --coverage
```

**Definition of done:** All 6 ACs pass. Coverage ≥80% on new files.

---

#### Story E4-S3: Weekly output count tile in Ops header

**BLOCKED UNTIL:** E4-S1 complete

**Context (2 sentences):**
The CP Command Centre shows "X deliverables this week" prominently in the agent header panel. AgentOperationsScreen shows agent name and status but no productivity count. This story adds a single count tile to the Ops header showing deliverables produced this calendar week.

**User story:** As a customer, I see at a glance how productive my agent has been this week, so I know whether it is actually working.

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` — header section to modify
2. `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` — data source
3. `src/mobile/src/hooks/useHiredAgents.ts` — check deliverables hook availability

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | Modify — add weekly-output tile below agent name in header |
| `src/mobile/src/screens/agents/__tests__/AgentOperationsScreen.test.tsx` | Modify — add weekly count tile test |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Tile with `testID="ops-weekly-output"` renders in Ops header | Assert element present |
| AC2 | Count derived from `deliverables` filtered to `created_at >= startOfCurrentWeek()` | Mock 3 deliverables in current week + 2 older; assert tile shows "3" |
| AC3 | Shows "0 this week" when no recent deliverables | Mock empty; assert "0 this week" text |
| AC4 | Does not crash when deliverables list is undefined | Mock undefined; assert no error |

**Code patterns to copy exactly:**
```tsx
// Week filter helper
function startOfCurrentWeek(): Date {
  const now = new Date();
  const day = now.getDay(); // 0=Sun
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(now.setDate(diff));
}

// Count this week's deliverables
const weekStart = startOfCurrentWeek();
const weeklyCount = (deliverables ?? []).filter(d =>
  d.created_at && new Date(d.created_at) >= weekStart
).length;

<View testID="ops-weekly-output" style={styles.weeklyTile}>
  <Text style={{color: colors.neonCyan, fontFamily: typography.fontFamily.displayBold, fontSize: 22}}>
    {weeklyCount}
  </Text>
  <Text style={{color: colors.textSecondary, fontSize: 12}}>this week</Text>
</View>
```

**BDD scenario:**
```
Scenario: Agent produced 5 deliverables this week
  Given AgentOperationsScreen with 5 deliverables dated this week
  When screen renders
  Then ops-weekly-output tile shows "5"
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="AgentOperations" --coverage
```

**Definition of done:** All 4 ACs pass. Coverage ≥80%.

---

#### Story E4-S4: Ops parity test suite

**BLOCKED UNTIL:** E4-S1, E4-S2, E4-S3 complete

**Context (2 sentences):**
Stories E4-S1 through E4-S3 add new behaviours to `AgentOperationsScreen`. This story adds integration-level parity tests that confirm the Ops screen matches all CP Command Centre features defined in the MOB-PARITY-2 scope, serving as a regression guard for future changes.

**User story:** As a developer, a parity test suite catches any regression that removes pause/resume, scheduled posts, or weekly output from the Ops screen.

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/__tests__/AgentOperationsScreen.test.tsx` — extend this
2. `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` — current implementation
3. `src/mobile/src/components/ScheduledPostsSection.tsx` — created in E4-S2

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/agents/__tests__/AgentOperationsScreen.test.tsx` | Modify — add parity suite block |

**Acceptance criteria (parity suite):**

| # | Test ID | Assertion |
|---|---|---|
| AC1 | `ops-parity-pause-btn` | Active agent renders pause button |
| AC2 | `ops-parity-resume-btn` | Paused agent renders resume button |
| AC3 | `ops-parity-scheduled-posts` | ScheduledPostsSection renders inside scheduler section |
| AC4 | `ops-parity-weekly-output` | ops-weekly-output tile is present |
| AC5 | `ops-parity-approvals-section` | approvals section renders with correct count |

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="AgentOperations" --coverage
```

**Definition of done:** All 5 ACs pass. Coverage ≥80%.

---

## Iteration 3 — Content Approval + Deliverables + Inbox Completeness

**Scope:** ContentDraftApprovalCard gains reject-with-reason input. New ScheduledPostsScreen shows the full scheduled posts list page. DeliverableDetailScreen lets customers read full deliverable content. Inbox gains badge count + notification type chips. Parity test suite.
**Lane:** A (wire existing APIs)
**⏱ Estimated:** 5h | **Come back:** 2026-04-17 12:00 UTC
**Epics:** E5, E6, E7, E8, E9

### Dependency Map (Iteration 3)
```
E5-S1 (Reject with reason)           — independent
E6-S1 (ScheduledPostsScreen)         — independent (new screen)
E7-S1 (DeliverableDetailScreen)      — independent (new screen)
E8-S1 (Inbox badge + type chips)     — independent
E9-S1 (Parity test suite It3)        — depends on E5–E8 complete
```

---

### Epic E5: Customer can reject content with a reason

**Branch:** `feat/MOB-PARITY-2-it3-approvals-deliverables`

---

#### Story E5-S1: ContentDraftApprovalCard gains reject-with-reason input

**BLOCKED UNTIL:** none (Iteration 2 merged before starting Iteration 3)

**Context (2 sentences):**
`ContentDraftApprovalCard.tsx` has an `onReject(id)` callback but no text input for a rejection reason — the agent receives no feedback on why its content was rejected. The CP web review panel has a "Reason for rejection" textarea. Mobile must match this: tapping Reject expands a text input, and confirming sends reason alongside the rejection.

**User story:** As a customer, when I reject a content draft I can type a short reason (e.g. "wrong tone") so the agent knows what to fix.

**Files to read first (max 3):**
1. `src/mobile/src/components/ContentDraftApprovalCard.tsx` — current card (has Approve/Reject but no reason field)
2. `src/mobile/src/hooks/useApprovalQueue.ts` — `reject(deliverableId)` mutation to extend
3. `src/mobile/src/screens/agents/__tests__/` — find existing approval test to update

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/components/ContentDraftApprovalCard.tsx` | Modify — tap Reject expands reason `TextInput`; confirm sends `onRejectWithReason(id, reason)` |
| `src/mobile/src/hooks/useApprovalQueue.ts` | Modify — add `rejectWithReason(deliverableId, reason)` mutation calling `POST .../reject` with `{reason}` body |
| `src/mobile/src/__tests__/ContentDraftApprovalCard.test.tsx` | Create — tests for reject expansion + reason submission |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Tapping Reject shows `TextInput` with `testID="reject-reason-input"` (not visible initially) | Assert input hidden initially; tap Reject; assert visible |
| AC2 | Confirm Rejection button with `testID="reject-reason-confirm"` appears after reason is typed | Type reason; assert confirm button appears |
| AC3 | Tapping Confirm calls `onRejectWithReason(id, "reason text")` | Assert callback called with both args |
| AC4 | Cancel button dismisses input without calling reject | Tap Reject → Cancel; assert `onRejectWithReason` not called |
| AC5 | Confirm disabled when reason field is empty | Empty input; assert confirm button disabled |
| AC6 | `rejectWithReason` mutation sends `{reason}` in POST body | Mock cpApiClient.post; assert body contains `{reason: "..."}` |

**Code patterns to copy exactly:**
```tsx
// ContentDraftApprovalCard — reject state
const [rejectMode, setRejectMode] = React.useState(false);
const [rejectReason, setRejectReason] = React.useState('');

// Show/hide pattern
{!rejectMode
  ? <TouchableOpacity testID="reject-btn" onPress={() => setRejectMode(true)}>
      <Text>Reject</Text>
    </TouchableOpacity>
  : <>
      <TextInput
        testID="reject-reason-input"
        value={rejectReason}
        onChangeText={setRejectReason}
        placeholder="Reason for rejection…"
        multiline
        style={[styles.reasonInput, {borderColor: colors.error, color: colors.textPrimary}]}
      />
      <View style={styles.rejectActions}>
        <TouchableOpacity testID="reject-reason-cancel" onPress={() => { setRejectMode(false); setRejectReason(''); }}>
          <Text>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="reject-reason-confirm"
          disabled={rejectReason.trim().length === 0}
          onPress={() => { onRejectWithReason(deliverable.id, rejectReason.trim()); setRejectMode(false); }}
        >
          <Text>Confirm Rejection</Text>
        </TouchableOpacity>
      </View>
    </>
}

// In useApprovalQueue.ts — extend reject mutation
async function rejectDeliverableWithReason(hiredAgentId: string, deliverableId: string, reason: string): Promise<void> {
  await cpApiClient.post(
    `/cp/hired-agents/${hiredAgentId}/approval-queue/${deliverableId}/reject`,
    { reason }
  );
}
```

**BDD scenario:**
```
Scenario: Customer rejects a draft with a reason
  Given ContentDraftApprovalCard renders a pending draft
  When customer taps Reject
  Then a TextInput appears for the reason
  When customer types "Wrong tone for our audience" and taps Confirm
  Then onRejectWithReason is called with the deliverable id and that reason text
  And the reason TextInput disappears
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="ContentDraftApproval" --coverage
```

**Definition of done:** All 6 ACs pass. Coverage ≥80%.

---

### Epic E6: Customer sees a full scheduled-posts list page

**Branch:** `feat/MOB-PARITY-2-it3-approvals-deliverables`

---

#### Story E6-S1: ScheduledPostsScreen — full list page with status and platform

**BLOCKED UNTIL:** none

**Context (2 sentences):**
`ScheduledPostsSection` (Iteration 2) embedded a miniature list inside AgentOperations. Customers need a dedicated full-screen view of ALL scheduled posts for an agent, matching the CP "Campaign" page with filter tabs by status. This story creates `ScheduledPostsScreen` as a standalone screen accessible from the Ops screen's scheduler section.

**User story:** As a customer, I can tap "See all posts" in the Ops scheduler section and view the complete list of my DMA's posts with platform icons and status, paginated, with pull-to-refresh.

**Files to read first (max 3):**
1. `src/mobile/src/navigation/types.ts` — to add `ScheduledPosts` route to `MyAgentsStackParamList`
2. `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` — `listScheduledPosts` added in E4-S2
3. `src/mobile/src/screens/agents/index.ts` — export list to add new screen

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/agents/ScheduledPostsScreen.tsx` | Create — full-page list with status filter tabs, FlashList, pull-to-refresh |
| `src/mobile/src/navigation/types.ts` | Modify — add `ScheduledPosts: { hiredAgentId: string }` to `MyAgentsStackParamList` |
| `src/mobile/src/screens/agents/index.ts` | Modify — export `ScheduledPostsScreen` |
| `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | Modify — add "See all posts →" link tapping into ScheduledPostsScreen |
| `src/mobile/src/screens/agents/__tests__/ScheduledPostsScreen.test.tsx` | Create — render, filter, empty, error tests |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Screen renders with `testID="scheduled-posts-screen"` | Assert element present |
| AC2 | Posts list uses FlashList (not FlatList) | Assert `FlashList` in render tree |
| AC3 | Three filter tabs: All, Queued, Published | Assert tabs with `testID="filter-all"`, `"filter-queued"`, `"filter-published"` |
| AC4 | Tapping "Queued" tab shows only queued posts | Mock 2 queued + 1 published; tap Queued; assert 2 items visible |
| AC5 | Empty state `testID="scheduled-posts-empty"` when no posts match filter | Mock empty; assert empty state |
| AC6 | Pull-to-refresh triggers refetch | Simulate refresh; assert refetch called |

**Code patterns to copy exactly:**
```tsx
// NFR: FlashList for lists
import { FlashList } from '@shopify/flash-list';

<FlashList
  testID="scheduled-posts-list"
  data={filteredPosts}
  renderItem={({item}) => <PostRow post={item} />}
  estimatedItemSize={60}
  keyExtractor={item => item.id}
  ListEmptyComponent={
    <EmptyState testID="scheduled-posts-empty" message="No posts match this filter" />
  }
  refreshControl={
    <RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={colors.neonCyan} />
  }
/>

// Filter tabs
type PostFilter = 'all' | 'queued' | 'published' | 'failed';
const [activeFilter, setActiveFilter] = React.useState<PostFilter>('all');
const filteredPosts = (posts ?? []).filter(p =>
  activeFilter === 'all' ? true : p.status === activeFilter
);
```

**BDD scenario:**
```
Scenario: Customer filters to queued posts
  Given ScheduledPostsScreen with 3 queued + 2 published posts
  When customer taps the "Queued" filter tab
  Then only 3 posts are shown
  And each shows a "Queued" status chip
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="ScheduledPostsScreen" --coverage
```

**Definition of done:** All 6 ACs pass. Coverage ≥80%.

---

### Epic E7: Customer reads the full content of a deliverable

**Branch:** `feat/MOB-PARITY-2-it3-approvals-deliverables`

---

#### Story E7-S1: DeliverableDetailScreen — full content view with approve/reject

**BLOCKED UNTIL:** none

**Context (2 sentences):**
`InboxScreen.tsx` shows a truncated 200-character preview of each deliverable. Tapping it goes nowhere — there is no detail screen. The CP Deliverables page shows the full text and approve/reject actions. This story creates a `DeliverableDetailScreen` that shows full content, the platform, type, created date, and inline approve/reject.

**User story:** As a customer, I can tap any deliverable in the Inbox to read the complete content and approve or reject it without going to the web app.

**Files to read first (max 3):**
1. `src/mobile/src/navigation/types.ts` — add `DeliverableDetail` route
2. `src/mobile/src/screens/agents/InboxScreen.tsx` — add navigation on row tap
3. `src/mobile/src/hooks/useAllDeliverables.ts` — data source for single deliverable

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/screens/agents/DeliverableDetailScreen.tsx` | Create — full content + approve/reject |
| `src/mobile/src/navigation/types.ts` | Modify — add `DeliverableDetail: { deliverableId: string; hiredAgentId: string }` to `MyAgentsStackParamList` |
| `src/mobile/src/screens/agents/InboxScreen.tsx` | Modify — tap on deliverable card navigates to `DeliverableDetail` |
| `src/mobile/src/screens/agents/index.ts` | Modify — export `DeliverableDetailScreen` |
| `src/mobile/src/screens/agents/__tests__/DeliverableDetailScreen.test.tsx` | Create — tests for full content render, approve, reject |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Screen renders with `testID="deliverable-detail-screen"` | Assert present |
| AC2 | Full content text visible (not truncated) | Mock deliverable with 500-char content; assert all 500 chars in output |
| AC3 | Platform, type, and created date visible | Assert `testID="detail-platform"`, `"detail-type"`, `"detail-created-at"` |
| AC4 | Approve button (`testID="detail-approve-btn"`) calls approve mutation | Tap; assert mutation called with correct ids |
| AC5 | Reject button (`testID="detail-reject-btn"`) shows reject-with-reason flow (same pattern as E5-S1) | Tap reject; assert reason input appears |
| AC6 | Tapping a deliverable row in InboxScreen navigates to DeliverableDetailScreen | Mock navigation; tap row; assert navigate called with correct params |

**Code patterns to copy exactly:**
```tsx
// Loading / error / content states
if (isLoading) return <LoadingSpinner testID="detail-loading" />;
if (error || !deliverable) return <ErrorView message="Could not load deliverable" onRetry={refetch} testID="detail-error" />;

// Full content (no truncation)
<ScrollView testID="deliverable-detail-screen">
  <Text testID="detail-platform" style={{color: colors.textSecondary}}>{deliverable.target_platform}</Text>
  <Text testID="detail-type" style={{color: colors.textSecondary}}>{deliverable.type}</Text>
  <Text testID="detail-created-at" style={{color: colors.textSecondary}}>
    {deliverable.created_at ? new Date(deliverable.created_at).toLocaleDateString() : '—'}
  </Text>
  <Text style={{color: colors.textPrimary, fontFamily: typography.fontFamily.body, marginTop: spacing.md}}>
    {deliverable.content_preview}  {/* full text from API, not truncated */}
  </Text>
</ScrollView>

// Action buttons
<TouchableOpacity testID="detail-approve-btn" onPress={() => approve(deliverable.id)}>
  <Text>Approve</Text>
</TouchableOpacity>
<TouchableOpacity testID="detail-reject-btn" onPress={() => setRejectMode(true)}>
  <Text>Reject</Text>
</TouchableOpacity>
```

**BDD scenario:**
```
Scenario: Customer reads full content before approving
  Given a deliverable with 600-character content
  When customer taps it in Inbox
  Then DeliverableDetailScreen opens showing all 600 characters
  And Approve and Reject buttons are visible
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="DeliverableDetail|InboxScreen" --coverage
```

**Definition of done:** All 6 ACs pass. Coverage ≥80%.

---

### Epic E8: Inbox shows badge count and notification type chips

**Branch:** `feat/MOB-PARITY-2-it3-approvals-deliverables`

---

#### Story E8-S1: Inbox tab badge count + notification type chips

**BLOCKED UNTIL:** none

**Context (2 sentences):**
The "Inbox" tab in the bottom navigation has no badge count — customers don't know there are items needing attention without opening the tab. Also, all items in the Inbox look the same visually: there are no type chips to distinguish "Approval needed" from "Agent update" from "Billing alert". This story wires the badge count from `pendingDeliverables.length` and adds a type chip on each Inbox row.

**User story:** As a customer, I see a badge number on the Inbox tab when I have pending approvals, and each notification shows a type label so I can prioritise at a glance.

**Files to read first (max 3):**
1. `src/mobile/src/navigation/MainTabNavigator.tsx` (or equivalent tab navigator file) — badge prop location
2. `src/mobile/src/screens/agents/InboxScreen.tsx` — deliverable rows to add chips to
3. `src/mobile/src/hooks/useAllDeliverables.ts` — pending count source

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/navigation/MainTabNavigator.tsx` | Modify — pass `tabBarBadge={pendingCount || undefined}` on the MyAgentsTab |
| `src/mobile/src/screens/agents/InboxScreen.tsx` | Modify — add `TypeChip` to each deliverable row |
| `src/mobile/src/__tests__/InboxScreen.test.tsx` | Modify or create — badge count test, chip render test |

**Acceptance criteria:**

| # | Criterion | Test |
|---|---|---|
| AC1 | Tab badge renders with pending count when > 0 | Mock 3 pending; assert badge "3" in navigator |
| AC2 | Tab badge is undefined (hidden) when count is 0 | Mock 0 pending; assert badge undefined |
| AC3 | Each deliverable row shows a type chip: "Approval needed" / "Agent update" / "Billing alert" | Mock different types; assert correct label per row |
| AC4 | Chip `testID` follows pattern `"chip-{type}"` | Assert `testID="chip-approval-needed"` renders |
| AC5 | Chips use themed colors (warning for approval, cyan for update, error for billing) | Assert chip style includes correct color |

**Code patterns to copy exactly:**
```tsx
// In MainTabNavigator — badge
const { data: allDeliverables } = useAllDeliverables();
const pendingCount = (allDeliverables ?? []).filter(d => d.status === 'pending').length;

// On the tab button for MyAgentsTab
tabBarBadge={pendingCount > 0 ? pendingCount : undefined}

// TypeChip in InboxScreen
function getChipConfig(type: string): { label: string; color: string } {
  if (type === 'content_draft') return { label: 'Approval needed', color: colors.warning };
  if (type === 'agent_update')  return { label: 'Agent update',     color: colors.neonCyan };
  if (type === 'billing_alert') return { label: 'Billing alert',    color: colors.error };
  return { label: 'Notification', color: colors.textSecondary };
}

const chip = getChipConfig(item.type);
<View testID={`chip-${chip.label.toLowerCase().replace(/ /g,'-')}`}
  style={[styles.chip, {borderColor: chip.color, backgroundColor: chip.color + '18'}]}>
  <Text style={{color: chip.color, fontSize: 10, fontFamily: typography.fontFamily.bodyBold}}>
    {chip.label}
  </Text>
</View>
```

**BDD scenario:**
```
Scenario: Customer has 2 pending approvals
  Given the app loads with 2 content_draft deliverables in "pending" status
  Then the Inbox tab shows badge "2"
  And each row in the Inbox shows an "Approval needed" chip
```

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="InboxScreen|MainTabNavigator" --coverage
```

**Definition of done:** All 5 ACs pass. Coverage ≥80%.

---

### Epic E9: Parity test suite for Iteration 3

**Branch:** `feat/MOB-PARITY-2-it3-approvals-deliverables`

---

#### Story E9-S1: Parity test suite — all Iteration 3 screens and components

**BLOCKED UNTIL:** E5-S1, E6-S1, E7-S1, E8-S1 complete

**Context (2 sentences):**
All Iteration 3 epics (E5–E8) add new components and screens. This parity suite adds integration-level BDD scenarios that verify the complete set of features delivered in Iteration 3 remain green as a regression guard. It also adds a cross-feature scenario: approve-from-detail then verify Inbox badge decrements.

**User story:** As a developer, a permanent parity test suite detects regressions in content approval reject-with-reason, scheduled posts, deliverable detail, and inbox badges.

**Files to read first (max 3):**
1. `src/mobile/src/__tests__/` — find or create parity test file
2. `src/mobile/src/screens/agents/DeliverableDetailScreen.tsx` — created in E7-S1
3. `src/mobile/src/screens/agents/InboxScreen.tsx` — modified in E7-S1 and E8-S1

**Files to create / modify:**

| File | Action |
|---|---|
| `src/mobile/src/__tests__/MOB-PARITY-2-parity.test.tsx` | Create — cross-feature parity suite |

**Acceptance criteria (parity test assertions):**

| # | Test ID | Assertion |
|---|---|---|
| AC1 | `parity-reject-reason-input` | ContentDraftApprovalCard: reject reason input appears on Reject tap |
| AC2 | `parity-scheduled-posts-screen` | ScheduledPostsScreen renders with FlashList |
| AC3 | `parity-deliverable-detail-full-content` | DeliverableDetailScreen shows untruncated content |
| AC4 | `parity-inbox-badge` | Tab badge shows pending count ≥ 1 |
| AC5 | `parity-cross-approve-badge-decrement` | After approving a deliverable in detail screen, badge count decrements by 1 |

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run --rm mobile-test jest --testPathPattern="MOB-PARITY-2-parity" --coverage
```

**Definition of done:** All 5 ACs pass. Coverage ≥80% on parity file.

---

## Prerequisite Evidence Blocks

### Before Iteration 2 starts

| Required | Evidence |
|---|---|
| Iteration 1 PR merged to main | PR URL: _(fill when merged)_ |
| `docs/mob-parity-2-plan` plan file on main | _(confirm with `git show origin/main:docs/mobile/iterations/MOB-PARITY-2-mobile-full-parity.md`) |

### Before Iteration 3 starts

| Required | Evidence |
|---|---|
| Iteration 2 PR merged to main | PR URL: _(fill when merged)_ |

---

*Plan ready: MOB-PARITY-2 | File: `docs/mobile/iterations/MOB-PARITY-2-mobile-full-parity.md`*
