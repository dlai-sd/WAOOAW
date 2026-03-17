# CP-STUDIO-1 — My Agents Inline Activation Studio Iteration Plan

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | CP-STUDIO-1 |
| Feature area | Customer Portal FrontEnd — My Agents activation and hire handoff |
| Created | 2026-03-17 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | defect_list_8_Mar_2026.md |
| Platform index | docs/CONTEXT_AND_INDEX.md (file map §13) |
| Total iterations | 1 |
| Total epics | 1 |
| Total stories | 5 |

## Vision Intake

- Area: CP FrontEnd first, with Hire Receipt and Authenticated Portal handoff behavior inside the customer portal.
- Outcome: A customer who hires an agent lands in My Agents and completes identity and YouTube setup inline, without being bounced into a separate setup screen.
- Out of scope: Rebuilding Plant runtime logic, removing the large My Agents top banner, or deleting HireSetupWizard.tsx entirely.
- Lane: Lane A — wire existing APIs only; use current CP services and My Agents data contracts rather than introducing new backend endpoints.
- Urgency: One iteration only, sized so a single merge delivers the corrected surface and journey.

## Zero-Cost Agent Constraints

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained and names exact file paths and line ranges |
| No working memory across files | Shell patterns and handoff snippets are embedded inline in each story |
| No planning ability | Stories are sequential, atomic, and stay on one epic branch |
| Token cost per file read | Max 3 files to read per story |
| Binary inference only | Acceptance criteria are observable pass/fail behaviors |

## PM Review Checklist

- [x] EXPERT PERSONAS filled
- [x] Epic title names a customer outcome, not a technical action
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant code snippets inline
- [x] Every story card has max 3 files in Files to read first
- [x] Every CP story states the exact pattern: A, B, C, or N/A
- [x] Every new backend route story embeds waooaw_router when needed
- [x] Every GET route story says get_read_db_session when needed
- [x] Every story that adds env vars lists exact Terraform file paths to update when needed
- [x] Every story has BLOCKED UNTIL or none
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Stories are sequenced so dependencies stay on the same branch
- [x] Iteration count minimized for PR-only delivery
- [x] Related handoff and studio work kept in the same iteration
- [x] No placeholders remain

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — move hire handoff and activation editing into a single My Agents inline studio using existing CP services | 1 | 5 | 5.5h | 2026-03-17 21:00 UTC |

**Estimate basis:** FE wiring = 30 min | UI shell refactor = 90 min | regression and Playwright pass = 60 min | 20% buffer included.

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
3. Click the model dropdown at the top of the chat panel and select Agent mode
4. Click `+` to start a new agent session
5. Type `@` and select platform-engineer
6. Paste the block below and press Enter
7. Go away and come back at 2026-03-17 21:00 UTC

**Iteration 1 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite engineer + Senior UX systems engineer
Activate these personas NOW. Begin the epic with:
  "Acting as a senior React and UX engineer, I will implement the My Agents inline studio by following the current story card and its exact test command."

PLAN FILE: docs/CP/iterations/CP-STUDIO-1-my-agents-inline-studio.md
YOUR SCOPE: Iteration 1 only — Epic E1. Do not invent more epics or stories.
TIME BUDGET: 5.5h. If you reach 6.5h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the Agent Execution Rules section in this plan file.
3. Read the Iteration 1 section in this plan file.
4. Read nothing else before starting.
5. Execute stories in this order: E1-S1 -> E1-S2 -> E1-S3 -> E1-S4 -> E1-S5.
6. When all story tests pass, open the iteration PR, post the PR URL, and HALT.
```

### Iteration 2

No Iteration 2 is planned for CP-STUDIO-1. Do not create one unless a human explicitly splits the scope into a new plan revision.

## Agent Execution Rules

### Rule -1 — Activate Expert Personas

Read the EXPERT PERSONAS field from the task and activate them before any code changes.

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/cp-studio-1-it1-e1
git commit --allow-empty -m "chore(cp-studio-1): start iteration 1"
git push origin feat/cp-studio-1-it1-e1

gh pr create \
  --base main \
  --head feat/cp-studio-1-it1-e1 \
  --draft \
  --title "tracking: CP-STUDIO-1 Iteration 1 — in progress" \
  --body "## tracking: CP-STUDIO-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Carry studio entry state through the portal
- [ ] [E1-S2] Make payment handoff point only to My Agents
- [ ] [E1-S3] Adopt PP-style studio shell inside My Agents
- [ ] [E1-S4] Keep identity and YouTube edits inline
- [ ] [E1-S5] Prove the inline studio journey end to end

_Live updates posted as comments below._"
```

