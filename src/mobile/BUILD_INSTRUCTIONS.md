# Quick Build Instructions for WAOOAW Mobile

## Build Demo APK Now

```bash
cd /workspaces/WAOOAW/src/mobile

# 1. Install EAS CLI (if not already installed)
npm install -g eas-cli

# 2. Login to Expo
eas login

# 3. Initialize EAS Project (first time only)
eas init

# 4. Build APK for demo backend
eas build --profile demo --platform android

# This will:
# - Use backend: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app
# - Build an AAB file for Play Store
# - Take 10-20 minutes
# - Provide download link when complete
```

## Configuration Summary

### ✅ Already Configured
- **Backend URL**: GCP demo backend (waooaw-api-demo-ryvhxvrdna-el.a.run.app)
- **EAS Build Profile**: `demo` in eas.json
- **Firebase**: Android app configured in waooaw-oauth project
- **Package Name**: com.waooaw.app
- **App Name**: WAOOAW
- **Version**: 1.0.0

### 📦 What Gets Built
- **Format**: AAB (Android App Bundle)
- **Backend**: GCP Cloud Run demo environment
- **Features Enabled**:
  - ✅ All navigation (Home, Discover, My Agents, Profile)
  - ✅ Demo skip button for testing
  - ✅ Voice commands
  - ✅ Agent browsing
  - ✅ Firebase analytics (disabled in dev)
  - ❌ Razorpay payments (disabled for demo)
  - ❌ Google OAuth (requires Play Store listing)

### 🎯 Build Process
1. EAS uploads code to Expo servers
2. Builds on cloud infrastructure
3. Signs with auto-managed key
4. Provides download link

## After Build Completes

### Download & Test
```bash
# List your builds
eas build:list

# Download latest
# (EAS provides direct download link in email/terminal)
```

### Install on Device
1. Transfer AAB to device (or use APK build)
2. Enable "Install from Unknown Sources"
3. Install and test
4. Verify:
   - App launches successfully
   - Skip demo button works
   - Bottom tabs navigate correctly
   - Backend connection works (if backend is up)

## Upload to Play Store

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for complete Play Store submission steps.

**Quick version**:
1. Create app in Play Console
2. Upload the AAB file  
3. Fill store listing (description, screenshots, etc.)
4. Submit for review
5. Wait 1-3 days for approval

## Troubleshooting

### Build Fails
```bash
# Clear cache and retry
eas build --clear-cache --profile demo --platform android
```

### Need APK Instead of AAB?
Change in `eas.json`:
```json
"demo": {
  "android": {
    "buildType": "apk"  // Changed from "aab"
  }
}
```

### Backend Not Responding
- Verify: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app
- May need cold start (first request takes 30-60s)
- Check GCP Cloud Run logs

## Next Steps

1. Run build command above
2. Wait for build to complete (~15 mins)
3. Download AAB
4. Test on device
5. Follow DEPLOYMENT_GUIDE.md to submit to Play Store

**Questions?** See DEPLOYMENT_GUIDE.md for detailed instructions and troubleshooting.
