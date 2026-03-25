# MOBILE-COMP-1 — Mobile CP Compliance Iteration Plan

## Objective

Bring the mobile application into practical compliance with CP web for the highest-value customer journeys in one iteration: discover, hire, connect, operate, review, and manage subscriptions from a truthful mobile experience on both Android and iOS builds in Expo. The iteration focuses on removing dead ends, replacing placeholder state with live state, and aligning information architecture so mobile behaves like a reliable CP companion instead of a partially wired shell.

## Authoritative Defect List

This plan uses the previously identified mobile-vs-CP defect set as the authoritative defect list.

| Defect ID | Root cause | Impact | Best possible solution/fix |
|---|---|---|---|
| D1 | `HireWizard` exists in navigation types and deep links but is not registered in `MainNavigator` | Customers can hit a dead-end or inconsistent hire path from discover surfaces | Register the route in the correct stack, align typed params, and add navigation regression tests |
| D2 | `ConnectorSetupCard` uses local `isConnected` state only | Platform connection appears successful on mobile without any real backend truth | Replace the fake connector step with real CP/Plant connection state and actionable connect/disconnect flow |
| D3 | Hire/setup handoff is generic and not tied cleanly into hired-agent runtime management | Customers can start a hire but do not get a CP-truthful follow-through into operations | Make hire completion, runtime lookup, and next-step navigation flow into real hired-agent and trial destinations |
| D4 | `NotificationsScreen` renders demo `actionableNotifications` instead of a live feed | Inbox-like alerts look polished but are not trustworthy | Create a real notifications service/hook, render live loading/empty/error states, and preserve deep-link actions |
| D5 | `SubscriptionManagementScreen` shows hard-coded plan values and triggers Razorpay with placeholder identifiers | Billing and renewal state are misleading | Bind the screen to live subscription/hired-agent data and only expose CTAs that reflect real state |
| D6 | `HomeScreen` uses static priority pills/cards and timeout-based refresh | Mobile home is not an operational cockpit like CP | Derive priorities from live agent, approval, and trial data with truthful empty/loading states |
| D7 | Mobile shell labels and menu routes are only partially aligned to CP outcomes | Customers have to infer where to act next across tabs and profile surfaces | Tighten IA, labels, route affordances, and parity cues across Home, My Agents, and Profile |
| D8 | Mobile already has partial DMA/runtime support, but the route from hire to connect to operate is fragmented | DMA and other hired workflows feel incomplete compared with CP | Sequence the mobile journey so discovery, hire, connect, and operations feel continuous and real |

## Epic / Story Tracker

| Epic | Story | Title | Tracking status | Branch | Test plan / doc update |
|---|---|---|---|---|---|
| E1 | E1-S1 | Restore hire-route and navigation parity | Not started | `feat/MOBILE-COMP-1-it1-e1` | Extend mobile navigation and hire journey tests |
| E1 | E1-S2 | Replace fake platform connect with live runtime truth | Not started | `feat/MOBILE-COMP-1-it1-e1` | Extend hire wizard and connector tests |
| E2 | E2-S1 | Replace demo notifications with live actionable inbox | Not started | `feat/MOBILE-COMP-1-it1-e2` | Extend notifications screen tests |
| E2 | E2-S2 | Turn home into a live mobile cockpit | Not started | `feat/MOBILE-COMP-1-it1-e2` | Extend home and hook tests |
| E3 | E3-S1 | Make billing and subscription state truthful | Not started | `feat/MOBILE-COMP-1-it1-e3` | Extend subscription and payment hook tests |
| E3 | E3-S2 | Align shell parity across Android and iOS and close iteration docs | Not started | `feat/MOBILE-COMP-1-it1-e3` | Update mobile test assets doc after iteration PR |

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `MOBILE-COMP-1` |
| Feature area | Mobile App — CP compliance parity across hire, operate, notifications, home, and billing |
| Created | 2026-03-25 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/mobile/mobile_approach.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13, mobile §23) |
| Total iterations | 1 |
| Total epics | 3 |
| Total stories | 6 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows. Every story card is self-contained and names the exact mobile files to inspect first.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | One iteration only, 3 epics, 6 stories, self-contained story cards |
| No working memory across files | Exact file paths and code patterns are embedded inline |
| No planning ability | Stories are atomic, acceptance criteria are binary, execution order is fixed |
| Token cost per file read | Max 3 files in each story's “Files to read first” section |
| Merge overhead | One iteration PR only; no second iteration or docs-only housekeeping pass |

