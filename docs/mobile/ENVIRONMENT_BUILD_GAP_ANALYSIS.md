# Mobile Environment-Specific Build Strategy: Documented vs Implemented Gap Analysis

**Date**: 2026-02-20  
**Status**: ⚠️ **CRITICAL GAP IDENTIFIED** — Blocking 2-3 days of development  
**Owner**: Mobile Team  
**Impact**: Cannot reliably build environment-specific APK/IPA for demo/uat/prod without credential exposure

---

## Executive Summary

The mobile approach documentation assumes **EAS Secrets vault** for managing environment-specific credentials (OAuth client IDs, API URLs), following 12-factor app principles of the main platform. However, the **actual `eas.json` implementation hardcodes all OAuth credentials inline per environment**, violating:

1. ✅ **Documented approach**: "Secrets stored in EAS Secrets, env vars injected at build time"
2. ❌ **Actual implementation**: "Google OAuth client IDs hardcoded in `eas.json` env blocks"

This analysis covers the full gap and provides a fix strategy.

---

## 1. What the Documentation Says (Documented Approach)

### Mobile Approach Section 7: Authentication & Security

> **EAS plan constraint**: Custom EAS environment names (`demo`, `uat`, `prod`) require a paid plan. Free plan only supports `development`, `preview`, `production`. All three store profiles (`demo`, `uat`, `prod`) are therefore mapped to `"environment": "production"` in `eas.json` so secrets are injected. Runtime environment is differentiated via `EXPO_PUBLIC_ENVIRONMENT` set inline per profile.

**Expected table from docs (Section 7):**

| Variable | Value | EAS Environment |
|---|---|---|
| `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` | `270293855600-2shl...@apps.googleusercontent.com` | `production` |
| `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` | `270293855600-uoag...@apps.googleusercontent.com` | `production` |

