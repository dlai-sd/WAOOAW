# MOBILE-FUNC-1 — Mobile App Functional Completeness

| Field | Value |
|---|---|
| Plan ID | MOBILE-FUNC-1 |
| Created | 2025-07-18 |
| Status | Draft |
| Author | GitHub Copilot |
| Service area | `src/mobile/` (primarily); one story touches `src/Plant/` |
| Lane | A (Iterations 1-2 are pure mobile Lane A); Iteration 3 has one Lane B story (Plant endpoint) |
| Estimated total | ~7 h |

---

## PM Review Checklist

- [x] All placeholders filled — zero `[PLACEHOLDER]` remain
- [x] Every story is self-contained (exact file paths, 2-3 sentence context)
- [x] NFR code patterns embedded inline — no "see NFRReusable.md" references
- [x] Story sizes: 30 min (small fix), 45 min (single hook/service), 90 min (screen creation)
- [x] Max 6 stories per iteration
- [x] Lane A precedes Lane B — Iterations 1 & 2 are fully Lane A; Lane B story is Iteration 3 S8a
- [x] Lane B story (S8a) is in Iteration 3; its mobile counterpart (S8b) is marked BLOCKED UNTIL S8a merged

---

## Overview

### Background

The mobile app has six functional gaps that block real users from completing key journeys:

1. **F1 — Mock deliverables in Trial Dashboard**: `TrialDashboardScreen.tsx` (lines 75-124) uses a hardcoded `getMockDeliverables()` function with a `// TODO: Replace with API call when backend is ready` comment. The Plant Gateway `GET /api/v1/deliverables` endpoint already exists and is ready.
2. **F2 — Five navigation-registered screens have no `.tsx` file**: `SearchResults`, `FilterAgents` (in `DiscoverStackParamList`), `ActiveTrialsList`, `HiredAgentsList` (in `MyAgentsStackParamList`), and `Settings` (in `ProfileStackParamList`) are typed in `navigation/types.ts` but have no screen component. They are also not registered in `MainNavigator.tsx`, so navigating to them will crash the app.
3. **F3 — Four profile tab screens missing**: `Notifications`, `PaymentMethods`, `SubscriptionManagement`, `HelpCenter` are in `ProfileStackParamList` but have no `.tsx` file and are not registered in `ProfileNavigator` inside `MainNavigator.tsx`.
4. **F4 — Razorpay SDK commented out**: `src/mobile/src/services/payment/razorpay.service.ts` line 8 has `// import RazorpayCheckout from 'react-native-razorpay'; // REMOVED for demo build`, replaced by a stub that always returns `demo_payment_id`. Real payments are never processed.
5. **F5 — No push notifications**: No FCM token registration exists anywhere in the mobile codebase. Plant Gateway has no endpoint to store FCM tokens. The `Notifications` screen will be a placeholder; the actual notification registration requires a new Plant route (Lane B).
6. **F6 — EditProfile calls CP Backend directly**: `EditProfileScreen.tsx` line 23 imports `cpApiClient` and line 63 calls `await cpApiClient.patch('/cp/profile', payload)`. All other mobile screens call Plant Gateway via `apiClient`. The CP Backend is a thin proxy and the mobile should always go to Plant Gateway directly.

### Goal

After this plan is merged: Trial Dashboard shows real deliverables; all nine missing screens exist and are registered in the navigator; Razorpay processes real payments in UAT/prod; users can register for push notifications; and EditProfile calls Plant Gateway instead of CP Backend.

### Out of Scope

- Screen UI design polish beyond dark-theme scaffolding (placeholder content acceptable for missing screens that need design work)
- MOBILE-NFR-1 items (Sentry, retry, Apple Sign-In)
- Any PP or CP Backend changes unrelated to the FCM token endpoint

### Success Criteria

- [x] `TrialDashboardScreen.tsx` uses `useQuery` to call `GET /api/v1/deliverables?subscription_id=<trialId>` and renders real data
- [x] Navigating to `SearchResults`, `FilterAgents`, `ActiveTrialsList`, `HiredAgentsList`, `Settings` does not crash
- [x] Navigating to `Notifications`, `PaymentMethods`, `SubscriptionManagement`, `HelpCenter` does not crash
- [x] `razorpay.service.ts` uses the real `RazorpayCheckout` SDK import in non-dev builds
- [x] `POST /api/v1/customers/fcm-token` Plant Backend endpoint exists, is authenticated, and stores the token
- [x] Mobile app registers the FCM token with Plant Backend after successful sign-in
- [x] `EditProfileScreen.tsx` imports `apiClient` (not `cpApiClient`) and calls `PATCH /api/v1/customers/profile`
- [x] TypeScript compiles with zero errors after each iteration

---

## Dependencies

| Dependency | Notes |
|---|---|
| MOBILE-NFR-1 | Independent — can run in parallel. No ordering constraint. |
| Plant Gateway — `PATCH /api/v1/customers/profile` | Must already exist for S2 (F6 fix). Verify that this endpoint exists in `src/Plant/Gateway/` before implementing S2; if absent, S2 is blocked and must create it (Lane B). |
| `react-native-razorpay` in package.json | Already listed in `package.json`. S6 only removes the comment; no `npm install` required. |
| Firebase project config | Required for S8a/S8b (push notifications). `FIREBASE_CONFIG` keys are already in `environment.config.ts` interface — populate them in UAT/prod `.env` files. |
| Plant Backend — waooaw_router, get_db_session | S8a creates one new Plant Gateway route; must follow `waooaw_router()` factory and `get_db_session()` (write route, so not read-replica). |

