# WAOOAW Mobile App - App Store Assets Checklist

**Date**: 2026-02-18  
**Version**: 1.0  
**Target**: iOS App Store + Google Play Store

---

## 📱 iOS App Store Assets (Story 5.4)

### Required Screenshots (Per Device Size)

**Note**: Apple requires screenshots for each device size. Use iPhone 16 Pro Max (6.7") and iPad Pro (12.9") as primary.

#### iPhone 6.7" Display (Required)
- [ ] 1290 x 2796 pixels (portrait) OR 2796 x 1290 pixels (landscape)
- [ ] Screenshot 1: Discover Screen (agent marketplace with search)
- [ ] Screenshot 2: Agent Detail Screen (agent profile with CTA)
- [ ] Screenshot 3: Hire Wizard (payment flow)
- [ ] Screenshot 4: My Agents Screen (active trials dashboard)
- [ ] Screenshot 5: Trial Dashboard (deliverables and progress)
- [ ] Screenshot 6 (Optional): Voice Control (FAB + voice commands)

#### iPad Pro 12.9" Display (Required for universal app)
- [ ] 2048 x 2732 pixels (portrait) OR 2732 x 2048 pixels (landscape)
- [ ] Same 5-6 screenshots adapted for iPad layout

**Tools to Use**:
- Expo Dev Client on physical device or simulator
- macOS Screenshot (Cmd+Shift+4 for simulator, Cmd+Shift+5 for recording)
- Figma frames (1290x2796) for marketing overlays

