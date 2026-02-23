# ✅ Mobile Environment-Specific Build Implementation — Quick Reference

## What Was Done

Implemented **3-layer environment-specific configuration** to eliminate hardcoded credentials and support demo/uat/prod builds:

### Changes Made

| Component | Before | After | Why |
|-----------|--------|-------|-----|
| **eas.json** | OAuth credentials hardcoded in `env` blocks | References `$VARIABLE_NAME` from secrets | Credentials no longer in source code |
| **app.json** | `APP_ENV: "development"` always | Dynamic `app.config.js` reads EAS profile | App detects correct environment at runtime |
| **CI/CD** | No secret injection | GitHub Secrets matrix per env | Builds use correct credentials per environment |
| **Local Dev** | Modify eas.json manually | `.env.local` template | Clean local dev setup |

---

## Files Changed

```
✨ NEW:
  src/mobile/app.config.js                    (Dynamic app config)
  src/mobile/.env.local.example               (Local dev template)
  docs/mobile/GITHUB_SECRETS_SETUP.md         (Secrets guide)
  docs/mobile/IMPLEMENTATION_COMPLETE.md      (This implementation summary)

🔧 MODIFIED:
  src/mobile/eas.json                         (Use $VAR references)
  .github/workflows/mobile-cd.yml             (Inject per-env secrets)

✓ UNCHANGED:
  src/mobile/.gitignore                       (Already excludes .env.local)
```

---

## Next: Set Up Secrets (5 minutes)

### 1. GitHub Repository Secrets

Go to: https://github.com/dlai-sd/WAOOAW/settings/secrets/actions

Create **8 secrets** (4 per environment):

**Demo:**
```
EXPO_PUBLIC_API_URL_DEMO                      = https://plant.demo.waooaw.com
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO    = 270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_DEMO        = 270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com
EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_DEMO       = com.googleusercontent.apps.270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu
```

**Production:**
```
EXPO_PUBLIC_API_URL_PROD                      = https://plant.waooaw.com
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_PROD    = <prod-client-id>
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_PROD        = <prod-client-id>
EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_PROD       = <prod-scheme>
```

### 2. EAS Secrets Vault (Optional but Recommended)

```bash
cd src/mobile
eas secret:create EXPO_PUBLIC_API_URL_DEMO --scope production --value "https://plant.demo.waooaw.com"
eas secret:create EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO --scope production --value "270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com"
# ... repeat for all 8 secrets
```

---

## Test It

### Local Development
```bash
cd src/mobile
cp .env.local.example .env.local
# Edit .env.local with demo credentials (or your local GCP project)
npm start
```

### CI/CD Pipeline
```bash
git tag mobile-v0.1.0-beta.1
git push origin mobile-v0.1.0-beta.1
# -> Triggers GitHub Actions -> EAS Build with demo credentials
```

---

## Key Benefits

| Benefit | Impact |
|---------|--------|
| **No hardcoded credentials** | Can be safely committed; credentials in separate secure vault |
| **Credential rotation in 2 minutes** | Update GitHub Secret; no git commit needed |
| **Per-environment isolation** | demo, uat, prod can have separate OAuth clients |
| **Clean local dev** | `.env.local` file is gitignored; developers don't modify shared files |
| **12-factor compliance** | Config external to code; follows platform standards |

---

## Architecture

```
┌─ EAS Profile (demo, uat, prod)
│
├─ app.config.js (reads EAS_BUILD_PROFILE)
│  └─ Injects environment into app config
│
├─ eas.json (references $VARIABLES)
│  └─ GitHub Secrets (CI/CD) or .env.local (local dev)
│
├─ oauth.config.ts (reads EXPO_PUBLIC_GOOGLE_*)
│  └─ OAuth client IDs from env vars
│
└─ api.config.ts (reads EXPO_PUBLIC_API_URL)
   └─ API endpoint from env vars
```

---

## Documentation

- **Setup Secrets**: `docs/mobile/GITHUB_SECRETS_SETUP.md`
- **Gap Analysis**: `docs/mobile/ENVIRONMENT_BUILD_GAP_ANALYSIS.md`
- **Implementation**: `docs/mobile/IMPLEMENTATION_COMPLETE.md`
- **Mobile Approach**: `docs/mobile/mobile_approach.md` (Section 7 & 13)

---

## Troubleshooting

### ❌ Build fails with "Error 400: invalid_request"
→ OAuth client IDs missing or wrong in GitHub Secrets  
→ Check: `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO` exists and matches GCP

### ❌ "Google OAuth not configured" at runtime
→ `app.config.js` not injecting env vars  
→ Check: `eas.json` uses `$VARIABLE_NAME` syntax

### ❌ Build passes but uses wrong API URL
→ `$EXPO_PUBLIC_API_URL_DEMO` not set in GitHub Secrets  
→ Check: All 8 secrets are created (4 per environment)

**Full troubleshooting**: See `docs/mobile/GITHUB_SECRETS_SETUP.md`

---

## Rollback

If needed, revert is **zero-risk**:

```bash
git revert <commit-hash>  # Reverts code changes
# GitHub Secrets unchanged (independent of code)
# Can restore old behavior by reverting code while keeping new secrets
```

---

🎉 **Ready to test! Start with setting up GitHub Secrets, then test local dev and CI/CD.**