### Rule 1 — Branch discipline

One epic equals one branch. All five stories in this plan commit to `feat/cp-studio-1-it1-e1` sequentially.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card. Do not refactor unrelated CP pages, do not redesign other portal tabs, and do not add backend endpoints.

### Rule 3 — Tests before the next story

Write every test in the story card before moving to the next story. Run the exact command listed in the story card.

### Rule 4 — Commit, push, notify after every story

```bash
git add -A
git commit -m "feat(cp-studio-1): complete current story"
git push origin feat/cp-studio-1-it1-e1

git add docs/CP/iterations/CP-STUDIO-1-my-agents-inline-studio.md
git commit -m "docs(cp-studio-1): mark current story done"
git push origin feat/cp-studio-1-it1-e1

gh pr comment \
  $(gh pr list --head feat/cp-studio-1-it1-e1 --json number -q '.[0].number') \
  --body "✅ Current story done — $(git rev-parse --short HEAD)
Files changed: see commit diff
Tests: current story test command passed
Next: proceed to the next story in plan order"
```

### Rule 5 — Docker integration check after the epic

```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/MyAgents.test.tsx src/__tests__/AuthenticatedPortal.test.tsx src/test/HireReceipt.test.tsx
cd src/CP/FrontEnd && npm run test:e2e -- hire-journey.spec.ts
```

### Rule 6 — STUCK PROTOCOL

After 3 failed attempts on the same story:

```bash
git add -A && git commit -m "WIP: current story blocked — paste exact error"
git push origin feat/cp-studio-1-it1-e1
gh pr create \
  --base main \
  --head feat/cp-studio-1-it1-e1 \
  --title "WIP: current story — blocked" \
  --draft \
  --body "Blocked on: paste failing test name
Error: paste exact error message
Attempted fixes:
1. paste what you tried first
2. paste what you tried second"
```

Post the draft PR URL and halt.

### Rule 7 — Iteration PR

```bash
git checkout main && git pull
git checkout -b feat/cp-studio-1-it1
git merge --no-ff feat/cp-studio-1-it1-e1
git push origin feat/cp-studio-1-it1

gh pr create \
  --base main \
  --head feat/cp-studio-1-it1 \
  --title "feat(cp-studio-1): iteration 1 — My Agents inline activation studio" \
  --body "## CP-STUDIO-1 Iteration 1

### Stories completed
- E1-S1 Carry studio entry state through the portal
- E1-S2 Make payment handoff point only to My Agents
- E1-S3 Adopt PP-style studio shell inside My Agents
- E1-S4 Keep identity and YouTube edits inline
- E1-S5 Prove the inline studio journey end to end

### Frontend verification
- Vitest targeted suite passed
- Playwright hire journey passed"
```

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | CP BackEnd remains a thin proxy only | Architecture drift |
| 2 | Use existing `gatewayRequestJson` contracts from CP FrontEnd services | Duplicate transport logic |
| 3 | Every data-fetching state shows loading, error, and empty handling | Silent failures |
| 4 | `X-Correlation-ID` continues to flow through existing CP clients | Broken tracing |
| 5 | PR targets `main` only | Work does not ship |

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer stays in My Agents from payment to setup | Carry studio entry state through the portal | 🔴 Not Started | — |
| E1-S2 | 1 | Customer stays in My Agents from payment to setup | Make payment handoff point only to My Agents | 🔴 Not Started | — |
| E1-S3 | 1 | Customer stays in My Agents from payment to setup | Adopt PP-style studio shell inside My Agents | 🔴 Not Started | — |
| E1-S4 | 1 | Customer stays in My Agents from payment to setup | Keep identity and YouTube edits inline | 🔴 Not Started | — |
| E1-S5 | 1 | Customer stays in My Agents from payment to setup | Prove the inline studio journey end to end | 🔴 Not Started | — |

## Iteration 1 — My Agents Inline Activation Studio

**Scope:** Customers resume paid setup inside My Agents, edit identity and YouTube requirements inline, and no longer detour into a separate setup wizard.
**Lane:** A — wire existing APIs only
**⏱ Estimated:** 5.5h | **Come back:** 2026-03-17 21:00 UTC
**Epics:** E1

