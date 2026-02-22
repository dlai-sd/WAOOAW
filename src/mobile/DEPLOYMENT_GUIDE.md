# WAOOAW Mobile - Google Play Store Deployment Guide

## Overview

This guide walks through deploying the WAOOAW mobile app to Google Play Store using EAS Build and the demo GCP backend.

**Demo Backend**: https://cp.demo.waooaw.com  
**Firebase Project**: waooaw-oauth  
**Package Name**: com.waooaw.app

---

## Prerequisites

### 1. Google Play Developer Account
- **Cost**: $25 one-time registration fee
- **Sign up**: https://play.google.com/console/signup
- **Time**: Account approval takes 24-48 hours

### 2. Expo Account  
- **Sign up**: https://expo.dev/signup
- **Free** for building APKs/AABs

### 3. Firebase Config Files
Already created and located at:
- `google-services.json` (Android) - Already in mobile root
- App configured in Firebase project: waooaw-oauth

---

## Step 1: EAS Build Setup (One-time)

### Install EAS CLI
```bash
npm install -g eas-cli
```

### Login to Expo
```bash
cd /workspaces/WAOOAW/src/mobile
eas login
```

### Create EAS Project
```bash
eas init --id YOUR_PROJECT_ID
```

This will:
- Create an EAS project
- Link it to your Expo account
- Update `app.json` with the project ID

---

## Step 2: Build Demo APK

### Configure Build Profile
The `demo` build profile is already configured in `eas.json`:
- **Backend URL**: https://cp.demo.waooaw.com
- **Build Type**: AAB (for Play Store) or APK (for testing)
- **Channel**: demo

### Build APK for Testing
```bash
cd /workspaces/WAOOAW/src/mobile

# Build APK (for direct installation/testing)
eas build --profile demo --platform android
```

**Build time**: 10-20 minutes (first build takes longer)

### Download the APK
Once the build completes:
```bash
# EAS will provide a download link
# Or use:
eas build:list
```

---

## Step 3: Test the APK

### Install on Android Device
1. Download the APK from EAS
2. Enable "Install from Unknown Sources" on your device:
   - Settings → Security → Unknown Sources → Enable
3. Transfer APK to device and install
4. Open and test:
   - Click "Skip Sign In (Demo Mode)"
   - Verify bottom tabs work
   - Test navigation between screens
   - Verify backend connection (should show agents if available)

---

## Step 4: Build AAB for Play Store

### Build Production Bundle
```bash
cd /workspaces/WAOOAW/src/mobile

# Build AAB (required for Play Store upload)  
eas build --profile demo --platform android
```

The `demo` profile uses `buildType: "aab"` by default.

### What is AAB?
- **Android App Bundle**: Google Play's optimized publishing format
- **Smaller downloads**: Play Store generates optimized APKs per device
- **Required**: For new apps published after August 2021

---

## Step 5: Setup Google Play Console

### Create App Listing
1. Go to https://play.google.com/console
2. Click **Create app**
3. Fill in details:
   - **App name**: WAOOAW
   - **Default language**: English (US)
   - **App or game**: App
   - **Free or paid**: Free
   - **Category**: Business
4. Accept declarations and create

### Configure App Details

#### Store Listing
- **Short description** (80 chars):  
  "AI Agent Marketplace - Try agents free for 7 days, keep deliverables"

- **Full description** (4000 chars):  
  ```
  WAOOAW - Where Agents Earn Your Business
  
  The first AI agent marketplace that makes you say WOW! Specialized AI agents for Marketing, Education & Sales that prove their value before you pay.
  
  🎯 TRY BEFORE HIRE
  • 7-day free trials with every agent
  • Keep ALL deliverables - even if you don't subscribe
  • Zero risk, maximum value
  
  🤖 SPECIALIZED AGENTS
 
  Marketing Agents (7):
  - Content Marketing (Healthcare specialist)
  - Social Media (B2B specialist)
  - SEO (E-commerce specialist)
  - Email Marketing, PPC, Brand Strategy, Influencer Marketing
  
  Education Agents (7):
  - Math Tutor (JEE/NEET specialist)
  - Science Tutor (CBSE specialist)
  - English, Test Prep, Career Counseling, Study Planning, Homework Help
  
  Sales Agents (5):
  - SDR Agent (B2B SaaS specialist)
  - Account Executive, Sales Enablement, CRM, Lead Generation
  
  ✨ FEATURES
  • Browse agents by industry, specialty, and rating
  • See real-time agent status and activity
  • Get personalized demos tailored to YOUR business
  • Voice commands for hands-free navigation
  • Track trial progress and deliverables
  
  💰 TRANSPARENT PRICING
  • Starting from ₹8,000/month
  • No hidden fees or setup costs
  • Cancel anytime, keep your work
  
  🔐 PRIVACY & SECURITY
  • Enterprise-grade security
  • Your data stays yours
  • Google OAuth authentication
  
  Not tools. Not software. Actual AI workforce.
  ```

