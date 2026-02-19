# WAOOAW Mobile - Quick Deployment Reference

**Date**: February 19, 2026  
**Target**: Google Play Store

---

## 🚨 Critical Fix Applied - App Now Works!

**What was broken**: App couldn't connect to backend (wrong API URL hardcoded)  
**What's fixed**: App now reads correct backend URL from environment variables  
**Backend**: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app ✅

---

## ⚡ Deploy to Play Store in 3 Steps

### Step 1: Setup GitHub Secrets (5 minutes)

Go to: https://github.com/dlai-sd/WAOOAW/settings/secrets/actions

Add these two secrets:

1. **EXPO_TOKEN**
   ```bash
   # Get your token
   eas login
   eas whoami
   # Copy token from: https://expo.dev/accounts/[your-account]/settings/access-tokens
   ```

2. **GOOGLE_PLAY_SERVICE_ACCOUNT_JSON**
   ```bash
   # 1. Go to: https://play.google.com/console → API Access
   # 2. Create service account
   # 3. Download JSON key
   # 4. Copy entire JSON content to GitHub secret
   ```

### Step 2: Run Deployment (1 click)

1. Go to: https://github.com/dlai-sd/WAOOAW/actions/workflows/mobile-playstore-deploy.yml
2. Click "Run workflow"
3. Select:
   - Environment: **demo**
   - Track: **internal**
   - Release notes: "Initial release with demo backend"
4. Click "Run workflow" button

### Step 3: Wait & Verify (20-30 minutes)

- ✅ Build completes (~15 min)
- ✅ Submits to Play Store (~5 min)
- ✅ Available in internal track (~1-2 hours after submit)

Check status:
- GitHub: https://github.com/dlai-sd/WAOOAW/actions
- EAS: https://expo.dev/accounts/waooaw/projects/waooaw-mobile/builds
- Play Console: https://play.google.com/console

---

## 🧪 Test Locally First (Optional but Recommended)

```bash
cd /workspaces/WAOOAW/src/mobile

# Build APK with fixes
eas build --profile demo --platform android

# Download and install on device
# Verify app connects to backend successfully
```

---

## 📋 What Changed (Technical)

### Files Modified

1. **src/mobile/src/config/api.config.ts**
   - ✅ Now reads `EXPO_PUBLIC_API_URL` from environment
   - ✅ Added proper environment detection
   - ✅ Increased timeout to 15s for Cloud Run

2. **src/mobile/eas.json**
   - ✅ Added `EXPO_PUBLIC_ENVIRONMENT` variable
   - ✅ Created `demo-store` build profile (AAB for Play Store)
   - ✅ Updated submit configuration

3. **.github/workflows/mobile-playstore-deploy.yml** (NEW)
   - ✅ Automated Build & Submit workflow
   - ✅ Quality checks (lint, typecheck, tests)
   - ✅ Slack notifications
   - ✅ Rollback plan on failure

### Build Profiles

| Profile | Use Case | Format | Backend |
|---------|----------|--------|---------|
| `demo` | Local testing | APK | GCP Demo |
| `demo-store` | Play Store internal/beta | AAB | GCP Demo |
| `production` | Play Store production | AAB | Production |

---

## 🎯 Deployment Tracks

### Internal Track (Recommended First)
- Up to 100 testers
- No Google review required
- Available in 1-2 hours
- Perfect for team testing

```bash
# Deploy to internal
Environment: demo
Track: internal
```

### Alpha Track
- Up to 1000 testers
- No Google review required
- Good for beta testers

```bash
# Deploy to alpha
Environment: demo
Track: alpha
```

### Production Track
- Public release
- Requires Google review (1-3 days)
- Can do gradual rollout (10% → 50% → 100%)

```bash
# Deploy to production
Environment: production
Track: production
```

---

## 🐛 Common Issues & Quick Fixes

### Issue: Build fails immediately
```bash
# Fix: Check GitHub secrets
# Ensure EXPO_TOKEN is valid:
eas whoami
# Should show your Expo username
```

### Issue: Submit fails
```bash
# Fix: Check Play Console service account
# 1. Play Console → API Access
# 2. Grant permissions: Release to testing tracks
# 3. Re-upload service account JSON to GitHub
```

### Issue: App still doesn't work
```bash
# Fix: Clear cache and rebuild
eas build --profile demo --platform android --clear-cache

# Verify environment in logs:
# Should see: "[API Config] Using EXPO_PUBLIC_API_URL for demo: https://waooaw-api-demo..."
```

---

## 📞 Need Help?

1. **Full Documentation**: [GOOGLE_PLAY_CICD_SETUP.md](./GOOGLE_PLAY_CICD_SETUP.md)
2. **GitHub Actions Logs**: https://github.com/dlai-sd/WAOOAW/actions
3. **EAS Build Logs**: https://expo.dev/accounts/waooaw/projects/waooaw-mobile/builds
4. **Troubleshooting**: See full guide Section "Troubleshooting"

---

## ✅ Next Steps After First Deployment

- [ ] Install app from Play Console
- [ ] Test all screens work
- [ ] Verify API calls succeed
- [ ] Add more testers to internal track
- [ ] Gather feedback
- [ ] Deploy to alpha/beta when ready
- [ ] Plan production release

---

**Ready to deploy? Start with Step 1 above! 🚀**