> Agent: Execute exactly one story at a time. Read only the files listed in that story before changing code.

---

## Vision Intake

- Area: Mobile app, using CP web as the compliance benchmark.
- Outcome: Customers can browse, hire, connect, operate, review, and manage subscriptions from mobile with truthful state and no broken paths.
- Out of scope: No infrastructure or deployment changes; no database schema changes; no new marketplace concepts or net-new product areas; no CP web redesign beyond parity reference; no broad Plant business-logic refactor.
- Lane: Lane A first, with minimal Lane B allowed only if a missing endpoint or thin proxy is the only blocker to mobile parity.
- Urgency: Single iteration only, multiple epics inside one plan, optimized for one meaningful PR to `main`.

---

## PM Review Checklist

- [ ] EXPERT PERSONAS filled for mobile execution
- [ ] Epic titles name customer outcomes, not technical actions
- [ ] Every story has an exact branch name
- [ ] Every story card embeds relevant code patterns inline
- [ ] Every story card has max 3 files in “Files to read first”
- [ ] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [ ] Every new backend route story embeds the `waooaw_router()` snippet
- [ ] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [ ] Every story that adds env vars lists the exact Terraform files to update
- [ ] Every story has `BLOCKED UNTIL` or `none`
- [ ] Iteration has time estimate and come-back datetime
- [ ] Iteration has a complete GitHub agent launch block
- [ ] STUCK PROTOCOL is in Agent Execution Rules
- [ ] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [ ] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A mobile parity pass across hire, runtime truth, notifications, home, billing, and shell alignment, with minimal Lane B only if a missing endpoint blocks shipping | 3 | 6 | 6h | 2026-03-25 23:30 IST |

**Estimate basis:** navigation or screen parity = 45 min | live data wiring = 60 min | cross-surface shell alignment = 60 min | Jest / typecheck / doc update = 30 min. Buffer already included.

---

## How to Launch Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: clean main with current merge tip visible
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` → select **platform-engineer**
6. Paste the block below and press **Enter**
7. Come back at **2026-03-25 23:30 IST**

**Iteration 1 agent task** (paste verbatim):

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Mobile app designer expert in UI UX using Expo.dev for front end + Senior React 18 / TypeScript / Fluent UI engineer + Senior React Native / Expo / TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a Mobile app designer expert in UI UX using Expo.dev for front end and a Senior React 18 / TypeScript / Fluent UI engineer, I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOBILE-COMP-1-mobile-cp-compliance.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, and E3. Do not create another iteration.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git fetch origin && git log --oneline origin/main | head -3
   You must be on main or able to branch from main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute epics in this order: E1 → E2 → E3
6. After each story: run the story tests, push code on the epic branch, update the story status in the plan tracker, and then move to the next story.
7. When all stories pass acceptance criteria, open one iteration PR to `main`. Post the PR URL. HALT.
```

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all other instructions.

### Rule -1 — Activate Expert Personas

Activate: **Mobile app designer expert in UI UX using Expo.dev for front end**, **Senior React 18 / TypeScript / Fluent UI engineer**, and **Senior React Native / Expo / TypeScript engineer**.

Begin every epic with:

> *"Acting as a Mobile app designer expert in UI UX using Expo.dev for front end and a Senior React 18 / TypeScript / Fluent UI engineer, I will [what] by [approach]."*

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull origin main
git checkout -b feat/MOBILE-COMP-1-it1-e1
git commit --allow-empty -m "chore(MOBILE-COMP-1): start iteration 1"
git push -u origin feat/MOBILE-COMP-1-it1-e1