---

## Epics & Time Estimates

| Epic | Stories | Est. Time |
|---|---|---|
| E1 — Real deliverables API | S1 | 45 min |
| E2 — Fix EditProfile to Plant Gateway | S2 | 30 min |
| E3 — Missing Discover screens | S3 | 90 min |
| E4 — Missing MyAgents + Settings screens | S4 | 90 min |
| E5 — Missing Profile convenience screens | S5 | 45 min |
| E6 — Restore Razorpay SDK | S6 | 30 min |
| E7 — PaymentMethods + SubscriptionManagement | S7 | 90 min |
| E8 — Push notification infrastructure | S8 | 90 min |

---

## Iteration 1 — Core data + navigation fixes (Lane A)

**Estimated time:** 2 h 45 min  
**Goal:** Wire real deliverables API, fix EditProfile routing bug, scaffold the two most-used missing screens.

---

### S1 — Replace mock deliverables with real API call

**Goal:** Remove `getMockDeliverables()` from `TrialDashboardScreen.tsx` and replace it with a React Query `useQuery` call to the Plant Gateway `GET /api/v1/deliverables` endpoint, passing `subscription_id` from `route.params.trialId`.

**Context:** `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` — lines 74-124 contain `getMockDeliverables()` and `const deliverables = getMockDeliverables()`. The Plant Gateway already exposes `GET /api/v1/deliverables` which accepts a `subscription_id` query parameter and returns an array matching the existing `Deliverable` type in `src/mobile/src/types/hiredAgents.types.ts`. The hook file `src/mobile/src/hooks/useHiredAgents.ts` is the correct place to add a `useDeliverables(subscriptionId)` hook following the same pattern as `useHiredAgent()` at lines 28-40 in that file.

**Files to edit:**
- `src/mobile/src/hooks/useHiredAgents.ts` — add `useDeliverables(subscriptionId: string)` hook
- `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` — replace mock with hook call

**Files to read first:**
- `src/mobile/src/hooks/useHiredAgents.ts` (full file — for pattern)
- `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` (full file — for integration)
- `src/mobile/src/types/hiredAgents.types.ts` (full file — for Deliverable type)

**Acceptance criteria:**
- [x] `useDeliverables(subscriptionId)` hook added to `useHiredAgents.ts`, calls `GET /api/v1/deliverables?subscription_id=<id>`, has `retry: 2` and `retryDelay: (i) => Math.min(1000 * Math.pow(2, i), 10000)`
- [x] `getMockDeliverables()` function removed from `TrialDashboardScreen.tsx`
- [x] `const deliverables = getMockDeliverables()` replaced with `const { data: deliverables = [], isLoading: delivLoading } = useDeliverables(trialId)`
- [x] Loading state handled (show spinner while `delivLoading`)
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// useHiredAgents.ts — add after the last existing hook:
const fetchDeliverables = async (subscriptionId: string): Promise<Deliverable[]> => {
  const response = await apiClient.get<Deliverable[]>('/api/v1/deliverables', {
    params: { subscription_id: subscriptionId },
  });
  return response.data;
};

export const useDeliverables = (subscriptionId: string) => {
  return useQuery({
    queryKey: ['deliverables', subscriptionId],
    queryFn: () => fetchDeliverables(subscriptionId),
    enabled: !!subscriptionId,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
  });
};

// TrialDashboardScreen.tsx — replace getMockDeliverables usage:
import { useHiredAgent, useDeliverables } from '@/hooks/useHiredAgents';

// Inside component, after the useHiredAgent call:
const { data: deliverables = [], isLoading: delivLoading } = useDeliverables(trialId);

// Where getMockDeliverables() was called:
// const deliverables = getMockDeliverables();  ← DELETE this line
// Use deliverables directly (already bound above)
```

---

### S2 — Fix EditProfileScreen to call Plant Gateway instead of CP Backend

**Goal:** Replace the `cpApiClient` import and call in `EditProfileScreen.tsx` with `apiClient` pointing at Plant Gateway's `PATCH /api/v1/customers/profile` endpoint, aligning with the architecture invariant that mobile screens must not call CP Backend directly.

**Context:** `src/mobile/src/screens/profile/EditProfileScreen.tsx` — line 23 imports `cpApiClient from '../../lib/cpApiClient'` and line 63 calls `await cpApiClient.patch('/cp/profile', payload)`. All other mobile screens call Plant Gateway via `src/mobile/src/lib/apiClient.ts`. CP Backend is a thin proxy layer and should not receive direct mobile traffic. The Plant Gateway `PATCH /api/v1/customers/profile` endpoint is the correct target. **Before implementing**: verify that `PATCH /api/v1/customers/profile` exists in `src/Plant/Gateway/app/api/`; if the file is absent, create a stub route file there first.

**Files to edit:**
- `src/mobile/src/screens/profile/EditProfileScreen.tsx` — swap import + call path

**Files to read first:**
- `src/mobile/src/screens/profile/EditProfileScreen.tsx` (full file)
- `src/mobile/src/lib/apiClient.ts` (lines 1-30 — for import path)

**Acceptance criteria:**
- [x] Line 23 import changed from `cpApiClient from '../../lib/cpApiClient'` to `apiClient from '../../lib/apiClient'`
- [x] The `cpApiClient` import is completely removed (no unused import)
- [x] Line 63 call changed from `cpApiClient.patch('/cp/profile', payload)` to `apiClient.patch('/api/v1/customers/profile', payload)`
- [x] No other logic in the file is changed
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// EditProfileScreen.tsx — replace line 23:
// REMOVE: import cpApiClient from '../../lib/cpApiClient';
// ADD:
import apiClient from '../../lib/apiClient';

// Line 63 — replace call:
// REMOVE: await cpApiClient.patch('/cp/profile', payload);
// ADD:
await apiClient.patch('/api/v1/customers/profile', payload);
```

