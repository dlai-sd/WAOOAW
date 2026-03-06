# MOBILE-NFR-1 — Mobile App NFR Hardening

| Field | Value |
|---|---|
| Plan ID | MOBILE-NFR-1 |
| Created | 2025-07-18 |
| Status | Draft |
| Author | GitHub Copilot |
| Service area | `src/mobile/` |
| Lane | A (all mobile-only changes; no new backend routes required) |
| Estimated total | ~4 h |

---

## PM Review Checklist

- [x] All placeholders filled — zero `[PLACEHOLDER]` remain
- [x] Every story is self-contained (exact file paths, 2-3 sentence context)
- [x] NFR code patterns embedded inline — no "see NFRReusable.md" references
- [x] Story sizes: 30 min (small UI), 45 min (single hook/service), 90 min (platform integration)
- [x] Max 6 stories per iteration
- [x] Lane A stories only (no new Plant/CP backend endpoints required)
- [x] Story dependencies marked with BLOCKED UNTIL

---

## Overview

### Background

The mobile app ships to UAT and production with three critical NFR regressions:

1. **Sentry crash reporting is fully stubbed out** — `sentry.config.ts` has the real `@sentry/react-native` import commented out and replaced with a no-op stub object. All four environment configs set `sentryDsn: undefined`, so no crash is ever reported to Sentry even in prod.
2. **React Query hooks retry with no backoff delay** — `useHiredAgents.ts`, `useAgents.ts`, `useAgentDetail.ts`, `useAgentTypes.ts` all specify `retry: 2` with no `retryDelay`, meaning failed network calls are retried immediately, potentially flooding the Plant Gateway.
3. **`cpApiClient.ts` has no retry interceptor** — The Axios instance in `src/mobile/src/lib/cpApiClient.ts` has an auth + correlation request interceptor but no response interceptor for retry, so transient errors in the profile PATCH flow silently fail.
4. **Registration flow has no client-side submit throttle** — The `SignUpScreen` and `OTPVerificationScreen` have no debounce or cooldown on form submit; a user (or bot) can tap repeatedly and fire multiple concurrent auth requests to the Plant Gateway.
5. **iOS build does not exist; Apple Sign-In is not implemented** — `eas.json` has only `development`, `demo`, `uat`, and `prod` Android profiles. iOS is fully absent, blocking the iOS market.

### Goal

After this plan is merged, UAT and prod builds will report crashes to Sentry; React Query will retry with exponential back-off; the CP API client will retry transient errors; the registration UI will throttle concurrent submits; and the iOS EAS build profile will exist with Apple Sign-In wired.

### Out of Scope

- Push notifications (covered in MOBILE-FUNC-1)
- Any Plant Backend or CP Backend changes
- Fixing the architectural inconsistency of `cpApiClient` (covered in MOBILE-FUNC-1 S2)
- Adding server-side rate limiting to Plant Gateway auth routes (separate Plant work)

### Success Criteria

- [x] Sentry project receives at least one test event from a UAT build
- [x] React Query hooks in `useHiredAgents.ts`, `useAgents.ts`, `useAgentDetail.ts`, `useAgentTypes.ts` all include `retryDelay` with exponential back-off
- [x] `cpApiClient.ts` response interceptor retries 429/5xx with back-off ≤ 3 attempts
- [x] Tapping the Sign-Up submit button rapidly fires only one request in 2 s window
- [x] OTP resend shows a 60-second cooldown timer
- [x] iOS EAS build profile exists in `eas.json` and produces a working simulator build
- [x] `expo-apple-authentication` renders Apple Sign-In button on iOS

---

## Dependencies

| Dependency | Notes |
|---|---|
| GCP Secret Manager — SENTRY_DSN | Must be created in `waooaw-oauth` project before Iteration 1 deploys to UAT. Inject as `EXPO_PUBLIC_SENTRY_DSN` env var in EAS profile. |
| Apple Developer account | Required for Apple Sign-In entitlement in Iteration 2. |
| Expo SDK ≥ 50 | `expo-apple-authentication` requires Managed Workflow + SDK 50+. Already satisfied. |

