# CP-MOBILE-1 — Customer Portal Mobile-Native Web Iteration Plan

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-MOBILE-1` |
| Feature area | Customer Portal authenticated web experience on phone-sized screens |
| Created | 2026-03-13 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 1 |
| Total stories | 5 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows. Every story is self-contained, names exact files, and keeps the read set tight so execution can proceed without repo-wide exploration.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Each story card names exact files, lines, and target changes |
| No working memory across files | CP shell and NFR boundary reminders are embedded inline in each story |
| No planning ability | Stories are atomic and sequential |
| Token cost per file read | Max 3 files to read first per story |
| Binary inference only | Acceptance criteria and test commands are pass/fail |

> **Agent:** Execute exactly ONE story at a time. Read only your story card, then act.

---

## PM Review Checklist (tick every box before publishing)

- [x] **EXPERT PERSONAS filled** — each iteration task names the required frontend personas
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR boundary snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or `none`)
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend before frontend where needed
- [x] Iteration count minimized for PR-only delivery
- [x] Related frontend work kept in the same iteration
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A frontend-only mobile-native shell, layout, and responsive regression coverage for CP authenticated pages | 1 | 5 | 5h | 2026-03-13 20:00 UTC |

**Estimate basis:** FE shell/layout change = 45–60 min per story | Focused Vitest regression = 30 min | Docker regression = 15 min | PR = 10 min. Buffer already included.

### PR-Overhead Optimization Rules

- One iteration only, per user request.
- One epic keeps all closely related frontend slices on the same branch and PR.
- No backend, infra, or deployment work is included because current evidence shows a pure CP FrontEnd gap.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` in the message box → select **platform-engineer** from the dropdown
6. Copy the block below and paste into the message box → press **Enter**
7. Go away. Come back at: **2026-03-13 20:00 UTC**

**Iteration 1 agent task** (paste verbatim — do not modify):

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite engineer + Senior responsive CSS engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/cp_mobile_native.md
YOUR SCOPE: Iteration 1 only — Epic E1. Do not touch any other plan.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute stories in this order: E1-S1 → E1-S2 → E1-S3 → E1-S4 → E1-S5
6. After the final story, run the Docker test command in Rule 5, open the iteration PR against main, post the PR URL, and HALT.
```

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas

Use the personas listed in the task block before editing any code.

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/cp-mobile-1-it1-e1
git commit --allow-empty -m "chore(cp-mobile-1): start iteration 1"
git push origin feat/cp-mobile-1-it1-e1

gh pr create \
  --base main \
  --head feat/cp-mobile-1-it1-e1 \
  --draft \
  --title "tracking: CP-MOBILE-1 Iteration 1 — in progress" \
  --body "## tracking: CP-MOBILE-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Phone customer can open and close portal navigation
- [ ] [E1-S2] Phone customer can use header controls without crowding
- [ ] [E1-S3] Phone customer can use My Agents and Goals Setup without overflow
- [ ] [E1-S4] Phone customer can use Trial Dashboard, Inbox, and Profile Settings without overflow
- [ ] [E1-S5] Responsive regressions are covered and iteration is docker-validated

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline

One epic = one branch. Iteration 1 uses `feat/cp-mobile-1-it1-e1`.

### Rule 2 — Scope lock

Implement only the acceptance criteria in the story card. Do not add new backend APIs, do not modify Plant or PP, and do not redesign unrelated CP pages.

### Rule 3 — Tests before the next story

Run the exact test command listed in the story card before moving to the next story.

### Rule 4 — Commit + push + notify after every story

```bash
git add -A
git commit -m "feat(cp-mobile-1): [story title]"
git push origin feat/cp-mobile-1-it1-e1

git add docs/mobile/iterations/cp_mobile_native.md
git commit -m "docs(cp-mobile-1): mark [story-id] done"
git push origin feat/cp-mobile-1-it1-e1
```

### Rule 5 — Docker integration test after the epic

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```

### Rule 6 — STUCK PROTOCOL

After 3 failed fix attempts on the same blocker:

```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/cp-mobile-1-it1-e1
```

Post the exact blocker and halt.

### Rule 7 — Iteration PR