---

### S3 — Create SearchResultsScreen + FilterAgentsScreen + register in navigator

**Goal:** Create the two missing Discover stack screens and register them in `DiscoverNavigator` inside `MainNavigator.tsx` so the app no longer crashes when navigating to `SearchResults` or `FilterAgents`.

**Context:** `src/mobile/src/navigation/types.ts` — `DiscoverStackParamList` (lines 74-86) defines `SearchResults: { query: string }` and `FilterAgents: { industry?, minRating?, maxPrice? }` but neither has a `.tsx` file and neither is registered in `DiscoverNavigator` (lines 62-77 of `MainNavigator.tsx`). `DiscoverScreen.tsx` in `src/mobile/src/screens/discover/` is the reference for dark-theme styling and `useTheme()` patterns. New screen files go under `src/mobile/src/screens/discover/`.

**Files to create:**
- `src/mobile/src/screens/discover/SearchResultsScreen.tsx`
- `src/mobile/src/screens/discover/FilterAgentsScreen.tsx`

**Files to edit:**
- `src/mobile/src/screens/discover/index.ts` — export new screens
- `src/mobile/src/navigation/MainNavigator.tsx` — register new screens in `DiscoverNavigator`

**Files to read first:**
- `src/mobile/src/screens/discover/DiscoverScreen.tsx` (full file — styling reference)
- `src/mobile/src/navigation/MainNavigator.tsx` (lines 60-80 — DiscoverNavigator block)
- `src/mobile/src/navigation/types.ts` (lines 68-92 — Discover types)

**Acceptance criteria:**
- [x] `SearchResultsScreen.tsx` renders a dark-theme (`colors.black` background) screen showing the `query` param and a placeholder agent list (can use mocked data for now; real search API is a separate story)
- [x] `FilterAgentsScreen.tsx` renders filter controls for `industry`, `minRating`, `maxPrice` with dark-theme styling
- [x] Both screens have a back-navigation header matching the existing `AgentDetailScreen` pattern
- [x] Both screens are exported from `src/mobile/src/screens/discover/index.ts`
- [x] Both screens are registered in `DiscoverNavigator` in `MainNavigator.tsx` using `<DiscoverStack.Screen />`
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// SearchResultsScreen.tsx — scaffold (follow DiscoverScreen.tsx pattern for styling):
import React from 'react';
import { View, Text, StyleSheet, SafeAreaView, FlatList } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { DiscoverStackScreenProps } from '@/navigation/types';

type Props = DiscoverStackScreenProps<'SearchResults'>;

export const SearchResultsScreen = ({ route, navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { query } = route.params;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <View style={{ padding: spacing.md }}>
        <Text style={[typography.heading2, { color: colors.white }]}>
          Results for "{query}"
        </Text>
        {/* TODO: wire to GET /api/v1/agents?search=query in a follow-on story */}
        <Text style={[typography.body, { color: colors.textSecondary, marginTop: spacing.sm }]}>
          Search results coming soon.
        </Text>
      </View>
    </SafeAreaView>
  );
};

// MainNavigator.tsx — add inside DiscoverNavigator after existing screens:
import { SearchResultsScreen, FilterAgentsScreen } from '../screens/discover';

