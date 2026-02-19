# Firebase Configuration for WAOOAW Mobile App

## Firebase Services Integration

This document outlines Firebase services integration for monitoring, analytics, and crash reporting across all environments.

---

## Services Used

1. **Firebase Analytics** - User behavior tracking, conversion funnels
2. **Firebase Crashlytics** - Real-time crash reporting
3. **Firebase Performance Monitoring** - App performance metrics
4. **Firebase Remote Config** - Feature flags and A/B testing (future)
5. **Firebase Cloud Messaging (FCM)** - Push notifications (future)

---

## Environment Setup

### Development Environment

**Firebase Project**: `waooaw-dev` (Recommended separate project for testing)

**Configuration** (src/mobile/google-services-dev.json):
```json
{
  "project_info": {
    "project_number": "REPLACE_WITH_DEV_PROJECT_NUMBER",
    "firebase_url": "https://waooaw-dev.firebaseio.com",
    "project_id": "waooaw-dev",
    "storage_bucket": "waooaw-dev.appspot.com"
  },
  "client": [
    {
      "client_info": {
        "mobilesdk_app_id": "REPLACE_WITH_DEV_ANDROID_APP_ID",
        "android_client_info": {
          "package_name": "com.waooaw.app.dev"
        }
      },
      "oauth_client": [],
      "api_key": [
        {
          "current_key": "REPLACE_WITH_DEV_API_KEY"
        }
      ],
      "services": {
        "appinvite_service": {
          "other_platform_oauth_client": []
        }
      }
    }
  ],
  "configuration_version": "1"
}
```

**iOS Configuration** (src/mobile/GoogleService-Info-dev.plist):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CLIENT_ID</key>
    <string>REPLACE_WITH_DEV_IOS_CLIENT_ID</string>
    <key>REVERSED_CLIENT_ID</key>
    <string>REPLACE_WITH_REVERSED_CLIENT_ID</string>
    <key>API_KEY</key>
    <string>REPLACE_WITH_DEV_IOS_API_KEY</string>
    <key>GCM_SENDER_ID</key>
    <string>REPLACE_WITH_DEV_SENDER_ID</string>
    <key>PLIST_VERSION</key>
    <string>1</string>
    <key>BUNDLE_ID</key>
    <string>com.waooaw.app.dev</string>
    <key>PROJECT_ID</key>
    <string>waooaw-dev</string>
    <key>STORAGE_BUCKET</key>
    <string>waooaw-dev.appspot.com</string>
    <key>IS_ADS_ENABLED</key>
    <false/>
    <key>IS_ANALYTICS_ENABLED</key>
    <true/>
    <key>IS_APPINVITE_ENABLED</key>
    <false/>
    <key>IS_GCM_ENABLED</key>
    <true/>
    <key>IS_SIGNIN_ENABLED</key>
    <true/>
    <key>GOOGLE_APP_ID</key>
    <string>REPLACE_WITH_DEV_GOOGLE_APP_ID</string>
    <key>DATABASE_URL</key>
    <string>https://waooaw-dev.firebaseio.com</string>
</dict>
</plist>
```

---

### Staging Environment

**Firebase Project**: `waooaw-staging`

**Configuration**: Similar to dev, but with staging project IDs
- Android: `com.waooaw.app.staging`
- iOS: `com.waooaw.app.staging`

---

### Production Environment

**Firebase Project**: `waooaw-prod`

**Configuration**: Production keys from GCP Secret Manager
- Android: `com.waooaw.app`
- iOS: `com.waooaw.app`

---

## Analytics Events Tracking

### User Journey Events

```typescript
// src/mobile/src/services/analytics/firebase.analytics.ts

import analytics from '@react-native-firebase/analytics';

