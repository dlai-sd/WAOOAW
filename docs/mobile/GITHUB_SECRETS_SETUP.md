# GitHub Actions Secrets Configuration for Mobile CD/CD

This document explains how to configure GitHub repository secrets for mobile environment-specific builds.

## Overview

The mobile CI/CD pipeline (`mobile-cd.yml`) injects per-environment secrets during EAS builds. These secrets are referenced in `eas.json` as `$VARIABLE_NAME` syntax and replaced at build time.

**Environments:**
- `demo`: Internal testing, Play Store internal testing track
- `prod`: Production (App Store & Play Store)

## Required GitHub Secrets

Create the following repository secrets in GitHub (Settings → Secrets and variables → Actions):

### Demo Environment Secrets

| Secret Name | Value | Description |
|---|---|---|
| `EXPO_PUBLIC_API_URL_DEMO` | `https://plant.demo.waooaw.com` | Demo API Gateway URL |
| `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO` | `270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com` | Demo Android OAuth client ID (from GCP) |
| `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_DEMO` | `270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com` | Demo Web OAuth client ID (from GCP) |
| `EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_DEMO` | `com.googleusercontent.apps.270293855600-2shl...` | Demo OAuth redirect scheme (extracted from Android client ID) |

### Production Environment Secrets

| Secret Name | Value | Description |
|---|---|---|
| `EXPO_PUBLIC_API_URL_PROD` | `https://plant.waooaw.com` | Production API Gateway URL |
| `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_PROD` | `<production-android-client-id>` | Production Android OAuth client ID (from GCP) |
| `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_PROD` | `<production-web-client-id>` | Production Web OAuth client ID (from GCP) |
| `EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_PROD` | `com.googleusercontent.apps.<prod-client-hash>` | Production OAuth redirect scheme |

### Existing Secrets (Already Configured)

These should already exist in your GitHub repository:

| Secret Name | Purpose |
|---|---|
| `EXPO_TOKEN` | EAS Build authentication token |
| `EXPO_APPLE_ID` | Apple ID for iOS submission |
| `EXPO_APPLE_APP_SPECIFIC_PASSWORD` | App-specific password for Apple ID |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_KEY` | Google Play service account JSON (base64 encoded) |

## How to Set Up Secrets

### Option 1: GitHub UI (Recommended for visibility)

1. Go to: https://github.com/dlai-sd/WAOOAW/settings/secrets/actions
2. Click **New repository secret**
3. Enter secret name (e.g., `EXPO_PUBLIC_API_URL_DEMO`)
4. Paste the value
5. Click **Add secret**
6. Repeat for all secrets in the table above

### Option 2: GitHub CLI

```bash
# Demo environment secrets
gh secret set EXPO_PUBLIC_API_URL_DEMO --body "https://plant.demo.waooaw.com"
gh secret set EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO --body "270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com"
gh secret set EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_DEMO --body "270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com"
gh secret set EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_DEMO --body "com.googleusercontent.apps.270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu"

# Production environment secrets (fill in actual values)
gh secret set EXPO_PUBLIC_API_URL_PROD --body "https://plant.waooaw.com"
gh secret set EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_PROD --body "<prod-android-client-id>"
gh secret set EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_PROD --body "<prod-web-client-id>"
gh secret set EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_PROD --body "<prod-oauth-scheme>"
```

### Option 3: Bulk Update (Script)

Create a file `secrets.env`:

```env
EXPO_PUBLIC_API_URL_DEMO=https://plant.demo.waooaw.com
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO=270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_DEMO=270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com
EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_DEMO=com.googleusercontent.apps.270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu
EXPO_PUBLIC_API_URL_PROD=https://plant.waooaw.com
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_PROD=<prod-android-client-id>
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_PROD=<prod-web-client-id>
EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_PROD=<prod-oauth-scheme>
```

Then run:

```bash
while IFS='=' read -r key value; do
  gh secret set "$key" --body "$value"
done < secrets.env
```

## Secret Injection Flow

```
GitHub Secret                          ↓
(EXPO_PUBLIC_API_URL_DEMO)            
                                      ↓
GitHub Actions Workflow               
(mobile-cd.yml: env: {...})           
                                      ↓
EAS Build                             
(--profile demo)                       
                                      ↓
eas.json                              
("EXPO_PUBLIC_API_URL": "$EXPO_PUBLIC_API_URL_DEMO")
                                      ↓
app.config.js                         
(reads process.env variables)         
                                      ↓
Build Output                          
(APK/IPA with environment-specific config)
```

## Verification

After setting secrets, verify that builds work:

```bash
# Trigger a build with a beta tag (staging environment)
git tag mobile-v0.1.0-beta.1
git push origin mobile-v0.1.0-beta.1

# Check GitHub Actions: https://github.com/dlai-sd/WAOOAW/actions
# Look for "Mobile CD (Deployment)" job and verify build passes
```

If the build fails with `Error 400: invalid_request — invalid client`, the secrets are likely not set correctly. Check:

1. Are all `EXPO_PUBLIC_GOOGLE_*` secrets present in GitHub?
2. Are the values exactly correct (no extra spaces, wrong client IDs)?
3. Is the EAS token (`EXPO_TOKEN`) valid?

## Rotating Secrets

To rotate a secret (e.g., if credentials were compromised):

1. Generate new credentials in GCP OAuth console or API provider
2. Update GitHub repository secret: Go to Settings → Secrets → Edit secret → Update value
3. No code changes required — next build will use new credentials
4. Old secret expires automatically (no git commit needed)

## Security Best Practices

1. **Never hardcode secrets in source code** — All credentials are in GitHub Secrets
2. **Limit secret access** — Only the `mobile-cd.yml` workflow can see these secrets
3. **Audit trail** — GitHub logs all secret access; check audit log regularly
4. **Rotation schedule** — Rotate secrets every 90 days
5. **Least privilege** — OAuth clients should have minimal required scopes

## Troubleshooting

### Build fails with `Error 400: invalid_request`

**Cause:** OAuth client IDs don't match or are missing from GitHub Secrets

**Fix:**
1. Verify secret names match exactly: `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO`
2. Verify values are correct (copy-paste from GCP console to avoid typos)
3. Check that all 8 secrets are set (4 per environment: API URL, Android ID, Web ID, OAuth scheme)

### Build passes but app shows "Google OAuth not configured"

**Cause:** `app.config.js` is not picking up injected env vars

**Fix:**
1. Verify `app.config.js` exports a function (not static object)
2. Check that `eas.json` uses `$VARIABLE_NAME` syntax in env blocks
3. Run local test: `EXPO_PUBLIC_API_URL_DEMO=test eas build --profile demo --non-interactive`

### Secrets not visible in workflow logs

**This is expected** — GitHub automatically masks secrets in logs for security. You'll see `***` instead of actual values.

## References

- [GitHub Encrypted secrets documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [EAS Build Secrets documentation](https://docs.expo.dev/build-reference/variables/)
- [WAOOAW Mobile CD Workflow](.github/workflows/mobile-cd.yml)
- [EAS Configuration](src/mobile/eas.json)
- [App Configuration](src/mobile/app.config.js)