### Dependency Map (Iteration 1)

```text
E1-S1 -> E1-S2 -> E1-S3 -> E1-S4 -> E1-S5
```

### Epic E1: Customer stays in My Agents from payment to setup

**Branch:** `feat/cp-studio-1-it1-e1`
**User story:** As a paying customer, I can finish activation from the My Agents operating surface, so that the handoff feels truthful and setup never fragments across disconnected screens.

#### Story E1-S1: Carry studio entry state through the portal

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/cp-studio-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` lines 60-183 already define `portalEntry` and derive `selectedAgentId`, but the state stops at page and agent identity. Extend that contract so the portal can carry `subscriptionId`, `studioStep`, and `studioFocus`, then update `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 1806-1868 to accept those values on first render and prefer the incoming subscription over localStorage or the first roster item.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | 60-183 | `PortalLocationState`, `portalEntry`, derived initial state, `renderPage()` |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1806-1868 | selected subscription bootstrapping and localStorage fallback |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | 303-324 | existing payment-confirmed banner expectations |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | modify | Add typed `studioStep` and `studioFocus` fields to the portal-entry contract and pass them into `<MyAgents />`. |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Extend props so initial subscription and initial studio state are honored exactly once during first load. |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | modify | Assert the portal keeps the user on My Agents while preserving the requested subscription and studio step. |

**Code patterns to copy exactly:**
```typescript
type StudioStep = 'identity' | 'platforms' | 'review'
type StudioFocus = 'identity' | 'youtube' | 'review'

type PortalEntry = {
  page: 'my-agents'
  agentId?: string
  subscriptionId?: string
  studioStep?: StudioStep
  studioFocus?: StudioFocus
  source?: JourneySource
}

const [studioStep, setStudioStep] = useState<StudioStep>(initialStudioStep ?? 'identity')
const [studioFocus, setStudioFocus] = useState<StudioFocus>(initialStudioFocus ?? 'identity')
```

**Acceptance criteria (binary pass/fail only):**
1. Entering the portal with `portalEntry.subscriptionId` selects that exact hired agent in My Agents on first render.
2. Entering the portal with `studioStep` opens that step without changing the browser path to `/hire/setup/...`.
3. Existing fallback behavior still works when no portal-entry studio state is provided.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | Render portal with payment-confirmed journey context, subscription ID, and `studioStep: 'identity'` | My Agents receives the requested subscription and stays on portal flow |
| E1-S1-T2 | same | Render portal with no studio metadata | Existing My Agents landing behavior still renders |

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test:run -- src/__tests__/AuthenticatedPortal.test.tsx
```

**Commit message:** `feat(cp-studio-1): carry studio entry state through the portal`

**Done signal:** `E1-S1 done. Changed: AuthenticatedPortal, MyAgents, AuthenticatedPortal.test. Tests: T1 ✅ T2 ✅`

#### Story E1-S2: Make payment handoff point only to My Agents

**BLOCKED UNTIL:** E1-S1 committed to `feat/cp-studio-1-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/cp-studio-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/CP/FrontEnd/src/pages/HireReceipt.tsx` lines 83-118 still advertise a separate Continue Setup path, and `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` lines 394-402 still route the payment-confirmed banner back to `/hire/setup/{subscriptionId}`. Replace that detour with a single truthful handoff into My Agents setup, preserve the payment confirmation and support reference content, and create a focused receipt test so this regression cannot return.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/HireReceipt.tsx` | 1-120 | button layout and current Continue Setup navigation |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | 394-437 | payment-confirmed banner CTA |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | 303-324 | current resume-setup expectation |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/HireReceipt.tsx` | modify | Delete the `/hire/setup/...` navigation branch and make the primary action open My Agents with the correct portal-entry studio state. |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | modify | Change the payment-confirmed banner primary CTA so it reinforces My Agents as the setup surface. |
| `src/CP/FrontEnd/src/test/HireReceipt.test.tsx` | create | Add a focused render test that verifies payment confirmation routes to My Agents instead of `/hire/setup/...`. |

**Code patterns to copy exactly:**
```typescript
navigate('/portal', {
  state: {
    portalEntry: {
      page: 'my-agents',
      agentId,
      subscriptionId,
      source: 'payment-confirmed',
      studioStep: 'identity',
      studioFocus: 'identity',
    },
  },
})
```

**Acceptance criteria:**
1. Hire Receipt no longer contains a CTA that navigates to `/hire/setup/{subscriptionId}`.
2. The payment-confirmed banner inside AuthenticatedPortal opens My Agents setup, not the standalone hire wizard.
3. The receipt still shows order ID and subscription ID support references.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/CP/FrontEnd/src/test/HireReceipt.test.tsx` | Render receipt with subscription and agent query params, click primary CTA | `navigate('/portal', { state: { portalEntry: ... } })` is called |
| E1-S2-T2 | `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | Click payment-confirmed banner CTA | No `/hire/setup/...` navigation occurs |

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/HireReceipt.test.tsx src/__tests__/AuthenticatedPortal.test.tsx
```