export const analyticsService = {
  // Authentication
  async trackSignIn(method: 'google' | 'apple' | 'email') {
    await analytics().logLogin({ method });
  },
  
  async trackSignUp(method: 'google' | 'apple' | 'email') {
    await analytics().logSignUp({ method });
  },
  
  // Agent Discovery
  async trackAgentView(agentId: string, agentName: string, industry: string) {
    await analytics().logViewItem({
      item_id: agentId,
      item_name: agentName,
      item_category: industry,
    });
  },
  
  async trackAgentSearch(searchTerm: string, resultsCount: number) {
    await analytics().logSearch({
      search_term: searchTerm,
      results_count: resultsCount,
    });
  },
  
  // Hire Flow (Conversion Funnel)
  async trackHireStart(agentId: string, planType: 'monthly' | 'quarterly' | 'annual') {
    await analytics().logBeginCheckout({
      item_id: agentId,
      value: 12000, // default value, update with actual
      currency: 'INR',
      item_category: planType,
    });
  },
  
  async trackHireComplete(agentId: string, planType: string, amount: number) {
    await analytics().logPurchase({
      transaction_id: `hire_${agentId}_${Date.now()}`,
      value: amount,
      currency: 'INR',
      items: [{
        item_id: agentId,
        item_name: `Agent ${agentId}`,
        item_category: planType,
        price: amount,
        quantity: 1,
      }],
    });
  },
  
  async trackHireCancel(agentId: string, step: string) {
    await analytics().logEvent('hire_cancel', {
      agent_id: agentId,
      cancel_step: step,
    });
  },
  
  // Trial Management
  async trackTrialStart(agentId: string) {
    await analytics().logEvent('trial_start', { agent_id: agentId });
  },
  
  async trackTrialComplete(agentId: string, converted: boolean) {
    await analytics().logEvent('trial_complete', {
      agent_id: agentId,
      converted,
    });
  },
  
  async trackDeliverableView(deliverableId: string, type: string) {
    await analytics().logEvent('deliverable_view', {
      deliverable_id: deliverableId,
      type,
    });
  },
  
  // Voice Control
  async trackVoiceCommand(command: string, success: boolean) {
    await analytics().logEvent('voice_command', {
      command,
      success,
    });
  },
  
  // Screen Views (Auto-tracked in React Navigation)
  async trackScreen(screenName: string, screenClass: string) {
    await analytics().logScreenView({
      screen_name: screenName,
      screen_class: screenClass,
    });
  },
};
```

---

## Crashlytics Integration

### Setup

```typescript
// src/mobile/src/services/monitoring/crashlytics.ts

import crashlytics from '@react-native-firebase/crashlytics';

export const crashlyticsService = {
  // Initialize (call in App.tsx on mount)
  async initialize() {
    // Enable crash collection (disabled in dev by default)
    if (__DEV__) {
      await crashlytics().setCrashlyticsCollectionEnabled(false);
    } else {
      await crashlytics().setCrashlyticsCollectionEnabled(true);
    }
  },
  
  // Set user context
  async setUser(userId: string, email?: string) {
    await crashlytics().setUserId(userId);
    if (email) {
      await crashlytics().setAttribute('email', email);
    }
  },
  
  // Log non-fatal errors
  async recordError(error: Error, context?: Record<string, any>) {
    if (context) {
      Object.entries(context).forEach(([key, value]) => {
        crashlytics().setAttribute(key, String(value));
      });
    }
    await crashlytics().recordError(error);
  },
  
  // Log custom events (for debugging crashes)
  async log(message: string) {
    await crashlytics().log(message);
  },
  
  // Test crash (use only in testing)
  async testCrash() {
    crashlytics().crash();
  },
};
```

**Integration in App.tsx**:
```typescript
import { crashlyticsService } from './services/monitoring/crashlytics';
import { useAuthStore } from './store/authStore';

useEffect(() => {
  crashlyticsService.initialize();
  
  // Set user context when authenticated
  const user = useAuthStore.getState().user;
  if (user) {
    crashlyticsService.setUser(user.id, user.email);
  }
}, []);
```

---

## Performance Monitoring

### Setup

```typescript
// src/mobile/src/services/monitoring/firebase.performance.ts

import perf from '@react-native-firebase/perf';

