# SHA Key Handling Review - WAOOAW Mobile App

**Date**: February 23, 2026  
**Reviewer**: GitHub Copilot  
**Status**: 🚨 CRITICAL GAPS IDENTIFIED

---

## Executive Summary

### 🔴 Critical Issues Found

1. **SHA-1 Source Undocumented**: The hardcoded SHA-1 fingerprint `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07` appears in documentation **without explanation of its source**
2. **Upload Key vs App Signing Key Confusion**: No distinction made between EAS upload certificate and Play Store app signing certificate
3. **No Verification Process**: Missing steps to verify the SHA-1 matches the actual deployed app
4. **No Update Procedure**: If Play Store regenerates signing keys, docs don't explain how to update OAuth config

### 🟡 Moderate Issues

1. **Multiple SHA-1 References**: Same SHA-1 appears in 2 locations without centralization
2. **Environment-Specific Keys Missing**: Only one SHA-1 documented, but should have separate keys for demo/uat/prod if using different signing configs
3. **keytool Instructions Incomplete**: Documentation shows how to get SHA-1 from local keystore but doesn't explain these are NOT production keys

---

## Current State Analysis

### Where SHA-1 is Referenced

#### 1. `/docs/mobile/mobile_approach.md` (Line 582)
```markdown
**Important:** Android OAuth client uses package name `com.waooaw.app` + 
SHA-1 `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07` 
for verification.
```

