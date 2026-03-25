# MOBILE-COMP-1 — Mobile CP Compliance Iteration Plan

## Objective

Bring the mobile application into practical compliance with CP web for the highest-value customer journeys in one iteration: discover, hire, connect, operate, review, and manage subscriptions from a truthful mobile experience on both Android and iOS builds in Expo. The iteration focuses on removing dead ends, replacing placeholder state with live state, and aligning information architecture so mobile behaves like a reliable CP companion instead of a partially wired shell.

## Authoritative Defect List

This plan uses the previously identified mobile-vs-CP defect set as the authoritative defect list.

| Defect ID | Root cause | Impact | Best possible solution/fix |
|---|---|---|---|
| D1 | `HireWizard` exists in navigation types and deep links but is not registered in `MainNavigator` | Customers can hit a dead-end or inconsistent hire path from discover surfaces | Register the route in the correct stack, align typed params, and add navigation regression tests |
| D2 | `ConnectorSetupCard` uses local `isConnected` state only | Platform connection appears successful on mobile without any real backend truth | Replace the fake connector step with truthful preflight guidance and route customers into real post-hire connection surfaces |
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
| E1 | E1-S2 | Replace fake platform connect with truthful hire handoff | Not started | `feat/MOBILE-COMP-1-it1-e1` | Extend hire wizard and connector tests |
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

- [x] EXPERT PERSONAS filled for mobile execution
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant code patterns inline
- [x] Every story card has max 3 files in “Files to read first”
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet when applicable (none planned)
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()` when applicable (none planned)
- [x] Every story that adds env vars lists the exact Terraform files to update when applicable (none planned)
- [x] Every story has `BLOCKED UNTIL` or `none`
- [x] Iteration has time estimate and come-back datetime
- [x] Iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [x] No placeholders remain

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
  "Acting as a Mobile app designer expert in UI UX using Expo.dev for front end and a Senior React 18 / TypeScript / Fluent UI engineer, I will deliver the epic outcome by implementing the exact story scope and validation steps in this plan."

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

> *"Acting as a Mobile app designer expert in UI UX using Expo.dev for front end and a Senior React 18 / TypeScript / Fluent UI engineer, I will deliver the epic outcome by implementing the exact story scope and validation steps in this plan."*

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
- [ ] E1-S2 Replace fake platform connect with truthful hire handoff
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

**Outcome:** A customer can start from discovery, enter the mobile hire journey, see truthful setup expectations, and land in a real post-hire destination without fake connection states.

### E1-S1 — Restore hire-route and navigation parity

**Story size**: 45 min  
**Branch**: `feat/MOBILE-COMP-1-it1-e1`  
**BLOCKED UNTIL**: none

#### Context

`HireWizard` is declared in `src/mobile/src/navigation/types.ts`, used by discover surfaces, and mapped in deep links, but it is not registered in `src/mobile/src/navigation/MainNavigator.tsx`. This is a pure Lane A mobile fix: no backend changes, no new endpoint, just route registration, typed param alignment, and regression coverage so the path works on Android and iOS alike.

#### Files to read first (max 3)
1. `src/mobile/src/navigation/MainNavigator.tsx`
2. `src/mobile/src/navigation/types.ts`
3. `src/mobile/src/screens/discover/AgentDetailScreen.tsx`

#### Files to create / modify

| File | Purpose |
|---|---|
| `src/mobile/src/navigation/MainNavigator.tsx` | Register `HireWizard` in the Discover stack |
| `src/mobile/src/navigation/types.ts` | Keep typed params and deep-link config aligned |
| `src/mobile/__tests__/navigation.test.ts` | Add regression for the route registration |
| `src/mobile/__tests__/hireWizardScreen.test.tsx` | Add entry-path regression from discover flow |

#### Code patterns to copy exactly

**Typed screen registration pattern**
```tsx
<DiscoverStack.Navigator
  screenOptions={{
    headerShown: false,
    contentStyle: { backgroundColor: colors.black },
  }}
>
  <DiscoverStack.Screen name="Discover" component={DiscoverScreen} />
  <DiscoverStack.Screen name="AgentDetail" component={AgentDetailScreen} />