export const performanceService = {
  // Trace API calls
  async traceAPICall<T>(
    url: string,
    method: string,
    apiCall: () => Promise<T>
  ): Promise<T> {
    const trace = await perf().startTrace(`api_${method}_${url.replace(/\//g, '_')}`);
    trace.putAttribute('method', method);
    trace.putAttribute('url', url);
    
    try {
      const startTime = Date.now();
      const result = await apiCall();
      const duration = Date.now() - startTime;
      
      trace.putMetric('response_time', duration);
      trace.putAttribute('status', 'success');
      await trace.stop();
      
      return result;
    } catch (error) {
      trace.putAttribute('status', 'error');
      await trace.stop();
      throw error;
    }
  },
  
  // Trace screen rendering
  async traceScreenLoad(screenName: string, renderFunction: () => Promise<void>) {
    const trace = await perf().startTrace(`screen_${screenName}`);
    
    try {
      await renderFunction();
      await trace.stop();
    } catch (error) {
      await trace.stop();
      throw error;
    }
  },
  
  // Custom metrics
  async startTrace(name: string) {
    return await perf().startTrace(name);
  },
};
```

**Integration in API Client**:
```typescript
// src/mobile/src/lib/apiClient.ts
import { performanceService } from '../services/monitoring/firebase.performance';

apiClient.interceptors.request.use(async (config) => {
  // Start performance trace
  config.metadata = { startTime: Date.now() };
  return config;
});

apiClient.interceptors.response.use(
  async (response) => {
    const duration = Date.now() - response.config.metadata.startTime;
    
    // Log to Firebase Performance
    const trace = await performanceService.startTrace(
      `api_${response.config.method}_${response.config.url}`
    );
    trace.putMetric('response_time', duration);
    trace.putAttribute('status_code', String(response.status));
    await trace.stop();
    
    return response;
  },
  async (error) => {
    const duration = Date.now() - error.config?.metadata?.startTime || 0;
    
    // Log error to Firebase Performance
    const trace = await performanceService.startTrace(
      `api_${error.config?.method}_${error.config?.url}`
    );
    trace.putMetric('response_time', duration);
    trace.putAttribute('status_code', String(error.response?.status || 0));
    trace.putAttribute('error', 'true');
    await trace.stop();
    
    return Promise.reject(error);
  }
);
```

---

## Sentry Integration (Alternative/Complementary to Crashlytics)

**Why use Sentry alongside Firebase?**
- More detailed error context (breadcrumbs, user actions)
- Better error grouping and deduplication
- Release health tracking
- Performance monitoring for transactions

### Setup

```bash
# Install Sentry
npm install --save @sentry/react-native
npx @sentry/wizard -i reactNative -p ios android
```

```typescript
// src/mobile/src/config/sentry.config.ts

import * as Sentry from '@sentry/react-native';
import { config } from './env';