**Design Guidelines**:
- ✅ Use dark theme (#0a0a0a background)
- ✅ Show real agent data (not lorem ipsum)
- ✅ Include status indicators (🟢 Available, 🟡 Working)
- ✅ Highlight neon accents (#00f2fe cyan, #667eea purple)
- ✅ Add text overlays explaining features (optional but recommended)
- ❌ No personal data (use test accounts)
- ❌ No UI chrome (hide status bar/notch if possible)

---

### App Preview Video (Optional but Recommended)

- [ ] Duration: 15-30 seconds
- [ ] Size: 1920 x 1080 pixels (landscape) OR 1080 x 1920 pixels (portrait)
- [ ] Format: .mov, .mp4, or .m4v
- [ ] Max file size: 500 MB
- [ ] Content:
  - 0-5s: Show app icon → splash screen → sign in
  - 5-10s: Browse agents (scroll through marketplace)
  - 10-20s: Select agent → view details → "Hire Agent" CTA
  - 20-25s: Hire wizard (quick flow: details → payment)
  - 25-30s: Success confirmation + end frame with logo

**Tools**:
- macOS Screen Recording (Cmd+Shift+5)
- QuickTime Player (trim/edit)
- iMovie or Final Cut Pro (overlay text, music)

**Video Guidelines**:
- ✅ Show smooth transitions (60 FPS)
- ✅ Use a test account with real data
- ✅ Include voiceover or subtitles explaining each step
- ✅ End with call-to-action: "Download WAOOAW to hire your AI agent"
- ❌ No sound effects without voiceover (mute user's system)
- ❌ No copyrighted music (use Epidemic Sound or Apple's library)

---

### App Store Metadata

#### App Name (Max 30 characters)
- [ ] **Primary**: "WAOOAW - AI Agent Marketplace"
- [ ] **Alternative**: "WAOOAW: Hire AI Agents"

#### Subtitle (Max 30 characters)
- [ ] **Primary**: "Try Agents, Keep Results"
- [ ] **Alternative**: "AI Agents Earn Your Business"

#### Promotional Text (Max 170 characters) - Editable without new version
```
🎉 New: 19+ specialized AI agents across Marketing, Education & Sales. 
Try free for 7 days. Keep all deliverables. No risk.
```

#### Description (Max 4000 characters)
```markdown
WAOOAW is the first AI agent marketplace where agents earn your business by proving value before you pay.

🚀 WHY WAOOAW?

• Try Before Hire: 7-day free trials, keep all deliverables
• Marketplace DNA: Browse agents like hiring talent on Upwork
• Zero Risk: Cancel anytime, you keep the work
• Specialized Agents: 19+ agents with real expertise

🤖 AVAILABLE AGENTS

MARKETING (7 Agents)
- Content Marketing (Healthcare specialist)
- Social Media (B2B specialist)
- SEO (E-commerce specialist)
- Email Marketing, PPC, Brand Strategy, Influencer Marketing

EDUCATION (7 Agents)
- Math Tutor (JEE/NEET prep)
- Science Tutor (CBSE specialist)
- English Language, Test Prep, Career Counseling, Study Planning

SALES (5 Agents)
- SDR Agent (B2B SaaS specialist)
- Account Executive, Sales Enablement, CRM Management, Lead Generation

🎯 KEY FEATURES

✅ Personalized Demos: See agents work on YOUR business
✅ Live Activity Feed: Watch agents deliver results in real-time
✅ Voice Control: "Show me marketing agents for healthcare"
✅ Progress Tracking: Monitor trial deliverables daily
✅ Secure Payments: Razorpay integration (₹8,000-18,000/mo)

💼 WHO IT'S FOR

- Startups needing marketing/sales help without full-time hires
- Students wanting personalized tutoring (JEE, NEET, CBSE)
- Small businesses scaling operations with AI agents
- Coaches/educators seeking AI assistants

🔒 PRIVACY & SECURITY

- Google OAuth2 sign-in
- Encrypted local storage (JWT tokens)
- No data sharing without consent
- GDPR compliant

📱 REQUIREMENTS

- iOS 13.0 or later
- Internet connection for agent interactions
- Optional: Microphone access for voice commands

💰 PRICING

- Free to browse and compare agents
- 7-day free trial (keep all deliverables)
- Paid plans: ₹8,000-18,000/month per agent
- Cancel anytime, no lock-in contracts

🌟 WHAT MAKES US DIFFERENT

Unlike SaaS tools, WAOOAW agents are autonomous AI workers with:
- Personality and specializations (not generic)
- Real-time status (🟢 Available, 🟡 Working, 🔴 Offline)
- Portfolio of past deliverables
- Ratings and reviews from actual customers

🎉 GET STARTED

1. Browse 19+ agents by industry or skill
2. Read specializations, ratings, pricing
3. Request personalized demo (free)
4. Start 7-day trial
5. Keep deliverables even if you cancel

Questions? support@waooaw.com

WAOOAW: Agents Earn Your Business™
```

#### Keywords (Max 100 characters total, comma-separated)
```
AI agents,marketplace,automation,marketing,education,sales,tutors,freelance,workforce
```

**Note**: Research App Store keywords using tools like:
- App Store Connect (Search Ads Popularity)
- AppTweak, Sensor Tower, App Annie

#### Support URL
```
https://waooaw.com/support
```

#### Marketing URL (Optional)
```
https://waooaw.com
```

#### Privacy Policy URL (Required)
```
https://waooaw.com/privacy-policy
```

---

### App Icon (Required)

- [ ] Size: 1024 x 1024 pixels (PNG, no transparency, no rounded corners)
- [ ] Design: WAOOAW logo on dark background (#0a0a0a or gradient)
- [ ] Color: Neon cyan (#00f2fe) + purple (#667eea) accents
- [ ] Style: Modern, tech-forward, palindrome visual cue

**Design Concept**:
- Option 1: "WAOOAW" text (Space Grotesk font) with neon glow
- Option 2: Abstract "W" icon with bidirectional symmetry (palindrome)
- Option 3: AI agent avatar (robot/silicon chip) with marketplace vibe

**Tool**: Figma, Adobe Illustrator, or Canva Pro

---

### Content Rights

- [ ] **Age Rating**: 4+ (No objectionable content)
- [ ] **Category**: 
  - Primary: Business
  - Secondary: Productivity
- [ ] **Copyright**: © 2026 WAOOAW Technologies Private Limited

---

## 🤖 Google Play Store Assets (Story 5.7)

### Required Screenshots

**Phone Screenshots** (JPEG or PNG, 16:9 aspect ratio)
- [ ] Minimum 2, maximum 8 screenshots
- [ ] Size: 1080 x 1920 pixels (portrait) OR 1920 x 1080 pixels (landscape)
- [ ] Screenshot 1: Discover Screen
- [ ] Screenshot 2: Agent Detail Screen
- [ ] Screenshot 3: Hire Wizard (payment)
- [ ] Screenshot 4: My Agents Screen
- [ ] Screenshot 5: Trial Dashboard (deliverables)

**Tablet Screenshots** (Optional but recommended for universal app)
- [ ] Size: 1920 x 1200 pixels (landscape) OR 1200 x 1920 pixels (portrait)
- [ ] Same 5 screenshots adapted for tablet layout

**Design Guidelines** (Same as iOS):
- Use dark theme, real data, neon accents
- No personal data, no status bar

---

### Feature Graphic (Required)

- [ ] Size: 1024 x 500 pixels (JPEG or PNG)
- [ ] Design: Hero banner for Play Store page
- [ ] Content:
  - Left side: WAOOAW logo + tagline "Agents Earn Your Business"
  - Right side: 3-4 agent avatars with status dots
  - Background: Dark (#0a0a0a) with neon accents
  - Text: "Try Free for 7 Days • Keep All Deliverables"

**Tool**: Figma or Canva Pro

---

### Promo Video (Optional)

- [ ] YouTube URL (unlisted or public)
- [ ] Same video as iOS (1080p, 15-30s)
- [ ] Auto-plays when users visit Play Store page

---

### Play Store Metadata

#### App Name (Max 50 characters)
```
WAOOAW: AI Agent Marketplace - Try Before Hire
```

#### Short Description (Max 80 characters)
```
Hire specialized AI agents. 7-day trial, keep deliverables. Zero risk.
```

#### Full Description (Max 4000 characters)
```markdown
(Use same description as iOS, formatted for Play Store)

WAOOAW is the first AI agent marketplace where agents earn your business by proving value before you pay.

🚀 WHY WAOOAW?
• Try Before Hire: 7-day free trials, keep all deliverables
• Marketplace DNA: Browse agents like hiring talent
• Zero Risk: Cancel anytime, you keep the work
• Specialized Agents: 19+ agents with real expertise

🤖 AVAILABLE AGENTS
[Same content as iOS]

[...rest of description...]
```

#### Category
- [ ] **Primary**: Business
- [ ] **Secondary**: Productivity

#### Tags (Max 5)
```
AI, Marketplace, Automation, Agents, Productivity
```

#### Contact Details
- [ ] Website: https://waooaw.com
- [ ] Email: support@waooaw.com
- [ ] Phone: +91-XXXXXXXXXX (optional)
- [ ] Privacy Policy: https://waooaw.com/privacy-policy

#### Content Rating
- [ ] Use Google Play Console Content Rating Questionnaire
- [ ] Expected: Everyone (ages 3+)

---

## 📝 Legal & Compliance (Stories 5.5 & 5.6)

### Privacy Policy (Required)

**URL**: https://waooaw.com/privacy-policy

**Must Include**:
- [ ] Data collection practices (email, phone, payment info)
- [ ] How data is used (authentication, payment processing, analytics)
- [ ] Third-party services (Google OAuth, Razorpay, Firebase, Sentry)
- [ ] User rights (access, deletion, export)
- [ ] Cookie policy (if web-based dashboard exists)
- [ ] GDPR compliance (for EU users)
- [ ] Contact information for privacy concerns

**Tool**: Use a privacy policy generator (e.g., Termly, iubenda) customized for WAOOAW.

---

### Terms of Service (Required)

**URL**: https://waooaw.com/terms-of-service

**Must Include**:
- [ ] Acceptance of terms
- [ ] User accounts and registration
- [ ] 7-day trial terms (keep deliverables, no refunds post-trial)
- [ ] Payment terms (Razorpay, ₹8,000-18,000/mo subscriptions)
- [ ] Agent usage policies (what users can/cannot do with agents)
- [ ] Intellectual property (agent deliverables ownership)
- [ ] Limitation of liability
- [ ] Termination clause
- [ ] Dispute resolution

**Tool**: Consult legal counsel or use template from TermsFeed, Rocket Lawyer.

---

## 🔧 Pre-Submission Checklist

### Technical Requirements

**iOS (TestFlight & App Store)**
- [ ] App builds successfully with EAS (`eas build --profile production --platform ios`)
- [ ] App launches without crashes on iOS 13.0+
- [ ] All API endpoints use HTTPS (not HTTP in production)
- [ ] App supports both portrait and landscape orientations (if applicable)
- [ ] App handles poor network conditions gracefully
- [ ] Push notification entitlements configured (if used)
- [ ] In-App Purchase entitlements configured (if used - likely for subscriptions)
- [ ] Apple Sign In implemented (if other social login exists - REQUIRED by Apple)
- [ ] No private APIs used
- [ ] No placeholder text ("Lorem ipsum") in production

**Android (Play Store Internal Track & Production)**
- [ ] App builds successfully with EAS (`eas build --profile production --platform android`)
- [ ] App launches without crashes on Android 6.0+
- [ ] APK/AAB signed with release keystore
- [ ] ProGuard/R8 configured (minification enabled in production)
- [ ] Permissions declared in AndroidManifest.xml (camera, microphone, storage)
- [ ] Google Play Services dependencies updated
- [ ] No hardcoded secrets (all in GCP Secret Manager)
- [ ] No placeholder assets in production

---

### App Review Guidelines Compliance

**iOS App Store Review Guidelines**
- [ ] App function is clear from metadata and screenshots
- [ ] No references to non-iOS platforms (Android) in iOS version
- [ ] No beta/test disclaimers in production build
- [ ] No incentivized reviews or ratings prompts
- [ ] Subscription cancellation clearly explained
- [ ] Physical goods NOT sold via In-App Purchase (agents are services, OK)
- [ ] No cryptocurrency or NFT features (N/A for WAOOAW)
- [ ] No user-generated content moderation issues (N/A - agents controlled by WAOOAW)

**Google Play Store Policies**
- [ ] App uses standard Android UI patterns
- [ ] No deceptive behavior (clearly communicate trial terms)
- [ ] Family policy compliant if targeting children (unlikely for WAOOAW)
- [ ] Subscription terms comply with Play billing policies
- [ ] No gambling or contests (N/A)
- [ ] Ads policy compliant (N/A if no ads)

---

## 📦 Asset Delivery Checklist

### Files to Prepare

**For iOS Submission**:
- [ ] `waooaw-ios-screenshots-6.7inch` (folder with 5-6 PNG files)
- [ ] `waooaw-ios-screenshots-12.9inch` (folder with 5-6 PNG files - if iPad)
- [ ] `waooaw-ios-preview-video.mov` (optional, <500MB)
- [ ] `waooaw-icon-1024.png` (app icon, 1024x1024)
- [ ] `app-store-metadata.txt` (name, subtitle, description, keywords)

**For Android Submission**:
- [ ] `waooaw-android-screenshots-phone` (folder with 5-8 PNG files)
- [ ] `waooaw-android-screenshots-tablet` (folder with 5 PNG files - optional)
- [ ] `waooaw-feature-graphic-1024x500.png` (Play Store banner)
- [ ] `waooaw-promo-video-youtube-url.txt` (optional)
- [ ] `play-store-metadata.txt` (name, short desc, full desc, tags)

**Legal Documents**:
- [ ] `privacy-policy.pdf` (upload to waooaw.com/privacy-policy)
- [ ] `terms-of-service.pdf` (upload to waooaw.com/terms-of-service)

---

## 🎨 Design Tools & Resources

**Screenshot Templates**:
- Figma: Search "App Store Screenshots Template" in Community
- Apple Design Resources: https://developer.apple.com/design/resources/
- Android Asset Studio: https://romannurik.github.io/AndroidAssetStudio/

**Video Editing**:
- iMovie (Mac, free)
- DaVinci Resolve (Mac/Windows, free)
- Final Cut Pro (Mac, paid but professional)

**Stock Assets** (if needed for marketing):
- Unsplash, Pexels (free images)
- Lottie Files (free animations)
- Flaticon (icons)

**Music** (for promo video):
- YouTube Audio Library (free, no attribution)
- Epidemic Sound (paid, royalty-free)
- Artlist (paid, high-quality)

---

## 🚀 Submission Timeline

| Week | Task | Owner | Status |
|------|------|-------|--------|
| Week 11 Day 1-2 | Create all screenshots (iOS + Android) | Design Team | 🔴 |
| Week 11 Day 3 | Record and edit promo video (15-30s) | Marketing | 🔴 |
| Week 11 Day 4 | Write all metadata (descriptions, keywords) | Product | 🔴 |
| Week 11 Day 5 | Finalize Privacy Policy + Terms of Service | Legal | 🔴 |
| Week 12 Day 1 | Submit to TestFlight (iOS Internal Testing) | Mobile Dev | 🔴 |
| Week 12 Day 1 | Submit to Play Store Internal Track (Android) | Mobile Dev | 🔴 |
| Week 12 Day 2-6 | Internal testing (10 testers, both platforms) | QA Team | 🔴 |
| Week 12 Day 7 | Fix critical bugs from internal testing | Mobile Dev | 🔴 |
| Week 13 Day 1 | Submit to App Store Review (iOS) | Mobile Dev | 🔴 |
| Week 13 Day 1 | Submit to Play Store Production Review (Android) | Mobile Dev | 🔴 |
| Week 13 Day 2-5 | App Store review process (2-4 days typical) | Apple/Google | 🔴 |
| Week 13 Day 6-7 | Apps live! 🎉 Launch marketing campaign | Marketing | 🔴 |

---

## ✅ Final Checklist Before Submission

**48 Hours Before Submission**:
- [ ] All team members tested latest build (iOS + Android)
- [ ] No crashes reported in last 7 days
- [ ] All screenshots finalized and approved
- [ ] Metadata reviewed by product + marketing teams
- [ ] Privacy Policy + Terms live on waooaw.com
- [ ] Support email (support@waooaw.com) monitored
- [ ] Razorpay production keys configured and tested
- [ ] Google OAuth production client IDs active
- [ ] Firebase Analytics + Crashlytics integrated and tested
- [ ] Sentry error tracking operational

**24 Hours Before Submission**:
- [ ] Final EAS production build (`mobile-v1.0.0` tag)
- [ ] Build uploaded to TestFlight/Play Console
- [ ] 10 internal testers invited and testing
- [ ] Zero P0/P1 bugs reported
- [ ] App Store Connect metadata uploaded
- [ ] Play Console metadata uploaded

**Submission Day**:
- [ ] Click "Submit for Review" in App Store Connect
- [ ] Click "Submit for Review" in Play Console
- [ ] Monitor email for rejection notices
- [ ] Prepare hotfix branch in case of issues
- [ ] Announce internally: "We've submitted! 🚀"

---

**Next Steps After Approval**:
1. Monitor Crashlytics + Sentry for first 48 hours
2. Respond to initial user reviews within 24 hours
3. Plan Version 1.1 based on feedback
4. Setup staged rollout (10% → 50% → 100% over 7 days)

---

**Document Status**: ✅ Ready for Story 5.4 Implementation  
**Last Updated**: 2026-02-18  
**Owner**: Mobile Team + Design Team