</DiscoverStack.Navigator>
```

**Typed route declaration pattern**
```ts
export type DiscoverStackParamList = {
  Discover: undefined;
  AgentDetail: { agentId: string };
  HireWizard: { agentId: string; step?: number };
  SearchResults: { query: string };
  FilterAgents: {
    industry?: string;
    minRating?: number;
    maxPrice?: number;
  };
};
```

#### What to build

Register `HireWizard` in the Discover stack, keep the typed route and linking config in sync, and verify that discover surfaces navigate there without `any`-based drift or missing-screen runtime failures. Preserve existing dark theme, safe-area spacing, and tab ownership; this story is about route integrity, not redesign.

#### Test plan

1. Extend `src/mobile/__tests__/navigation.test.ts` to assert `HireWizard` is mounted in the Discover stack.
2. Extend `src/mobile/__tests__/hireWizardScreen.test.tsx` to assert the discover path reaches the wizard with the expected `agentId`.
3. Run:

```bash
cd src/mobile && npm run typecheck
cd src/mobile && npm test -- --runInBand __tests__/navigation.test.ts __tests__/hireWizardScreen.test.tsx
```

#### Acceptance criteria
- [ ] Discover stack registers `HireWizard`
- [ ] Agent detail “hire” path navigates to the wizard without runtime errors
- [ ] Deep-link config remains aligned with the route name and params
- [ ] Android and iOS layout remain unchanged except for the route becoming reachable
- [ ] `npm run typecheck` exits 0

### E1-S2 — Replace fake platform connect with truthful hire handoff

**Story size**: 75 min  
**Branch**: `feat/MOBILE-COMP-1-it1-e1`  
**BLOCKED UNTIL**: E1-S1 committed

#### Context

The current `HireWizardScreen` shows a local “connected” state in step 2 via `ConnectorSetupCard`, but at that moment the customer does not yet have a real runtime or persisted platform connection. This creates false confidence. This story is still Lane A: do not invent pre-hire connection writes. Instead, make the step honest, explain that connection becomes real only after the runtime exists, and hand the customer into a real next destination after trial start.

#### Files to read first (max 3)
1. `src/mobile/src/screens/hire/HireWizardScreen.tsx`
2. `src/mobile/src/components/ConnectorSetupCard.tsx`
3. `src/mobile/src/screens/agents/TrialDashboardScreen.tsx`

#### Files to create / modify

| File | Purpose |
|---|---|
| `src/mobile/src/screens/hire/HireWizardScreen.tsx` | Remove fake connected success state and route the user to a truthful post-hire destination |
| `src/mobile/src/components/ConnectorSetupCard.tsx` | Recast the card as preflight guidance instead of local success simulation |
| `src/mobile/__tests__/connectorSetupCard.test.tsx` | Assert no fake connected state is produced from local toggle only |
| `src/mobile/__tests__/hireWizardFourSteps.test.tsx` | Assert post-trial handoff uses the real returned identifier |

#### Code patterns to copy exactly

**Truthful CP-style runtime handoff pattern**
```ts
navigation.navigate('TrialDashboard', {
  trialId: result.subscription_id,
  subscriptionId: result.subscription_id,
});
```

**Existing live platform-summary capability to keep in mind**
```ts
const response = await cpApiClient.get<PlatformConnection[]>(
  `/cp/hired-agents/${encodeURIComponent(hiredAgentId)}/platform-connections`
);
return response.data || [];
```

#### What to build

Remove the fake “connected / disconnected” success pattern from the pre-hire step. Replace it with honest preflight guidance that explains what platform will need to be connected and when. After successful trial creation, send the customer to a real runtime destination using the returned subscription identifier so the next action happens in truthful runtime state. If a follow-up CTA is needed, it should point into `TrialDashboard` or the existing hired-agent flow, not a local-only step state.

#### Test plan

1. Update `connectorSetupCard.test.tsx` so the component is validated as a truthful guidance card, not a fake persisted connection toggle.
2. Update `hireWizardFourSteps.test.tsx` to assert successful completion navigates using the returned subscription/runtime identifier.
3. Run:

```bash
cd src/mobile && npm test -- --runInBand __tests__/connectorSetupCard.test.tsx __tests__/hireWizardFourSteps.test.tsx __tests__/hireWizardScreen.test.tsx
```

#### Acceptance criteria
- [ ] Step 2 no longer presents local-only connected success as if the backend were updated
- [ ] Copy explains that real channel connection happens after runtime creation
- [ ] Successful trial start routes to a real destination using returned identifiers
- [ ] No fake persisted state survives a rerender or refresh
- [ ] Existing hire wizard tests stay green

## Epic E2 — Customer sees live action items instead of placeholder mobile state

**Outcome:** Notifications and home surfaces behave like a reliable CP companion, showing real work to review, real runtime cues, and honest loading, empty, and error states.

### E2-S1 — Replace demo notifications with live actionable inbox

**Story size**: 75 min  
**Branch**: `feat/MOBILE-COMP-1-it1-e2`  
**BLOCKED UNTIL**: E1-S2 committed

#### Context

`NotificationsScreen.tsx` currently renders a hard-coded `actionableNotifications` array. The mobile app already has enough live data to generate a truthful action center from hired-agent summary, trial status, and runtime-readiness cues without adding backend scope. This is Lane A with no new API endpoint: derive the list from existing hooks and preserve the existing deep-link behavior into `AgentOperations` where a runtime ID exists.

#### Files to read first (max 3)
1. `src/mobile/src/screens/profile/NotificationsScreen.tsx`
2. `src/mobile/src/hooks/useHiredAgents.ts`
3. `src/mobile/src/screens/agents/MyAgentsScreen.tsx`

#### Files to create / modify

| File | Purpose |
|---|---|
| `src/mobile/src/screens/profile/NotificationsScreen.tsx` | Replace demo notifications with a live derived inbox |
| `src/mobile/src/hooks/useHiredAgents.ts` or `src/mobile/src/hooks/useMobileActionCenter.ts` | Centralize derived mobile action items if needed |
| `src/mobile/__tests__/NotificationsScreen.test.tsx` | Assert loading, empty, error, and live-action states |

#### Code patterns to copy exactly

**Existing React Query freshness pattern**
```ts
return useQuery({
  queryKey: ['hiredAgents'],
  queryFn: () => hiredAgentsService.listMyAgents(),
  staleTime: 1000 * 60 * 2,
  gcTime: 1000 * 60 * 15,
  refetchOnWindowFocus: true,
  retry: 2,
  retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
});
```

**Existing AgentOperations deep-link pattern**
```ts
parentNavigation?.navigate('MyAgentsTab', {
  screen: target.screen,
  params: target.params,
});
```

#### What to build

Replace demo cards with derived live actions such as approvals needed, trial ending soon, configuration incomplete, connection health warnings, or recent publication readiness, based only on existing live hooks and services. The screen must show loading, empty, and error states honestly. Preserve current deep-link behavior into `AgentOperations` wherever the action can be tied to a runtime ID.

#### Test plan

1. Extend `NotificationsScreen.test.tsx` for loading, empty, and derived-action rendering.
2. Assert pressing a live action still routes to the correct `focusSection`.
3. Run:

```bash
cd src/mobile && npm test -- --runInBand __tests__/NotificationsScreen.test.tsx __tests__/AgentOperationsScreen.test.tsx
```

#### Acceptance criteria
- [ ] No hard-coded demo notification array remains in the rendered path
- [ ] Screen renders live loading, empty, and error states
- [ ] At least the top actionable states come from real hired-agent/runtime data
- [ ] Deep-link taps still route into the correct `AgentOperations` section
- [ ] The screen remains truthful on both Android and iOS layouts

### E2-S2 — Turn home into a live mobile cockpit

**Story size**: 60 min  
**Branch**: `feat/MOBILE-COMP-1-it1-e2`  
**BLOCKED UNTIL**: E2-S1 committed

#### Context

`HomeScreen.tsx` currently uses static pills, static priorities, and a timeout-based refresh. Customers need a real “Today” cockpit that reflects the same operational truth mobile already knows through hired-agent and runtime summary hooks. This story keeps the UI bold but makes the content factual.

#### Files to read first (max 3)
1. `src/mobile/src/screens/home/HomeScreen.tsx`
2. `src/mobile/src/hooks/useHiredAgents.ts`
3. `src/mobile/src/screens/agents/MyAgentsScreen.tsx`

#### Files to create / modify

| File | Purpose |
|---|---|
| `src/mobile/src/screens/home/HomeScreen.tsx` | Replace static pills/cards with live priority derivation |
| `src/mobile/__tests__/coreScreens.test.tsx` or `src/mobile/__tests__/App.test.tsx` | Cover mounted home states |
| `src/mobile/__tests__/agentHooks.test.tsx` or a home-specific test | Cover derived priorities and refresh behavior |

#### Code patterns to copy exactly

**Existing refresh / query usage direction**
```ts
const { data: hiredAgents, isLoading, error, refetch } = useHiredAgents();
```

**Existing tab-navigation helper direction**
```ts
const navigateToTab = React.useCallback(
  (tabName: 'DiscoverTab' | 'MyAgentsTab', screen: 'Discover' | 'MyAgents') => {
    navigation.getParent()?.navigate(tabName, { screen });
  },
  [navigation]
);
```

#### What to build

Replace static priority text and hard-coded pills with live counts and derived priorities from current hires, trial state, and runtime setup state. Replace the timeout refresh with real `refetch()` behavior. If there is no actionable data, render a useful empty state that points customers to Discover or My Agents instead of pretending there is work waiting.

#### Test plan

1. Add home-screen tests for live loaded state, empty state, and refresh callback.
2. Verify that quick actions still route correctly.
3. Run:

```bash
cd src/mobile && npm test -- --runInBand __tests__/coreScreens.test.tsx __tests__/agentHooks.test.tsx
```

#### Acceptance criteria
- [ ] Home pills and priorities are derived from live data, not hard-coded copy
- [ ] Pull-to-refresh triggers real refetch logic instead of `setTimeout`
- [ ] Empty state points to a valid next action
- [ ] Quick actions still navigate correctly
- [ ] No placeholder operational claims remain on the home screen

## Epic E3 — Customer can trust billing and shell navigation on mobile

**Outcome:** Subscription surfaces show real state, shell labels and routes are easier to act through, and the iteration exits with tests and test-asset docs updated.

### E3-S1 — Make billing and subscription state truthful

**Story size**: 75 min  
**Branch**: `feat/MOBILE-COMP-1-it1-e3`  
**BLOCKED UNTIL**: E2-S2 committed

#### Context

`SubscriptionManagementScreen.tsx` currently hard-codes the plan name, amount, renewal date, and a placeholder payment call using `agentId: 'current'`. Mobile already has subscription-adjacent live data through hired-agent summary and can add a lightweight service/hook if needed. This story is Lane A. Do not create fake billing data and do not trigger payment with placeholder identifiers.

#### Files to read first (max 3)
1. `src/mobile/src/screens/profile/SubscriptionManagementScreen.tsx`
2. `src/mobile/src/services/hiredAgents/hiredAgents.service.ts`
3. `src/mobile/src/types/hiredAgents.types.ts`

#### Files to create / modify

| File | Purpose |
|---|---|
| `src/mobile/src/screens/profile/SubscriptionManagementScreen.tsx` | Bind the screen to live subscription state |
| `src/mobile/src/services/subscriptions/subscriptions.service.ts` or `src/mobile/src/hooks/useSubscriptions.ts` | Add a lightweight live data path if current services are insufficient |
| `src/mobile/__tests__/useRazorpay.test.ts` | Ensure payment flow is only called with real identifiers |
| `src/mobile/__tests__/coreScreens.test.tsx` or a new subscription test | Assert truthful rendering states |

#### Code patterns to copy exactly

**Safe CP client usage pattern**
```ts
const response = await cpApiClient.get<MyAgentsSummaryResponse>('/cp/my-agents/summary');
return response.data.instances || [];
```

**Truthful payment trigger rule**
```ts
await processPayment({ agentId, planType: 'monthly', amount });
```

Use this pattern only with real identifiers and values. Never pass `'current'` or hard-coded money values.

#### What to build

Replace placeholder subscription copy with live state. If exact plan pricing is unavailable from current APIs, show truthful subscription status, billing period, and next action without inventing a fake plan tier. Hide or disable renewal/upgrade/payment actions unless the screen has real identifiers and values needed to call Razorpay correctly.

#### Test plan

1. Add tests for live loaded state, no-subscription state, and disabled/hidden CTA when payment context is incomplete.
2. Extend `useRazorpay.test.ts` or screen tests so placeholder IDs can no longer trigger payment.
3. Run:

```bash
cd src/mobile && npm test -- --runInBand __tests__/useRazorpay.test.ts __tests__/coreScreens.test.tsx
cd src/mobile && npm run typecheck
```

#### Acceptance criteria
- [ ] No hard-coded plan name, amount, or renewal date remains in the rendered screen path
- [ ] Payment flow is never triggered with placeholder identifiers or placeholder money values
- [ ] Screen shows truthful loaded, empty, and error states
- [ ] Customers can still reach the next correct action from the screen
- [ ] Typecheck stays green

### E3-S2 — Align shell parity across Android and iOS and close iteration docs

**Story size**: 60 min  
**Branch**: `feat/MOBILE-COMP-1-it1-e3`  
**BLOCKED UNTIL**: E3-S1 committed

#### Context

The mobile shell is visually strong but still drifts from CP in labels, route affordances, and action framing. The highest-value cleanup in this iteration is not a redesign; it is convergence: make the shell easier to understand, preserve Expo-safe Android and iOS layout behavior, and then update the existing mobile test-assets doc so the iteration lands cleanly.

#### Files to read first (max 3)
1. `src/mobile/src/navigation/MainNavigator.tsx`
2. `src/mobile/src/screens/profile/ProfileScreen.tsx`
3. `docs/testing/ExistingTestAssets.md`

#### Files to create / modify

| File | Purpose |
|---|---|
| `src/mobile/src/navigation/MainNavigator.tsx` | Tighten tab labels and parity wording |
| `src/mobile/src/screens/profile/ProfileScreen.tsx` | Align menu copy and next-action framing to CP outcomes |
| `src/mobile/src/screens/home/HomeScreen.tsx` or `src/mobile/src/screens/hire/HireWizardScreen.tsx` | Fix any Android/iOS spacing or safe-area issues discovered while executing the iteration |
| `src/mobile/__tests__/safeArea.test.tsx` | Keep Android and iOS layout expectations covered |
| `docs/testing/ExistingTestAssets.md` | Update the mobile row for the new or expanded tests added in this iteration |

#### Code patterns to copy exactly

**Safe-area app-shell pattern**
```tsx
<SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
  <ScrollView
    contentContainerStyle={{
      paddingHorizontal: spacing.screenPadding.horizontal,
      paddingVertical: spacing.screenPadding.vertical,
    }}
  >