---

## Epics & Time Estimates

| Epic | Stories | Est. Time |
|---|---|---|
| E1 — Sentry crash reporting | S1 | 45 min |
| E2 — React Query back-off | S2 | 30 min |
| E3 — cpApiClient retry interceptor | S3 | 45 min |
| E4 — Registration submit throttle | S4 | 30 min |
| E5 — Apple Sign-In + iOS EAS profile | S5 | 90 min |

---

## Iteration 1 — Sentry + Retry patterns

**Estimated time:** 2 h  
**Goal:** Ship Sentry to UAT/prod; add back-off to all React Query hooks; add retry interceptor to cpApiClient.

---

### S1 — Restore real Sentry crash reporting

**Goal:** Re-enable `@sentry/react-native` in `sentry.config.ts` and populate `sentryDsn` for UAT and prod environment configs so crashes are reported in non-demo builds.

**Context:** `src/mobile/src/config/sentry.config.ts` — line 6 has `// import * as Sentry from '@sentry/react-native'; // REMOVED for demo build` replaced with a no-op stub object. The `initSentry()` function already contains all the correct logic (checks `sentryDsn` and `config.features.crashReporting`) — the only changes required are (a) restore the real import, (b) remove the stub object, (c) set `sentryDsn` in the UAT and prod configs at `src/mobile/src/config/environment.config.ts` lines 206 and 248.

**Files to read:** `src/mobile/src/config/sentry.config.ts` (full), `src/mobile/src/config/environment.config.ts` (lines 190-260)

**Acceptance criteria:**
- [x] Line 6 of `sentry.config.ts` is the real import: `import * as Sentry from '@sentry/react-native';`
- [x] The no-op stub object (lines 7-18) is removed
- [x] `environment.config.ts` UAT block sets `sentryDsn: process.env.EXPO_PUBLIC_SENTRY_DSN ?? ''`
- [x] `environment.config.ts` prod block sets `sentryDsn: process.env.EXPO_PUBLIC_SENTRY_DSN ?? ''`
- [x] Development and demo blocks keep `sentryDsn: undefined` (no crash reporting in non-prod)
- [x] `initSentry()` early-returns when `sentryDsn` is falsy — no change to existing guard logic
- [x] TypeScript compiles with zero errors: `cd src/mobile && npx tsc --noEmit`

**Code patterns to copy exactly:**

```typescript
// sentry.config.ts — FINAL file header (replace stub with real import)
import * as Sentry from '@sentry/react-native';
// Remove lines 7-19 (the no-op const Sentry = { ... } stub object)
// Keep the existing initSentry() function unchanged — it already guards on sentryDsn

// environment.config.ts — UAT block monitoring section (line ~206)
monitoring: {
  sentryDsn: process.env.EXPO_PUBLIC_SENTRY_DSN ?? '',
},

// environment.config.ts — prod block monitoring section (line ~248)
monitoring: {
  sentryDsn: process.env.EXPO_PUBLIC_SENTRY_DSN ?? '',
},

// Development + demo blocks remain unchanged:
monitoring: {
  sentryDsn: undefined,
},
```

---

### S2 — Add `retryDelay` to all React Query hooks

**Goal:** Replace bare `retry: 2` / `retry: 1` options in all four React Query hook files with `retry` + `retryDelay` that implements the platform-standard exponential back-off (1 s, 2 s, 4 s, capped at 10 s).

**Context:** Four hook files (listed below) each call `useQuery(...)` with `retry: 2` and no `retryDelay`. Without `retryDelay`, React Query defaults to a 1 000 ms fixed delay for all retries (v5) or retries instantly (v4), potentially flooding the Plant Gateway. The platform standard (from `CLAUDE.md`) is: "Retry 429/5xx/network-drop with exponential backoff (3×, 1s/2s/4s+jitter)".