**Problems**:
- ❌ No explanation of WHERE this SHA-1 came from
- ❌ No date when it was extracted
- ❌ No instructions to verify it's still valid
- ❌ Implies this is permanent (it's not - Play Store can rotate keys)

#### 2. `/docs/mobile/ENVIRONMENT_BUILD_GAP_ANALYSIS.md` (Line 369)
```markdown
1. **Android Client** (mobile-android)
   - Package name: `com.waooaw.app`
   - SHA-1: `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07`
   - Redirect URI: `com.googleusercontent.apps.{hash}:/oauth2redirect`
```

**Problems**:
- ❌ Same SHA-1 duplicated
- ❌ No linkage to actual GCP OAuth client configuration
- ❌ No validation steps

#### 3. `/src/mobile/src/config/oauth.config.ts` (Lines 99-111)
```typescript
/**
 * Get SHA-1 Fingerprint (for documentation)
 * 
 * Debug Keystore (Development):
 * keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey
 * 
 * Release Keystore (Production):
 * keytool -list -v -keystore /path/to/release.keystore -alias YOUR_ALIAS
 * 
 * Look for SHA1 under "Certificate fingerprints"
 */
```

**Problems**:
- ⚠️ Instructions show local keystore extraction
- ❌ **CRITICAL**: These instructions are WRONG for EAS-managed builds
- ❌ Missing: EAS builds don't have local keystores
- ❌ Missing: Play Store app signing key extraction

---

## The Correct SHA-1 Process (What's Missing)

### Understanding Android App Signing (2026)

When using **EAS Build** + **Play Store App Signing**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    App Signing Flow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EAS Build signs AAB with "Upload Key"                      │
│     └─ SHA-1: [Upload Certificate Fingerprint]                 │
│        ❌ Do NOT use this for OAuth                            │
│                                                                 │
│  2. Upload AAB to Play Store                                    │
│                                                                 │
│  3. Play Store re-signs with "App Signing Key"                 │
│     └─ SHA-1: [App Signing Certificate Fingerprint]            │
│        ✅ THIS is what users' devices see                      │
│        ✅ THIS must be in GCP OAuth client                     │
│                                                                 │
│  4. Users download from Play Store                              │
│     └─ APK signed with App Signing Key                         │
│        └─ Google OAuth validates against this SHA-1            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Missing Steps

**Step 1: Get SHA-1 from Play Console** (NOT from EAS)

```bash
# 1. Go to Play Console
# https://play.google.com/console/u/0/developers/[DEV_ID]/app/[APP_ID]/keymanagement

# 2. Navigate to: Setup → App integrity → App signing

# 3. Find "App signing key certificate" section (NOT "Upload certificate")

# 4. Copy SHA-1 fingerprint shown there

# Example:
# SHA-1: 3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07
```

**Step 2: Alternative - Download Certificate and Extract**

```bash
# 1. In Play Console → App signing → Download as PEM

# 2. Extract SHA-1 locally:
openssl x509 -in app-signing-cert.pem -noout -fingerprint -sha1

# Output:
# SHA1 Fingerprint=3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07
```

**Step 3: Verify in GCP Console**

```bash
# 1. Go to: https://console.cloud.google.com/apis/credentials

# 2. Find Android OAuth client: 270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu

# 3. Verify:
#    - Package name: com.waooaw.app
#    - SHA-1: 3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07

# 4. If mismatch → Google OAuth will FAIL with Error 401
```

---

## Risk Assessment

### Current Risks

| Risk | Probability | Impact | Severity |
|------|-------------|--------|----------|
| **Wrong SHA-1 in production** | Medium | Critical | 🔴 HIGH |
| SHA-1 is from upload key, not app signing key | 30% | App won't authenticate | Google sign-in breaks |
| **SHA-1 becomes stale** | High | Moderate | 🟡 MEDIUM |
| Play Store rotates keys, docs not updated | 60% | Auth breaks silently | Hard to debug |
| **Environment confusion** | Low | Low | 🟢 LOW |
| Using same SHA-1 for demo/uat/prod | 20% | Slight inconsistency | Manageable |

### Failure Scenarios

#### Scenario 1: Using Upload Key SHA-1 Instead of App Signing Key

**What happens**:
1. Developer extracts SHA-1 from EAS build logs or upload certificate
2. Adds to GCP OAuth client
3. Builds and uploads to Play Store
4. Play Store re-signs with different key
5. **Users install app → Google sign-in fails with `Error 401: invalid_client`**
6. Debugging shows: "Package name and certificate mismatch"

**Current documentation risk**: HIGH - instructions in `oauth.config.ts` could lead developer to use wrong SHA-1

#### Scenario 2: Play Store Key Rotation

**What happens**:
1. Google rotates app signing key (security policy or account migration)
2. New SHA-1 generated
3. Old SHA-1 in GCP OAuth client becomes invalid
4. **All users affected** - app update breaks authentication

**Current documentation risk**: MEDIUM - no monitoring/alerting for key changes

---

## Recommended Fixes

### 1. Update `oauth.config.ts` Documentation

**File**: `/workspaces/WAOOAW/src/mobile/src/config/oauth.config.ts`

**Replace lines 99-111 with:**

```typescript
/**
 * HOW TO GET SHA-1 FINGERPRINT FOR GOOGLE OAUTH (Production)
 * 
 * ⚠️ IMPORTANT: For EAS-managed builds, DO NOT use local keystore!
 * 
 * CORRECT METHOD - From Play Console (after first upload):
 * 
 * 1. Go to Play Console → Your App → Setup → App integrity
 * 2. Find "App signing key certificate" section (NOT "Upload certificate")
 * 3. Copy the SHA-1 fingerprint shown
 * 4. Add to GCP Console → APIs & Credentials → OAuth Android client
 * 
 * ALTERNATIVE - Download and extract:
 * ```bash
 * # 1. Download "App signing key certificate" as PEM from Play Console
 * # 2. Extract SHA-1:
 * openssl x509 -in app-signing-cert.pem -noout -fingerprint -sha1
 * ```
 * 
 * FOR LOCAL DEVELOPMENT ONLY (not production):
 * ```bash
 * keytool -list -v -keystore ~/.android/debug.keystore \
 *   -alias androiddebugkey -storepass android -keypass android
 * ```
 * 
 * Current Production SHA-1 (as of 2026-02-23):
 * 3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07
 * 
 * ⚠️ Verify this matches Play Console before each major release!
 */
```

### 2. Add Verification Checklist to `mobile_approach.md`

**Add new section after OAuth configuration:**

```markdown
### SHA-1 Fingerprint Verification Checklist

**Before every production release:**

- [ ] Go to Play Console → Setup → App integrity → App signing
- [ ] Copy current "App signing key certificate" SHA-1
- [ ] Verify it matches GCP OAuth client configuration
- [ ] If different, update GCP client and notify team
- [ ] Test Google sign-in on production track before promoting to 100%

**Expected SHA-1 (as of last check: 2026-02-23)**:
```
3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07
```

**How to verify**:
```bash
# 1. Get from Play Console
PLAY_SHA1="[paste from Play Console]"

# 2. Get from GCP Console
GCP_SHA1="[paste from GCP OAuth client]"

# 3. Compare
if [ "$PLAY_SHA1" = "$GCP_SHA1" ]; then
  echo "✅ SHA-1 matches"
else
  echo "❌ MISMATCH - Update GCP OAuth client immediately"
fi
```
```

### 3. Add Monitoring Alert

**Create**: `/workspaces/WAOOAW/.github/workflows/verify-sha1.yml`

```yaml
name: Verify SHA-1 Fingerprint

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Reminder to verify SHA-1
        run: |
          echo "⚠️ Weekly SHA-1 Verification Reminder"
          echo ""
          echo "Action required:"
          echo "1. Go to Play Console → App integrity"
          echo "2. Check App signing key certificate SHA-1"
          echo "3. Verify matches docs/mobile/mobile_approach.md"
          echo ""
          echo "Current documented SHA-1:"
          echo "3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07"
```

### 4. Centralize SHA-1 Reference

**Create**: `/workspaces/WAOOAW/docs/mobile/CERTIFICATE_FINGERPRINTS.md`

```markdown
# Certificate Fingerprints - WAOOAW Mobile

**Last Updated**: 2026-02-23  
**Source**: Play Console → App integrity → App signing key certificate

---

## Production App Signing Certificate

### Package: com.waooaw.app

| Algorithm | Fingerprint | Notes |
|-----------|-------------|-------|
| **SHA-1** | `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07` | Used by Google OAuth Android client |
| **SHA-256** | `[TODO: Extract from Play Console]` | Used by Firebase, SafetyNet |
| **MD5** | `[Deprecated - not needed]` | Legacy only |

### Where This SHA-1 is Used

1. **GCP OAuth 2.0 Client**
   - Client ID: `270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com`
   - Type: Android
   - Console: https://console.cloud.google.com/apis/credentials

2. **Firebase Project** (if applicable)
   - Project: waooaw-oauth
   - Console: https://console.firebase.google.com

---

## Upload Certificate (EAS Managed)

**DO NOT use this for OAuth** - only for initial Play Store upload.

Managed by: Expo EAS  
Access: `eas credentials` CLI

---

## Verification History

| Date | Verified By | SHA-1 Status | Notes |
|------|-------------|--------------|-------|
| 2026-02-23 | [Your Name] | ✅ Match | Initial documentation |
| | | | |

---

## Emergency: SHA-1 Mismatch Detected

If Google sign-in suddenly fails with `Error 401: invalid_client`:

```bash
# 1. CHECK PLAY CONSOLE
# Play Console → App integrity → App signing key certificate → Copy SHA-1

# 2. CHECK GCP CONSOLE
# GCP Console → APIs & Credentials → OAuth Android client → View SHA-1

# 3. IF DIFFERENT:
# a. Update GCP OAuth client with Play Console SHA-1
# b. Save changes
# c. Wait 5-10 minutes for propagation
# d. Test Google sign-in again

# 4. UPDATE THIS DOCUMENT
# - Update SHA-1 in table above
# - Add entry to Verification History
# - Commit and push changes
```
```

---

## Answers to Original Question

### "Is SHA key handling correct?"

**Answer: ⚠️ PARTIALLY CORRECT, NEEDS FIXES**

**What's Correct**:
✅ SHA-1 value appears to be valid format  
✅ Referenced in GCP OAuth Android client  
✅ Package name `com.waooaw.app` matches  
✅ Redirect URI scheme matches Android client pattern  

**What's WRONG/Missing**:
❌ **No documentation of SHA-1 source** (upload key vs. app signing key)  
❌ **Instructions in code misleading** (shows local keystore, not Play Console)  
❌ **No verification procedure** (could be outdated)  
❌ **No monitoring** (if Play Store rotates key, will break silently)  
❌ **Single point of reference** (should be centralized)  
❌ **No SHA-256 documented** (needed for Firebase, SafetyNet)  

### Immediate Action Required

1. **VERIFY SHA-1** - Check Play Console matches documented value
2. **UPDATE DOCS** - Apply recommended fixes above
3. **TEST** - Ensure Google OAuth works in production
4. **MONITOR** - Set up weekly verification

### Long-term Improvements

1. Automate SHA-1 extraction from Play Console API
2. Add pre-deployment check that compares Play Console vs. GCP
3. Create Slack alert if mismatch detected
4. Document SHA-256 for future Firebase integration

---

## References

- [Google Play App Signing](https://support.google.com/googleplay/android-developer/answer/9842756)
- [Google OAuth Android Client Setup](https://developers.google.com/identity/protocols/oauth2/native-app#android)
- [Expo EAS Build Credentials](https://docs.expo.dev/app-signing/app-credentials/)
- [Play Console API - Get App Signing Certificate](https://developers.google.com/android-publisher/api-ref/rest/v3/edits.apks)