```

**Tab label ownership pattern**
```tsx
<Tab.Screen
  name="MyAgentsTab"
  component={MyAgentsNavigator}
  options={{
    title: 'Ops',
    tabBarButtonTestID: 'mobile-my-agents-tab',
  }}
/>
```

Keep the structure, but update labels only if they improve CP parity and customer clarity.

#### What to build

Tighten shell wording so the tabs and profile menu speak more clearly in CP language, especially around My Agents, billing, and support routes. Fix any padding, footer, or scroll affordance issues found on Android and iOS while executing the iteration. Then update `docs/testing/ExistingTestAssets.md` to reflect the iteration’s new or expanded mobile tests before opening the final PR.

#### Test plan

1. Extend `safeArea.test.tsx` if any layout behavior changes.
2. Extend the nearest navigation or core screen tests if tab labels or menu flows change.
3. Update `docs/testing/ExistingTestAssets.md` after all mobile tests are green on this branch.
4. Run:

```bash
cd src/mobile && npm test -- --runInBand __tests__/safeArea.test.tsx __tests__/navigation.test.ts __tests__/coreScreens.test.tsx
cd src/mobile && npm run typecheck
```

#### Acceptance criteria
- [ ] Tab labels and profile action wording are clearer and closer to CP outcomes
- [ ] Android and iOS safe-area and scroll behavior remain correct after shell adjustments
- [ ] The iteration does not introduce clipped or unreachable footer/header actions
- [ ] `docs/testing/ExistingTestAssets.md` reflects the mobile test changes added in this iteration
- [ ] Iteration-wide typecheck and targeted Jest tests pass before PR creation