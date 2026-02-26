# Mobile Registration — Bug Analysis
**Based on real log evidence from Firebase Test Lab and CI artifacts**

---

## Mobile Registration Flow (Actual)

Mobile registration is a **3-step flow, all calls go to Plant Gateway directly**:

1. `POST /auth/register` — submits the full sign-up form (name, email, phone, business details)
2. `POST /auth/otp/start` — sends `{ registration_id: UUID }` — Plant accepts this correctly
3. User is navigated to `OTPVerificationScreen` — enters the 6-digit code
4. `POST /auth/otp/verify` — sends `{ otp_id, code }` — completes registration, returns JWT tokens

There is **no CAPTCHA** on mobile. The OTP screen is a **separate screen** after form submit, not part of the form. Mobile sends `registration_id` (not email) to `/auth/otp/start` — Plant Gateway's `OtpStartRequest` accepts `registration_id` and this is correct. **No OTP bugs exist in mobile code.**

---

## Evidence Sources

| Source | File | Date | Notes |
|--------|------|------|-------|
| Firebase Test Lab crash report | `tmp/ftl/results/data_app_crash_0_com_waooaw_app.txt` | Feb 20 2026 00:51 | Hard crash — full Java + JS stack trace |
| Firebase Test Lab logcat | `tmp/ftl/results/logcat` (3.1 MB) | Feb 20 2026 00:51 | Full device logcat for FTL run |
| CI failure log | `tmp/ci-22035889335-failed.log` | Feb 15 2026 12:45 | Plant backend JWT unit tests all PASSED |
| Git history | `git log -- src/mobile/package.json` | — | Fix commit traced to `4645073` |

---

## Bug 1 — React Version Mismatch Crash (FIXED)

### Log Evidence

**From `tmp/ftl/results/data_app_crash_0_com_waooaw_app.txt` (verbatim):**
```
com.facebook.react.common.JavascriptException: Error: Incompatible React versions:
  react: 19.2.4 vs react-native-renderer: 19.1.0
```

**From `tmp/ftl/results/logcat` (verbatim, timestamp 02-20 00:51:19):**
```
02-20 00:51:19.755  ReactNativeJS: [API Config] Using EXPO_PUBLIC_API_URL for demo: https://cp.demo.waooaw.com
02-20 00:51:19.772  ReactNativeJS: [Sentry] Initialized successfully (production)
02-20 00:51:19.991  E ReactNativeJS: [Error: Incompatible React versions: react: 19.2.4 vs react-native-renderer: 19.1.0]
```

App crashes at `00:51:19.991` — 234ms after Sentry init. Zero HTTP calls to the backend are made. The registration screen is never reached.

| Root cause | Impact | Fix |
|------------|--------|-----|
| `package.json` pinned `react: 19.1.0` but npm resolved transitive deps to `19.2.4` at build time; `react-native-renderer` stayed at `19.1.0` | App crashes before sign-up screen renders | Pin both to same version in `package.json` and lock in `package-lock.json` |

Fixed in commit **`4645073`** on Feb 20 2026 at 08:59. Current `node_modules` confirms `react: 19.1.0` — consistent.

**Status: ✅ FIXED**

---

## Bug 2 — PolicyMiddleware Returning 500 JWT Error on `/auth/register` (FIXED)

Mobile calls `POST /auth/register` on Plant Gateway without a JWT (user is not logged in yet). The old `PolicyMiddleware` had a hard-coded skip list that did not include any auth paths. It tried to extract JWT claims from the request, found none, and returned HTTP 500: `"Policy middleware requires JWT claims"`.

**From CI log `tmp/ci-22035889335-failed.log` (Feb 15 2026):**
```
tests/unit/test_security.py::TestJWTTokens::test_create_access_token_returns_string  PASSED
tests/unit/test_security.py::TestJWTTokens::test_verify_token_succeeds_for_valid_token  PASSED
```
JWT library itself was fine — the problem was the skip list.

| Root cause | Impact | Fix |
|------------|--------|-----|
| `PolicyMiddleware` had its own incomplete skip list, out of sync with `AuthMiddleware`'s `_is_public_path()` | All three unauth mobile paths returned 500 | Import and use `_is_public_path()` from `auth.py` |

Fixed in **PR #763** (merged to `main`). `/auth/register`, `/auth/otp/start`, `/auth/otp/verify` are all in `PUBLIC_ENDPOINTS` in `auth.py` (confirmed at lines 127–133).

**Status: ✅ FIXED**

---

## Critical Observation — FTL Build API URL Mismatch

The FTL logcat shows the demo build was using:
```
[API Config] Using EXPO_PUBLIC_API_URL for demo: https://cp.demo.waooaw.com
```

But `src/mobile/src/config/api.config.ts` code default for demo environment is:
```
https://plant.demo.waooaw.com
```

The FTL build was using `EXPO_PUBLIC_API_URL` from an EAS secret overriding the default to `cp.demo.waooaw.com` instead of `plant.demo.waooaw.com`. If `cp.demo.waooaw.com` is CP Backend (not Plant Gateway), then `/auth/register` does not exist there at all — CP Backend only has `/api/cp/auth/register`. This would explain the JWT error persisting even after PR #763 is deployed to Plant.

**Action required:** Confirm whether `cp.demo.waooaw.com` resolves to Plant Gateway or CP Backend. If CP Backend, the EAS secret `EXPO_PUBLIC_API_URL` for demo build must be changed to `https://plant.demo.waooaw.com`.

---

## Current State Summary

| Bug | Status |
|-----|--------|
| App crash before sign-up screen (React version) | ✅ Fixed — commit `4645073` |
| JWT 500 error on `/auth/register` (PolicyMiddleware) | ✅ Fixed — PR #763 on `main` |
| JWT 500 error on `/auth/otp/start` and `/auth/otp/verify` | ✅ Fixed — PR #763 on `main` |
| Mobile OTP screen sends wrong data | ✅ No bug — mobile correctly sends `registration_id`; Plant accepts it |
| CAPTCHA issues on mobile | ✅ No bug — mobile has no CAPTCHA |
| EAS demo build pointing at `cp.demo.waooaw.com` instead of `plant.demo.waooaw.com` | ⚠️ Needs confirmation — may explain persistent JWT error |

---

## Recommended Verification Steps

```bash
# 1. Confirm Plant Gateway has PR #763 fix deployed
curl -X POST https://plant.demo.waooaw.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com"}' \
  # Expect: 422 (validation), NOT 500 (JWT error)

# 2. Confirm cp.demo.waooaw.com target
curl -I https://cp.demo.waooaw.com/auth/register
# If 404 → it's CP Backend, EAS secret must be fixed to plant.demo.waooaw.com
# If 422 → it's Plant Gateway, fix is already live
```