<DiscoverStack.Screen name="SearchResults" component={SearchResultsScreen} />
<DiscoverStack.Screen name="FilterAgents" component={FilterAgentsScreen} />
```

---

## Iteration 2 — Remaining screens + Razorpay enable (Lane A)

**Estimated time:** 2 h 45 min  
**Goal:** Create the remaining five missing screens (ActiveTrialsList, HiredAgentsList, Settings, Notifications, HelpCenter); restore the real Razorpay SDK.

---

### S4 — Create ActiveTrialsListScreen + HiredAgentsListScreen + SettingsScreen

**Goal:** Create the three missing MyAgents and Profile stack screens and register them in their respective navigators.

**Context:** `src/mobile/src/navigation/types.ts` — `MyAgentsStackParamList` defines `ActiveTrialsList: undefined` and `HiredAgentsList: undefined` (lines 97-105). `ProfileStackParamList` defines `Settings: undefined` (line 109). Neither screen file exists. `MyAgentsScreen.tsx` in `src/mobile/src/screens/agents/` is the reference for the agents tab styling. `ProfileScreen.tsx` in `src/mobile/src/screens/profile/` is the reference for the profile tab styling. New agents-tab screens go in `src/mobile/src/screens/agents/`; the Settings screen goes in `src/mobile/src/screens/profile/`.

**Files to create:**
- `src/mobile/src/screens/agents/ActiveTrialsListScreen.tsx`
- `src/mobile/src/screens/agents/HiredAgentsListScreen.tsx`
- `src/mobile/src/screens/profile/SettingsScreen.tsx`

**Files to edit:**
- `src/mobile/src/screens/agents/index.ts` — export new screens
- `src/mobile/src/screens/profile/index.ts` — export `SettingsScreen` (create index.ts if missing)
- `src/mobile/src/navigation/MainNavigator.tsx` — register in `MyAgentsNavigator` and `ProfileNavigator`

**Files to read first:**
- `src/mobile/src/screens/agents/MyAgentsScreen.tsx` (first 60 lines — styling reference)
- `src/mobile/src/screens/profile/ProfileScreen.tsx` (first 60 lines — styling reference)
- `src/mobile/src/navigation/MainNavigator.tsx` (lines 78-115 — MyAgentsNavigator + ProfileNavigator blocks)
- `src/mobile/src/hooks/useHiredAgents.ts` (full file — for useActiveTrials / useHiredAgents hooks if they exist)

**Acceptance criteria:**
- [x] `ActiveTrialsListScreen.tsx` uses `useHiredAgents` hook filtered by `trial_status === 'active'` and renders a dark-theme list; falls back to a "No active trials" empty state
- [x] `HiredAgentsListScreen.tsx` uses `useHiredAgents` hook filtered by `status === 'hired'` and renders a dark-theme list; falls back to a "No hired agents" empty state
- [x] `SettingsScreen.tsx` renders a dark-theme list of preference items (notifications toggle, privacy policy link, terms link, sign-out); sign-out calls `authStore.signOut()`
- [x] All three screens exported from their respective `index.ts`
- [x] All three screens registered in the appropriate navigator in `MainNavigator.tsx`
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// ActiveTrialsListScreen.tsx — scaffold:
import React from 'react';
import { View, Text, FlatList, SafeAreaView, TouchableOpacity } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useHiredAgents } from '@/hooks/useHiredAgents';
import type { MyAgentsStackScreenProps } from '@/navigation/types';

type Props = MyAgentsStackScreenProps<'ActiveTrialsList'>;

export const ActiveTrialsListScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { data: agents = [], isLoading } = useHiredAgents();
  const activeTrials = agents.filter((a) => a.trial_status === 'active');

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <Text style={[typography.heading2, { color: colors.white, padding: spacing.md }]}>
        Active Trials
      </Text>
      <FlatList
        data={activeTrials}
        keyExtractor={(item) => item.hired_instance_id}
        ListEmptyComponent={
          <Text style={{ color: colors.textSecondary, padding: spacing.md }}>
            No active trials.
          </Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={{ padding: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.textSecondary + '30' }}
            onPress={() => navigation.navigate('TrialDashboard', { trialId: item.hired_instance_id })}
          >
            <Text style={{ color: colors.white }}>{item.agent_id}</Text>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
};

// MainNavigator.tsx — add inside MyAgentsNavigator:
import { MyAgentsScreen, TrialDashboardScreen, ActiveTrialsListScreen, HiredAgentsListScreen } from '../screens/agents';

<MyAgentsStack.Screen name="ActiveTrialsList" component={ActiveTrialsListScreen} />
<MyAgentsStack.Screen name="HiredAgentsList" component={HiredAgentsListScreen} />

// MainNavigator.tsx — add inside ProfileNavigator:
import { SettingsScreen } from '../screens/profile';

<ProfileStack.Screen name="Settings" component={SettingsScreen} />
```

---

### S5 — Create NotificationsScreen + HelpCenterScreen

**Goal:** Create the two simpler profile tab screens (notification preferences UI-only placeholder; help center with static content) and register them in `ProfileNavigator`.

**Context:** `src/mobile/src/navigation/types.ts` — `ProfileStackParamList` defines `Notifications: undefined` and `HelpCenter: undefined` (lines 113, 119). No `.tsx` file exists for either. `NotificationsScreen` is a UI-only placeholder for now (push notification registration is implemented in S8b). `HelpCenterScreen` is a static screen with FAQ content and a mailto/support link. Both go in `src/mobile/src/screens/profile/`.

**Files to create:**
- `src/mobile/src/screens/profile/NotificationsScreen.tsx`
- `src/mobile/src/screens/profile/HelpCenterScreen.tsx`

**Files to edit:**
- `src/mobile/src/screens/profile/index.ts` — export new screens
- `src/mobile/src/navigation/MainNavigator.tsx` — register in `ProfileNavigator`

**Files to read first:**
- `src/mobile/src/screens/profile/SettingsScreen.tsx` (just created in S4 — for pattern consistency)
- `src/mobile/src/navigation/MainNavigator.tsx` (ProfileNavigator block — confirm current registrations)

**Acceptance criteria:**
- [x] `NotificationsScreen.tsx` renders a dark-theme placeholder with a "Push Notifications" toggle (UI-only, state stays local; the actual FCM wiring is S8b)
- [x] `HelpCenterScreen.tsx` renders a static FAQ list with a "Contact Support: support@waooaw.com" mailto link using `Linking.openURL`
- [x] Both exported from `src/mobile/src/screens/profile/index.ts`
- [x] Both registered in `ProfileNavigator` in `MainNavigator.tsx`
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// NotificationsScreen.tsx — scaffold:
import React, { useState } from 'react';
import { View, Text, Switch, SafeAreaView } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import type { ProfileStackScreenProps } from '@/navigation/types';

type Props = ProfileStackScreenProps<'Notifications'>;

export const NotificationsScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const [pushEnabled, setPushEnabled] = useState(false);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <Text style={[typography.heading2, { color: colors.white, padding: spacing.md }]}>
        Notifications
      </Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', padding: spacing.md }}>
        <Text style={{ flex: 1, color: colors.white }}>Push Notifications</Text>
        <Switch
          value={pushEnabled}
          onValueChange={setPushEnabled}
          trackColor={{ true: colors.neonCyan }}
        />
      </View>
    </SafeAreaView>
  );
};

