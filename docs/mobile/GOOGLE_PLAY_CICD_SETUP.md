# WAOOAW Mobile - Google Play Store CI/CD Setup Guide

**Date**: February 19, 2026  
**Status**: Ready for deployment  
**Backend**: GCP Demo (https://waooaw-api-demo-ryvhxvrdna-el.a.run.app)

---

## 🎉 What Was Fixed

### Critical Bug - OTA App Not Working

**Root Cause Identified**: The mobile app had two conflicting configuration systems:
- `api.config.ts` used hardcoded URLs (`https://cp.demo.waooaw.com`)
- `eas.json` set `EXPO_PUBLIC_API_URL` to correct backend (`https://waooaw-api-demo-ryvhxvrdna-el.a.run.app`)

**Problem**: `api.config.ts` did NOT read `EXPO_PUBLIC_API_URL`, causing the app to connect to non-existent backend.

**Solution Applied**:
1. ✅ Updated `api.config.ts` to read `EXPO_PUBLIC_API_URL` environment variable
2. ✅ Added proper environment detection from `APP_ENV` in eas.json
3. ✅ Added `EXPO_PUBLIC_ENVIRONMENT` for explicit environment detection
4. ✅ Created new `demo-store` build profile for Play Store (AAB format)
5. ✅ Increased timeout to 15s for Cloud Run cold starts

**Files Modified**:
- `src/mobile/src/config/api.config.ts` - Now reads environment variables
- `src/mobile/eas.json` - Added `demo-store` profile and environment variables
- `.github/workflows/mobile-playstore-deploy.yml` - NEW automated deployment workflow

---

## 🚀 Quick Start - Deploy to Play Store NOW

### Option 1: Manual Workflow Dispatch (Recommended for First Deployment)

```bash
# 1. Go to GitHub Actions
# https://github.com/dlai-sd/WAOOAW/actions/workflows/mobile-playstore-deploy.yml

# 2. Click "Run workflow"
# 3. Select:
#    - Environment: demo
#    - Track: internal
#    - Release notes: "Initial demo release with GCP backend"

# 4. Click "Run workflow"
```

**What happens**:
- ✅ Runs lint, typecheck, and tests
- ✅ Builds Android App Bundle (AAB) with demo backend
- ✅ Submits to Google Play Store internal track
- ✅ Sends Slack notification (if configured)
- ✅ Takes ~20-30 minutes total

### Option 2: Tag-Based Deployment

```bash
# For demo/internal releases
git tag mobile-playstore-v1.0.0-demo.1
git push origin mobile-playstore-v1.0.0-demo.1

# For production releases (after testing)
git tag mobile-playstore-v1.0.0
git push origin mobile-playstore-v1.0.0
```

---

## 📋 Prerequisites Setup (One-Time)

### 1. GitHub Secrets (CRITICAL - Required Before First Deployment)

Navigate to: `https://github.com/dlai-sd/WAOOAW/settings/secrets/actions`

Add these secrets:

#### **EXPO_TOKEN** (Required)
```bash
# 1. Install EAS CLI
npm install -g eas-cli

# 2. Login to Expo
eas login

# 3. Generate token
eas whoami
# Copy your Expo account name

# 4. Generate token
eas build:configure
# This will show your token or you can get it from:
# https://expo.dev/accounts/[your-account]/settings/access-tokens

# 5. Add to GitHub Secrets
# Name: EXPO_TOKEN
# Value: [your token from above]
```

#### **GOOGLE_PLAY_SERVICE_ACCOUNT_JSON** (Required)
```bash
# 1. Go to Google Play Console
# https://play.google.com/console/u/0/developers/[YOUR_DEVELOPER_ID]/api-access

# 2. Click "Create new service account"

# 3. Follow these steps:
#    a. Go to Google Cloud Console
#    b. Create new service account
#    c. Name: "waooaw-mobile-deployment"
#    d. Grant role: "Service Account User"

# 4. Create JSON key:
#    a. Click on service account
#    b. Keys tab → Add Key → Create new key
#    c. Choose JSON format
#    d. Download the JSON file

# 5. In Play Console:
#    a. Done → Grant access
#    b. App permissions → Select WAOOAW app
#    c. Account permissions:
#       ✅ View app information and download bulk reports (read-only)
#       ✅ Release apps to testing tracks
#       ✅ Release apps to production

# 6. Copy ENTIRE contents of downloaded JSON file

# 7. Add to GitHub Secrets:
# Name: GOOGLE_PLAY_SERVICE_ACCOUNT_JSON
# Value: [paste entire JSON content]
```

Example JSON structure (DO NOT use this, use your own):
```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "waooaw-mobile-deployment@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

#### **SLACK_WEBHOOK** (Optional - for notifications)
```bash
# 1. Go to Slack App settings
# https://api.slack.com/apps

# 2. Create new app or select existing

# 3. Incoming Webhooks → Add New Webhook to Workspace

# 4. Copy webhook URL

# 5. Add to GitHub Secrets:
# Name: SLACK_WEBHOOK
# Value: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### **GOOGLE_PLAY_DEVELOPER_ID** (Optional - for environment URL)
```bash
# 1. Go to Play Console
# 2. Copy developer ID from URL
# https://play.google.com/console/u/0/developers/[THIS_IS_YOUR_ID]/

# 3. Add to GitHub Secrets:
# Name: GOOGLE_PLAY_DEVELOPER_ID
# Value: [your developer ID]
```

#### **GOOGLE_PLAY_APP_ID** (Optional - for environment URL)
```bash
# 1. Go to Play Console → Your App
# 2. Copy app ID from URL or App Integrity section
# Usually starts with digits, e.g., 4975500000000000000

# 3. Add to GitHub Secrets:
# Name: GOOGLE_PLAY_APP_ID
# Value: [your app ID]
```

---

### 2. Google Play Store App Setup (One-Time)

If you haven't created the app listing yet:

```bash
# Manual creation in Play Console:

1. Go to https://play.google.com/console
2. Click "Create app"
3. Fill in:
   - App name: WAOOAW
   - Default language: English (United States)
   - App or game: App
   - Free or paid: Free
   - Category: Business
4. Accept declarations
5. Create app

# Complete these sections (can be done after first upload):
- Store listing (descriptions, screenshots)
- Content rating questionnaire
- Target audience
- Privacy policy
- App content
```

---

## 🔄 Deployment Workflows

### Demo/Internal Testing Track

**When to use**: Initial testing, QA, beta testers

```bash
# Option A: Workflow Dispatch
1. Go to GitHub Actions
2. Run workflow: mobile-playstore-deploy.yml
3. Select:
   - Environment: demo
   - Track: internal
   - Release notes: Your notes here

# Option B: Git Tag
git tag mobile-playstore-v1.0.0-demo.1
git push origin mobile-playstore-v1.0.0-demo.1
```

**What happens**:
- Builds with `demo-store` profile
- Backend: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app
- Submits to internal track (up to 100 testers)
- Available within 1-2 hours

### Production Track

**When to use**: Public release to all users

```bash
# Option A: Workflow Dispatch
1. Go to GitHub Actions
2. Run workflow: mobile-playstore-deploy.yml
3. Select:
   - Environment: production
   - Track: production
   - Release notes: Your notes here

# Option B: Git Tag (recommended)
git tag mobile-playstore-v1.0.0
git push origin mobile-playstore-v1.0.0
```

**What happens**:
- Builds with `production` profile
- Backend: https://api.waooaw.com
- Submits to production track
- Creates GitHub release
- Review by Google: 1-3 days

---

## 🧪 Testing Before Play Store Submission

### Test the Fixed App Locally

```bash
cd /workspaces/WAOOAW/src/mobile

# Build demo APK with fixes
eas build --profile demo --platform android

# This will now correctly use:
# - Backend: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app
# - Timeout: 15s (for cold starts)
# - Environment: demo
```

After build completes (~15 minutes):
1. Download APK from EAS
2. Install on Android device
3. **Verify**:
   - App launches without errors
   - Skip sign-in works
   - Bottom navigation works
   - API calls succeed (check with agent discovery screen)
   - No network timeout errors

### Debug API Configuration

Add this to check at runtime:

```javascript
// In App.tsx or any screen
import { getAPIConfig, getCurrentEnvironment } from './src/config/api.config';

console.log('🔍 DEBUG API Config:', {
  environment: getCurrentEnvironment(),
  apiUrl: getAPIConfig().apiBaseUrl,
  envVar: process.env.EXPO_PUBLIC_API_URL,
});
```

Expected output (demo build):
```
🔍 DEBUG API Config: {
  environment: "demo",
  apiUrl: "https://waooaw-api-demo-ryvhxvrdna-el.a.run.app",
  envVar: "https://waooaw-api-demo-ryvhxvrdna-el.a.run.app"
}
```

---

## 📊 Monitoring & Rollout

### Check Deployment Status

```bash
# 1. GitHub Actions
https://github.com/dlai-sd/WAOOAW/actions

# 2. EAS Build Dashboard
https://expo.dev/accounts/waooaw/projects/waooaw-mobile/builds

# 3. Google Play Console
https://play.google.com/console/u/0/developers/[YOUR_ID]/app/[APP_ID]/releases/overview

# 4. Check build status via CLI
cd /workspaces/WAOOAW/src/mobile
eas build:list --platform android --limit 5
```

### Gradual Rollout (Recommended for Production)

```bash
# After initial approval, roll out gradually:

1. Go to Play Console → Production
2. Start with 10% rollout
3. Monitor for 24 hours:
   - Crash rate < 1%
   - ANR (App Not Responding) rate < 0.5%
   - User ratings > 4.0
4. If metrics good:
   - Increase to 50% after 24h
   - Increase to 100% after 48h
5. If metrics bad:
   - Halt rollout
   - Investigate crashes
   - Deploy hotfix
```

### Key Metrics to Monitor

| Metric | Threshold | Action if breached |
|--------|-----------|-------------------|
| Crash-free rate | > 99% | Halt rollout if < 97% |
| ANR rate | < 0.5% | Investigate if > 1% |
| API error rate | < 1% | Check backend logs |
| Avg. rating | > 4.0 | Review user feedback |
| Install success | > 95% | Check app size/compatibility |

---

## 🐛 Troubleshooting

### Build Fails with "Invalid credentials"

```bash
# Check EXPO_TOKEN
eas whoami
# Should show your Expo account name

# If not logged in:
eas login

# Regenerate token and update GitHub secret
```

### Submit Fails with "Invalid service account"

```bash
# 1. Verify JSON format in GitHub secret
# Should be valid JSON, no extra quotes

# 2. Check service account permissions in Play Console
# - View app information ✅
# - Release to testing tracks ✅
# - Release to production ✅

# 3. Verify app is linked to service account
# Play Console → Setup → API access → Service accounts
```

### App Still Using Wrong API URL

```bash
# 1. Check eas.json has EXPO_PUBLIC_API_URL
cat src/mobile/eas.json | grep EXPO_PUBLIC_API_URL

# 2. Rebuild with --clear-cache
eas build --profile demo --platform android --clear-cache

# 3. Check logs during build
# Look for: "[API Config] Using EXPO_PUBLIC_API_URL for demo: ..."
```

### "App not uploaded" in Play Console

```bash
# 1. Check build completed successfully
eas build:list --platform android --limit 1

# 2. Manual upload as fallback:
# - Download AAB from EAS
# - Go to Play Console → Release → Production → Create new release
# - Upload AAB manually

# 3. Check app signing configuration
# Play Console → Setup → App integrity → App signing
```

### Build Times Out (> 30 minutes)

```bash
# 1. Check EAS build queue
# Could be experiencing delays

# 2. Use smaller resource class temporarily
# Edit eas.json: "resourceClass": "medium" → "default"

# 3. Clear cache and retry
eas build --profile demo --platform android --clear-cache
```

---

## 🎯 Post-Deployment Checklist

After successful deployment:

- [ ] Verify app appears in internal track (Play Console)
- [ ] Add testers to internal testing group
- [ ] Install app from Play Store (not direct APK)
- [ ] Test complete user journey:
  - [ ] App launch
  - [ ] Skip sign-in (demo mode)
  - [ ] Agent discovery
  - [ ] Agent detail
  - [ ] Hire wizard (if payments enabled)
  - [ ] My agents screen
- [ ] Check analytics (if enabled):
  - [ ] Firebase console
  - [ ] Sentry (if configured)
- [ ] Monitor backend metrics:
  - [ ] API response times
  - [ ] Error rates
  - [ ] Cold start performance
- [ ] Review crash reports (Play Console → Vitals)
- [ ] Check user feedback (if public release)

---

## 📈 Release Strategy

### Recommended First Release

```
Track: Internal
Users: Team + 5-10 beta testers
Duration: 1 week
Success criteria:
- Zero crashes
- All core flows work
- API calls successful
- Average usage > 10 min/session
```

### Recommended Second Release

```
Track: Alpha (closed testing)
Users: 50-100 beta testers
Duration: 2 weeks
Success criteria:
- Crash rate < 1%
- User ratings > 4.0
- Core features tested at scale
```

### Production Release

```
Track: Production (open testing or full rollout)
Rollout: 10% → 50% → 100% over 1 week
Success criteria:
- Crash rate < 0.5%
- ANR rate < 0.2%
- User ratings > 4.2
- No critical bugs reported
```

---

## 🔗 Useful Links

- **GitHub Repository**: https://github.com/dlai-sd/WAOOAW
- **GitHub Actions**: https://github.com/dlai-sd/WAOOAW/actions
- **EAS Dashboard**: https://expo.dev/accounts/waooaw/projects/waooaw-mobile/builds
- **Google Play Console**: https://play.google.com/console
- **Firebase Console**: https://console.firebase.google.com/project/waooaw-oauth
- **GCP Demo Backend**: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app
- **Backend Logs**: https://console.cloud.google.com/run?project=waooaw-oauth

---

## 📞 Support

**Issues with deployment?**
1. Check workflow logs: GitHub Actions → mobile-playstore-deploy.yml
2. Check EAS build logs: https://expo.dev/accounts/waooaw/projects/waooaw-mobile/builds
3. Check Play Console status: https://play.google.com/console
4. Review this guide's troubleshooting section above

**Questions?**
- Create GitHub issue: https://github.com/dlai-sd/WAOOAW/issues
- Check mobile docs: `/workspaces/WAOOAW/docs/mobile/`
- Review EAS documentation: https://docs.expo.dev/build/introduction/

---

## 🎉 Next Steps

1. ✅ **Immediate**: Set up GitHub secrets (EXPO_TOKEN, GOOGLE_PLAY_SERVICE_ACCOUNT_JSON)
2. ✅ **Today**: Run first deployment to internal track
3. ✅ **This Week**: Test with team, gather feedback
4. ✅ **Next Week**: Deploy to alpha/beta track
5. ✅ **In 2 Weeks**: Production release preparation

**The app is now fixed and ready for deployment! 🚀**