**Files to edit:**
- `src/mobile/src/hooks/useHiredAgents.ts` — 7 `useQuery` calls with `retry: 2` (lines 38, 63, 85, 109, 131, 153, 176)
- `src/mobile/src/hooks/useAgents.ts` — 2 `useQuery` calls with `retry: 2` and 1 with `retry: 1` (lines 36, 62)
- `src/mobile/src/hooks/useAgentDetail.ts` — 2 `useQuery` calls with `retry: 2` (lines 42, 74)
- `src/mobile/src/hooks/useAgentTypes.ts` — 1 `useQuery` call with `retry: 2` (line 32)

**Acceptance criteria:**
- [x] All `useQuery` calls in the four files above include `retryDelay` option
- [x] `retryDelay` implements exponential back-off capped at 10 000 ms
- [x] `retry: 2` is unchanged (keep existing retry count)
- [x] TypeScript compiles with zero errors: `cd src/mobile && npx tsc --noEmit`

**Code patterns to copy exactly:**

```typescript
// Replace every bare `retry: N` with the following two options together:
retry: 2,
retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),

// Example — useHiredAgents.ts line 36-40 before:
  return useQuery({
    queryKey: ['hired-agent', subscriptionId],
    queryFn: () => fetchHiredAgent(subscriptionId),
    retry: 2,
  });

// After:
  return useQuery({
    queryKey: ['hired-agent', subscriptionId],
    queryFn: () => fetchHiredAgent(subscriptionId),
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
  });
// Apply this same pattern to EVERY useQuery call in the four files.
```

---

### S3 — Add retry interceptor to `cpApiClient.ts`

**Goal:** Add a response interceptor to `src/mobile/src/lib/cpApiClient.ts` that retries 429 / 5xx / network-drop errors up to 2 times with the same exponential back-off already used in `apiClient.ts`.

**Context:** `src/mobile/src/lib/cpApiClient.ts` is a lightweight Axios instance used by `EditProfileScreen.tsx` for `PATCH /cp/profile`. It has a request interceptor (auth + correlation) but no response interceptor. The existing `src/mobile/src/lib/apiClient.ts` has a full retry interceptor pattern (lines 100-140); copy that pattern verbatim, adjusted for the simpler CP client. Note: MOBILE-FUNC-1 S2 will later migrate `EditProfileScreen` off `cpApiClient`, but adding the interceptor now ensures any interim UAT usage is resilient.

**Files to edit:** `src/mobile/src/lib/cpApiClient.ts`  
**Reference file (read for pattern):** `src/mobile/src/lib/apiClient.ts` lines 95-145

**Acceptance criteria:**
- [x] `cpApiClient.ts` has a response interceptor registered after the request interceptor
- [x] Interceptor retries on status 429, 500, 502, 503, 504, or network drop (no `response`)
- [x] Max 2 retry attempts (`retryCount < 2`)
- [x] Back-off: `Math.min(1000 * Math.pow(2, retryCount), 10000)` ms
- [x] Retry counter stored on `_retryCount` property of `config` (same pattern as `apiClient.ts`)
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// Add after the request interceptor inside createCpAxiosInstance()
// (paste after the existing instance.interceptors.request.use(...) block)

const RETRYABLE_STATUSES = new Set([429, 500, 502, 503, 504]);

type RetryableConfig = typeof instance.defaults & { _retryCount?: number };