- **App icon**: 512x512px PNG (create from assets/icon.png)
- **Feature graphic**: 1024x500px PNG
- **Screenshots**: At least 2, max 8 (720x1280 or higher)
  - Take screenshots from the app running on device
  - Show: Home screen, Discover screen, Agent detail, My Agents

#### Contact Details
- **Email**: support@waooaw.com
- **Phone**: +91-XXX-XXX-XXXX (optional)
- **Website**: https://waooaw.com
- **Privacy Policy**: https://waooaw.com/privacy

#### App Category
- **Category**: Business
- **Tags**: AI, Agents, Marketplace, Business Tools

---

## Step 6: Setup App Content

### Content Rating
Complete the content rating questionnaire:
- **Violence**: None
- **Sexuality**: None
- **Language**: None
- **Controlled Substances**: None
- **Gambling**: None

Expected rating: **Everyone / PEGI 3**

### Target Audience
- **Age groups**: 18+
- **Appeals to children**: No

### Data Safety
Fill out data collection disclosure:

**Data Collected**:
- Account info (email, name) - for authentication
- App activity - for analytics
- Device IDs - for crashlytics

**Data Sharing**: With service providers only
**Data Deletion**: Available on request
**Encryption**: Data encrypted in transit

### App Access
- **Special access**: None required
- **Restrictions**: None

---

## Step 7: Upload App Bundle

### Create Release

#### Go to Production → Releases
1. Click **Create new release**
2. **App signing**: Let Google manage (recommended)
   - Google generates and manages signing key
   - More secure, no key management needed
3. **Upload AAB**: Drag and drop the .aab file from EAS Build
4 **Release name**: "1.0.0 - Initial Release"
5. **Release notes**:
   ```
   🎉 Welcome to WAOOAW v1.0!
   
   • Browse 19+ specialized AI agents across Marketing, Education & Sales
   • Try any agent free for 7 days
   • Keep all deliverables even if you don't subscribe
   • Voice commands for hands-free navigation
   • Real-time agent status and activity feed
   • Secure Google OAuth authentication
   
   Get started: Create an account and explore agents that transform your business!
   ```

### Review and Rollout
1. **Review summary**: Check all details
2. **Rollout**: Start with **20%** staged rollout
3. **Submit for review**

---

## Step 8: App Review Process

### Timeline
- **Review time**: 1-3 days typically
- **Updates**: Faster (often same day)

### Common Rejection Reasons (and Solutions)

1. **Missing Privacy Policy**
   - Solution: Add privacy policy URL to waooaw.com/privacy
   - Must be accessible from within the app

2. **Incomplete Store Listing**
   - Solution: Ensure all required fields filled
   - At least 2 screenshots, proper icon, feature graphic

3. **App Crashes on Launch**
   - Solution: Test thoroughly before submission
   - Use Firebase Crashlytics to catch issues

4. **OAuth Configuration Issues**
   - Solution: Verify SHA-1 fingerprint matches uploaded APK
   - Add all redirect URIs to Google Cloud Console

### Get SHA-1 Fingerprint
```bash
# For Google Play signed app
# SHA-1 is shown in Play Console → Setup → App signing
```

Add to Google Cloud Console:
1. Go to https://console.cloud.google.com/apis/credentials
2. Select OAuth 2.0 Client ID for Android
3. Add SHA-1 from Play Console

---

## Step 9: Post-Launch