```bash
git checkout main && git pull
git checkout -b feat/cp-mobile-1-it1
git merge --no-ff feat/cp-mobile-1-it1-e1
git push origin feat/cp-mobile-1-it1

gh pr create \
  --base main \
  --head feat/cp-mobile-1-it1 \
  --title "feat(cp-mobile-1): mobile-native CP portal shell" \
  --body "## CP-MOBILE-1 Iteration 1

### Stories completed
[paste tracking table rows]

### Docker integration
All containers exited 0 ✅"
```

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | CP BackEnd stays a thin proxy only | Architecture violation |
| 2 | Existing `/cp/*` and `/api/v1/*` boundaries stay intact | Route drift |
| 3 | No env-specific values in frontend code or CSS | Promotion model drift |
| 4 | Existing help-toggle behavior must keep working | UX regression |
| 5 | Frontend must preserve loading, error, and empty states | Silent failures |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer can use the portal naturally on a phone | Phone customer can open and close portal navigation | 🟢 Done | — |
| E1-S2 | 1 | Customer can use the portal naturally on a phone | Phone customer can use header controls without crowding | 🔴 Not Started | — |
| E1-S3 | 1 | Customer can use the portal naturally on a phone | Phone customer can use My Agents and Goals Setup without overflow | 🔴 Not Started | — |
| E1-S4 | 1 | Customer can use the portal naturally on a phone | Phone customer can use Trial Dashboard, Inbox, and Profile Settings without overflow | 🔴 Not Started | — |
| E1-S5 | 1 | Customer can use the portal naturally on a phone | Responsive regressions are covered and iteration is docker-validated | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Customer can use the portal naturally on a phone

**Scope:** Signed-in CP customers can navigate, read, and act inside the existing authenticated portal on narrow screens without sidebar dead-ends, action crowding, or card overflow.
**Lane:** A — wire and refine the existing frontend shell and styling only.
**⏱ Estimated:** 5h | **Come back:** 2026-03-13 20:00 UTC
**Epics:** E1

### Dependency Map (Iteration 1)

```text
E1-S1 → E1-S2 → E1-S3 → E1-S4 → E1-S5
```

---

### Epic E1: Customer can use the portal naturally on a phone

**Branch:** `feat/cp-mobile-1-it1-e1`
**User story:** As a signed-in customer using a phone, I can open the CP portal, move between sections, and use key pages without horizontal overflow or desktop-only navigation.

---

#### Story E1-S1: Phone customer can open and close portal navigation

**BLOCKED UNTIL:** none
**Estimated time:** 60 min
**Branch:** `feat/cp-mobile-1-it1-e1`
**CP BackEnd pattern:** N/A — frontend shell only, no API change.

**What to do (self-contained — read this card, then act):**
> `src/CP/FrontEnd/src/main.tsx` line 6 imports only `globals.css`, which leaves `src/CP/FrontEnd/src/styles/responsive.css` unused even though that file already defines `.mobile-menu-toggle`, `.portal-overlay`, and `.portal-sidebar.open`. In `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx`, line 147 only tracks `sidebarCollapsed`, while lines 418–499 render a desktop collapse-only sidebar. Import the responsive stylesheet, add `mobileNavOpen` state, render a mobile menu trigger in the portal header, add an overlay close path, and ensure selecting a navigation item closes the mobile drawer while desktop collapse behavior still works.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/main.tsx` | 1–12 | Existing CSS imports |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | 124–520 | `sidebarCollapsed`, portal header, sidebar markup, nav item click behavior |
| `src/CP/FrontEnd/src/styles/responsive.css` | 1–160 | Existing mobile drawer classes that are currently dead |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/main.tsx` | modify | Import `./styles/responsive.css` immediately after `globals.css`. |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | modify | Add `mobileNavOpen` state, a menu button in the header, drawer/overlay classes, `aria` labels, and close-on-navigation behavior without removing the desktop collapse toggle. |
| `src/CP/FrontEnd/src/styles/responsive.css` | modify | Align the existing mobile drawer selectors to the real CP portal markup and ensure the overlay and menu button appear only on narrow screens. |

**Code patterns to copy exactly** (boundary rules — do not invent new service calls):

```typescript
// CP FrontEnd service boundary rule: keep existing backend boundaries untouched in this story.
import { gatewayRequestJson } from './gatewayApiClient'

export async function getResource(): Promise<ResourceData> {
  return gatewayRequestJson<ResourceData>('/cp/resource', { method: 'GET' })
}
```