instance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as RetryableConfig;
    const status = error.response?.status ?? 0;
    const isNetworkDrop = !error.response && error.code !== 'ERR_CANCELED';
    const isRetryable = RETRYABLE_STATUSES.has(status) || isNetworkDrop;
    const retryCount = originalRequest._retryCount ?? 0;

    if (isRetryable && retryCount < 2) {
      originalRequest._retryCount = retryCount + 1;
      const backoff = Math.min(1000 * Math.pow(2, retryCount), 10000);
      await new Promise((resolve) => setTimeout(resolve, backoff));
      return instance(originalRequest);
    }

    return Promise.reject(error);
  }
);
```

---

## Iteration 2 — Registration throttle + iOS / Apple Sign-In

**Estimated time:** 2 h  
**Goal:** Add client-side submit throttle to auth screens; add iOS EAS build profile and Apple Sign-In button.

---

### S4 — Add submit debounce + OTP resend cooldown to auth screens

**Goal:** Prevent multiple concurrent auth requests by (a) disabling the Sign-Up submit button for 2 s after a tap and (b) showing a 60-second countdown timer on the OTP resend button.

**Context:** `src/mobile/src/screens/auth/SignUpScreen.tsx` renders a "Create Account" button that calls the Plant Gateway registration route. `src/mobile/src/screens/auth/OTPVerificationScreen.tsx` renders a "Resend Code" button. Neither has any rate-limiting or cooldown logic. Plant Gateway is the authoritative rate limiter; this story adds client-side UX protection that reinforces it and prevents duplicate network calls from accidental double-taps. The `useRef` + `Date.now()` debounce pattern is safe for React Native (no need for lodash.debounce).

**Files to edit:**
- `src/mobile/src/screens/auth/SignUpScreen.tsx`
- `src/mobile/src/screens/auth/OTPVerificationScreen.tsx`

**Acceptance criteria:**
- [x] Sign-Up submit button is disabled for 2 000 ms after each tap; `isSubmitting` state prevents concurrent calls
- [x] OTP resend button shows `Resend (Ns)` countdown from 60 s and is disabled during countdown
- [x] Countdown resets to 60 s on screen mount and on each successful resend
- [x] No `lodash` dependency added; use `useRef` + `Date.now()` for debounce, `setInterval` for countdown
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// SignUpScreen.tsx — add inside component, before return statement:
const lastSubmitRef = React.useRef<number>(0);
const DEBOUNCE_MS = 2000;

const handleSubmit = async () => {
  const now = Date.now();
  if (now - lastSubmitRef.current < DEBOUNCE_MS) return; // guard double-tap
  lastSubmitRef.current = now;
  setIsSubmitting(true);
  try {
    // ... existing registration logic ...
  } finally {
    setIsSubmitting(false);
  }
};
// Disable submit button: disabled={isSubmitting}

// OTPVerificationScreen.tsx — add cooldown timer
const [resendCooldown, setResendCooldown] = React.useState(60);
const timerRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

const startCooldown = React.useCallback(() => {
  setResendCooldown(60);
  if (timerRef.current) clearInterval(timerRef.current);
  timerRef.current = setInterval(() => {
    setResendCooldown((prev) => {
      if (prev <= 1) {
        clearInterval(timerRef.current!);
        return 0;
      }
      return prev - 1;
    });
  }, 1000);
}, []);

React.useEffect(() => {
  startCooldown(); // start on mount
  return () => { if (timerRef.current) clearInterval(timerRef.current); };
}, []);

// Resend button label: resendCooldown > 0 ? `Resend (${resendCooldown}s)` : 'Resend Code'
// Resend button disabled: resendCooldown > 0
// Call startCooldown() after successful resend API call
```

---

### S5 — Add Apple Sign-In + iOS EAS build profile

**Goal:** Add `expo-apple-authentication` plugin, render an Apple Sign-In button exclusively on iOS, and add an iOS EAS build profile to `eas.json` so the app can be built and submitted to the App Store.

**Context:** `src/mobile/app.json` — the Expo managed-workflow config. `src/mobile/eas.json` — the EAS build profiles file; currently has `development`, `demo`, `uat`, `prod` Android profiles only. `src/mobile/src/screens/auth/SignInScreen.tsx` — the Google Sign-In screen where the Apple button should appear. `src/mobile/src/stores/authStore.ts` — the Zustand auth store where Apple credential handling should live. The Apple Sign-In flow is distinct from Google: use `expo-apple-authentication` `AppleAuthenticationScope.FULL_NAME` + `EMAIL`; store the `identityToken` as the bearer token to Plant Gateway's `/api/v1/auth/apple` endpoint.