gh pr create \
  --base main \
  --head feat/MOBILE-COMP-1-it1-e1 \
  --draft \
  --title "tracking: MOBILE-COMP-1 Iteration 1 — in progress" \
  --body "## tracking: MOBILE-COMP-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] E1-S1 Restore hire-route and navigation parity
- [ ] E1-S2 Replace fake platform connect with live runtime truth
- [ ] E2-S1 Replace demo notifications with live actionable inbox
- [ ] E2-S2 Turn home into a live mobile cockpit
- [ ] E3-S1 Make billing and subscription state truthful
- [ ] E3-S2 Align shell parity across Android and iOS and close iteration docs

Live updates posted as comments below." 
```

### Rule 1 — Branch discipline

One epic = one branch.

- E1 branch: `feat/MOBILE-COMP-1-it1-e1`
- E2 branch: `feat/MOBILE-COMP-1-it1-e2`
- E3 branch: `feat/MOBILE-COMP-1-it1-e3`

All stories in the same epic commit sequentially to the same branch.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card. Do not refactor unrelated code, do not redesign CP web, and do not invent new product areas.

### Rule 3 — Test before the next story

After each story:
1. Run the story-specific Jest/typecheck command in the story card.
2. If the story changes shared navigation or live data wiring, run the listed regression test too.
3. Only then move to the next story.

### Rule 4 — Update the tracker after every story

After a story passes:
1. Change that story's `Tracking status` in the tracker table from `Not started` to `Done`.
2. Commit the code changes.
3. Commit the tracker update.
4. Push.
5. Post a comment to the tracking draft PR with story ID, files changed, and tests passed.

### Rule 5 — Test-plan update rule

If a story adds or materially changes mobile tests, extend the closest existing mobile test file instead of creating redundant coverage. After the final iteration PR is ready, update `docs/testing/ExistingTestAssets.md` for the mobile row in the same branch before opening the final PR.

### Rule 6 — Docker / Codespace only

Use the devcontainer / Codespace environment only. No local virtualenvs, no host-level Python setup, no off-plan tooling.

### Rule 7 — STUCK PROTOCOL

If blocked for more than 20 minutes or after 2 failed fix attempts:

```bash
git add -A && git commit -m "WIP: MOBILE-COMP-1 blocked at [story-id] — [reason]"
git push origin [current-epic-branch]

gh pr create \
  --base main \
  --head [current-epic-branch] \
  --draft \
  --title "WIP: MOBILE-COMP-1 — blocked at [story-id]" \
  --body "Blocked on: [exact test or runtime issue]
Error: [exact error]
Attempted fixes:
1. [approach one]
2. [approach two]"
```

HALT after posting the draft PR URL.

### Rule 8 — Final validation and PR

After E3-S2:

```bash
cd src/mobile && npm run typecheck
cd src/mobile && npm test -- --runInBand --maxWorkers=2
```

Then create one iteration branch and one PR to `main`.

---

## Iteration 1 — Mobile CP Compliance

### Dependency Map

- E1 first: removes dead ends and fake connection state that would invalidate later live-state work.
- E2 second: replaces demo data with real actionable state for notifications and home.
- E3 last: makes billing truthful and aligns shell parity, then closes test docs for the finished iteration.

## Epic E1 — Customer can move from discovery to hire without dead ends

**Outcome:** A customer can start from discovery, enter the mobile hire journey, connect the required platform using real state, and land in a truthful next step without fake success states.

## Epic E2 — Customer sees live action items instead of placeholder mobile state

**Outcome:** Notifications and home surfaces behave like a reliable CP companion, showing real work to review, real runtime cues, and honest empty states.

## Epic E3 — Customer can trust billing and shell navigation on mobile

**Outcome:** Subscription surfaces show real state, shell labels and routes are easier to act through, and the iteration exits with tests and test-asset docs updated.