// HelpCenterScreen.tsx — key Linking.openURL pattern:
import { Linking } from 'react-native';

const handleContactSupport = () => {
  Linking.openURL('mailto:support@waooaw.com');
};

// MainNavigator.tsx — add inside ProfileNavigator:
<ProfileStack.Screen name="Notifications" component={NotificationsScreen} />
<ProfileStack.Screen name="HelpCenter" component={HelpCenterScreen} />
```

---

### S6 — Restore real Razorpay SDK + enable payments feature flag

**Goal:** Remove the stub mock in `razorpay.service.ts` and restore the real `import RazorpayCheckout from 'react-native-razorpay'` import; enable the `payments: true` feature flag in UAT and prod environment configs.

**Context:** `src/mobile/src/services/payment/razorpay.service.ts` — line 8 is `// import RazorpayCheckout from 'react-native-razorpay'; // REMOVED for demo build`. Lines 9-11 define a stub that returns `demo_payment_id`. `react-native-razorpay` is already in `package.json` (no `npm install` needed). `src/mobile/src/config/environment.config.ts` — the `features.payments` boolean controls whether payment flows are reachable; check current values in UAT and prod configs (approximately lines 155-170 and 240-252).

**Files to edit:**
- `src/mobile/src/services/payment/razorpay.service.ts` — restore real import, remove stub
- `src/mobile/src/config/environment.config.ts` — set `payments: true` in UAT and prod feature blocks

**Files to read first:**
- `src/mobile/src/services/payment/razorpay.service.ts` (full file)
- `src/mobile/src/config/environment.config.ts` (lines 140-260 — UAT + prod feature blocks)

**Acceptance criteria:**
- [x] Line 8 of `razorpay.service.ts` is the real import: `import RazorpayCheckout from 'react-native-razorpay';`
- [x] The stub `const RazorpayCheckout = { open: async ... }` lines are removed
- [x] `features.payments` set to `true` in "uat" config block
- [x] `features.payments` set to `true` in "prod" config block
- [x] `features.payments` remains `false` in "development" and "demo" blocks (no real charges in demo)
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// razorpay.service.ts — final import at top of file (replace stub):
import RazorpayCheckout from 'react-native-razorpay'; // real SDK — no stub
// Remove lines 9-11 (the const RazorpayCheckout = {...} stub object)

// environment.config.ts — UAT features block (find line ~159):
features: {
  analytics: true,
  crashReporting: true,
  performance: true,
  payments: true,  // ← change from false to true
},

// environment.config.ts — prod features block (find line ~201):
features: {
  analytics: true,
  crashReporting: true,
  performance: true,
  payments: true,  // ← change from false to true
},
```

---

## Iteration 3 — Payments screens + push notifications (Lane A + Lane B)

**Estimated time:** 3 h  
**BLOCKED UNTIL:** Iteration 2 (S6 — Razorpay SDK) is merged before starting S7.

---

### S7 — Create PaymentMethodsScreen + SubscriptionManagementScreen

**Goal:** Create the two remaining profile tab screens for payment management, register them in `ProfileNavigator`, and wire `SubscriptionManagementScreen` to the Razorpay payment flow using the existing `useRazorpay` hook.

**Context:** `src/mobile/src/navigation/types.ts` — `ProfileStackParamList` defines `PaymentMethods: undefined` and `SubscriptionManagement: undefined` (lines 115-117). Neither has a `.tsx` file. The `useRazorpay` hook at `src/mobile/src/hooks/useRazorpay.ts` wraps the `razorpay.service.ts` service for React components. `PaymentMethodsScreen` shows stored card/UPI summary (read from Plant Gateway `GET /api/v1/customers/payment-methods` if it exists, else static placeholder). `SubscriptionManagementScreen` shows current subscription and a "Renew / Upgrade" CTA that triggers the Razorpay payment modal. Both screens go in `src/mobile/src/screens/profile/`.

**BLOCKED UNTIL:** S6 (Iteration 2) merged.

**Files to create:**
- `src/mobile/src/screens/profile/PaymentMethodsScreen.tsx`
- `src/mobile/src/screens/profile/SubscriptionManagementScreen.tsx`

**Files to edit:**
- `src/mobile/src/screens/profile/index.ts` — export new screens
- `src/mobile/src/navigation/MainNavigator.tsx` — register in `ProfileNavigator`

**Files to read first:**
- `src/mobile/src/hooks/useRazorpay.ts` (full file — for payment trigger pattern)
- `src/mobile/src/hooks/useHiredAgents.ts` (lines 60-90 — for subscription query pattern)
- `src/mobile/src/screens/profile/SettingsScreen.tsx` (full file — styling reference)
- `src/mobile/src/navigation/MainNavigator.tsx` (ProfileNavigator block — confirm current registrations)

**Acceptance criteria:**
- [x] `PaymentMethodsScreen.tsx` renders a dark-theme list of payment methods with an "Add Payment Method" CTA (static for now; calls `useRazorpay` flow on tap)
- [x] `SubscriptionManagementScreen.tsx` shows current subscription status and a "Renew / Upgrade" button that calls the `useRazorpay` hook's `initiatePayment()` function
- [x] Both screens exported from `src/mobile/src/screens/profile/index.ts`
- [x] Both screens registered in `ProfileNavigator` in `MainNavigator.tsx`
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// SubscriptionManagementScreen.tsx — Razorpay trigger pattern:
import { useRazorpay } from '@/hooks/useRazorpay';
import { useAuthStore } from '@/store/authStore'; // adjust import path as needed

export const SubscriptionManagementScreen = ({ navigation }: Props) => {
  const { colors, spacing, typography } = useTheme();
  const { initiatePayment, isLoading: paymentLoading } = useRazorpay();

  const handleRenew = async () => {
    try {
      // agentId and planId should come from the user's current subscription;
      // for scaffold, use placeholders — wire to authStore subscription data
      await initiatePayment({ agentId: 'current', planId: 'monthly' });
    } catch (error) {
      // useRazorpay already shows Alert on error — no double-handling needed
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      <Text style={[typography.heading2, { color: colors.white, padding: spacing.md }]}>
        Subscription
      </Text>
      <TouchableOpacity
        style={{
          margin: spacing.md,
          padding: spacing.md,
          backgroundColor: colors.neonCyan,
          borderRadius: 12,
          alignItems: 'center',
          opacity: paymentLoading ? 0.6 : 1,
        }}
        onPress={handleRenew}
        disabled={paymentLoading}
      >
        <Text style={{ color: colors.black, fontWeight: '700' }}>
          {paymentLoading ? 'Processing...' : 'Renew / Upgrade'}
        </Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
};

// MainNavigator.tsx — add inside ProfileNavigator:
<ProfileStack.Screen name="PaymentMethods" component={PaymentMethodsScreen} />
<ProfileStack.Screen name="SubscriptionManagement" component={SubscriptionManagementScreen} />
```