```text
CP BackEnd thin-proxy rule:
- Do not add direct fetch calls to Plant from the component.
- Do not create CP BackEnd business logic for a layout-only story.
- Preserve existing `/cp/*` and `/api/v1/*` route usage exactly as-is.
```

**Acceptance criteria:**
- On narrow screens, a visible menu control opens the sidebar as an overlay drawer.
- Tapping outside the drawer closes it.
- Choosing a sidebar destination closes the drawer.
- On desktop widths, the existing collapsed sidebar behavior still works.

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test -- --run src/__tests__/AuthenticatedPortal.test.tsx
```

---

#### Story E1-S2: Phone customer can use header controls without crowding

**BLOCKED UNTIL:** E1-S1 committed and pushed
**Estimated time:** 45 min
**Branch:** `feat/cp-mobile-1-it1-e1`
**CP BackEnd pattern:** N/A — frontend shell only, no API change.

**What to do (self-contained — read this card, then act):**
> `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` lines 429–456 place chips, help toggle, theme toggle, and sign-out actions in one dense row. `src/CP/FrontEnd/src/styles/globals.css` lines 1620–1815 and 2270–2765 collapse some spacing but do not give the portal header a mobile-first action stack. Rework the header action grouping and responsive styles so the shell still exposes help/theme/sign-out on phones without overflow or clipped controls.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | 418–520 | Header action order, chips, toggles, sign-out |
| `src/CP/FrontEnd/src/styles/globals.css` | 1620–1815 | Portal shell base styles |
| `src/CP/FrontEnd/src/styles/globals.css` | 2270–2765 | Existing responsive portal rules |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | modify | Wrap chips and controls into mobile-friendly groups and keep current labels/test ids intact. |
| `src/CP/FrontEnd/src/styles/globals.css` | modify | Add mobile rules for stacked or wrapped header controls, preserved help-box toggle visibility, and touch-friendly spacing. |

**Code patterns to copy exactly** (boundary rules — do not widen scope):

```text
Frontend-only scope rule:
- Keep this story inside CP FrontEnd.
- No edits in src/CP/BackEnd/, src/Plant/, src/PP/, Docker, Terraform, or workflows.
- Preserve existing component props and test ids unless the story explicitly requires a new one.
```

**Acceptance criteria:**
- Header controls remain fully visible and tappable at phone widths.
- Help toggle, theme toggle, and sign-out remain reachable without horizontal scrolling.
- Existing desktop header appearance stays intact.

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test -- --run src/__tests__/AuthenticatedPortal.test.tsx
```

---

#### Story E1-S3: Phone customer can use My Agents and Goals Setup without overflow

**BLOCKED UNTIL:** E1-S2 committed and pushed
**Estimated time:** 60 min
**Branch:** `feat/cp-mobile-1-it1-e1`
**CP BackEnd pattern:** N/A — existing services only, no API change.

**What to do (self-contained — read this card, then act):**
> `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` line 1914 still uses `minWidth: '300px'`, and `src/CP/FrontEnd/src/pages/authenticated/GoalsSetup.tsx` lines 301 and 331 still enforce 260–320px layout assumptions. Replace these desktop-biased widths with phone-safe flex/grid behavior so card content wraps inside the viewport instead of forcing horizontal overflow.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1881–1970 | Agent summary row and card width assumptions |
| `src/CP/FrontEnd/src/pages/authenticated/GoalsSetup.tsx` | 258–345 | Goal form grid and `minWidth` constraints |
| `src/CP/FrontEnd/src/__tests__/GoalsSetup.test.tsx` | 1–220 | Existing expectations that may need responsive-safe updates |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Remove hard minimum widths that exceed small viewports and allow summary/action blocks to wrap. |
| `src/CP/FrontEnd/src/pages/authenticated/GoalsSetup.tsx` | modify | Replace fixed min widths and wide auto-fit values with narrower mobile-safe values while preserving content hierarchy. |
| `src/CP/FrontEnd/src/__tests__/GoalsSetup.test.tsx` | modify | Update or add assertions only if rendering changes break existing expectations. |

**Code patterns to copy exactly** (frontend regression rule):

```text
Responsive regression rule:
- Prefer wrapping and narrower `minmax()` values over fixed `minWidth` pixels.
- Keep semantic content order unchanged so existing tests and accessibility labels remain stable.
- Preserve all existing data-fetching, loading, error, and empty states exactly as-is.
```

**Acceptance criteria:**
- My Agents content fits within 360px-wide screens without horizontal scrolling.
- Goals Setup cards and forms stack cleanly on phones.
- Existing behavior on tablet and desktop remains readable.

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test -- --run src/__tests__/GoalsSetup.test.tsx src/__tests__/MyAgents.test.tsx
```

---

#### Story E1-S4: Phone customer can use Trial Dashboard, Inbox, and Profile Settings without overflow

**BLOCKED UNTIL:** E1-S3 committed and pushed
**Estimated time:** 60 min
**Branch:** `feat/cp-mobile-1-it1-e1`
**CP BackEnd pattern:** N/A — existing services only, no API change.

**What to do (self-contained — read this card, then act):**
> `src/CP/FrontEnd/src/pages/TrialDashboard.tsx` lines 271 and 318, `src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx` lines 85 and 135, and `src/CP/FrontEnd/src/pages/authenticated/ProfileSettings.tsx` line 220 still encode desktop-oriented minimum widths. Replace those constraints with mobile-safe wrapping so the dashboard panels, inbox cards, and profile modal content stay inside the viewport at phone widths.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/TrialDashboard.tsx` | 240–340 | Fixed-width dashboard columns |
| `src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx` | 70–160 | Card grids and flex children with min widths |
| `src/CP/FrontEnd/src/pages/authenticated/ProfileSettings.tsx` | 200–320 | Modal card width assumptions |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/TrialDashboard.tsx` | modify | Allow the main dashboard columns to wrap at phone widths without clipped text. |
| `src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx` | modify | Narrow the grid minima and remove flex child widths that force overflow. |
| `src/CP/FrontEnd/src/pages/authenticated/ProfileSettings.tsx` | modify | Replace the modal card minimum width with viewport-safe sizing while keeping the desktop max width. |

**Code patterns to copy exactly** (frontend regression rule):

```text
Viewport safety rule:
- No new fixed widths wider than the target phone viewport.
- Use width: 100% with max-width constraints instead of hard minWidth where possible.
- Preserve existing copy, icons, and component structure unless viewport safety requires a wrapper.
```

**Acceptance criteria:**
- Trial Dashboard panels stack or wrap cleanly on narrow screens.
- Inbox cards and summaries stay within viewport width.
- Profile Settings opens without forcing sideways scrolling.

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test -- --run src/test/App.test.tsx
```

---

#### Story E1-S5: Responsive regressions are covered and iteration is docker-validated

**BLOCKED UNTIL:** E1-S4 committed and pushed
**Estimated time:** 45 min
**Branch:** `feat/cp-mobile-1-it1-e1`
**CP BackEnd pattern:** N/A — test and validation story only.

**What to do (self-contained — read this card, then act):**
> Extend the CP frontend regression suite so the mobile shell changes are asserted instead of relying on visual inspection. Use `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` for the portal shell behavior, and add or adjust focused assertions in existing CP frontend tests only where required by the responsive work. After focused Vitest passes, run the Docker regression command for the repo and keep the plan tracking table current.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | 1–260 | Existing sidebar/help-toggle assertions to extend for mobile navigation |
| `src/CP/FrontEnd/src/__tests__/GoalsSetup.test.tsx` | 1–220 | Existing responsive-safe behavior expectations |
| `src/CP/FrontEnd/src/test/App.test.tsx` | 1–220 | Broader app smoke coverage touched by portal shell imports |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | modify | Add assertions for the mobile menu trigger, drawer open/close behavior, and preserved help toggle rendering. |
| `src/CP/FrontEnd/src/__tests__/GoalsSetup.test.tsx` | modify | Adjust only if responsive layout changes alter stable render assumptions. |
| `docs/mobile/iterations/cp_mobile_native.md` | modify | Mark completed stories as `🟢 Done` as execution proceeds. |

**Code patterns to copy exactly** (frontend test rule):

```text
Frontend test rule:
- Assert behavior, not CSS pixel values.
- Verify the mobile menu control exists, opens the drawer, and closes on user action.
- Keep tests focused on CP FrontEnd and do not mock new backend behavior for a layout-only change.
```

**Acceptance criteria:**
- Focused CP frontend tests pass for the mobile portal shell.
- The full Docker regression command for the repo exits 0, or a concrete blocker is recorded with STUCK PROTOCOL.
- The tracking table in this plan reflects completed stories.

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test -- --run src/__tests__/AuthenticatedPortal.test.tsx src/__tests__/GoalsSetup.test.tsx src/test/App.test.tsx
```