**Commit message:** `feat(cp-studio-1): make payment handoff point only to My Agents`

**Done signal:** `E1-S2 done. Changed: HireReceipt, AuthenticatedPortal, HireReceipt.test. Tests: T1 ✅ T2 ✅`

#### Story E1-S3: Adopt PP-style studio shell inside My Agents

**BLOCKED UNTIL:** E1-S2 committed to `feat/cp-studio-1-it1-e1`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 2003-2216 currently use top-row section buttons and one large bordered card, which is why setup feels like a tabbed admin page instead of a studio. Use `src/PP/FrontEnd/src/pages/AgentSetupStudio.tsx` lines 337-384 and 626-633 plus `src/PP/FrontEnd/src/styles/globals.css` lines 610-818 as the reference contract, then rebuild only the My Agents setup surface into a stable shell with a left rail, descriptive header, scrollable middle body, and sticky bottom actions while leaving the big My Agents banner untouched.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/FrontEnd/src/pages/AgentSetupStudio.tsx` | 337-384, 626-633 | shell structure, left rail, canvas body, bottom action bar |
| `src/PP/FrontEnd/src/styles/globals.css` | 610-818 | grid shell, sticky rail, scrollable body, sticky footer |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 2003-2216 | current page header, section buttons, configure area |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Replace the current configure tab layout with a studio shell that keeps selection controls above the shell and moves setup content into rail/header/body/action regions. |
| `src/CP/FrontEnd/src/styles/globals.css` | modify | Add CP-specific studio classes that mirror the PP shell behavior without changing unrelated portal styles. |

**Code patterns to copy exactly:**
```css
.cp-agent-studio-shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 1.5rem;
}

.cp-agent-studio-rail {
  position: sticky;
  top: 1.5rem;
  align-self: start;
}

.cp-agent-studio-canvas-body {
  flex: 1;
  overflow-y: auto;
}

.cp-agent-studio-action-bar {
  position: sticky;
  bottom: 0;
}
```

**Acceptance criteria:**
1. My Agents setup shows a left step rail, top descriptive pane, scrollable middle content, and sticky bottom navigation.
2. The big top My Agents banner remains visible outside the studio shell.
3. Switching steps changes content inside the shell without resizing the overall page into a series of disjoint cards.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S3-T1 | `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | Render MyAgents with one hired marketing agent | Step rail labels render alongside the selected subscription UI |
| E1-S3-T2 | same | Click a different studio step | The step-specific heading changes in place |

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/MyAgents.test.tsx
```

**Commit message:** `feat(cp-studio-1): adopt pp-style studio shell inside My Agents`

**Done signal:** `E1-S3 done. Changed: MyAgents, globals.css, MyAgents.test. Tests: T1 ✅ T2 ✅`

#### Story E1-S4: Keep identity and YouTube edits inline

**BLOCKED UNTIL:** E1-S3 committed to `feat/cp-studio-1-it1-e1`
**Estimated time:** 90 min
**Branch:** `feat/cp-studio-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 240-393 already have `ConfigureAgentPanel`, and lines 1120-1709 already compute digital-marketing review actions and YouTube readiness, but the review actions still send users away from the real operating surface. Rewire those actions so identity and YouTube setup change the active studio step locally, keep the fields editable inside the studio body, and stop rendering the `DigitalMarketingBriefSummaryCard` summary clutter inside this activation path.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 240-393 | `ConfigureAgentPanel` inputs and save behavior |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1120-1709 | review action generation, approval card path, Open YouTube setup behavior |
| `src/CP/FrontEnd/src/components/PlatformConnectionsPanel.tsx` | 135-280 | inline platform connection loading and connect/remove flow |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Replace any `navigate('/hire/setup/...')` review actions with local studio-step transitions, render ConfigureAgentPanel in the identity step, and render platform connection / YouTube connection guidance in the platform step. |
| `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | modify | Flip existing route-jump tests so they assert inline step changes and no navigation calls. |

**Code patterns to copy exactly:**
```typescript
const openStudioStep = (step: StudioStep, focus: StudioFocus) => {
  setActiveSection('configure')
  setStudioStep(step)
  setStudioFocus(focus)
}