---

### S8 — Push notification infrastructure (Plant Backend endpoint + mobile FCM registration)

**Goal:** Create Plant Gateway endpoint `POST /api/v1/customers/fcm-token` to store device FCM tokens, then wire the mobile app to register with Firebase (via `expo-notifications`) and send the token to Plant Gateway after successful sign-in.

**Context — Plant Backend (S8a, Lane B):** Plant Gateway is at `src/Plant/Gateway/`. New route files follow the `waooaw_router()` factory (hard rule from `CLAUDE.md`). The router is registered in `src/Plant/Gateway/app/main.py`. Customer table is in `src/Plant/Gateway/app/models/` — check for an existing `fcm_token` column or add a migration. Write routes use `get_db_session()` (not `get_read_db_session()`). The route must require authentication (Bearer token).

**Context — Mobile (S8b, Lane A):** `expo-notifications` is the correct package for Expo Managed Workflow FCM access. FCM token registration should happen in `src/mobile/src/stores/authStore.ts` inside `signIn()` and `signInWithGoogle()` (and `signInWithApple()` from MOBILE-NFR-1 S5), after the access token is stored. `src/mobile/src/config/environment.config.ts` already has a `FIREBASE_CONFIG` interface field — populate it in UAT/prod environments.

**S8b BLOCKED UNTIL:** S8a Plant Gateway PR merged.

**Files to create (S8a):**
- `src/Plant/Gateway/app/api/customers_fcm.py` — new route file for FCM token endpoint

**Files to edit (S8a):**
- `src/Plant/Gateway/app/main.py` — register the new router
- `src/Plant/Gateway/app/models/customer.py` — add `fcm_token` column (or confirm it exists)

**Files to create (S8b):**
- `src/mobile/src/services/notifications/pushNotifications.service.ts` — FCM token registration helper

**Files to edit (S8b):**
- `src/mobile/src/stores/authStore.ts` — call `registerPushToken()` after successful sign-in
- `src/mobile/src/screens/profile/NotificationsScreen.tsx` (created in S5) — wire the toggle to `registerPushToken()`

**Files to read first (S8a):**
- `src/Plant/Gateway/app/main.py` (lines 1-60 — to see how existing routers are registered)
- Any existing `src/Plant/Gateway/app/api/cp_customers.py` or similar (for route file pattern)
- `src/Plant/Gateway/app/models/customer.py` (full file — to check fcm_token column)

**Files to read first (S8b):**
- `src/mobile/src/stores/authStore.ts` (full file — to see signIn action)
- `src/mobile/src/config/environment.config.ts` (lines 40-55 — FIREBASE_CONFIG interface)

**Acceptance criteria:**
- [x] `POST /api/v1/customers/fcm-token` returns 200 with `{ "status": "ok" }` for authenticated requests with valid token
- [x] Route uses `waooaw_router()` factory and `get_db_session()`
- [x] Route is registered in `main.py`
- [x] `registerPushToken()` in mobile calls `expo-notifications` to get the device push token, then calls `apiClient.post('/api/v1/customers/fcm-token', { token })` — guarded by `Platform.OS !== 'web'`
- [x] `registerPushToken()` is called from `authStore.login()` after user is set (fire-and-forget; wired in NotificationsScreen toggle too)
- [x] TypeScript + Python both compile with zero errors

**Code patterns to copy exactly:**

```python
# src/Plant/Gateway/app/api/customers_fcm.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.routing import waooaw_router          # waooaw_router MANDATORY — never bare APIRouter
from core.database import get_db_session        # write route — not read-replica
from core.security import get_current_customer  # existing auth dependency

router = waooaw_router(prefix="/customers", tags=["customers"])

@router.post("/fcm-token", status_code=200)
async def store_fcm_token(
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_customer=Depends(get_current_customer),
) -> dict:
    """Store or update the FCM push token for the authenticated customer."""
    token = payload.get("token", "")
    if token:
        current_customer.fcm_token = token
        await db.commit()
    return {"status": "ok"}
```