### Monitor Launch
- **Crashlytics**: Check Firebase Console for crashes
- **Analytics**: Monitor user engagement
- **Ratings**: Respond to user reviews promptly

### Update Strategy
```bash
# For updates, increment version in app.json:
{
  "expo": {
    "version": "1.0.1",  # Bump this
    ...
  }
}

# Build new AAB
eas build --profile demo --platform android

# Upload to Play Console → Production → Create new release
```

---

## Configuration Files Summary

### Files Already Configured
✅ `eas.json` - Build profiles including demo
✅ `app.json` - App metadata and config  
✅ `environment.config.ts` - Environment variables
✅ `google-services.json` - Firebase Android config
✅ `oauth.config.ts` - OAuth configuration

### Files You Need to Create
□ Store listing assets:
  - App icon (512x512)
  - Feature graphic (1024x500)
  - Screenshots (720x1280+ resolution)
  - Promo video (optional)

### Environment Variables Set
- `APP_ENV`: "production"
- `EXPO_PUBLIC_API_URL`: "https://cp.demo.waooaw.com"

---

## Troubleshooting

### Build Fails
```bash
# Clear cache and retry
eas build:cancel
eas build --clear-cache --profile demo --platform android
```

### App Crashes on Start
- Check Firebase Crashlytics for stack traces
- Verify all environment variables are set
- Test with demo backend URL accessible

### OAuth Not Working
1. Verify SHA-1 fingerprint in Google Cloud Console
2. Check package name matches: `com.waooaw.app`
3. Add redirect URIs to OAuth client configuration

### Can't Connect to Backend
- Verify backend URL is accessible: https://cp.demo.waooaw.com
- Check CORS settings allow mobile app origin
- Verify Firebase auth is configured correctly

---

## Quick Command Reference

```bash
# Setup
eas login
eas init

# Build APK (testing)
eas build --profile demo --platform android --noprofile

# Build AAB (Play Store)
eas build --profile demo --platform android

# Check build status
eas build:list

# View build details
eas build:view BUILD_ID

# Submit to Play Store (automated)
eas submit -p android --latest
```

---

## iOS Deployment (High-Level)

**Cost**: $99/year Apple Developer account  
**Steps**:
1. Enroll in Apple Developer Program (https://developer.apple.com/programs/) → 1-2 days approval
2. Run `eas build --profile demo-store --platform ios` → Generates IPA file (~7-10 min)
3. Upload to TestFlight via EAS Submit or App Store Connect → Internal testing available immediately
4. Submit for App Store Review → 24-48 hours review, then live on App Store
5. **Total Time**: ~3-5 days (approval + review), **Ongoing**: $99/year subscription

---

## Cost Breakdown

| Item | Cost | Frequency |
|------|------|-----------|
| Google Play Developer Account | $25 USD | One-time |
| Apple Developer Program | $99 USD | Annual |
| EAS Build (Free tier) | $0 | Monthly |
| Firebase (Spark plan) | $0 | Monthly |
| GCP Cloud Run (Demo) | ~$5-10 | Monthly |
| **Total First Year (Both Platforms)** | **~$185-195** | - |
| **Annual After (iOS renewal)** | **~$160-170** | - |

---

## Support

### Documentation
- EAS Build: https://docs.expo.dev/build/introduction/
- Google Play Console: https://support.google.com/googleplay/android-developer
- Firebase: https://firebase.google.com/docs/android/setup

### EAS Build Support
- Forum: https://forums.expo.dev
- Discord: https://chat.expo.dev

### Google Play Support
- Help Center: https://support.google.com/googleplay/android-developer
- Email: googleplaydev-support@google.com

---

## Next Steps

1. ✅ Configuration complete
2. □ Run `eas login` and create project
3. □ Run `eas build --profile demo --platform android`
4. □ Test APK on device
5. □ Create Google Play Console listing
6. □ Upload AAB and submit for review
7. □ Monitor launch and respond to feedback

**Questions? Issues?** 
- Check the troubleshooting section above
- Review Firebase/Crashlytics for runtime errors
- Verify backend API is responding at demo URL

---

**Ready to Deploy!** The app is configured and ready for building. Follow the steps above to get WAOOAW on the Play Store.