// Review actions
onClick={() => openStudioStep('identity', 'identity')}
onClick={() => openStudioStep('platforms', 'youtube')}
```

**Acceptance criteria:**
1. Clicking Open identity setup switches the My Agents studio to the identity step and exposes editable fields there.
2. Clicking Open YouTube setup switches the My Agents studio to the platform step and keeps the user on My Agents.
3. The setup summary clutter card is removed from this activation flow.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S4-T1 | `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | Open a deliverable review card and click Open identity setup | Identity step content becomes active and `navigate` is not called |
| E1-S4-T2 | same | Click Open YouTube setup | Platform step content becomes active and `navigate` is not called |
| E1-S4-T3 | same | Render marketing activation path | Brief summary clutter card is absent from the setup shell |

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/MyAgents.test.tsx
```

**Commit message:** `feat(cp-studio-1): keep identity and youtube edits inline`

**Done signal:** `E1-S4 done. Changed: MyAgents, MyAgents.test. Tests: T1 ✅ T2 ✅ T3 ✅`

#### Story E1-S5: Prove the inline studio journey end to end

**BLOCKED UNTIL:** E1-S4 committed to `feat/cp-studio-1-it1-e1`
**Estimated time:** 60 min
**Branch:** `feat/cp-studio-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/CP/FrontEnd/src/test/MyAgents.test.tsx` lines 155-240 and 400-625 still encode the old route-jump assumptions, `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` lines 303-324 still expect the payment-confirmed banner to leave the portal, and `src/CP/FrontEnd/e2e/hire-journey.spec.ts` lines 462-519 still wait for `/hire/setup/{subscriptionId}`. Rewrite those assertions so the regression suite proves the customer now resumes on `/portal`, lands inside My Agents, and opens inline setup steps instead of a detached wizard.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | 155-240, 400-625 | route-jump tests and marketing review action assertions |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | 303-324 | payment-confirmed banner expectation |
| `src/CP/FrontEnd/e2e/hire-journey.spec.ts` | 462-519 | post-payment flow and URL assertions |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | modify | Replace every `/hire/setup/...` assertion with inline studio-step assertions. |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | modify | Assert the banner CTA keeps the flow inside `/portal`. |
| `src/CP/FrontEnd/e2e/hire-journey.spec.ts` | modify | Resume from receipt into My Agents and validate inline setup navigation rather than a standalone wizard URL. |

**Code patterns to copy exactly:**
```typescript
await page.waitForURL(/\/portal/)
await expect(page.getByText('My Agents')).toBeVisible()
await page.getByRole('button', { name: 'Open YouTube setup' }).click()
await expect(page.getByText(/platform connections/i)).toBeVisible()
```

**Acceptance criteria:**
1. Targeted Vitest coverage passes with My Agents and AuthenticatedPortal expecting portal-based inline setup.
2. The hire journey Playwright spec no longer waits for `/hire/setup/{subscriptionId}`.
3. The E2E path verifies at least one inline setup action inside My Agents after payment confirmation.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S5-T1 | `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | Run updated marketing flow test | No `navigate('/hire/setup/...')` assertion remains |
| E1-S5-T2 | `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | Run payment-confirmed banner test | Portal CTA keeps the user on `/portal` |
| E1-S5-T3 | `src/CP/FrontEnd/e2e/hire-journey.spec.ts` | Run hire journey | Post-payment path resumes in My Agents and opens inline setup |

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test:run -- src/test/MyAgents.test.tsx src/__tests__/AuthenticatedPortal.test.tsx src/test/HireReceipt.test.tsx
cd src/CP/FrontEnd && npm run test:e2e -- hire-journey.spec.ts
```

**Commit message:** `feat(cp-studio-1): prove the inline studio journey end to end`

**Done signal:** `E1-S5 done. Changed: MyAgents.test, AuthenticatedPortal.test, hire-journey.spec. Tests: T1 ✅ T2 ✅ T3 ✅`