```typescript
// src/mobile/src/services/notifications/pushNotifications.service.ts
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import apiClient from '../../lib/apiClient';

export const registerPushToken = async (): Promise<void> => {
  if (Platform.OS === 'web') return; // expo-notifications unsupported on web

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') return; // user denied — do not proceed

  const tokenData = await Notifications.getExpoPushTokenAsync();
  const token = tokenData.data;

  await apiClient.post('/api/v1/customers/fcm-token', { token });
};

// authStore.ts — call after setAccessToken inside signIn():
import { registerPushToken } from '../services/notifications/pushNotifications.service';

// Inside signIn() after: await secureStorage.setAccessToken(response.data.access_token):
registerPushToken().catch(() => {}); // fire-and-forget — push token failure must not block login
```

---

## How to Launch

### Iteration 1 — agent task (Copilot Agent mode)

```
You are implementing MOBILE-FUNC-1 Iteration 1 for the WAOOAW mobile app.

Working directory: /workspaces/WAOOAW

Read these files FIRST before writing any code:
1. src/mobile/src/hooks/useHiredAgents.ts (full file)
2. src/mobile/src/types/hiredAgents.types.ts (full file)
3. src/mobile/src/screens/agents/TrialDashboardScreen.tsx (full file)
4. src/mobile/src/screens/profile/EditProfileScreen.tsx (full file)
5. src/mobile/src/lib/apiClient.ts (lines 1-30)
6. src/mobile/src/screens/discover/DiscoverScreen.tsx (first 60 lines)
7. src/mobile/src/navigation/MainNavigator.tsx (lines 60-80)
8. src/mobile/src/navigation/types.ts (lines 68-92)

Then implement these three stories in order:

--- STORY S1 (45 min) ---
File: src/mobile/src/hooks/useHiredAgents.ts
Change: Add useDeliverables(subscriptionId) hook at the end of the file.
The hook must call GET /api/v1/deliverables?subscription_id=<id>, return Deliverable[],
and include retry: 2 and retryDelay: (i) => Math.min(1000 * Math.pow(2, i), 10000).

File: src/mobile/src/screens/agents/TrialDashboardScreen.tsx
Change: Import useDeliverables from useHiredAgents.
Add: const { data: deliverables = [], isLoading: delivLoading } = useDeliverables(trialId);
Remove: getMockDeliverables() function and the const deliverables = getMockDeliverables() line.
Handle delivLoading state (show a spinner or null while loading).
See MOBILE-FUNC-1 S1 code block for exact patterns.

--- STORY S2 (30 min) ---
File: src/mobile/src/screens/profile/EditProfileScreen.tsx
Change ONLY line 23: remove cpApiClient import; add apiClient import from '../../lib/apiClient'.
Change ONLY line 63: change cpApiClient.patch('/cp/profile', payload) to apiClient.patch('/api/v1/customers/profile', payload).
No other changes.

--- STORY S3 (90 min) ---
Create: src/mobile/src/screens/discover/SearchResultsScreen.tsx
Create: src/mobile/src/screens/discover/FilterAgentsScreen.tsx
Both screens use dark theme (colors.black background) and match DiscoverScreen styling.
See MOBILE-FUNC-1 S3 code block for SearchResultsScreen scaffold.
FilterAgentsScreen should show filter controls (picker for industry, slider or text input for minRating/maxPrice).

Edit: src/mobile/src/screens/discover/index.ts
Add exports for SearchResultsScreen and FilterAgentsScreen.

Edit: src/mobile/src/navigation/MainNavigator.tsx
Import SearchResultsScreen and FilterAgentsScreen from '../screens/discover'.
Register both in DiscoverNavigator using <DiscoverStack.Screen />.

After all stories: run cd src/mobile && npx tsc --noEmit and fix any TypeScript errors.
Commit: feat(mobile): MOBILE-FUNC-1 it1 — real deliverables, profile fix, discover screens
```

---

### Iteration 2 — agent task (Copilot Agent mode)

```
You are implementing MOBILE-FUNC-1 Iteration 2 for the WAOOAW mobile app.
BLOCKED UNTIL: Iteration 1 PR is merged.

Working directory: /workspaces/WAOOAW

Read these files FIRST before writing any code:
1. src/mobile/src/screens/agents/MyAgentsScreen.tsx (first 60 lines — styling reference)
2. src/mobile/src/screens/profile/ProfileScreen.tsx (first 60 lines — styling reference)
3. src/mobile/src/navigation/MainNavigator.tsx (lines 78-115 — navigator blocks)
4. src/mobile/src/navigation/types.ts (lines 95-125 — MyAgents + Profile type definitions)
5. src/mobile/src/hooks/useHiredAgents.ts (full file — for ActiveTrialsList/HiredAgentsList)
6. src/mobile/src/services/payment/razorpay.service.ts (full file)
7. src/mobile/src/config/environment.config.ts (lines 140-260 — feature flags)

Then implement these three stories in order:

--- STORY S4 (90 min) ---
Create: src/mobile/src/screens/agents/ActiveTrialsListScreen.tsx
Create: src/mobile/src/screens/agents/HiredAgentsListScreen.tsx
Create: src/mobile/src/screens/profile/SettingsScreen.tsx
ActiveTrialsListScreen uses useHiredAgents() filtered by trial_status === 'active'.
HiredAgentsListScreen uses useHiredAgents() filtered by the hired status.
SettingsScreen shows notification toggle, privacy policy link (navigate to PrivacyPolicy screen), terms link (navigate to TermsOfService screen), and sign-out button calling authStore.signOut().
Edit: src/mobile/src/screens/agents/index.ts — export new agent screens.
Edit: src/mobile/src/screens/profile/index.ts — export SettingsScreen (create index.ts if missing).
Edit: src/mobile/src/navigation/MainNavigator.tsx — register all three in correct navigators.
See MOBILE-FUNC-1 S4 code block for patterns.

--- STORY S5 (45 min) ---
Create: src/mobile/src/screens/profile/NotificationsScreen.tsx
Create: src/mobile/src/screens/profile/HelpCenterScreen.tsx
NotificationsScreen: dark-theme screen with a push notification toggle (UI-only local state; FCM wiring is done in S8b).
HelpCenterScreen: static FAQ list with a mailto:support@waooaw.com link using Linking.openURL.
Edit: src/mobile/src/screens/profile/index.ts — export both screens.
Edit: src/mobile/src/navigation/MainNavigator.tsx — register both in ProfileNavigator.
See MOBILE-FUNC-1 S5 code block for patterns.

--- STORY S6 (30 min) ---
File: src/mobile/src/services/payment/razorpay.service.ts
Change: Remove the stub const RazorpayCheckout = { open: async ... } object.
Change: Restore line 8 to the real import: import RazorpayCheckout from 'react-native-razorpay';
File: src/mobile/src/config/environment.config.ts
Change: Set payments: true in the UAT feature block.
Change: Set payments: true in the prod feature block.
Leave development and demo blocks unchanged (payments: false).
See MOBILE-FUNC-1 S6 code block for exact patterns.

After all stories: run cd src/mobile && npx tsc --noEmit and fix any TypeScript errors.
Commit: feat(mobile): MOBILE-FUNC-1 it2 — MyAgents screens, profile screens, Razorpay enabled
```