**Files to edit:**
- `src/mobile/app.json` — add `expo-apple-authentication` plugin
- `src/mobile/eas.json` — add iOS build profiles (development-ios, uat-ios, prod-ios)
- `src/mobile/src/screens/auth/SignInScreen.tsx` — add Apple Sign-In button (iOS only, via `Platform.OS === 'ios'`)
- `src/mobile/src/stores/authStore.ts` — add `signInWithApple()` action

**Acceptance criteria:**
- [x] `app.json` plugins array includes `"expo-apple-authentication"`
- [x] `eas.json` has `uat-ios` and `prod-ios` profiles with `"platform": "ios"`, matching `uat` and `prod` Android `env` blocks respectively
- [x] Apple Sign-In button renders on iOS only (guarded with `Platform.OS === 'ios'`)
- [x] `authStore.signInWithApple()` calls `AppleAuthentication.signInAsync`, extracts `identityToken`, and calls Plant Gateway `POST /api/v1/auth/apple` with the token
- [x] On success, access token is stored via `secureStorage.setAccessToken()`
- [x] TypeScript compiles with zero errors

**Code patterns to copy exactly:**

```typescript
// app.json — add to "plugins" array:
"expo-apple-authentication"

// eas.json — add iOS profiles (place after prod Android profile):
"uat-ios": {
  "extends": "uat",
  "platform": "ios",
  "distribution": "internal"
},
"prod-ios": {
  "extends": "prod",
  "platform": "ios",
  "distribution": "store"
}

// SignInScreen.tsx — Apple button (render ONLY on iOS):
import { Platform } from 'react-native';
import * as AppleAuthentication from 'expo-apple-authentication';

{Platform.OS === 'ios' && (
  <AppleAuthentication.AppleAuthenticationButton
    buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
    buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
    cornerRadius={12}
    style={{ width: '100%', height: 44 }}
    onPress={handleAppleSignIn}
  />
)}

// authStore.ts — add signInWithApple action:
signInWithApple: async () => {
  const credential = await AppleAuthentication.signInAsync({
    requestedScopes: [
      AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
      AppleAuthentication.AppleAuthenticationScope.EMAIL,
    ],
  });
  const { identityToken } = credential;
  if (!identityToken) throw new Error('Apple Sign-In: missing identity token');
  // Exchange Apple identity token for WAOOAW access token
  const response = await apiClient.post('/api/v1/auth/apple', { identity_token: identityToken });
  await secureStorage.setAccessToken(response.data.access_token);
  set({ user: response.data.user, isAuthenticated: true });
},
```

---

## How to Launch

### Iteration 1 — agent task (Copilot Agent mode)

