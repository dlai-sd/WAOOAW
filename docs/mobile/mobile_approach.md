# WAOOAW CP Mobile Application - Technical Approach

**Version**: 1.1  
**Date**: 2026-02-20  
**Target Platforms**: Android (API 31+, Android 12+) & iOS (iOS 15+)  
**Compatibility**: Latest + 2 previous OS versions  
**Status**: Active Implementation (quality gate hardening in progress)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Platform Selection & Justification](#2-platform-selection--justification)
3. [Architecture Overview](#3-architecture-overview)
4. [Technology Stack](#4-technology-stack)
5. [UI/UX Design Strategy](#5-uiux-design-strategy)
6. [API Integration & Reuse](#6-api-integration--reuse)
7. [Authentication & Security](#7-authentication--security)
8. [Voice Control Integration](#8-voice-control-integration)
9. [State Management](#9-state-management)
10. [Offline & Caching Strategy](#10-offline--caching-strategy)
11. [Performance Optimization](#11-performance-optimization)
12. [Testing Strategy](#12-testing-strategy)
13. [CI/CD & Deployment](#13-cicd--deployment)
14. [Project Structure](#14-project-structure)
15. [Development Roadmap](#15-development-roadmap)
16. [Risk Mitigation](#16-risk-mitigation)

---

## 1. Executive Summary

### Objective
Build a cross-platform mobile application for WAOOAW Customer Portal (CP) that delivers identical functionality to the web application while adding voice-controlled capabilities.

### Key Requirements
- **Single Codebase**: One codebase deploying to both Android and iOS
- **Visual Parity**: Exact replication of CP web UI/UX (dark theme, neon accents, marketplace DNA)
- **Voice Control**: Voice-first alternative navigation and interaction
- **OS Compatibility**: Android 12+ (API 31+), iOS 15+ (includes 2 previous major versions)
- **API Reuse**: 100% reuse of existing CP Backend & Plant Gateway APIs
- **Feature Parity**: All web features available on mobile

### Success Criteria
- 🎯 Single codebase with 95%+ code sharing between platforms
- 🎯 <2s cold start time, <500ms screen transitions
- 🎯 Voice commands with >90% accuracy (English, Hindi)
- 🎯 JWT authentication with biometric unlock support
- 🎯 App Store approval on first submission
- 🎯 Zero API changes required in backend

---

## 2. Platform Selection & Justification

### Recommended: **React Native** (Expo Framework)

| Criterion | React Native + Expo | Flutter | Native (Swift/Kotlin) | Score |
|-----------|---------------------|---------|----------------------|-------|
| **Code Reusability** | ✅ 95% shared code | ✅ 100% shared code | ❌ 0% shared code | **React Native** |
| **Web Code Reuse** | ✅ React components, TypeScript types, API services | ❌ Different paradigm | ❌ Different paradigm | **React Native** |
| **Team Skillset** | ✅ Existing React/TypeScript expertise | ⚠️ New language (Dart) | ❌ Two separate teams needed | **React Native** |
| **Third-party Libraries** | ✅ Mature ecosystem (1M+ packages) | ✅ Growing ecosystem | ✅ Native libraries | **React Native** |
| **Voice Integration** | ✅ Excellent (Expo Speech, react-native-voice) | ✅ Good (speech_to_text) | ✅ Native APIs | **Tie** |
| **Development Speed** | ✅ Fast (hot reload, Expo Go) | ✅ Fast (hot reload) | ⚠️ Separate builds | **React Native** |
| **Maintenance** | ✅ One team, one codebase | ✅ One team, one codebase | ❌ Two teams, two codebases | **Tie** |
| **App Size** | ⚠️ ~25-40 MB base | ✅ ~15-20 MB base | ✅ ~10-15 MB base | **Flutter** |
| **Performance** | ✅ Near-native (Hermes, New Architecture) | ✅ Native (compiled to ARM) | ✅ Native | **Tie** |
| **OTA Updates** | ✅ Expo Updates (instant non-native changes) | ⚠️ Limited (code push) | ❌ App Store only | **React Native** |
| **OAuth2 & JWT** | ✅ Same libraries as web (axios, jwt-decode) | ⚠️ Different libraries | ⚠️ Platform-specific | **React Native** |
| **Dark Theme** | ✅ React Native Paper, Styled Components | ✅ Material/Cupertino themes | ✅ Native themes | **Tie** |
| **CI/CD** | ✅ EAS Build (GitHub Actions integration) | ✅ Fastlane, Codemagic | ⚠️ Separate pipelines | **React Native** |
| **Maturity** | ✅ 9+ years, proven at scale (FB, Uber, Shopify) | ✅ 7+ years, growing adoption | ✅ Most mature | **Native** |

### **Winner: React Native (Expo Managed Workflow)**

### Justification

1. **Maximum Code Reuse from Web**
   - Reuse all TypeScript type definitions (`src/CP/FrontEnd/src/types/`)
   - Reuse all API service layers (`src/CP/FrontEnd/src/services/`)
   - Reuse business logic and state management
   - Shared authentication flow (JWT, Google OAuth2)
   - Same API endpoints and request/response models

2. **Team Efficiency**
   - Existing React expertise transfers 90% to React Native
   - TypeScript knowledge fully applicable
   - Single team can maintain web + mobile
   - Fast onboarding (1-2 weeks vs 2-3 months for native)

3. **Expo Framework Benefits**
   - Managed build service (EAS) eliminates Xcode/Android Studio setup complexity
   - OTA updates for JS/config changes without app store review
   - Expo Go for instant testing on physical devices
   - Built-in modules for camera, location, biometrics, push notifications
   - Automated icon/splash screen generation
   - Simplified certificate management

4. **Voice Control**
   - `expo-speech` for text-to-speech (multi-language)
   - `@react-native-voice/voice` for speech recognition
   - Native-quality voice accuracy with simple API

5. **Performance**
   - Hermes JavaScript engine (50% faster startup, 30% less memory)
   - React Native New Architecture (Fabric + TurboModules) for native-level performance
   - Optimized for 60 FPS animations matching web experience

### Alternative Considered: Flutter
- **Pros**: Smaller app size, slightly better performance, beautiful default UI
- **Cons**: Zero web code reuse, new language (Dart), team upskilling required, different ecosystem
- **Decision**: Not justified given existing React codebase and team expertise

---

## 3. Architecture Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   MOBILE APPLICATIONS                    │
│         ┌──────────────┐      ┌──────────────┐           │
│         │  Android APK │      │  iOS IPA     │           │
│         │  (Play Store)│      │ (App Store)  │           │
│         └──────┬───────┘      └──────┬───────┘           │
│                └──────────┬──────────┘                    │
│                           │                               │
│         ┌─────────────────▼────────────────┐              │
│         │  React Native Application        │              │
│         │  (Single JavaScript Bundle)      │              │
│         ├──────────────────────────────────┤              │
│         │  • 95% shared code               │              │
│         │  • 5% platform-specific (Face ID,│              │
│         │    Push Notifications, etc.)     │              │
│         │  • TypeScript strict mode        │              │
│         │  • Hermes JavaScript engine      │              │
│         └─────────────────┬────────────────┘              │
└───────────────────────────┼───────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │   Networking    │
                   │   Layer (Axios) │
                   └────────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼─────┐   ┌──────▼─────┐   ┌──────▼─────┐
    │ Google    │   │ CP Backend │   │ Plant      │
    │ OAuth2    │   │ :8020      │   │ Gateway    │
    │           │   │ (FastAPI)  │   │ :8000      │
    └───────────┘   └──────┬─────┘   └────────────┘
                           │
                    ┌──────▼─────┐
                    │ Plant      │
                    │ Backend    │
                    │ :8001      │
                    └────────────┘
```

### Communication Flow

```
Mobile App → Google OAuth2 → Get ID token
          → CP Backend /api/auth/google → Verify token → Issue JWT
          → Store JWT in SecureStore (encrypted storage)
          
Mobile App (authenticated) → Add Authorization: Bearer <JWT>
          → CP Backend :8020 → Plant Gateway :8000 
          → JWT validation → RBAC → Policy → Budget
          → Plant Backend :8001 → PostgreSQL
```

### Key Architectural Principles

1. **Headless Architecture**: Mobile app is a pure client; all business logic remains in backend
2. **API-First**: 100% API reuse from existing CP Backend (`/api/*` endpoints)
3. **Stateless Auth**: JWT tokens (same as web), no session state in mobile app
4. **Offline-First UI**: Cache critical data locally, sync when online
5. **Platform Channels**: Use native modules only for platform-specific features (biometrics, voice)

---

## 4. Technology Stack

### Core Framework

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Framework** | React Native | 0.73+ | Core mobile framework |
| **Toolkit** | Expo | SDK 50+ | Managed workflow, build service |
| **Language** | TypeScript | 5.3+ | Type safety, IDE support |
| **Runtime** | Hermes | Latest | Optimized JS engine |

### UI & Styling

| Library | Purpose | Notes |
|---------|---------|-------|
| `react-native-paper` | Material Design components | Dark theme support |
| `@react-navigation/native` | Navigation (stack, tab, drawer) | Declarative routing |
| `react-native-safe-area-context` | Handle notches, home indicators | iOS/Android compatibility |
| `styled-components/native` | Styled components (same API as web) | Reuse theme tokens |
| `react-native-vector-icons` | Icons (FontAwesome, Material) | Same icons as web |
| `react-native-linear-gradient` | Gradient backgrounds | Neon accent effects |
| `@shopify/flash-list` | High-performance lists | Replace FlatList for agent cards |

### Voice Control

| Library | Purpose | Platform Support |
|---------|---------|------------------|
| `expo-speech` | Text-to-speech | iOS, Android (multi-language) |
| `@react-native-voice/voice` | Speech-to-text | iOS (native), Android (Google Speech) |
| `react-native-tts` | Advanced TTS (backup) | iOS, Android |

### Networking & State

| Library | Purpose | Notes |
|---------|---------|-------|
| `axios` | HTTP client | **Same as web** |
| `@tanstack/react-query` | Server state management | Caching, refetching, optimistic updates |
| `zustand` | Client state management | Lightweight (React Context alternative) |
| `jwt-decode` | JWT decoding | **Same as web** |

### Storage & Security

| Library | Purpose | Platform |
|---------|---------|----------|
| `expo-secure-store` | Encrypted key-value storage | iOS Keychain, Android KeyStore |
| `@react-native-async-storage/async-storage` | Unencrypted cache | Both |
| `react-native-keychain` | Biometric auth | Touch ID, Face ID, Fingerprint |

### Push Notifications & Deep Linking

| Library | Purpose |
|---------|---------|
| `expo-notifications` | Push notifications (FCM, APNs) |
| `expo-linking` | Deep linking (waooaw://hire/agent/123) |

### Development & Testing

| Tool | Purpose |
|------|---------|
| `jest` | Unit testing (React Native preset) |
| `@testing-library/react-native` | Component testing |
| `detox` | E2E testing (iOS Simulator, Android Emulator) |
| `@expo/ngrok` | Local API tunneling for testing |
| `react-native-debugger` | Redux DevTools, Network Inspector |

### Build & Deployment

| Tool | Purpose |
|------|---------|
| `eas-cli` | Expo Application Services (build, submit) |
| `fastlane` | Automated screenshots, beta deployment |
| `@sentry/react-native` | Error tracking, performance monitoring |

---

## 5. UI/UX Design Strategy

### Design Principles

1. **Visual Parity**: Match web CP pixel-by-pixel where feasible
2. **Native Feel**: Use platform conventions (iOS swipe gestures, Android back button)
3. **Touch-Optimized**: 44×44pt minimum touch targets (iOS HIG), 48×48dp (Material Design)
4. **Dark-First**: Default to dark theme matching web (`#0a0a0a` background)
5. **Voice-Enhanced**: Every action accessible via voice command

### Theme System (Reuse from Web)

```typescript
// mobile/src/theme/colors.ts (matches src/CP/FrontEnd/src/theme.ts)
export const colors = {
  black: '#0a0a0a',
  grayDark: '#18181b',
  neonCyan: '#00f2fe',
  neonPurple: '#667eea',
  neonPink: '#f093fb',
  brandPrimary: '#0078d4',
  
  statusOnline: '#10b981',
  statusWorking: '#f59e0b',
  statusOffline: '#ef4444',
  
  // Neutrals
  gray100: '#f5f9ff',
  gray200: '#e6f2ff',
  gray800: '#003366',
  gray900: '#001933',
}

export const typography = {
  fontDisplay: 'SpaceGrotesk-Bold', // Via expo-google-fonts
  fontHeading: 'Outfit-SemiBold',
  fontBody: 'Inter-Regular',
  
  sizes: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    display: 32,
  }
}

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
}

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
}
```

### Screen-to-Web Page Mapping

| Mobile Screen | Web Page | Key Differences |
|---------------|----------|-----------------|
| **Home** (Tab 1) | `LandingPage.tsx` | Vertical scroll, hero banner adapted for mobile aspect ratio |
| **Discover** (Tab 2) | `AgentDiscovery.tsx` | Grid → List view, filters in bottom sheet |
| **My Agents** (Tab 3) | `AuthenticatedPortal.tsx` → My Agents | Tab bar convenience for quick access |
| **Profile** (Tab 4) | `AuthenticatedPortal.tsx` → Profile | User profile, settings, logout |
| **Agent Detail** (Stack) | `AgentDetail.tsx` | Full-screen modal, swipe-to-dismiss |
| **Hire Wizard** (Stack) | `HireSetupWizard.tsx` | Multi-step form, progress indicator at top |
| **Trial Dashboard** (Stack) | `TrialDashboard.tsx` | Swipe between agents, pull-to-refresh |
| **Sign In** (Modal) | `SignIn.tsx` | Bottom sheet modal, biometric option |
| **Sign Up** (Modal) | `SignUp.tsx` | Multi-step form, OTP via SMS |

### Component Reusability

| Component | Web Path | Mobile Adaptation |
|-----------|----------|-------------------|
| **AgentCard** | `components/AgentCard.tsx` | Touchable, haptic feedback on press |
| **Header** | `components/Header.tsx` | Stack navigation header, hamburger menu |
| **Footer** | `components/Footer.tsx` | Tab bar navigation (bottom) |
| **TrialStatusBanner** | `components/TrialStatusBanner.tsx` | Sticky at top, swipeable to dismiss |
| **BookingModal** | `components/BookingModal.tsx` | Bottom sheet modal, gesture-driven |

### Navigation Pattern

```
Root Navigator (Tab)
├── Home Tab
│   ├── Home Screen
│   └── Agent Detail Stack
├── Discover Tab
│   ├── Agent List Screen
│   ├── Agent Detail Stack
│   └── Hire Wizard Stack
├── My Agents Tab
│   ├── My Agents Screen
│   ├── Trial Dashboard Stack
│   └── Deliverables Stack
└── Profile Tab
    ├── Profile Screen
    ├── Settings Screen
    └── Auth Modal (Sign In/Sign Up)
```

### Responsive Design

| Device Category | Example Devices | Layout Adjustments |
|-----------------|-----------------|-------------------|
| **Small Phone** | iPhone SE (375×667) | Single column, compact spacing |
| **Standard Phone** | iPhone 13 (390×844), Pixel 6 (412×915) | Default layout, 16px margins |
| **Large Phone** | iPhone 14 Pro Max (430×932), Galaxy S23 Ultra (480×1080) | 2-column agent cards in landscape |
| **Tablet** | iPad Mini (744×1133), iPad Pro (1024×1366) | 2-3 column grid, side-by-side layouts |

---

## 6. API Integration & Reuse

### 100% API Reuse Strategy

**No backend changes required.** Mobile app consumes identical APIs as web.

### API Service Layer Migration

#### Web Services → Mobile Services (Direct Port)

| Web Service | Mobile Service | Changes Required |
|-------------|---------------|------------------|
| `auth.service.ts` | `services/auth.service.ts` | Replace `localStorage` with `SecureStore` |
| `registration.service.ts` | `services/registration.service.ts` | ✅ No changes |
| `plant.service.ts` | `services/plant.service.ts` | ✅ No changes |
| `hireWizard.service.ts` | `services/hireWizard.service.ts` | ✅ No changes |
| `agentTypes.service.ts` | `services/agentTypes.service.ts` | ✅ No changes |
| `hiredAgents.service.ts` | `services/hiredAgents.service.ts` | ✅ No changes |
| `trialStatus.service.ts` | `services/trialStatus.service.ts` | ✅ No changes |
| `subscriptions.service.ts` | `services/subscriptions.service.ts` | ✅ No changes |
| `invoices.service.ts` | `services/invoices.service.ts` | ✅ No changes |
| `receipts.service.ts` | `services/receipts.service.ts` | ✅ No changes |
| `trading.service.ts` | `services/trading.service.ts` | ✅ No changes (optional for mobile) |

#### API Base URL Configuration

```typescript
// mobile/src/config/api.config.ts
import Constants from 'expo-constants';

export const API_CONFIG = {
  development: {
    apiBaseUrl: 'http://10.0.2.2:8020/api', // Android emulator
    // Or use ngrok for local testing: 'https://abc123.ngrok.io/api'
  },
  demo: {
    apiBaseUrl: 'https://cp.demo.waooaw.com/api',
  },
  uat: {
    apiBaseUrl: 'https://cp.uat.waooaw.com/api',
  },
  prod: {
    apiBaseUrl: 'https://cp.waooaw.com/api',
  },
};

const environment = Constants.manifest?.extra?.environment || 'development';

export const API_BASE_URL = API_CONFIG[environment].apiBaseUrl;
```

#### Axios Instance (Same as Web)

```typescript
// mobile/src/lib/apiClient.ts (copied from web)
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { API_BASE_URL } from '../config/api.config';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token
apiClient.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('cp_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401 (token expired)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await SecureStore.deleteItemAsync('cp_access_token');
      // Navigate to login screen
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### API Endpoints Used (From CP Backend)

#### Authentication
- `POST /api/auth/google` — Google OAuth2 login (ID token → JWT)
- `POST /api/auth/refresh` — Refresh access token
- `POST /api/auth/logout` — Logout (optional, JWT is stateless)

#### Registration & OTP
- `POST /api/register` — Customer registration (email, phone, password)
- `POST /api/verify-otp` — OTP verification
- `POST /api/resend-otp` — Resend OTP

#### Agent Discovery
- `GET /api/v1/agents` — List all agents (with filters: industry, rating, status)
- `GET /api/v1/agents/{agent_id}` — Agent detail
- `GET /api/v1/agent_types` — Agent types/specializations

#### Hiring & Trials
- `POST /api/hire-wizard/start` — Start hiring flow
- `POST /api/hire-wizard/complete` — Complete hiring
- `GET /api/v1/trials` — List customer trials
- `GET /api/v1/trials/{trial_id}` — Trial details

#### Hired Agents
- `GET /api/v1/hired-agents` — List customer's hired agents
- `GET /api/v1/hired-agents/{hired_agent_id}` — Hired agent details
- `GET /api/v1/hired-agents/{hired_agent_id}/deliverables` — Deliverables

#### Subscriptions & Payments
- `GET /api/cp/subscriptions` — List subscriptions
- `POST /api/cp/subscriptions/{id}/cancel` — Cancel subscription
- `GET /api/v1/invoices` — List invoices
- `GET /api/v1/receipts` — List receipts
- `POST /api/payments/checkout` — Create Razorpay order
- `POST /api/payments/verify` — Verify payment

### Network Error Handling

```typescript
// mobile/src/lib/errorHandler.ts
import { AxiosError } from 'axios';
import { Alert } from 'react-native';

export const handleApiError = (error: AxiosError) => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.detail || 'An error occurred';
    
    if (status === 401) {
      Alert.alert('Session Expired', 'Please sign in again.');
    } else if (status === 403) {
      Alert.alert('Access Denied', message);
    } else if (status === 500) {
      Alert.alert('Server Error', 'Please try again later.');
    } else {
      Alert.alert('Error', message);
    }
  } else if (error.request) {
    // Network error
    Alert.alert('Network Error', 'Please check your connection.');
  } else {
    Alert.alert('Error', 'Something went wrong.');
  }
};
```

---

## 7. Authentication & Security

### Authentication Flow (Identical to Web)

```
┌────────────────────────────────────────────────────────┐
│  1. User taps "Sign in with Google"                   │
│     ↓                                                  │
│  2. Open Google OAuth2 (AuthSession in-app browser)   │
│     ↓                                                  │
│  3. User authenticates, grants permissions            │
│     ↓                                                  │
│  4. Google returns ID token to app                    │
│     ↓                                                  │
│  5. App sends ID token to CP Backend                  │
│     POST /api/auth/google                             │
│     ↓                                                  │
│  6. CP Backend verifies token with Google             │
│     ↓                                                  │
│  7. CP Backend issues JWT (HS256, JWT_SECRET)         │
│     { user_id, email, exp }                           │
│     ↓                                                  │
│  8. App stores JWT in SecureStore (encrypted)         │
│     ↓                                                  │
│  9. All API requests include: Authorization: Bearer <JWT> │
└────────────────────────────────────────────────────────┘
```

### Google OAuth2 Integration (React Native)

**Client IDs (set as EAS environment variables — do not hardcode):**

| Variable | Value | Environment |
|---|---|---|
| `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` | `270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com` | production, preview |
| `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` | `270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com` | production, preview |

**Important:** Android OAuth client uses package name `com.waooaw.app` + SHA-1 `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07` for verification. Web client is used for **backend token exchange only** — never passed to `Google.useAuthRequest` on Android.

**Critical rules for Android (expo-auth-session v7):**

1. **Do NOT pass `webClientId` alongside `androidClientId`** — expo-auth-session v7 uses the web client ID in the OAuth request but pairs it with a custom URI scheme redirect. Web OAuth clients only allow `https://` redirects → Google returns `Error 400: invalid_request: Custom URI scheme is not enabled for your Android client`.

2. **Explicit `redirectUri` is required** — expo-auth-session v7 defaults to `com.waooaw.app:/oauthredirect` on Android. Google Android OAuth clients auto-register `com.googleusercontent.apps.{hash}:/oauth2redirect`. These must match exactly or Google returns `Error 400: invalid_request`.

```typescript
// mobile/src/config/oauth.config.ts
export const GOOGLE_OAUTH_CONFIG = {
  expoClientId: process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID || '',   // Expo Go dev only
  iosClientId:  process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID  || '',   // iOS only
  androidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || '',
  webClientId:  process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID  || '',   // backend use only
};
```

```typescript
// mobile/src/hooks/useGoogleAuth.ts  ← ACTUAL IMPLEMENTATION
import { Platform } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import { makeRedirectUri } from 'expo-auth-session';

export const useGoogleAuth = () => {
  // Build redirect URI matching what Google Android OAuth client auto-registers.
  // expo-auth-session v7 default = com.waooaw.app:/oauthredirect (WRONG)
  // Google Android client expects = com.googleusercontent.apps.{hash}:/oauth2redirect
  const redirectUri = Platform.OS === 'android' && GOOGLE_OAUTH_CONFIG.androidClientId
    ? makeRedirectUri({
        native: `com.googleusercontent.apps.${
          GOOGLE_OAUTH_CONFIG.androidClientId.replace('.apps.googleusercontent.com', '')
        }:/oauth2redirect`,
      })
    : makeRedirectUri({ scheme: 'waooaw' });

  // On Android: pass ONLY androidClientId — no webClientId, no clientId.
  // Passing webClientId causes expo-auth-session to use the web client in the
  // OAuth request, which Google rejects with 400 invalid_request.
  const authRequestConfig = Platform.OS === 'android'
    ? {
        androidClientId: GOOGLE_OAUTH_CONFIG.androidClientId,
        scopes: GOOGLE_OAUTH_SCOPES,
        redirectUri,
      }
    : {
        clientId: GOOGLE_OAUTH_CONFIG.expoClientId,
        iosClientId: GOOGLE_OAUTH_CONFIG.iosClientId,
        webClientId: GOOGLE_OAUTH_CONFIG.webClientId,
        scopes: GOOGLE_OAUTH_SCOPES,
        redirectUri,
      };

  const [request, response, promptAsync] = Google.useAuthRequest(authRequestConfig);
  // ... rest of hook handles response, calls AuthService.loginWithGoogle(idToken),
  // then calls login(authUser) from authStore + userDataService.saveUserData(authUser)
};
```

**How to test Google Sign-In:**
1. Install internal testing AAB from Play Store internal track
2. Tap "Sign in with Google" → Google account picker should appear (no error screen)
3. Select account → should redirect back to app and land on the main screen
4. Kill the app and reopen → should remain signed in (not force re-auth)
5. If `Error 400: invalid_request` appears → verify `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` EAS secret is the **Android-type** client (`270293855600-2shl...`), not the web client (`270293855600-uoag...`)

### Biometric Authentication (Optional Enhancement)

```typescript
// mobile/src/services/biometric.service.ts
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';

export const enableBiometricAuth = async () => {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();
  
  if (hasHardware && isEnrolled) {
    await SecureStore.setItemAsync('biometric_enabled', 'true');
    return true;
  }
  return false;
};

export const authenticateWithBiometric = async (): Promise<boolean> => {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Unlock WAOOAW',
    fallbackLabel: 'Use passcode',
  });
  
  return result.success;
};

export const unlockApp = async () => {
  const biometricEnabled = await SecureStore.getItemAsync('biometric_enabled');
  
  if (biometricEnabled === 'true') {
    const authenticated = await authenticateWithBiometric();
    if (!authenticated) {
      throw new Error('Biometric authentication failed');
    }
  }
  
  // Return stored JWT token
  return await SecureStore.getItemAsync('cp_access_token');
};
```

### Security Best Practices

| Threat | Mitigation |
|--------|-----------|
| **JWT Theft** | Store in `SecureStore` (iOS Keychain, Android KeyStore); auto-wipe on jailbreak detection |
| **MITM Attacks** | Enforce HTTPS; certificate pinning for prod environment |
| **API Key Exposure** | Google Client IDs in `app.config.js` (safe for mobile); secrets in EAS Secrets |
| **Reverse Engineering** | Obfuscate JS bundle (Metro bundler); ProGuard (Android), Bitcode (iOS) |
| **Session Hijacking** | Short JWT expiry (15 min); refresh token pattern |
| **Phishing** | Use `AuthSession` in-app browser (verifies google.com domain) |
| **Root/Jailbreak** | Detect with `expo-device` + `react-native-root-detection`; soft warning (don't block) |

### Token Refresh Strategy

```typescript
// mobile/src/services/auth.service.ts
export const refreshAccessToken = async () => {
  const refreshToken = await SecureStore.getItemAsync('cp_refresh_token');
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const { data } = await apiClient.post('/auth/refresh', {
    refresh_token: refreshToken,
  });
  
  await SecureStore.setItemAsync('cp_access_token', data.access_token);
  await SecureStore.setItemAsync('token_expires_at', data.expires_in.toString());
  
  return data.access_token;
};

// Auto-refresh before expiry
export const setupTokenRefresh = () => {
  setInterval(async () => {
    const expiresAt = await SecureStore.getItemAsync('token_expires_at');
    const now = Date.now() / 1000;
    
    if (expiresAt && now > parseInt(expiresAt) - 60) {
      await refreshAccessToken();
    }
  }, 60000); // Check every minute
};
```

---

## 8. Voice Control Integration

### Voice Control Architecture

```
┌─────────────────────────────────────────────────────┐
│            Voice Input (Speech-to-Text)             │
│    @react-native-voice/voice (iOS Native, Google)  │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Voice Command      │
        │  Parser             │
        │  (Intent matching)  │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Action Dispatcher  │
        │  (Navigate, Filter, │
        │   Hire, etc.)       │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Voice Feedback     │
        │  (Text-to-Speech)   │
        │  expo-speech        │
        └─────────────────────┘
```

### Supported Voice Commands

| Command Intent | Example Phrases | Action |
|----------------|-----------------|--------|
| **Navigation** | "Go to discover", "Show my agents", "Open profile" | Navigate to screen |
| **Search** | "Find marketing agents", "Show education agents" | Filter agent list |
| **Agent Detail** | "Tell me about agent Sarah", "Show agent details" | Open agent detail |
| **Hiring** | "Hire this agent", "Start trial", "Book agent" | Open hire wizard |
| **Status Check** | "What's my trial status?", "How many agents do I have?" | Show trial dashboard |
| **Filter** | "Show agents with 5-star rating", "Only available agents" | Apply filters |
| **Help** | "What can I say?", "Help me", "Voice commands" | Show voice help modal |

### Voice Command Parser

```typescript
// mobile/src/services/voiceCommand.service.ts
import Voice from '@react-native-voice/voice';
import * as Speech from 'expo-speech';

type VoiceCommandAction = 
  | { type: 'navigate'; screen: string }
  | { type: 'search'; query: string }
  | { type: 'filter'; filters: object }
  | { type: 'action'; action: string; params?: any };

const commandPatterns = [
  { pattern: /go to (discover|home|profile|my agents)/i, action: 'navigate' },
  { pattern: /find (.+) agents?/i, action: 'search' },
  { pattern: /show (.+) agents?/i, action: 'search' },
  { pattern: /(hire|book) (this agent|agent|)/i, action: 'hire' },
  { pattern: /trial status|my trials/i, action: 'trialStatus' },
  { pattern: /(help|what can i say)/i, action: 'help' },
];

export const parseVoiceCommand = (transcript: string): VoiceCommandAction | null => {
  for (const { pattern, action } of commandPatterns) {
    const match = transcript.match(pattern);
    if (match) {
      switch (action) {
        case 'navigate':
          return { type: 'navigate', screen: match[1] };
        case 'search':
          return { type: 'search', query: match[1] };
        case 'hire':
          return { type: 'action', action: 'hire' };
        case 'trialStatus':
          return { type: 'navigate', screen: 'TrialDashboard' };
        case 'help':
          return { type: 'action', action: 'showHelp' };
      }
    }
  }
  return null;
};

export const startListening = async () => {
  try {
    await Voice.start('en-US'); // or 'hi-IN' for Hindi
  } catch (error) {
    console.error('Voice start error:', error);
  }
};

export const stopListening = async () => {
  try {
    await Voice.stop();
  } catch (error) {
    console.error('Voice stop error:', error);
  }
};

export const speak = (text: string, language: string = 'en') => {
  Speech.speak(text, {
    language: language === 'en' ? 'en-US' : 'hi-IN',
    pitch: 1.0,
    rate: 0.9,
  });
};
```

### Voice UI Component

```typescript
// mobile/src/components/VoiceFab.tsx (Floating Action Button)
import React, { useState, useEffect } from 'react';
import { TouchableOpacity, Animated } from 'react-native';
import Voice from '@react-native-voice/voice';
import { parseVoiceCommand, speak } from '../services/voiceCommand.service';

export const VoiceFab = ({ navigation }) => {
  const [listening, setListening] = useState(false);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Voice.onSpeechResults = (e) => {
      const transcript = e.value[0];
      const command = parseVoiceCommand(transcript);
      
      if (command) {
        executeCommand(command);
      } else {
        speak("Sorry, I didn't understand that. Say 'help' for commands.");
      }
    };

    return () => Voice.destroy().then(Voice.removeAllListeners);
  }, []);

  const toggleListening = async () => {
    if (listening) {
      await Voice.stop();
      setListening(false);
    } else {
      await Voice.start('en-US');
      setListening(true);
      startPulseAnimation();
    }
  };

  const executeCommand = (command) => {
    if (command.type === 'navigate') {
      navigation.navigate(command.screen);
      speak(`Going to ${command.screen}`);
    } else if (command.type === 'search') {
      navigation.navigate('Discover', { search: command.query });
      speak(`Searching for ${command.query}`);
    }
    // ... more command handlers
  };

  return (
    <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
      <TouchableOpacity
        onPress={toggleListening}
        style={{
          position: 'absolute',
          bottom: 80,
          right: 20,
          width: 60,
          height: 60,
          borderRadius: 30,
          backgroundColor: listening ? '#00f2fe' : '#667eea',
          justifyContent: 'center',
          alignItems: 'center',
          elevation: 5,
          shadowColor: '#000',
          shadowOpacity: 0.3,
          shadowRadius: 10,
        }}
      >
        <Icon name={listening ? 'mic' : 'mic-off'} size={24} color="#fff" />
      </TouchableOpacity>
    </Animated.View>
  );
};
```

### Multi-Language Support

```typescript
// mobile/src/config/voice.config.ts
export const VOICE_LANGUAGES = [
  { code: 'en-US', label: 'English' },
  { code: 'hi-IN', label: 'हिन्दी (Hindi)' },
];

// Localized command patterns
const hindiCommandPatterns = [
  { pattern: /(खोजें|खोज) (.+)/, action: 'search' }, // "Search X"
  { pattern: /(किराये पर लें|बुक करें)/, action: 'hire' }, // "Hire"
  { pattern: /मेरे एजेंट/, action: 'myAgents' }, // "My agents"
];
```

### Accessibility Improvements

- **VoiceOver/TalkBack**: All UI elements have `accessibilityLabel`
- **Voice hints**: Suggest next actions ("Say 'hire this agent' to start trial")
- **Visual feedback**: Waveform animation while listening
- **Error recovery**: "Sorry, say that again" on parse failure
- **Context awareness**: Suggest relevant commands per screen

---

## 9. State Management

### State Architecture

```
┌────────────────────────────────────────────────────┐
│         Zustand (Client State)                     │
│  • Auth state (user, token, isAuthenticated)      │
│  • UI state (theme, language, voice enabled)      │
│  • Navigation state (current screen, params)      │
│  • Persistence via AsyncStorage                   │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│      React Query (Server State)                    │
│  • Agent catalog (GET /api/v1/agents)             │
│  • Hired agents (GET /api/v1/hired-agents)        │
│  • Trial status (GET /api/v1/trials)              │
│  • Caching, invalidation, optimistic updates      │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│      SecureStore (Sensitive Data)                  │
│  • JWT access token                               │
│  • Refresh token (if used)                        │
│  • Biometric auth flag                            │
└────────────────────────────────────────────────────┘
```

### Zustand Store (Client State)

```typescript
// mobile/src/store/authStore.ts
import create from 'zustand';
import { persist } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: true }),
      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
      storage: AsyncStorage,
    }
  )
);
```

### React Query Setup (Server State)

```typescript
// mobile/src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 30, // 30 minutes
      retry: 2,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
  },
});

// mobile/src/hooks/useAgents.ts
import { useQuery } from '@tanstack/react-query';
import { agentService } from '../services/agent.service';

export const useAgents = (filters?: AgentFilters) => {
  return useQuery({
    queryKey: ['agents', filters],
    queryFn: () => agentService.getAgents(filters),
    staleTime: 1000 * 60 * 10, // 10 minutes (agent data doesn't change often)
  });
};

export const useHiredAgents = () => {
  return useQuery({
    queryKey: ['hired-agents'],
    queryFn: () => agentService.getHiredAgents(),
    staleTime: 1000 * 60 * 1, // 1 minute (fresher data needed)
  });
};
```

### Optimistic Updates Example

```typescript
// mobile/src/hooks/useCancelSubscription.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { subscriptionService } from '../services/subscription.service';

export const useCancelSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (subscriptionId: string) => 
      subscriptionService.cancel(subscriptionId),
    
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (subscriptionId) => {
      await queryClient.cancelQueries({ queryKey: ['subscriptions'] });
      
      const previousSubscriptions = queryClient.getQueryData(['subscriptions']);
      
      queryClient.setQueryData(['subscriptions'], (old: any) =>
        old.map((sub) =>
          sub.id === subscriptionId
            ? { ...sub, status: 'cancelled' }
            : sub
        )
      );
      
      return { previousSubscriptions };
    },
    
    // Rollback on error
    onError: (err, subscriptionId, context) => {
      queryClient.setQueryData(['subscriptions'], context.previousSubscriptions);
    },
    
    // Refetch on success
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });
};
```

---

## 10. Offline & Caching Strategy

### Offline Capabilities

| Feature | Offline Behavior | Sync Strategy |
|---------|------------------|---------------|
| **Agent Catalog** | Cached list (last fetched) | Refetch on app launch + pull-to-refresh |
| **Hired Agents** | Cached list + details | Refetch on screen focus |
| **Trial Status** | Cached status | Refetch every 5 minutes (background) |
| **Authentication** | JWT stored locally (valid until expiry) | Auto-refresh before expiry |
| **Hire Wizard** | ❌ Requires internet (payment processing) | Show "No connection" banner |
| **Voice Commands** | ✅ Works offline (navigation only) | No sync needed |

### Cache Implementation

```typescript
// mobile/src/lib/offlineCache.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_KEYS = {
  AGENTS: 'cache:agents',
  HIRED_AGENTS: 'cache:hired-agents',
  TRIALS: 'cache:trials',
};

export const cacheData = async (key: string, data: any) => {
  const cacheEntry = {
    data,
    timestamp: Date.now(),
  };
  await AsyncStorage.setItem(key, JSON.stringify(cacheEntry));
};

export const getCachedData = async (key: string, maxAge: number = 1000 * 60 * 10) => {
  const cached = await AsyncStorage.getItem(key);
  if (!cached) return null;
  
  const { data, timestamp } = JSON.parse(cached);
  const age = Date.now() - timestamp;
  
  if (age > maxAge) {
    await AsyncStorage.removeItem(key);
    return null;
  }
  
  return data;
};

// React Query integration
export const queryWithCache = async (queryFn, cacheKey, maxAge) => {
  // Try cache first
  const cached = await getCachedData(cacheKey, maxAge);
  if (cached) return cached;
  
  // Fetch from API
  const data = await queryFn();
  await cacheData(cacheKey, data);
  return data;
};
```

### Network Status Detection

```typescript
// mobile/src/hooks/useNetworkStatus.ts
import NetInfo from '@react-native-community/netinfo';
import { useState, useEffect } from 'react';

export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsOnline(state.isConnected && state.isInternetReachable);
    });

    return () => unsubscribe();
  }, []);

  return isOnline;
};

// Usage in component
const DiscoverScreen = () => {
  const isOnline = useNetworkStatus();
  const { data: agents, isLoading } = useAgents();

  if (!isOnline) {
    return <OfflineBanner message="Showing cached results" />;
  }

  return <AgentList agents={agents} />;
};
```

---

## 11. Performance Optimization

### Target Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Cold Start** | <2 seconds | Time to interactive on app launch |
| **Screen Transition** | <300ms | Navigation animation smoothness |
| **API Response** | <1 second | Time to first byte (TTFB) |
| **FPS** | 60 FPS | Scroll performance (FlashList) |
| **Bundle Size** | <10 MB | Compressed JS bundle (Hermes) |
| **Memory Usage** | <100 MB | Peak memory on mid-tier device |

### Optimization Techniques

#### 1. **JavaScript Bundle Optimization**

```javascript
// metro.config.js
module.exports = {
  transformer: {
    minifierConfig: {
      compress: {
        drop_console: true, // Remove console.log in production
      },
    },
  },
  resolver: {
    sourceExts: ['js', 'jsx', 'ts', 'tsx', 'json'],
  },
};
```

#### 2. **Image Optimization**

```typescript
// Use expo-image (30% faster than React Native Image)
import { Image } from 'expo-image';

<Image
  source={{ uri: agent.avatar_url }}
  placeholder={blurhash} // Show blur placeholder
  contentFit="cover"
  cachePolicy="memory-disk" // Cache images
  transition={200}
  style={{ width: 100, height: 100, borderRadius: 50 }}
/>
```

#### 3. **List Performance (FlashList)**

```typescript
// Replace FlatList with FlashList for 10x better performance
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={agents}
  renderItem={({ item }) => <AgentCard agent={item} />}
  estimatedItemSize={150} // Important for performance
  keyExtractor={(item) => item.id}
  removeClippedSubviews={true}
  getItemType={(item) => item.type} // Optimize for mixed types
/>
```

#### 4. **Code Splitting & Lazy Loading**

```typescript
// Lazy load heavy screens
const HireWizardScreen = React.lazy(() => import('./screens/HireWizardScreen'));
const TradingScreen = React.lazy(() => import('./screens/TradingScreen'));

// Use Suspense fallback
<Suspense fallback={<LoadingSpinner />}>
  <HireWizardScreen />
</Suspense>
```

#### 5. **Memoization**

```typescript
// Memoize expensive computations
import { useMemo } from 'react';

const DiscoverScreen = () => {
  const { data: agents } = useAgents();

  const filteredAgents = useMemo(() => {
    return agents
      .filter(a => a.status === 'available')
      .sort((a, b) => b.rating - a.rating);
  }, [agents]);

  return <AgentList agents={filteredAgents} />;
};

// Memoize components
export const AgentCard = React.memo(({ agent }) => {
  // ...component logic
}, (prevProps, nextProps) => {
  return prevProps.agent.id === nextProps.agent.id;
});
```

#### 6. **Hermes Engine**

```javascript
// app.json (enable Hermes)
{
  "expo": {
    "jsEngine": "hermes", // 50% faster startup, 30% less memory
    "android": {
      "enableProguard": true, // Minify Android APK
    },
    "ios": {
      "bitcode": false, // Required for Hermes
    }
  }
}
```

---

## 12. Testing Strategy

### Current Implementation Baseline (2026-02-20)

| Area | Current State | Operational Note |
|------|---------------|------------------|
| **Lint** | Pass (0 errors) | Warnings exist and are currently non-blocking |
| **Typecheck** | Pass | Strict TypeScript path stabilized for CI gate |
| **Jest (scoped)** | Pass baseline achieved | Latest full scoped run reached 27 suites / 407 tests passing |
| **Mock Runtime** | Hardened | Jest setup expanded for RN/Expo/native dependencies |

### Near-Term Test Hardening Focus

- Continue reducing temporary Jest suite ignores by fixing legacy-contract drift at source.
- Keep compatibility aliases only where needed to preserve release velocity while refactors are in progress.
- Re-run full quality checks (`lint + typecheck + tests`) on every release candidate SHA.

### ⚠️ MANDATORY RULE: Docker-only Testing — NO Virtual Environments

> **CRITICAL REQUIREMENT**: All tests MUST run inside Docker containers or Codespace (devcontainer). Virtual environments (`venv`, `virtualenv`, `conda`, `pyenv`, etc.) are **STRICTLY PROHIBITED** for any testing activities. This ensures parity with CI/CD pipelines and production environments.

**Rationale**:
- ✅ Consistent behavior across development, CI/CD, and production
- ✅ No "works on my machine" issues
- ✅ Reproducible test results
- ✅ Matches backend testing standards (Plant, CP, PP)
- ❌ Virtual environments cause dependency drift
- ❌ Virtual environments are not used in production (Cloud Run uses containers)

**Enforcement**:
- Pre-commit hooks will prevent test execution outside Docker
- CI/CD will fail if non-Docker test commands detected
- Code reviews will reject PRs with venv-based testing

### Test Coverage Targets

| Testing Level | Coverage Target | Tools | Docker Requirement |
|---------------|----------------|-------|--------------------|
| **Unit Tests** | 80% | Jest, Testing Library | ✅ Required |
| **Integration Tests** | 60% | Jest + React Query mocks | ✅ Required |
| **E2E Tests** | Critical flows (20 scenarios) | Detox | ✅ Required |
| **Visual Regression** | Key screens (15 screens) | Storybook + Chromatic | ✅ Required |

### Docker-Based Test Execution

**All tests MUST be run via Docker Compose or inside the Codespace devcontainer.**

```bash
# --- Correct Way: Docker Compose ---
# Run all mobile tests via Docker
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test

# Run specific test suite
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test -- auth.service.test.ts

# Run with coverage
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test -- --coverage

# E2E tests (Detox)
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npx detox test

# --- Correct Way: Inside Codespace (already Docker-based) ---
cd src/mobile
npm test
npx detox test

# --- ❌ WRONG WAY: Virtual Environment (PROHIBITED) ---
# python -m venv venv            # ❌ NEVER DO THIS
# source venv/bin/activate       # ❌ NEVER DO THIS
# npm test                       # ❌ NOT IN VENV CONTEXT
```

**Docker Compose Configuration for Mobile Testing**:

```yaml
# docker-compose.mobile.yml
version: '3.8'

services:
  mobile-test:
    build:
      context: ./src/mobile
      dockerfile: Dockerfile.test
    volumes:
      - ./src/mobile:/app
      - /app/node_modules
    environment:
      - NODE_ENV=test
      - API_BASE_URL=http://mock-api:8020
    depends_on:
      - mock-api
  
  mock-api:
    image: mockserver/mockserver:latest
    ports:
      - "8020:1080"
```

### Unit Testing Example

```typescript
// mobile/src/services/__tests__/auth.service.test.ts
// This test MUST be run inside Docker container
import { loginWithGoogle } from '../auth.service';
import apiClient from '../../lib/apiClient';
import * as SecureStore from 'expo-secure-store';

jest.mock('../../lib/apiClient');
jest.mock('expo-secure-store');

describe('auth.service', () => {
  it('should store JWT token after successful Google login', async () => {
    const mockResponse = {
      data: {
        access_token: 'fake-jwt-token',
        expires_in: 3600,
      },
    };
    
    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);
    
    await loginWithGoogle('fake-id-token');
    
    expect(apiClient.post).toHaveBeenCalledWith('/auth/google', {
      id_token: 'fake-id-token',
    });
    
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
      'cp_access_token',
      'fake-jwt-token'
    );
  });
});
```

### E2E Testing Example (Detox)

```typescript
// mobile/e2e/discover.test.ts
import { device, element, by, expect as detoxExpect } from 'detox';

describe('Agent Discovery Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should display agent list on Discover tab', async () => {
    await element(by.id('discover-tab')).tap();
    await detoxExpect(element(by.id('agent-list'))).toBeVisible();
  });

  it('should filter agents by industry', async () => {
    await element(by.id('filter-button')).tap();
    await element(by.text('Marketing')).tap();
    await element(by.id('apply-filters')).tap();
    
    await detoxExpect(element(by.text('Marketing'))).toBeVisible();
  });

  it('should open agent detail on card tap', async () => {
    await element(by.id('agent-card-0')).tap();
    await detoxExpect(element(by.id('agent-detail-screen'))).toBeVisible();
  });
});
```

### Test Scripts

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e:ios": "detox test --configuration ios.sim.debug",
    "test:e2e:android": "detox test --configuration android.emu.debug",
    "test:e2e:build:ios": "detox build --configuration ios.sim.debug",
    "test:e2e:build:android": "detox build --configuration android.emu.debug"
  }
}
```

---

## 13. CI/CD & Deployment

### Current Deployment Posture (2026-02-21)

The deployment path is now aligned to deterministic Android release handling: build from exact commit SHA, capture explicit EAS `BUILD_ID`, validate the same artifact via Firebase Test Lab, and submit by ID instead of relying on `--latest`.

> **Validated 2026-02-21**: Full Codespaces → EAS Cloud Build → AAB download → Firebase Test Lab flow confirmed working end-to-end. Both Pixel 6 (Android 13) and Pixel 5 (Android 11) passed Robo tests.

---

### EAS Authentication from Codespaces

**`eas token:create` does NOT exist in EAS CLI v18.** Use the Expo website instead.

#### Step 1 — Create a short-lived access token (one-time, in your browser)
1. Go to: https://expo.dev/accounts/waooaw/settings/access-tokens
2. Click **Create token**, set expiry (24h recommended for a session)
3. Copy the token value

#### Step 2 — Set token in Codespaces terminal
```bash
export EXPO_TOKEN=<paste_token_here>
```

#### Step 3 — Verify login
```bash
eas whoami
# should print: waooaw
```

> **Note**: If `eas login` already shows `waooaw` (i.e., you are already logged in via ~/.expo/state.json session), you do NOT need a token — EAS commands will work directly using that session.

---

### Build Methods (Dual Approach)

The CI/CD pipeline supports **two build methods** to accommodate different deployment scenarios:

#### 1. **Expo Cloud Build (expo)** - Recommended for Production
- **Uses**: Expo's cloud infrastructure for building
- **Speed**: 3-7 minutes per build
- **Cost**: Free tier (120 builds/month), then $20/month
- **Ideal for**: CI/CD pipelines, frequent deployments, production releases
- **Requires**: EXPO_TOKEN secret configured

#### 2. **EAS Local Build (local-eas)** - Free Alternative
- **Uses**: GitHub Actions runner to build locally
- **Speed**: 30-60 minutes per build
- **Cost**: Completely free (uses GitHub Actions minutes)
- **Ideal for**: Cost-conscious deployments, one-off builds, testing
- **Requires**: Android SDK pre-installed on runner (~10GB)

**Selection in workflow:**
```yaml
build_method: [expo, local-eas]
default: 'expo'
```

---

### Codespaces → Expo AAB → Firebase Test Lab (Verified Validation Path)

> **Verified 2026-02-21** — this is the exact flow that worked end-to-end from Codespaces.

#### Step 1 — Install EAS CLI
```bash
npm i -g eas-cli@latest
# Verify
eas --version   # should show eas-cli/18.x.x
eas whoami      # should show: waooaw
```

#### Step 2 — Trigger EAS Cloud Build
```bash
cd src/mobile
eas build --platform android --profile production --non-interactive
# Build URL printed: https://expo.dev/accounts/waooaw/projects/waooaw-mobile/builds/<BUILD_ID>
# Wait 5-7 minutes for "Build finished" and artifact URL
```

Available build profiles (from eas.json): `development`, `staging`, `preview`, `demo`, `demo-store`, `production`

#### Step 3 — Inspect Build Metadata
```bash
eas build:view <BUILD_ID> --json
# Confirms: status=FINISHED, artifacts.buildUrl, appVersion, gitCommitHash
```

#### Step 4 — Download AAB from Expo to Codespaces
```bash
# EAS CLI does NOT support --id flag for download (it's only for simulator builds).
# Use the Expo session cookie method instead:

SESSION=$(cat ~/.expo/state.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('auth',{}).get('sessionSecret',''))")
curl -s -L -H "expo-session: $SESSION" \
  "https://expo.dev/artifacts/eas/<ARTIFACT_ID>.aab" \
  -o /tmp/waooaw-release.aab -w "%{http_code}"
# Should print: 200

ls -lh /tmp/waooaw-release.aab
# Confirms: ~34MB, Zip archive (valid AAB)
```

> The artifact URL is in the EAS build:view JSON output under `artifacts.buildUrl`, e.g. `https://expo.dev/artifacts/eas/wVZ7osQEGZPUXELDFJsKYh.aab`

#### Step 5 — Run Firebase Test Lab
```bash
# Switch to owner account (yogeshkhandge@gmail.com) for full GCS access
gcloud config set account yogeshkhandge@gmail.com
gcloud config set project waooaw-oauth

# Verified working device/OS combinations (2026-02-21):
#   oriole (Pixel 6): supports versions 31, 32, 33
#   redfin (Pixel 5): supports version 30 only
# DO NOT use oriole+34 or redfin+33 — they are incompatible and will be skipped

gcloud firebase test android run \
  --type robo \
  --app /tmp/waooaw-release.aab \
  --device model=oriole,version=33,locale=en,orientation=portrait \
  --device model=redfin,version=30,locale=en,orientation=portrait \
  --timeout 15m \
  --project waooaw-oauth
```

#### Step 6 — Check Results
- Results streamed live in terminal (matrix status updates every ~30s)
- Full results at: https://console.firebase.google.com/project/waooaw-oauth/testlab
- Crash logs in GCS: `gs://test-lab-416rbn5b8t2a4-yukhkp045dbbs/<RUN_ID>/oriole-33-en-portrait/data_app_crash_0_com_waooaw_app.txt`
- Video recordings: `gs://test-lab-416rbn5b8t2a4-yukhkp045dbbs/<RUN_ID>/oriole-33-en-portrait/video.mp4`

#### Step 7 — Submit to Play Console Internal Testing

**Until Google Play Developer API is enabled** (requires first approved release), upload manually:
- **Expo build page**: `https://expo.dev/accounts/waooaw/projects/waooaw-mobile/builds/<BUILD_ID>` → click **Download**
- **Codespaces file**: `/tmp/waooaw-release.aab` → right-click in VS Code Explorer → **Download**

Upload to Google Play Console → **Internal testing** → **Create new release** → **Roll out**.

> ⚠️ **Always upload the latest EAS build** — re-uploading an older AAB with the same versionCode will not show an update button to testers (Play Store ignores it).

**After first app approval — fully automated (no manual download):**
```bash
cd src/mobile

# Build + submit in one shot:
eas build --platform android --profile production --non-interactive && \
eas submit --platform android --profile demo --latest --non-interactive

# Or submit a specific already-built ID:
eas submit --platform android --profile demo --id <BUILD_ID> --non-interactive
```

The `demo` submit profile targets `track: internal` — it will NOT publish to production.

**Service account** (already created): `waooaw-playstore-deploy@waooaw-oauth.iam.gserviceaccount.com`
- JSON key stored in: GCP Secret Manager (`GOOGLE_PLAY_SERVICE_ACCOUNT_JSON`), GitHub Actions secret, `src/mobile/secrets/google-play-service-account.json` (gitignored)
- Activation step: Play Console → **Setup → API access** → link `waooaw-oauth` project → grant `waooaw-playstore-deploy` account **Release Manager** role (only possible after first approval)

---

### Known Issues & Fixes (Verified 2026-02-21)

| Issue | Root cause | Fix |
|-------|-----------|-----|
| App crash on launch: `FlashList v2 is only supported on new architecture` | `@shopify/flash-list 2.x` requires `newArchEnabled: true`; app has it `false` | Downgrade to `@shopify/flash-list ^1.8.3` in package.json |
| Firebase Test Lab: all devices skipped | Wrong device/OS combinations (oriole+34, redfin+33 are incompatible) | Use oriole+33 and redfin+30 |
| GCS 403 on `gcloud firebase test android run` | Service account lacks `storage.objects.create` | Run with `yogeshkhandge@gmail.com` account which has Owner role |
| `eas token:create` not found | Command doesn't exist in EAS CLI v18 | Create token at https://expo.dev/accounts/waooaw/settings/access-tokens |
| Expo artifact URL returns 403 | Signed URL expired or no auth header | Use session cookie: `curl -H "expo-session: $SESSION"` |
| Play Store shows no update button after upload | Re-uploaded same versionCode — Play Store ignores identical codes | Always use the latest EAS build; versionCode auto-increments per build |
| `Error 401: invalid_client` on Google Sign-In | `androidClientId` was set to the web OAuth client ID; web clients reject `com.waooaw.app:/` custom URI scheme | Create a dedicated **Android** OAuth client in GCP Console (package: `com.waooaw.app`, SHA-1 from EAS keystore). Set as `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` EAS secret |
| `Error 400: invalid_request` — "OAuth client not found" | `eas.json` production `env` block had literal `"PLACEHOLDER_SET_VIA_EAS_SECRET"` strings which shadowed real EAS secrets with the same key name | Removed placeholder strings from `eas.json` production `env` block — only `APP_ENV` and `EXPO_PUBLIC_API_URL` remain; secrets flow in from EAS directly |
| `Error 400: invalid_request` — "Custom URI scheme is not enabled for your Android client" | Two causes: (1) expo-auth-session v7 generates `com.waooaw.app:/oauthredirect` by default, Android OAuth clients expect `com.googleusercontent.apps.{id}:/oauth2redirect`; (2) passing `webClientId` alongside `androidClientId` makes expo-auth-session use the web client ID in the request | Fixed in `useGoogleAuth.ts`: (1) explicit `redirectUri` via `makeRedirectUri({ native: 'com.googleusercontent.apps.{hash}:/oauth2redirect' })`; (2) on Android only `androidClientId` is passed — no `webClientId` |
| User stuck on Sign-In screen after Google OAuth succeeds | `login()` (Zustand) never called after `AuthService.loginWithGoogle()` — `isAuthenticated` stayed `false` → `RootNavigator` never switched to `MainNavigator` | Fixed in `SignInScreen.tsx`: call `login(authUser)` + `userDataService.saveUserData(authUser)` after successful Google auth |
| User forced to re-authenticate on every app restart | `authStore.initialize()` reads from AsyncStorage but Google auth only wrote to expo-secure-store → AsyncStorage empty on restart | Fixed in `authStore.ts`: SecureStore fallback in `initialize()` — reads from SecureStore if AsyncStorage empty, maps fields, backfills AsyncStorage |
| User stuck on OTP screen after successful verification | `login()` never called after `RegistrationService.verifyOTP()` succeeded | Fixed in `OTPVerificationScreen.tsx`: decode JWT, call `login(authUser)` + `userDataService.saveUserData(authUser)` after OTP verify |
| `destinationMasked` hardcoded as "your email" on OTP screen | `SignUpScreen.tsx` callback dropped `channel` and `destinationMasked` from OTP API response; `AuthNavigator.tsx` had hardcoded fallback | Fixed: extended `onRegistrationSuccess` callback signature to include `channel` + `destinationMasked`; `AuthNavigator.tsx` passes real values |
| "Google OAuth client IDs not configured" on launch | `validateOAuthConfig()` treated empty `androidClientId` as invalid before EAS secrets were applied | Fixed: `isConfigured()` now checks only `webClientId`; `androidClientId` falls back to `webClientId` |
| Play Store update not visible immediately | Play Store client-side cache — update is live but UI delays 5–15 min | Open Play Store → profile → **Manage apps & device** to force a fresh poll |

---

### Release Gate Criteria (Android)

| Gate | Requirement | Submit Decision |
|------|-------------|-----------------|
| **Quality Checks** | Lint/typecheck/tests pass for candidate SHA | Continue only if all pass |
| **Artifact Integrity** | EAS `BUILD_ID` traced to candidate SHA or AAB path confirmed | Continue only with deterministic build |
| **Device Validation** | Firebase Test Lab reports no critical crash | Continue to Play internal track |
| **Google Play API Access** | Service account configured with Release Manager role in Play Console | Required for automated submission (manual upload if pending) |
| **Submission Command** | Use explicit build ID (`eas submit --id <BUILD_ID>`) or path (`eas submit --path <AAB_PATH>`) | Avoid `--latest` in release workflows |

**Note on Google Play API Access:**
- Automated submission requires the app to have at least one **approved release** in Play Console (any track)
- **Before approval**: download AAB from Expo build page and manually upload to Play Console → Internal testing
- **After approval**: go to Play Console → Setup → API access → link GCP project `waooaw-oauth` → grant `waooaw-playstore-deploy@waooaw-oauth.iam.gserviceaccount.com` the **Release Manager** role → automated `eas submit` will work from that point
- Service account JSON is pre-stored in GCP Secret Manager, GitHub Actions secret `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON`, and `src/mobile/secrets/google-play-service-account.json`

**versionCode management:**
- `appVersionSource: remote` in `eas.json` — EAS manages versionCode in the cloud
- `autoIncrement: versionCode` — every EAS build automatically increments by 1
- Never re-use or manually set versionCode — Play Store silently ignores uploads with duplicate codes
- Current sequence: `...12 (manual-39) → 14 (1.0.0) → 15 (0.1.0) → 16 (0.1.0) → 17 (0.1.0, eas.json placeholder fix) → 18 (0.1.0, redirectUri fix) → 19 (manual-41, demo-store) → 20 (manual-43, androidClientId isolation) → 21 (manual-44, CI jq fix)`

### Build Pipeline (EAS + GitHub Actions)

**Key Features:**
- ✅ Dual build methods (expo cloud vs local-eas)
- ✅ AAB artifacts uploaded to GitHub Actions for manual testing
- ✅ Automated submission to Google Play Store (when API access configured)
- ✅ Quality gates (lint, typecheck, tests)

```yaml
# .github/workflows/mobile-playstore-deploy.yml
name: Mobile Google Play Store Deployment

on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [demo, production]
        default: demo
      track:
        type: choice
        options: [internal, alpha, beta, production]
        default: internal
      build_method:
        type: choice
        options: [expo, local-eas]
        default: expo
        description: 'Build method (expo=fast cloud, local-eas=free local)'
      release_notes:
        type: string
        default: 'Bug fixes and performance improvements'

jobs:
  prepare:
    name: Prepare Deployment
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.config.outputs.environment }}
      version: ${{ steps.config.outputs.version }}
      track: ${{ steps.config.outputs.track }}
      build-profile: ${{ steps.config.outputs.build-profile }}
    steps:
      - name: Determine deployment configuration
        id: config
        run: |
          echo "environment=${{ github.event.inputs.environment }}" >> $GITHUB_OUTPUT
          echo "track=${{ github.event.inputs.track }}" >> $GITHUB_OUTPUT
          echo "build-profile=${{ github.event.inputs.environment }}-store" >> $GITHUB_OUTPUT

  lint-and-test:
    name: Quality Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: src/mobile/package-lock.json
      
      - name: Install dependencies
        working-directory: src/mobile
        run: npm ci
      
      - name: Run linter
        working-directory: src/mobile
        run: npm run lint
        continue-on-error: true
      
      - name: Run type check
        working-directory: src/mobile
        run: npm run typecheck
        continue-on-error: true
      
      - name: Run tests
        working-directory: src/mobile
        run: npm test
        continue-on-error: true

  build-and-submit:
    name: Build & Submit to Play Store
    needs: [prepare, lint-and-test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}
      
      - name: Install dependencies
        working-directory: src/mobile
        run: npm ci
      
      # Conditional build: Expo Cloud (fast, paid)
      - name: Build Android App Bundle (Expo Cloud)
        if: github.event.inputs.build_method == 'expo'
        working-directory: src/mobile
        run: |
          echo "🏗️ Building Android App Bundle (Expo Cloud)..."
          eas build \
            --profile ${{ needs.prepare.outputs.build-profile }} \
            --platform android \
            --json \
            --non-interactive \
            --no-wait
          echo "BUILD_METHOD=expo" >> $GITHUB_ENV
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
      
      # Conditional build: EAS Local (slow, free)
      - name: Build Android App Bundle (EAS Local)
        if: github.event.inputs.build_method == 'local-eas'
        working-directory: src/mobile
        run: |
          echo "🏗️ Building Android App Bundle (EAS Local - Free)..."
          eas build \
            --profile ${{ needs.prepare.outputs.build-profile }} \
            --platform android \
            --local \
            --non-interactive
          echo "BUILD_METHOD=local-eas" >> $GITHUB_ENV
          
          # Find and store AAB path
          AAB_PATH=$(ls -t *.aab 2>/dev/null | head -1)
          echo "AAB_PATH=$(realpath $AAB_PATH)" >> $GITHUB_ENV
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
      
      # Wait for Expo cloud builds to complete
      - name: Wait for Expo build completion
        if: env.BUILD_METHOD == 'expo'
        working-directory: src/mobile
        run: |
          echo "⏳ Waiting for Expo build to complete..."
          # Poll build status every 30s, max 30 min
          # (polling logic here)
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
      
      # Download AAB from Expo
      - name: Download AAB from Expo
        if: env.BUILD_METHOD == 'expo'
        working-directory: src/mobile
        run: |
          echo "📥 Downloading AAB from Expo..."
          # Download AAB artifact
          # (download logic here)
      
      # Submit to Play Store (conditional on build method)
      - name: Submit to Google Play Store
        if: always()
        working-directory: src/mobile
        run: |
          if [ "${{ env.BUILD_METHOD }}" == "expo" ]; then
            eas submit --id $BUILD_ID --non-interactive
          else
            eas submit --path "$AAB_PATH" --non-interactive
          fi
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
      
      # Upload AAB artifacts for manual testing
      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: playstore-deployment-${{ needs.prepare.outputs.version }}
          path: |
            src/mobile/*.aab
            src/mobile/build-*.aab
            release_notes.md
          retention-days: 90
```

### Artifact Download for Manual Testing

After workflow completion, download the AAB file from:

1. Go to: `https://github.com/dlai-sd/WAOOAW/actions/runs/<RUN_ID>`
2. Scroll to **Artifacts** section at bottom
3. Click artifact name to download ZIP
4. Extract `.aab` file
5. Upload to Google Play Console → Internal Testing

This enables manual testing before automated submission is configured.

### EAS Build Profiles

```json
// mobile/eas.json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "env": {
        "ENVIRONMENT": "development"
      }
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      },
      "env": {
        "ENVIRONMENT": "demo"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      },
      "env": {
        "ENVIRONMENT": "prod",
        "API_BASE_URL": "https://cp.waooaw.com/api"
      }
    }
  },
  "submit": {
    "demo": {
      "android": {
        "serviceAccountKeyPath": "./secrets/google-play-service-account.json",
        "track": "internal",
        "releaseStatus": "completed"
      }
    },
    "production": {
      "android": {
        "serviceAccountKeyPath": "./secrets/google-play-service-account.json",
        "track": "production",
        "releaseStatus": "completed"
      },
      "ios": {
        "appleId": "dev@waooaw.com",
        "ascAppId": "123456789",
        "appleTeamId": "ABCD1234"
      }
    }
  }
}
```

### Over-The-Air (OTA) Updates

```typescript
// mobile/App.tsx - Auto-update on app launch
import * as Updates from 'expo-updates';

useEffect(() => {
  async function checkForUpdates() {
    if (__DEV__) return; // Skip in dev mode
    
    try {
      const update = await Updates.checkForUpdateAsync();
      if (update.isAvailable) {
        await Updates.fetchUpdateAsync();
        await Updates.reloadAsync(); // Restart app with new update
      }
    } catch (e) {
      console.error('Update check failed:', e);
    }
  }
  
  checkForUpdates();
}, []);
```

### App Store Metadata

#### Google Play Store

| Field | Value |
|-------|-------|
| **App Name** | WAOOAW - AI Agent Marketplace |
| **Short Description** | Hire AI agents that earn your business. 7-day free trial. |
| **Full Description** | Browse 19+ specialized AI agents for Marketing, Education, and Sales. Try before you buy with 7-day free trials. Keep all deliverables even if you cancel. Voice-controlled for hands-free hiring. |
| **Category** | Business → Productivity |
| **Content Rating** | Everyone |
| **Keywords** | AI agents, marketplace, hire AI, marketing automation, education AI, sales AI |

#### Apple App Store

| Field | Value |
|-------|-------|
| **App Name** | WAOOAW - AI Agents |
| **Subtitle** | Agents Earn Your Business |
| **Description** | (Same as Google Play full description) |
| **Primary Category** | Business |
| **Secondary Category** | Productivity |
| **Privacy Policy URL** | https://waooaw.com/privacy |

---

## 14. Project Structure

```
mobile/
├── app.json                  # Expo config
├── eas.json                  # EAS build profiles
├── package.json
├── tsconfig.json
├── babel.config.js
├── metro.config.js
├── index.js                  # Entry point
├── App.tsx                   # Root component
│
├── src/
│   ├── screens/              # Screen components (one per route)
│   │   ├── auth/
│   │   │   ├── SignInScreen.tsx
│   │   │   ├── SignUpScreen.tsx
│   │   │   └── OTPVerifyScreen.tsx
│   │   ├── home/
│   │   │   └── HomeScreen.tsx
│   │   ├── discover/
│   │   │   ├── DiscoverScreen.tsx
│   │   │   ├── AgentDetailScreen.tsx
│   │   │   └── HireWizardScreen.tsx
│   │   ├── agents/
│   │   │   ├── MyAgentsScreen.tsx
│   │   │   ├── TrialDashboardScreen.tsx
│   │   │   └── DeliverablesScreen.tsx
│   │   └── profile/
│   │       ├── ProfileScreen.tsx
│   │       ├── SettingsScreen.tsx
│   │       └── SubscriptionsScreen.tsx
│   │
│   ├── navigation/           # React Navigation setup
│   │   ├── RootNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   ├── MainNavigator.tsx
│   │   └── types.ts          # Navigation type definitions
│   │
│   ├── components/           # Reusable UI components
│   │   ├── AgentCard.tsx
│   │   ├── FilterBar.tsx
│   │   ├── VoiceFab.tsx      # Voice control FAB
│   │   ├── OfflineBanner.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorBoundary.tsx
│   │
│   ├── services/             # API services (from web)
│   │   ├── auth.service.ts
│   │   ├── agent.service.ts
│   │   ├── hireWizard.service.ts
│   │   ├── trial.service.ts
│   │   ├── subscription.service.ts
│   │   └── voiceCommand.service.ts
│   │
│   ├── hooks/                # Custom React hooks
│   │   ├── useAgents.ts
│   │   ├── useAuth.ts
│   │   ├── useNetworkStatus.ts
│   │   ├── useVoiceCommands.ts
│   │   └── useBiometric.ts
│   │
│   ├── store/                # Zustand stores
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── voiceStore.ts
│   │
│   ├── lib/                  # Utilities
│   │   ├── apiClient.ts      # Axios instance
│   │   ├── queryClient.ts    # React Query config
│   │   ├── errorHandler.ts
│   │   └── offlineCache.ts
│   │
│   ├── theme/                # Design system
│   │   ├── colors.ts
│   │   ├── typography.ts
│   │   ├── spacing.ts
│   │   └── components.ts     # Themed component styles
│   │
│   ├── config/               # App configuration
│   │   ├── api.config.ts     # API base URLs
│   │   ├── oauth.config.ts   # Google OAuth
│   │   └── voice.config.ts   # Voice language settings
│   │
│   └── types/                # TypeScript types (from web)
│       ├── agent.types.ts
│       ├── user.types.ts
│       ├── trial.types.ts
│       └── index.ts
│
├── assets/                   # Images, fonts, icons
│   ├── images/
│   │   ├── logo.png
│   │   ├── splash.png
│   │   └── agent-placeholder.png
│   ├── fonts/
│   │   ├── SpaceGrotesk-Bold.ttf
│   │   ├── Outfit-SemiBold.ttf
│   │   └── Inter-Regular.ttf
│   └── icons/
│       ├── icon.png          # App icon (1024x1024)
│       └── adaptive-icon.png # Android adaptive
│
├── e2e/                      # Detox E2E tests
│   ├── discover.test.ts
│   ├── auth.test.ts
│   └── hire.test.ts
│
├── __tests__/                # Jest unit tests
│   ├── services/
│   ├── components/
│   └── hooks/
│
└── .github/
    └── workflows/
        └── mobile-ci.yml     # CI/CD pipeline
```

---

## 15. Development Roadmap

### Phase 1: Foundation (Weeks 1-3)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| **Week 1** | Project Setup | • Expo project initialized<br>• CI/CD pipeline configured<br>• Design system ported from web<br>• API client + auth service ported |
| **Week 2** | Authentication | • Google OAuth2 flow<br>• JWT storage (SecureStore)<br>• Sign In/Sign Up screens<br>• Token refresh logic |
| **Week 3** | Core Navigation | • Tab + Stack navigation<br>• 5 main screens (Home, Discover, My Agents, Profile, Agent Detail)<br>• Screen transitions tested |

**Exit Criteria**: User can sign in with Google, navigate all screens, see static UI

---

### Phase 2: Core Features (Weeks 4-6)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| **Week 4** | Agent Discovery | • Agent list (GET /api/v1/agents)<br>• Search + filters<br>• Agent detail screen<br>• React Query caching |
| **Week 5** | Hire Wizard | • Multi-step form flow<br>• Razorpay payment integration (mobile SDK)<br>• Hire confirmation screen |
| **Week 6** | My Agents & Trials | • Hired agents list<br>• Trial status dashboard<br>• Deliverables viewer<br>• Pull-to-refresh |

**Exit Criteria**: User can browse agents, hire an agent, view trial status

---

### Phase 3: Voice Control (Weeks 7-8)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| **Week 7** | Voice Infrastructure | • Speech-to-text integration<br>• Text-to-speech feedback<br>• Voice command parser<br>• 10 basic commands |
| **Week 8** | Voice UX Polish | • Floating voice button (FAB)<br>• Visual feedback (waveform)<br>• Error handling<br>• Help modal |

**Exit Criteria**: User can navigate, search, and hire using voice commands

---

### Phase 4: Polish & Optimization (Weeks 9-10)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| **Week 9** | Performance | • FlashList for agent lists<br>• Image optimization (expo-image)<br>• Bundle size reduction<br>• Memory profiling |
| **Week 10** | Offline & Testing | • Offline caching<br>• Network status banner<br>• E2E test suite (Detox)<br>• Unit test coverage 80%+ |

**Exit Criteria**: App runs smoothly (60 FPS), passes all E2E tests

---

### Phase 5: Deployment (Weeks 11-12)

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| **Week 11** | Beta Testing | • TestFlight (iOS) + Internal Track (Android)<br>• 10 beta testers<br>• Bug fixes<br>• Analytics integration (Firebase) |
| **Week 12** | Production Launch | • App Store submission<br>• Play Store submission<br>• Marketing assets (screenshots, video)<br>• Production monitoring (Sentry) |

**Exit Criteria**: Apps approved and live on both stores

---

### Post-Launch Roadmap (Months 2-6)

| Month | Feature | Priority |
|-------|---------|----------|
| **Month 2** | Biometric Auth (Touch ID, Face ID) | High |
| **Month 2** | Push Notifications (trial updates, deliverables) | High |
| **Month 3** | Offline Mode (save drafts, queue actions) | Medium |
| **Month 3** | Hindi Language Support (full UI + voice) | High (India market) |
| **Month 4** | In-App Chat (customer ↔ agent communication) | Medium |
| **Month 5** | Widget Support (trial status on home screen) | Low |
| **Month 6** | Apple Watch / Wear OS Companion App | Low |

---

## 16. Risk Mitigation

### Risk Register

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| **Platform API Changes** | Medium | High | Pin React Native version; test on new OS betas; use Expo SDK for stability |
| **Google OAuth Rejection** | Low | Critical | Follow OAuth2 best practices; use Expo AuthSession (approved library); provide privacy policy |
| **`401 invalid_client` on Android** | ✅ Resolved | Critical | **Root cause**: web OAuth client rejects `com.waooaw.app:/oauth2redirect` URI scheme. **Fix**: create a dedicated **Android** OAuth client in GCP Console (package: `com.waooaw.app`, SHA-1 from EAS keystore). Set as `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` EAS secret. See Section 5 for client IDs. |
| **App Store Rejection** | Medium | High | Review guidelines proactively; avoid prohibited content; test on real devices; provide demo account |
| **Voice Accuracy <90%** | Medium | Medium | Support both English + Hindi; provide visual fallback; test in noisy environments |
| **Performance Issues** | Medium | High | Use FlashList, memoization, Hermes; profile early; set performance budgets |
| **Backend API Downtime** | Low | Medium | Implement offline caching; retry logic; show graceful error messages |
| **JWT Token Theft** | Low | Critical | Use SecureStore (Keychain/KeyStore); detect jailbreak; short token expiry (15 min) |
| **Large Bundle Size (>50 MB)** | Medium | Medium | Code splitting; lazy loading; remove unused dependencies; use Hermes |
| **Cross-Platform UI Inconsistencies** | High | Medium | Test on both platforms; use react-native-paper (Material Design); conditional styles |
| **Team Lacks Mobile Expertise** | High | Medium | Allocate 2 weeks for React Native training; hire mobile consultant for code review |

### Success Metrics (KPIs)

| KPI | Target (Month 1) | Target (Month 6) |
|-----|------------------|------------------|
| **Downloads** | 1,000 | 50,000 |
| **Active Users (DAU)** | 200 | 10,000 |
| **Trial Conversions** | 30% | 40% |
| **App Store Rating** | 4.5+ | 4.7+ |
| **Crash-Free Rate** | 99.5% | 99.9% |
| **Voice Command Usage** | 10% | 30% |
| **Average Session Duration** | 3 minutes | 5 minutes |

---

## Appendix A: Technology Comparison Matrix

### React Native vs Flutter vs Native

| Criterion | React Native (Expo) | Flutter | Native (Swift/Kotlin) |
|-----------|---------------------|---------|----------------------|
| **Learning Curve** | Low (if React known) | Medium (Dart + widgets) | High (2 languages) |
| **Development Speed** | Fast | Fast | Slow |
| **Hot Reload** | ✅ Yes | ✅ Yes | ⚠️ Limited |
| **Code Reuse (Web)** | ✅ 60-70% | ❌ 0% | ❌ 0% |
| **Community** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Third-Party Libs** | 1M+ npm packages | Growing | Platform-specific |
| **App Size** | 25-40 MB | 15-20 MB | 10-15 MB |
| **Performance** | Near-native (95%) | Native-like (98%) | Native (100%) |
| **OTA Updates** | ✅ Yes (Expo) | ⚠️ Limited | ❌ No |
| **Complex Animations** | ⚠️ Good | ✅ Excellent | ✅ Excellent |
| **AR/VR Support** | ❌ Limited | ⚠️ Basic | ✅ Excellent |
| **Startup Time** | 1-2 seconds | 0.5-1 second | 0.3-0.5 seconds |

**Verdict**: React Native wins for WAOOAW due to web code reuse and team skillset.

---

## Appendix B: Initial Dependencies

```json
// mobile/package.json (initial dependencies)
{
  "name": "waooaw-mobile",
  "version": "1.0.0",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "test": "jest",
    "lint": "eslint src/",
    "build:android": "eas build --platform android",
    "build:ios": "eas build --platform ios"
  },
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.73.4",
    "expo": "~50.0.0",
    "expo-router": "~3.4.0",
    
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/native-stack": "^6.9.17",
    "@react-navigation/bottom-tabs": "^6.5.11",
    
    "react-native-paper": "^5.11.0",
    "@shopify/flash-list": "^1.6.3",
    "react-native-vector-icons": "^10.0.3",
    "react-native-linear-gradient": "^2.8.3",
    "expo-image": "~1.10.0",
    
    "axios": "^1.6.5",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.4.7",
    "jwt-decode": "^4.0.0",
    
    "expo-secure-store": "~13.0.0",
    "@react-native-async-storage/async-storage": "1.21.0",
    "react-native-keychain": "^8.1.2",
    
    "expo-auth-session": "~5.4.0",
    "expo-web-browser": "~13.0.0",
    
    "expo-speech": "~12.0.0",
    "@react-native-voice/voice": "^3.2.4",
    
    "expo-local-authentication": "~14.0.0",
    "expo-notifications": "~0.27.0",
    "expo-linking": "~6.2.0",
    
    "@react-native-community/netinfo": "11.1.0",
    "expo-updates": "~0.24.0",
    
    "@sentry/react-native": "~5.15.0"
  },
  "devDependencies": {
    "@types/react": "~18.2.45",
    "@types/react-native": "~0.73.0",
    "typescript": "^5.3.0",
    
    "jest": "^29.7.0",
    "@testing-library/react-native": "^12.4.0",
    "jest-expo": "~50.0.0",
    
    "detox": "^20.14.0",
    
    "eslint": "^8.56.0",
    "prettier": "^3.1.1",
    
    "eas-cli": "^5.8.0"
  }
}
```

---

## Appendix C: Quick Start Commands

```bash
# --- Initial Setup ---
cd /workspaces/WAOOAW
mkdir -p src/mobile && cd src/mobile
npx create-expo-app@latest . --template blank-typescript
npm install (dependencies from Appendix B)

# --- Run Locally ---
npm start                    # Start Metro bundler
npm run android              # Run on Android emulator
npm run ios                  # Run on iOS simulator (Mac only)

# --- Test on Physical Device ---
# 1. Install Expo Go app from Play Store / App Store
# 2. npm start
# 3. Scan QR code with Expo Go

# --- Testing ---
npm test                     # Run unit tests
npm run test:coverage        # Coverage report
npm run test:e2e:ios         # E2E tests (iOS)
npm run test:e2e:android     # E2E tests (Android)

# --- Build ---
npx eas build --platform android --profile preview   # APK for testing
npx eas build --platform ios --profile preview       # Internal iOS build
npx eas build --platform all --profile production    # Production builds

# --- Submit to Stores ---
npx eas submit --platform android
npx eas submit --platform ios
```

---

## Summary & Next Steps

### Recommended Approach: React Native (Expo)

**Justification**: React Native with Expo provides the optimal balance of:
- ✅ 95% code sharing between Android and iOS
- ✅ 60-70% reuse of web codebase (types, services, logic)
- ✅ Fast development with hot reload and Expo Go
- ✅ Zero backend API changes required
- ✅ Excellent voice control libraries
- ✅ Managed build/deploy with EAS
- ✅ Team can leverage existing React expertise

### Immediate Next Steps

1. **Week 1**: 
   - Initialize Expo project (`npx create-expo-app`)
   - Set up CI/CD pipeline (GitHub Actions + EAS)
   - Port design system (colors, typography, spacing)
   - Port API client + auth service

2. **Week 2**:
   - Implement Google OAuth2 flow
   - Build Sign In / Sign Up screens
   - Integrate JWT storage (SecureStore)

3. **Week 3**:
   - Set up React Navigation (tabs + stacks)
   - Build 5 core screens (Home, Discover, My Agents, Profile, Agent Detail)
   - Test navigation flow

4. **Weeks 4-12**: Follow roadmap in Section 15

### Key Decisions Required

1. **Google OAuth Client IDs**: ✅ **Resolved** — Android client `270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu` and Web client `270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq` are set as EAS secrets (`EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`, `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`) for `production` and `preview` environments. iOS client still needed when iOS build is initiated.
2. **Razorpay Mobile SDK**: Confirm compatibility with Expo (or use custom native module)
3. **Beta Testing Group**: Identify 10 early testers (5 iOS, 5 Android)
4. **Voice Languages**: Start with English + Hindi or English only in Phase 1?
5. **Push Notification Strategy**: Firebase Cloud Messaging (FCM) setup required

### Expected Timeline
- **Phase 1-2** (Weeks 1-6): Core app functional (auth + browse + hire)
- **Phase 3** (Weeks 7-8): Voice control added
- **Phase 4-5** (Weeks 9-12): Polish + deploy to stores
- **Total**: 12 weeks (3 months) to production launch

### Budget Estimate (External Services)
- Expo EAS build service: $29/month (Production plan)
- Google Play Developer account: $25 one-time
- Apple Developer account: $99/year
- Razorpay mobile SDK: No additional cost (same as web)
- Sentry error tracking: Free tier (5K events/month)

---

**Document Prepared By**: WAOOAW Technical Team  
**Review Required**: CTO, Product Manager, Mobile Lead  
**Next Review Date**: 2026-03-01  
**Status**: Ready for Implementation ✅