---

### Iteration 3 — agent task (Copilot Agent mode)

```
You are implementing MOBILE-FUNC-1 Iteration 3 for the WAOOAW platform.
BLOCKED UNTIL: Iteration 2 PR is merged (especially S6 — Razorpay SDK restored).

This iteration has TWO parts: S7 (mobile only) and S8 (Plant Backend + mobile).
Implement S8a (Plant Backend) FIRST, open a PR, merge it, then implement S8b (mobile).

Working directory: /workspaces/WAOOAW

Read these files FIRST before writing any code:
1. src/mobile/src/hooks/useRazorpay.ts (full file)
2. src/mobile/src/screens/profile/SettingsScreen.tsx (full file — styling reference)
3. src/mobile/src/navigation/MainNavigator.tsx (ProfileNavigator block)
4. src/Plant/Gateway/app/main.py (lines 1-60 — router registration pattern)
5. src/Plant/Gateway/app/models/customer.py (full file — check for fcm_token column)
6. src/mobile/src/stores/authStore.ts (full file — signIn action)
7. src/mobile/src/config/environment.config.ts (lines 40-55 — FIREBASE_CONFIG interface)

--- STORY S7 (90 min, Lane A — mobile only) ---
Create: src/mobile/src/screens/profile/PaymentMethodsScreen.tsx
Create: src/mobile/src/screens/profile/SubscriptionManagementScreen.tsx
PaymentMethodsScreen: dark-theme list showing stored payment methods (static placeholder list is acceptable; add "Add Payment Method" CTA that triggers useRazorpay).
SubscriptionManagementScreen: shows current subscription tier and a "Renew / Upgrade" button that calls useRazorpay hook's initiatePayment().
Edit: src/mobile/src/screens/profile/index.ts — export both screens.
Edit: src/mobile/src/navigation/MainNavigator.tsx — register both in ProfileNavigator.
See MOBILE-FUNC-1 S7 code block for SubscriptionManagementScreen Razorpay trigger pattern.

--- STORY S8a (45 min, Lane B — Plant Backend) ---
Create: src/Plant/Gateway/app/api/customers_fcm.py
This file must use waooaw_router() (never bare APIRouter — CI will block it).
Route: POST /customers/fcm-token — authenticated, stores token to customer.fcm_token column.
Uses get_db_session() (write route — not get_read_db_session).
Edit: src/Plant/Gateway/app/main.py — import and include the new router.
Edit: src/Plant/Gateway/app/models/customer.py — add fcm_token: Mapped[str | None] = mapped_column(String(255), nullable=True) if column does not exist.
See MOBILE-FUNC-1 S8 Python code block for exact route implementation.
After S8a: run Plant Gateway tests (docker-compose -f docker-compose.test.yml run plant-gateway-test pytest).

--- STORY S8b (45 min, Lane A — mobile; BLOCKED UNTIL S8a merged) ---
Run first: cd src/mobile && npx expo install expo-notifications
Create: src/mobile/src/services/notifications/pushNotifications.service.ts
Implement registerPushToken() using expo-notifications + apiClient.post('/api/v1/customers/fcm-token', { token }).
Function must be fire-and-forget safe (never rejects — wrap catch inside).
Edit: src/mobile/src/stores/authStore.ts — call registerPushToken().catch(() => {}) after setAccessToken() in signIn() and signInWithGoogle().
Edit: src/mobile/src/screens/profile/NotificationsScreen.tsx (from S5) — wire the push toggle to call registerPushToken() when toggled on.
See MOBILE-FUNC-1 S8 TypeScript code block for exact patterns.

After all stories: run cd src/mobile && npx tsc --noEmit and fix any TypeScript errors.
Commit (S7 + S8b): feat(mobile): MOBILE-FUNC-1 it3 — payment screens, push notifications
Commit (S8a, separate PR): feat(plant-gateway): add FCM token storage endpoint
```