```
You are implementing MOBILE-NFR-1 Iteration 1 for the WAOOAW mobile app.

Working directory: /workspaces/WAOOAW/src/mobile

Read these files FIRST before writing any code:
1. src/mobile/src/config/sentry.config.ts (full file)
2. src/mobile/src/config/environment.config.ts (lines 100-260)
3. src/mobile/src/hooks/useHiredAgents.ts (full file)
4. src/mobile/src/hooks/useAgents.ts (full file)
5. src/mobile/src/hooks/useAgentDetail.ts (full file)
6. src/mobile/src/hooks/useAgentTypes.ts (full file)
7. src/mobile/src/lib/cpApiClient.ts (full file)
8. src/mobile/src/lib/apiClient.ts (lines 95-145 — retry pattern reference)

Then implement these three stories in order:

--- STORY S1 (45 min) ---
File: src/mobile/src/config/sentry.config.ts
Change: Remove the no-op stub `const Sentry = { ... }` object (lines 7-18).
Change: Restore the real import: `import * as Sentry from '@sentry/react-native';`
Do NOT touch the initSentry() function body — it is already correct.

File: src/mobile/src/config/environment.config.ts
Change: In the UAT config block, set `sentryDsn: process.env.EXPO_PUBLIC_SENTRY_DSN ?? ''`
Change: In the prod config block, set `sentryDsn: process.env.EXPO_PUBLIC_SENTRY_DSN ?? ''`
Leave the development and demo blocks with `sentryDsn: undefined`.

--- STORY S2 (30 min) ---
Files: useHiredAgents.ts, useAgents.ts, useAgentDetail.ts, useAgentTypes.ts
Change: Add `retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000)` 
to EVERY useQuery call that already has `retry: 2` or `retry: 1`.
Do NOT change the retry count values.

--- STORY S3 (45 min) ---
File: src/mobile/src/lib/cpApiClient.ts
Change: Add a response interceptor after the request interceptor inside createCpAxiosInstance().
The interceptor must:
- Retry RETRYABLE_STATUSES = new Set([429, 500, 502, 503, 504]) or network drops
- Max 2 retries using _retryCount property on the config object
- Back-off: Math.min(1000 * Math.pow(2, retryCount), 10000) ms
See the exact code pattern in MOBILE-NFR-1 story S3 code block for copy-paste.

After all three stories: run `npx tsc --noEmit` and fix any TypeScript errors.
Commit: feat(mobile): MOBILE-NFR-1 it1 — Sentry DSN, RQ retryDelay, cpApiClient retry
```

---

### Iteration 2 — agent task (Copilot Agent mode)

```
You are implementing MOBILE-NFR-1 Iteration 2 for the WAOOAW mobile app.
BLOCKED UNTIL: Iteration 1 PR is merged.

Working directory: /workspaces/WAOOAW/src/mobile

Read these files FIRST before writing any code:
1. src/mobile/src/screens/auth/SignUpScreen.tsx (full file)
2. src/mobile/src/screens/auth/OTPVerificationScreen.tsx (full file)
3. src/mobile/src/screens/auth/SignInScreen.tsx (full file)
4. src/mobile/src/stores/authStore.ts (full file)
5. src/mobile/app.json (full file)
6. src/mobile/eas.json (full file)

Then implement these two stories in order:

--- STORY S4 (30 min) ---
File: src/mobile/src/screens/auth/SignUpScreen.tsx
Change: Add useRef-based 2000ms debounce guard to the submit handler.
Add `isSubmitting` state to disable the submit button during API call.
See MOBILE-NFR-1 S4 code block for the exact useRef + Date.now() debounce pattern.

File: src/mobile/src/screens/auth/OTPVerificationScreen.tsx
Change: Add 60-second resend cooldown using setInterval.
The resend button label must show `Resend (Ns)` during cooldown.
Cooldown starts on mount and resets after each successful resend.
See MOBILE-NFR-1 S4 code block for the exact setInterval + setResendCooldown pattern.

--- STORY S5 (90 min) ---
Run first: cd src/mobile && npx expo install expo-apple-authentication

File: src/mobile/app.json
Change: Add "expo-apple-authentication" to the plugins array.

File: src/mobile/eas.json
Change: Add `uat-ios` and `prod-ios` profiles.
See MOBILE-NFR-1 S5 code block for the exact eas.json additions.

File: src/mobile/src/screens/auth/SignInScreen.tsx
Change: Import Platform from react-native and AppleAuthentication from expo-apple-authentication.
Render AppleAuthenticationButton ONLY when Platform.OS === 'ios'.
See MOBILE-NFR-1 S5 code block for button placement and props.

File: src/mobile/src/stores/authStore.ts
Change: Add signInWithApple() async action.
See MOBILE-NFR-1 S5 code block for the identityToken exchange pattern with Plant Gateway POST /api/v1/auth/apple.

After all stories: run `npx tsc --noEmit` and fix any TypeScript errors.
Commit: feat(mobile): MOBILE-NFR-1 it2 — auth throttle, Apple Sign-In, iOS build profile
```