export const initSentry = () => {
  if (config.monitoring.sentryDsn && !__DEV__) {
    Sentry.init({
      dsn: config.monitoring.sentryDsn,
      environment: config.app.env, // development, staging, production
      tracesSampleRate: 1.0, // 100% in staging, reduce to 0.1 (10%) in production
      enableAutoSessionTracking: true,
      sessionTrackingIntervalMillis: 30000, // 30 seconds
      
      // Performance monitoring
      integrations: [
        new Sentry.ReactNativeTracing({
          tracingOrigins: ['localhost', config.api.baseUrl, /^\//],
          routingInstrumentation: new Sentry.ReactNavigationInstrumentation(),
        }),
      ],
      
      // Filter sensitive data
      beforeSend(event, hint) {
        // Remove sensitive user data
        if (event.user) {
          delete event.user.email;
          delete event.user.ip_address;
        }
        
        // Remove authorization headers
        if (event.request?.headers) {
          delete event.request.headers.Authorization;
        }
        
        return event;
      },
    });
  }
};
```

**Integration in App.tsx**:
```typescript
import { initSentry } from './config/sentry.config';
import * as Sentry from '@sentry/react-native';

// Initialize before App component
initSentry();

// Wrap App component
export default Sentry.wrap(App);
```

---

## Key Metrics to Track

### Business Metrics (Firebase Analytics)

| Metric | Event | Formula |
|--------|-------|---------|
| **Sign-Up Conversion** | `sign_up` / `app_open` | % of users who sign up |
| **Hire Conversion** | `purchase` / `view_item` | % of agent views that convert |
| **Trial-to-Paid** | `purchase` / `trial_start` | % of trials that convert to paid |
| **Agent Discovery** | `view_item_list` / `app_open` | % of users who browse agents |
| **Search Usage** | `search` / `screen_view(Discover)` | % of Discover visits with search |

### Technical Metrics (Firebase Performance + Crashlytics)

| Metric | Source | Target |
|--------|--------|--------|
| **Crash-Free Rate** | Crashlytics | >99.5% |
| **App Start Time** | Performance | <2s (cold start) |
| **API Response Time** | Performance | <500ms (p95) |
| **Screen Render Time** | Performance | <16ms (60 FPS) |
| **Memory Usage** | Performance | <150 MB (average) |

---

## Alerting & Monitoring Dashboard

### Firebase Crashlytics Alerts

Setup in Firebase Console → Crashlytics → Settings:

1. **New Crash Alert**: Email team when new crash type detected
2. **Velocity Alert**: >10 crashes/hour for same issue
3. **Regression Alert**: Previously resolved crash reoccurs
4. **ANR Alert** (Android): App Not Responding >5 instances/hour

### Sentry Alerts

Setup in Sentry → Alerts:

1. **Error Spike**: >100 errors in 1 hour (production)
2. **Release Health**: Crash-free rate <99% for new release
3. **Performance Degradation**: API response time >1s (p95)
4. **User Feedback**: User reports error via feedback widget

### GCP Cloud Monitoring Dashboard

Create dashboard in GCP Console → Monitoring → Dashboards:

**Panels**:
1. Mobile app crash rate (from Firebase)
2. API request rate (from backend Cloud Run services)
3. Database query latency (from Cloud SQL)
4. Cloud Storage bandwidth (OTA updates)
5. Error logs (from Cloud Logging)

---

## Privacy & Compliance

### Data Collection Transparency

**What we collect** (disclosed in Privacy Policy):
- ✅ User ID (anonymous Firebase Analytics ID)
- ✅ Device info (OS version, device model, screen size)
- ✅ App usage (screens viewed, features used)
- ✅ Performance data (crash logs, app speed)
- ✅ IP address (geolocation for analytics)

**What we DON'T collect**:
- ❌ Personal data without consent (Firebase auto-anonymizes)
- ❌ User content (agent conversations, deliverables)
- ❌ Payment details (handled by Razorpay, not logged)

### User Consent

```typescript
// src/mobile/src/components/analytics/AnalyticsConsent.tsx

import React, { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import analytics from '@react-native-firebase/analytics';

export const AnalyticsConsent = () => {
  const [consentGiven, setConsentGiven] = useState<boolean | null>(null);
  
  useEffect(() => {
    checkConsent();
  }, []);
  
  const checkConsent = async () => {
    const consent = await AsyncStorage.getItem('analytics_consent');
    setConsentGiven(consent === 'true');
    
    // Enable/disable Firebase Analytics based on consent
    await analytics().setAnalyticsCollectionEnabled(consent === 'true');
  };
  
  const acceptConsent = async () => {
    await AsyncStorage.setItem('analytics_consent', 'true');
    await analytics().setAnalyticsCollectionEnabled(true);
    setConsentGiven(true);
  };
  
  const declineConsent = async () => {
    await AsyncStorage.setItem('analytics_consent', 'false');
    await analytics().setAnalyticsCollectionEnabled(false);
    setConsentGiven(false);
  };
  
  if (consentGiven !== null) return null; // Consent already given/declined
  
  return (
    <Modal visible transparent>
      <View style={styles.container}>
        <Text style={styles.title}>Help us improve</Text>
        <Text style={styles.description}>
          We use analytics to understand how you use WAOOAW and improve your experience.
          No personal data is collected without your explicit permission.
        </Text>
        <Button title="Accept" onPress={acceptConsent} />
        <Button title="Decline" onPress={declineConsent} />
      </View>
    </Modal>
  );
};
```

---

## Testing Firebase Integration

### Local Testing (Development)

```bash
# Test Firebase connection
cd src/mobile
npm run ios
# In app: Check Firebase Console → Project Settings → General → Your apps → iOS/Android
# Status should show "Connected"

# Test Crashlytics (force crash)
# In app: Settings → Developer Options → Test Crash
# Check Firebase Console → Crashlytics → Crashes (should appear within 5 minutes)

# Test Analytics
# In app: Navigate through flows (sign in, browse agents, etc.)
# Firebase Console → Analytics → DebugView (enable debug mode first)
```

**Enable Analytics Debug Mode**:

iOS:
```bash
# Add to Xcode scheme: Product → Scheme → Edit Scheme → Run → Arguments
-FIRDebugEnabled
```

Android:
```bash
# Run command
adb shell setprop debug.firebase.analytics.app com.waooaw.app.dev
```

---

### Staging Testing

```bash
# Build staging app with EAS
cdworkspaces/WAOOAW/src/mobile
eas build --profile preview --platform ios

# Install on physical device
# Test all flows, check Firebase Console → Analytics → Events

# Trigger test crash
# Check Firebase Console → Crashlytics (should appear immediately)
```

---

### Production Monitoring

**Week 1 After Launch**:
1. Check Crashlytics daily for new crash types
2. Review top 10 events in Analytics (ensure tracking correct)
3. Monitor API response times in Performance
4. Review Sentry issues (triage P0/P1 errors)
5. Check Cloud Monitoring dashboard for infrastructure issues

**Ongoing**:
1. Weekly: Review Analytics funnel (sign-up → hire conversion)
2. Monthly: Audit crash-free rate (target >99.5%)
3. Quarterly: Review performance metrics vs targets

---

## Terraform Configuration for Firebase

```hcl
# cloud/terraform/mobile/firebase.tf

resource "google_firebase_project" "waooaw_mobile" {
  provider = google-beta
  project  = var.gcp_project_id
}

resource "google_firebase_android_app" "waooaw_android" {
  provider     = google-beta
  project      = var.gcp_project_id
  display_name = "WAOOAW Android"
  package_name = var.android_package_name
  
  depends_on = [google_firebase_project.waooaw_mobile]
}

resource "google_firebase_apple_app" "waooaw_ios" {
  provider      = google-beta
  project       = var.gcp_project_id
  display_name  = "WAOOAW iOS"
  bundle_id     = var.ios_bundle_id
  app_store_id  = var.ios_app_store_id
  
  depends_on = [google_firebase_project.waooaw_mobile]
}

# Analytics
resource "google_firebase_analytics" "waooaw_analytics" {
  provider = google-beta
  project  = var.gcp_project_id
  
  depends_on = [google_firebase_project.waooaw_mobile]
}
```

---

## FAQ

**Q: Should we use Firebase or Sentry?**  
A: Use BOTH. Firebase for mobile-specific features (Crashlytics, Analytics, Performance), Sentry for detailed error context and release health.

**Q: What's the cost?**  
A: Firebase Spark (free tier) sufficient for <50K daily active users. Sentry free tier: 5K errors/month. Budget $50/mo for production.

**Q: How to handle GDPR?**  
A: Implement consent modal (see AnalyticsConsent component). Respect user opt-out. Firebase auto-anonymizes IPs in EU.

**Q: Can we test Firebase locally?**  
A: Yes, use Firebase Local Emulator Suite for Analytics, Crashlytics in simulator (with debug mode enabled).

---

**Document Status**: ✅ Ready for Implementation  
**Last Updated**: 2026-02-18  
**Owner**: Mobile DevOps Team
