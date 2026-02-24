# Mobile App — DEVELOPER_ERROR Fix (Play App Signing SHA-1)

**Date**: February 24, 2026  
**Work Session**: Google Sign-In `DEVELOPER_ERROR` root cause analysis & fix  
**Status**: Fix committed (PR #755, awaiting merge) — Play Store build pending to verify on device

---

## Session Summary

Workflow run **"Mobile Google Play Store Deployment #84"** successfully built the AAB, submitted it to Expo, and uploaded it to the Google Play internal track. The internal tester received the update on device. However, Google Sign-In immediately threw `DEVELOPER_ERROR` (error code 10) on every attempt.

This session identified the root cause, applied the fix across all three required registration points, committed the change, and opened PR #755.

### Baseline Outcome

| Gate | Result | Notes |
|------|--------|-------|
| RCA identified | ✅ Complete | Play App Signing SHA-1 mismatch confirmed |
| `google-services.json` updated | ✅ Committed | PR #755 — second type-1 OAuth entry added |
| Firebase Console updated | ✅ Manual (done) | SHA-1 added to `com.waooaw.app` fingerprints |
| GCP OAuth client updated | ✅ Manual (done) | SHA-1 added to Android OAuth client |
| Play Store build with fix | ⏳ Pending | Trigger workflow after PR merge |
| On-device verification | ⏳ Pending | Results to follow after build lands |

---

## Root-Cause to Fix Mapping

| Root cause | Impact | Best possible solution/fix |
|-----------|--------|----------------------------|
| Google Play re-signs all AABs with its own **App Signing key** before delivery — the device's installed APK certificate SHA-1 (`8fd589b1…`) did not match the only registered hash (`14f7ccef…` — EAS upload keystore) | `DEVELOPER_ERROR` on every Google Sign-In attempt; fails before any network call | Added Play App Signing SHA-1 as a second type-1 Android OAuth client in `google-services.json`; same SHA-1 also registered in Firebase Console and GCP OAuth Android client |
| `google-services.json` only contained the EAS upload keystore SHA-1 (`14f7ccef…`) — no entry for the Google Play signing key | Both SHA-1s needed: one for direct APK installs (EAS/debug), one for Play Store delivered builds | Two `oauth_client` type-1 entries under `com.waooaw.app` — one per signing key |
| The `certificate_hash` stored was not the EAS upload key either — it was from a third keystore entirely (`14f7ccef` ≠ upload key `3ae569d6`) | Deep mismatch: three distinct SHA-1s involved (mystery keystore, EAS upload key, Play signing key) | Play signing SHA-1 is the authoritative one for Play-delivered apps; both EAS upload and Play signing are now registered |

---

## Key SHA-1 Reference (permanent record)

| Key | SHA-1 | Where registered |
|---|---|---|
| Mystery/historic keystore (was in `google-services.json`) | `14:F7:CC:EF:B7:D5:1C:1B:2F:FE:01:97:A5:D2:F6:9B:4F:B6:74:95` | `google-services.json` (kept for compatibility) |
| EAS upload key (signs AAB before Play upload) | `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07` | Firebase (pre-existing), GCP OAuth (pre-existing) |
| **Google Play App Signing key** (signs APK delivered to device) | `8F:D5:89:B1:20:14:85:E3:73:E8:0C:C0:B0:1B:56:74:E5:2F:5F:FA` | **`google-services.json` (added PR #755), Firebase (manual), GCP (manual)** |

> **How to re-verify Play signing SHA-1**: Play Console → WAOOAW app → Setup → App integrity → App signing tab → "App signing key certificate" section → SHA-1 fingerprint.

---

## Files Updated During Session

- `src/mobile/google-services.json` — added second `oauth_client` type-1 entry with Play App Signing SHA-1
- `docs/CONTEXT_AND_INDEX.md` — version 1.4 → 1.5; updated §12 (Latest Changes), §17 (Gotchas), §23 (Mobile DEVELOPER_ERROR note)

### Manual configuration (outside codebase)

| System | Action taken | Where |
|---|---|---|
| Firebase Console | Added SHA-1 `8F:D5:89…` to `com.waooaw.app` fingerprints | console.firebase.google.com → waooaw-oauth → Project Settings → Your apps |
| GCP Console | Added SHA-1 `8F:D5:89…` to Android OAuth client `270293855600-2shlgots…` | console.cloud.google.com/apis/credentials → waooaw-oauth |

---

## Play Console Navigation Reference (discovered this session)

For future reference — the "App integrity" section is only reachable **from within the app**, not from the developer account settings page:

1. Play Console Home → click app (WAOOAW)
2. Left sidebar → scroll past Test and release, Monitor and improve, Grow users, Monetize with Play
3. **Setup** section → **App integrity**
4. On the App integrity page → click **"App signing"** card (not "Play Integrity API")
5. SHA-1 is shown under **"App signing key certificate"** (not "Upload key certificate")

> ⚠️ App integrity is available even for apps that are not yet approved/published — the signing key is assigned the moment the first AAB is processed by Google Play.

---

## How DEVELOPER_ERROR works (for future debugging)

```
EAS builds AAB → signed with EAS upload keystore
                         ↓
Google Play re-signs APK with Play App Signing key (DIFFERENT SHA-1)
                         ↓
Device installs APK signed by Google's key
                         ↓
@react-native-google-signin reads APK signing cert → sends SHA-1 to Google Play Services
                         ↓
Google Play Services looks up SHA-1 in GCP Android OAuth client
                         ↓
No match found → DEVELOPER_ERROR (code 10) — fails locally, no network call made
```

The fix: register the Play App Signing SHA-1 everywhere GCP validates it (GCP OAuth client, Firebase, `google-services.json`).

---

## Deployment Readiness Snapshot

| Area | Current state | Next action |
|------|---------------|-------------|
| Root cause | Confirmed and fixed | — |
| `google-services.json` | Updated with Play signing SHA-1 | Merge PR #755 |
| Firebase Console | Play signing SHA-1 registered | — (done) |
| GCP OAuth Android client | Play signing SHA-1 registered | — (done) |
| Play Store build | Not yet triggered with fix | Run "Mobile Google Play Store Deployment" workflow after merge, `demo` / `internal` / `expo` |
| On-device verification | Pending | Install update from Play internal track → tap "Sign in with Google" → should succeed without `DEVELOPER_ERROR` |

---

## Next Session Priorities

1. Confirm workflow run after PR #755 merge completes successfully (build + Play upload).
2. Install the updated build from Google Play internal track on test device.
3. Verify Google Sign-In completes without `DEVELOPER_ERROR`.
4. If sign-in succeeds but backend returns 401 — check that `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_DEMO` EAS secret matches the web client ID (`270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq`) that the Plant backend verifies against.
5. If sign-in succeeds and auth completes — mark mobile Google Sign-In as end-to-end verified on Play Store build.