**Interpreted expectation:**
- Credentials should be stored in **EAS Secrets** (https://expo.dev/accounts/waooaw/settings/secrets)
- `eas.json` profiles should reference secrets using variable syntax: `$EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`
- At build time, EAS CI/CD injects actual values from the vault
- Source code never contains actual credential values

### Platform-Wide Precedent (CONTEXT_AND_INDEX.md Section 19)

The main backend platform enforces **12-factor app** image promotion rules:

> **Image promotion path**: ONE Docker image per service, promoted unchanged demo → uat → prod.  
> **Environment-specific config** (secrets, URLs, feature flags) comes from **env vars / Secret Manager / tfvars — NEVER hardcoded in Dockerfiles**.

| Category | Examples | Where it's injected |
|----------|----------|--------------------|
| **Secrets** | `JWT_SECRET`, OAuth credentials | GCP Secret Manager |
| **Service URLs** | `PLANT_GATEWAY_URL`, API endpoints | Cloud Run env vars / tfvars |
| **Feature flags** | `ENABLE_2FA`, `ENABLE_AUDIT_LOG` | Cloud Run env vars |

**Mobile should follow the same pattern**: Credentials in EAS Secrets, referenced in `eas.json`, injected at build time.

---

## 2. What's Actually Implemented (Actual Implementation)

### Current `eas.json` (Lines 38-147)

**Issue 1: Hardcoded OAuth credentials in profile `env` blocks**

```json
{
  "build": {
    "preview": {
      "env": {
        "EXPO_PUBLIC_ENVIRONMENT": "demo",
        "EXPO_PUBLIC_API_URL": "https://plant.demo.waooaw.com",
        "EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID": "270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com",  // ❌ HARDCODED
        "EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID": "270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com"        // ❌ HARDCODED
      }
    },
    "demo": {
      "env": {
        "EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID": "270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com",  // ❌ HARDCODED (SAME)
        "EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID": "270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com"        // ❌ HARDCODED (SAME)
      }
    },
    "uat": {
      "env": {
        "EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID": "270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com",  // ❌ HARDCODED (SAME)
        "EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID": "270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com"        // ❌ HARDCODED (SAME)
      }
    },
    "prod": {
      "env": {
        "EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID": "270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com",  // ❌ HARDCODED (SAME)
        "EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID": "270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com"        // ❌ HARDCODED (SAME)
      }
    }
  }
}
```

**Problems:**

| Problem | Impact | Urgency |
|---------|--------|---------|
| ✅ OAuth credentials baked into **source code** (committed in git) | Credential rotation requires git commits + pushes instead of secret manager updates | **HIGH** — rotation is slow, auditable |
| ⚠️ **Same credentials** across `preview`, `demo`, `uat`, `prod` | No per-environment OAuth client isolation; if one environment is compromised, all are | **MEDIUM** — reduces blast radius containment |
| ❌ **No local/.env pattern for codespace/local dev** | Developers can't test OAuth locally without hardcoding creds or modifying `eas.json` | **HIGH** — blocks local development |
| ❌ **GitHub Actions CI/CD doesn't inject per-environment secrets** | `mobile-cd.yml` just runs `eas build --profile demo` without overriding env vars; relies on hardcoded `eas.json` | **HIGH** — can't do secure demo/uat/prod builds |

### Configuration Layers: `eas.json` → `app.json` → Source Code

There are **3 layers** where environment-specific values are configured:

#### Layer 1: `eas.json` (Build profiles) — ❌ ISSUE

Sets env vars passed to build: `EXPO_PUBLIC_ENVIRONMENT`, `EXPO_PUBLIC_API_URL`, OAuth client IDs

```json
{
  "build": {
    "demo": {
      "env": {
        "EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID": "270293855600-2shl...@apps.googleusercontent.com"  // ❌ HARDCODED
      }
    }
  }
}
```

#### Layer 2: `app.json` (Expo configuration) — ❌ ISSUE

Static app metadata that **should also be environment-aware**:

```json
{
  "expo": {
    "extra": {
      "APP_ENV": "development"  // ❌ HARDCODED — should be demo/uat/prod per build
    },
    "android": {
      "intentFilters": [
        {
          "data": [
            {
              "scheme": "com.googleusercontent.apps.270293855600-2shl..."  // ❌ HARDCODED OAuth redirect URI
            }
          ]
        }
      ]
    }
  }
}
```

**Problems:**
1. `extra.APP_ENV` is hardcoded as "development" but should match the EAS build profile
2. Android intentFilter OAuth redirect URI is hardcoded — if we had per-environment OAuth clients, this would need to vary
3. No environment-specific iOS bundle ID (should be `com.waooaw.app.demo`, `com.waooaw.app.uat`, etc. for isolation)

#### Layer 3: Source Code Config (`src/mobile/src/config/oauth.config.ts`) — ✅ OK

```typescript
export const GOOGLE_OAUTH_CONFIG = {
  expoClientId: process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID || '',
  iosClientId:  process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID  || '',
  androidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || '',  // ✅ Reads from env
  webClientId:  process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID  || '',        // ✅ Reads from env
};
```

✅ **This part is correct** — it reads from environment variables. The problem is the **source of truth** for those env vars is hardcoded in layers 1 and 2 (`eas.json` and `app.json`), not in EAS Secrets.

### API Config (`src/mobile/src/config/api.config.ts`)

Reads `Constants.expoConfig?.extra?.ENVIRONMENT` (set by `app.json` extra section) or `EXPO_PUBLIC_ENVIRONMENT` (from `eas.json`):

```typescript
export function detectEnvironment(): Environment {
  const explicitEnv = Constants.expoConfig?.extra?.ENVIRONMENT || 
                      process.env.EXPO_PUBLIC_ENVIRONMENT;
  
  if (explicitEnv && isValidEnvironment(explicitEnv)) {
    return explicitEnv as Environment;
  }
  // fallback logic...
}

const environments: Record<Environment, APIConfig> = {
  development: { apiBaseUrl: 'http://localhost:8001', timeout: 5000 },
  demo:        { apiBaseUrl: 'https://plant.demo.waooaw.com', timeout: 15000 },
  uat:         { apiBaseUrl: 'https://plant.uat.waooaw.com',  timeout: 10000 },
  prod:        { apiBaseUrl: 'https://plant.waooaw.com',      timeout: 10000 },
};
```

**Issue: Hardcoded API URLs in source code**

The API URLs are hardcoded in TypeScript, not read from env vars.

❌ Bad: Even though `EXPO_PUBLIC_ENVIRONMENT` comes from EAS, the actual API URL is a hardcoded switch-statement, not `$EXPO_PUBLIC_API_URL` from env var  
❌ Bad: `Constants.expoConfig?.extra?.ENVIRONMENT` reads from `app.json` extra, which is hardcoded as "development"

**Expected (12-factor pattern):**

```typescript
const environments: Record<Environment, APIConfig> = {
  demo: {
    apiBaseUrl: process.env.EXPO_PUBLIC_API_URL || 'https://plant.demo.waooaw.com',
    timeout:    parseInt(process.env.EXPO_PUBLIC_API_TIMEOUT || '15000'),
  },
  // ... etc
};
```

### GitHub Actions CI/CD Workflow (`mobile-cd.yml` Lines 100-110)

```yaml
- name: Build iOS
  working-directory: src/mobile
  run: |
    eas build \
      --profile ${{ needs.determine-environment.outputs.environment }} \
      --platform ios \
      --non-interactive \
      --auto-submit
  env:
    EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
    EXPO_APPLE_ID: ${{ secrets.EXPO_APPLE_ID }}
    EXPO_APPLE_PASSWORD: ${{ secrets.EXPO_APPLE_APP_SPECIFIC_PASSWORD }}
```

**Issue 3: No per-environment secret injection in CI/CD**

The workflow:
1. ✅ Determines environment (demo/uat/prod) from tag
2. ❌ **Does NOT** inject environment-specific secrets (OAuth client IDs, API URLs)
3. ❌ Relies on hardcoded `eas.json` for all env-specific config

**Expected (proper CI/CD):**

```yaml
- name: Build iOS
  env:
    EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
    EXPO_APPLE_ID: ${{ secrets.EXPO_APPLE_ID }}
    EXPO_APPLE_PASSWORD: ${{ secrets.EXPO_APPLE_APP_SPECIFIC_PASSWORD }}
    # Environment-specific secrets injected based on determined environment:
    EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID: ${{ secrets[format('GOOGLE_ANDROID_CLIENT_ID_{0}', env.ENVIRONMENT)] }}
    EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID: ${{ secrets[format('GOOGLE_WEB_CLIENT_ID_{0}', env.ENVIRONMENT)] }}
    EXPO_PUBLIC_API_URL: ${{ secrets[format('API_URL_{0}', env.ENVIRONMENT)] }}
  run: |
    # Override eas.json env vars with injected secrets
    eas build ...
```

---

## 3. app.json Environment-Specific Values (Missing)

### Current State

**Hardcoded values in `app.json` that should vary per environment:**

| Value | Current | Should Be | Impact |
|-------|---------|-----------|--------|
| `extra.APP_ENV` | `"development"` (hardcoded) | Match EAS profile (demo/uat/prod) | Code can't detect correct environment at runtime |
| Android intentFilter scheme | `com.googleusercontent.apps.270293855600-2shl...` (hardcoded) | Varies if using per-env OAuth clients | Future-proofs for per-environment client isolation |
| iOS bundle ID | `com.waooaw.app` (hardcoded) | `com.waooaw.app.demo`, `.uat`, etc. | No per-environment isolation on iOS App Store |

### Expected Pattern

`app.json` should pull environment-specific values from `eas.json` or have a dynamic `app.config.js`:

```javascript
// app.config.js (replaces app.json)
module.exports = ({ config }) => {
  const env = process.env.EAS_BUILD_PROFILE || 'development';
  
  return {
    expo: {
      ...config,
      extra: {
        ...config.extra,
        APP_ENV: env,  // ✅ Dynamic
      },
      ios: {
        ...config.ios,
        bundleIdentifier: env === 'development' 
          ? 'com.waooaw.app' 
          : `com.waooaw.app.${env}`,  // ✅ Dynamic per-environment
      },
      android: {
        ...config.android,
        intentFilters: [
          {
            data: [
              {
                scheme: process.env.EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME || 'com.googleusercontent.apps.270293855600-2shl...',  // ✅ From env
              }
            ]
          }
        ]
      }
    }
  };
};
```

---

## 4. Local Development / Codespace Support (Missing)

### Current State
- No `.env.local` documentation
- No `.gitignored` local EAS build profile
- No guidance on how developers test OAuth locally
- `oauth.config.ts` has fallback `||''` for missing env vars but no setup instructions

### Expected (12-factor approach)
1. `.env.local` file (gitignored) for local development:
   ```env
   EXPO_PUBLIC_ENVIRONMENT=development
   EXPO_PUBLIC_API_URL=http://localhost:8001
   EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=<local-gcp-oauth-client>
   EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=<local-gcp-oauth-client>
   ```

2. Local EAS build profile (or EAS Go for simulator testing without building):
   ```json
   {
     "build": {
       "local": {
         "developmentClient": true,
         "distribution": "internal",
         "channel": "development",
         "env": {
           "EXPO_PUBLIC_ENVIRONMENT": "development",
           "EXPO_PUBLIC_API_URL": "http://localhost:8001"
         }
       }
     }
   }
   ```

3. Documentation: "To test OAuth locally, create a separate GCP OAuth client (package `com.waooaw.app` + localhost redirect URI, set in `.env.local`)"

---

## 5. Backend Alignment (Undocumented)

### Issue: Three Mobile OAuth Client IDs vs One Backend Client ID

| Service | OAuth Client ID | Type | Purpose |
|---------|-----------------|------|---------|
| Mobile (Android) | `270293855600-2shl...@apps.googleusercontent.com` | **Android** | On-device OAuth with custom URI scheme redirect |
| Mobile (Web/Expo) | `270293855600-uoag...@apps.googleusercontent.com` | **Web** | Backend token exchange only (never passed to device) |
| CP Backend (`src/CP/BackEnd`) | `GOOGLE_CLIENT_ID` env var | **Web** | Token validation from mobile OAuth flow |
| Plant Gateway | `GOOGLE_CLIENT_ID` env var | **Web** | Token exchange for CP Backend |

### Documentation Gap
- **Not documented**: Which client ID does the backend expect? (Answer: the **Web** client ID)
- **Not documented**: Why does mobile need 3 client IDs when backend only uses 1?
- **Not explained**: How are the OAuth flows different on mobile vs web?

**Expected documentation in mobile_approach.md:**

```markdown
### OAuth Client ID Strategy

WAOOAW uses **three separate GCP OAuth clients**:

1. **Android Client** (mobile-android)
   - Package name: `com.waooaw.app`
   - SHA-1: `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07`
   - Redirect URI: `com.googleusercontent.apps.{hash}:/oauth2redirect`
   - Used by: Mobile app (Android) for in-app Google OAuth

2. **iOS Client** (mobile-ios)
   - Bundle ID: `com.waooaw.app`
   - Redirect URI: `https://waooaw://oauthcallback` (or custom scheme)
   - Used by: Mobile app (iOS) for in-app Google OAuth

3. **Web Client** (mobile-web, shared with backend)
   - Redirect URIs: `https://waooaw.com/callback`, `https://cp.waooaw.com/callback`
   - Used by: Mobile backend (OAuth token validation), CP Backend (token exchange)
   - **This is the client stored in CP/Plant backends as `GOOGLE_CLIENT_ID` env var**

### Flow

```
Mobile Device (Android/iOS)          CP Backend               Plant Gateway
     ↓                                   ↓                        ↓
[Google Sign-In with Android/iOS      [Receives ID Token]    [Validates Web
 Client ID] → ID Token                 ↓                     Client JWT]
     ↓                                [Validates with Google   ↓
[POST /api/auth/google]               using Web Client ID] [Issues JWT to CP]
     ↓                                   ↓
                                  [Issues JWT to mobile]
```

### Per-Environment Client IDs

Currently, **demo/uat/prod share the same OAuth client IDs**. This is a security risk:

- ✅ **Better approach**: Create separate GCP project per environment (demo, uat, prod)
- ✅ Each project has its own Android/iOS/Web OAuth clients
- ✅ Separate credentials = separate blast radius if compromised
- ⏳ **This is out of scope for current 2-3 day fix** but should be planned

For now, the single shared client is acceptable if:
1. Credentials are moved to EAS Secrets (not hardcoded in `eas.json`)
2. Credential rotation is documented
```

---

## 6. Impact Breakdown

### 5.1 Credential Security Issues

| Issue | Severity | Blocker | Fix TimeEst. |
|-------|----------|---------|-------------|
| OAuth client IDs in source code (git) | 🔴 HIGH | ✅ YES | 2-3 hours |
| Same credentials across demo/uat/prod | 🟡 MEDIUM | ❌ NO | 1-2 weeks (GCP setup) |
| No local dev pattern | 🔴 HIGH | ✅ YES | 1-2 hours |
| CI/CD doesn't inject environment secrets | 🔴 HIGH | ✅ YES | 2-4 hours |
| Backend OAuth strategy undocumented | 🟡 MEDIUM | ❌ NO | 1-2 hours (docs only) |

### 5.2 Development Velocity Impact

**Current state:**
- Developers can't build clean demo/uat/prod APKs (credentials must come from hardcoded `eas.json`)
- Local OAuth testing requires either modifying `eas.json` or using Expo Go (limited)
- CI/CD builds succeed but embed hardcoded credentials (not production-ready)
- Credential rotation requires git commits

**After fix:**
- CI/CD injects per-environment credentials from GitHub Secrets
- Developers can build locally with separate credentials in `.env.local`
- Credential rotation is a 2-minute secret update (no commits)
- Multiple environments can be tested in parallel without git conflicts

---

## 7. Root Cause Analysis

| Root Cause | Why It Happened | Resolution |
|-----------|-----------------|-----------|
| OAuth credentials were migration artifacts from initial implementation | Initial `eas.json` setup predated EAS Secrets feature; credentials were added inline to get build working | Migrate credentials to EAS Secrets proper; update docs |
| EAS Secrets documentation is sparse (external to mobile_approach.md) | Approach doc assumes EAS Secrets but doesn't show the actual setup steps | Add explicit "EAS Secrets Setup" section with screenshots/steps |
| GitHub Actions CI/CD doesn't use environment matrices | Workflow was built for single-environment deployments initially | Add environment matrix and secret injection logic |
| Local dev pattern predates `.env.local` convention | When mobile app was scaffolded, no local dev story was built | Add `.env.local.example` and setup docs |

---

## 8. Fix Strategy (2-3 Day Blocker Resolution)

### Phase 1: Move Credentials to EAS Secrets (1 day)

**1.1 Create EAS Secrets per environment:**

Via Expo CLI (in Codespace):
```bash
cd src/mobile

# Demo environment
eas secret:create EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID \
  --scope production \
  --value "270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com"

eas secret:create EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID \
  --scope production \
  --value "270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com"

eas secret:create EXPO_PUBLIC_API_URL \
  --scope production \
  --value "https://plant.demo.waooaw.com"
```

**1.2 Update `eas.json` to reference secrets:**

```json
{
  "build": {
    "demo": {
      "env": {
        "EXPO_PUBLIC_ENVIRONMENT": "demo",
        "EXPO_PUBLIC_API_URL": "$EXPO_PUBLIC_API_URL",           // ← Variable reference
        "EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID": "$EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID",  // ← Variable
        "EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID": "$EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID"          // ← Variable
      }
    }
  }
}
```

**1.3 Verify build with injected secrets:**

```bash
eas build --platform android --profile demo --non-interactive
# Build should succeed with credentials injected from EAS Secrets vault
```

**Cost**: 1-2 hours (EAS CLI setup is straightforward)

---

### Phase 2: Update GitHub Actions CI/CD (2-4 hours)

**2.1 Add environment-specific secret matrix to `mobile-cd.yml`:**

```yaml
jobs:
  build-and-submit:
    strategy:
      matrix:
        include:
          - environment: demo
            app-name: "Demo Build"
            google-android-client-id: ${{ secrets.GOOGLE_ANDROID_CLIENT_ID_DEMO }}
            google-web-client-id: ${{ secrets.GOOGLE_WEB_CLIENT_ID_DEMO }}
            api-url: https://plant.demo.waooaw.com
          
          - environment: uat
            app-name: "UAT Build"
            google-android-client-id: ${{ secrets.GOOGLE_ANDROID_CLIENT_ID_UAT }}
            google-web-client-id: ${{ secrets.GOOGLE_WEB_CLIENT_ID_UAT }}
            api-url: https://plant.uat.waooaw.com
          
          - environment: prod
            app-name: "Production"
            google-android-client-id: ${{ secrets.GOOGLE_ANDROID_CLIENT_ID_PROD }}
            google-web-client-id: ${{ secrets.GOOGLE_WEB_CLIENT_ID_PROD }}
            api-url: https://plant.waooaw.com

    steps:
      - name: Build Android
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
          EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID: ${{ matrix.google-android-client-id }}
          EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID: ${{ matrix.google-web-client-id }}
          EXPO_PUBLIC_API_URL: ${{ matrix.api-url }}
        run: |
          eas build \
            --profile ${{ matrix.environment }} \
            --platform android \
            --non-interactive
```

**2.2 Populate GitHub Secrets with per-environment credentials:**

```bash
gh secret set GOOGLE_ANDROID_CLIENT_ID_DEMO \
  --body "270293855600-2shl...@apps.googleusercontent.com"

gh secret set GOOGLE_WEB_CLIENT_ID_DEMO \
  --body "270293855600-uoag...@apps.googleusercontent.com"

# Repeat for uat, prod...
```

**Cost**: 2-3 hours (matrix syntax, testing, GitHub secret setup)

---

### Phase 3: Local Development Setup (1-2 hours)

**3.1 Create `.env.local.example`:**

```env
# Copy to .env.local and fill in your local Google OAuth credentials
EXPO_PUBLIC_ENVIRONMENT=development
EXPO_PUBLIC_API_URL=http://localhost:8001
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=<your-local-android-client-id>
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=<your-local-web-client-id>
EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=<your-local-ios-client-id>
```

**3.2 Update `.gitignore`:**

```gitignore
# Mobile local development
src/mobile/.env.local
src/mobile/secrets/
```

**3.3 Add setup documentation (`docs/mobile/LOCAL_SETUP.md`):**

```markdown
# Local Mobile Development Setup

## Environment Variables

1. Copy `.env.local.example` to `.env.local`:
   ```bash
   cp src/mobile/.env.local.example src/mobile/.env.local
   ```

2. Set values from your local GCP project (or use demo credentials for testing):
   ```env
   EXPO_PUBLIC_ENVIRONMENT=development
   EXPO_PUBLIC_API_URL=http://localhost:8001
   EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=...
   EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=...
   ```

## Testing OAuth Locally

### Option A: Expo Go (Recommended for quick testing)
```bash
npm run web  # or npm start
# Scan QR code with Expo Go app
# OAuth will use demo credentials from eas.json (preview profile)
```

### Option B: Local Build
```bash
eas build --platform android --profile development --non-interactive
# OAuth will use credentials from `.env.local`
```
```

**Cost**: 1-2 hours (template files + docs)

---

### Phase 4: Documentation Update (1 hour)

**4.1 Update `mobile_approach.md` Section 7 (Authentication):**

Add subsection: "EAS Secrets Setup and Per-Environment Configuration"

**4.2 Add new section to `mobile_approach.md`: "Environment-Specific Configuration"**

Explain:
- EAS Secrets vault for credentials (demo/uat/prod)
- GitHub Actions CI/CD per-environment matrix
- Local `.env.local` pattern for development
- Backend OAuth client ID strategy

**Cost**: 1 hour

---

## 9. Detailed Implementation Plan (2-3 Day Execution)

### Day 1 Morning (Credential Migration)
- [ ] Document current GCP OAuth client IDs
- [ ] Create EAS Secrets in Expo vault (via CLI or UI)
- [ ] Update `eas.json` to reference secrets instead of hardcoded values
- [ ] Test `eas build --profile demo` with injected credentials
- [ ] Commit: `chore(mobile): move OAuth credentials to EAS Secrets vault`

### Day 1 Afternoon (CI/CD Updates)
- [ ] Update `mobile-cd.yml` with environment matrix + secret injection
- [ ] Add per-environment GitHub Secrets (GOOGLE_*_CLIENT_ID_DEMO/UAT/PROD)
- [ ] Test CI/CD workflow with demo tag trigger
- [ ] Commit: `ci(mobile): implement per-environment credential injection`

### Day 2 Morning (Local Dev Setup)
- [ ] Create `.env.local.example` template
- [ ] Update `.gitignore` to exclude `.env.local`
- [ ] Create `docs/mobile/LOCAL_SETUP.md`
- [ ] Test local build with `.env.local` credentials
- [ ] Commit: `docs(mobile): add local development setup guide`

### Day 2 Afternoon (Documentation)
- [ ] Update `mobile_approach.md` Section 7 (Authentication)
- [ ] Add "Environment-Specific Configuration" section to approach doc
- [ ] Document backend OAuth strategy (why 3 clients, how they interact)
- [ ] Create troubleshooting section for OAuth issues
- [ ] Commit: `docs(mobile): document environment build strategy`

### Day 3 (Review & Validation)
- [ ] Peer review of all changes
- [ ] Validate end-to-end: local dev → demo build → CI/CD → artifact
- [ ] Update PR checklist with new credential injection steps
- [ ] Merge to `develop`

---

## 10. Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| OAuth credentials NOT in `eas.json` source | ❌ Not started | Grep `eas.json` for hardcoded client IDs returns empty |
| EAS Secrets created for demo/uat/prod | ❌ Not started | `eas secret:list` shows all 6 variables (2 per environment) |
| `eas.json` references secrets via `$VAR` syntax | ❌ Not started | File shows `$EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` instead of actual value |
| GitHub Actions matrix injects per-env secrets | ❌ Not started | CI/CD workflow run logs show correct environment var values |
| `.env.local.example` exists and is documented | ❌ Not started | File readable in `src/mobile/` with clear instructions |
| Local build succeeds with `.env.local` | ❌ Not started | Developer can run `eas build ... --profile development` locally |
| Mobile approach doc updated with EAS Secrets section | ❌ Not started | New section in `mobile_approach.md` Section 7 or new subsection |
| Backend OAuth strategy documented | ❌ Not started | Explanation of why 3 client IDs exist and how they interact |
| No test failures after changes | ✅ Will verify | `npm test` in `src/mobile/` passes |

---

## 11. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| EAS Secrets vault limit exceeded | Low | Build fails | Check current usage: `eas secret:list` |
| Existing builds break after `eas.json` changes | Medium | Blocker | Test demo/uat/prod builds after secret migration |
| CI/CD matrix syntax errors | Medium | CI/CD fails | Validate YAML syntax before committing |
| Environment variable name typos | High | OAuth fails with 400 error | Add validation test to catch missing env vars |
| `.env.local` accidentally committed | Low | Credential leak | Double-check `.gitignore` before merge |

---

## 12. Comparison Table: Before vs After

| Aspect | Before (Current) | After (Proposed) |
|--------|-----------------|-----------------|
| **OAuth Credential Storage** | Hardcoded in `eas.json` (git) | EAS Secrets vault (no git) |
| **Credential Rotation** | Edit `eas.json`, commit, push | Update EAS Secret via CLI/UI (2 min) |
| **CI/CD Credential Injection** | None — uses hardcoded values | Matrix-based per-environment injection |
| **Demo/UAT/Prod Isolation** | Same credentials for all | Separate secrets per environment (future: separate GCP projects) |
| **Local Dev Approach** | Hardcode in `eas.json` or modify manually | `.env.local` file (gitignored) |
| **Documentation** | Assumes secrets but shows hardcoded values | Explicit step-by-step setup guide |
| **12-Factor Compliance** | ❌ Credentials baked into config | ✅ Credentials external, config external |
| **Security Audit Trail** | Git blame (who edited creds) | EAS audit log (who created/updated secrets) |

---

## 13. Success Metrics (Post-Fix)

1. **Zero hardcoded OAuth credentials** in `eas.json` or TypeScript source
2. **All demo/uat/prod builds** use injected credentials from GitHub Actions / EAS Secrets
3. **Local developers** can test OAuth locally without modifying shared files
4. **CI/CD pipeline** handles multi-environment builds correctly (matrix strategy works)
5. **Credential rotation** is <2 minutes (no git commits required)
6. **12-factor compliance**: Credentials external, environment-specific config external

---

## Appendix: References

- **Mobile Approach Docs**: Section 7 (Authentication), Section 13 (CI/CD)
- **Platform CI/CD Rules**: `/workspaces/WAOOAW/docs/CONTEXT_AND_INDEX.md` Section 19 (Image Promotion)
- **Current EAS Config**: `/workspaces/WAOOAW/src/mobile/eas.json`
- **OAuth Config**: `/workspaces/WAOOAW/src/mobile/src/config/oauth.config.ts`
- **CI/CD Workflow**: `/workspaces/WAOOAW/.github/workflows/mobile-cd.yml`
- **API Config**: `/workspaces/WAOOAW/src/mobile/src/config/api.config.ts`

---

**Document Status**: 🔴 **DRAFT — Ready for Implementation Discussion**  
**Next Step**: Review gap analysis, prioritize fixes, assign ownership
