# Mobile App Supporting Infrastructure Module

This Terraform module manages GCP resources that support the WAOOAW mobile application:

## Resources Created

### 1. Firebase Project
- **Firebase iOS App**: For analytics, crashlytics, performance monitoring
- **Firebase Android App**: Same capabilities for Android
- **Bundle IDs**: 
  - iOS: `com.waooaw.app` (production), `com.waooaw.app.staging` (staging)
  - Android: Same pattern

### 2. Cloud Storage Buckets
- **OTA Updates** (`{project-id}-mobile-ota-updates`): Stores Expo OTA update manifests
  - Versioning enabled
  - 90-day lifecycle (auto-delete old updates)
- **App Store Assets** (`{project-id}-mobile-store-assets`): Screenshots, videos, metadata
  - NEARLINE storage (cost-effective)
- **Mobile Logs** (`{project-id}-mobile-app-logs`): Archived app logs
  - COLDLINE storage
  - 365-day retention

### 3. Secret Manager Secrets
- `mobile-razorpay-test-key`: Razorpay test API key
- `mobile-razorpay-prod-key`: Razorpay production API key
- `mobile-google-oauth-ios-client-id`: Google OAuth client ID for iOS
- `mobile-google-oauth-android-client-id`: Google OAuth client ID for Android
- `mobile-eas-build-token`: EAS build token for CI/CD

### 4. Service Account
- **`mobile-cicd-sa`**: Service account for GitHub Actions CI/CD
  - Access to all secrets (read-only)
  - Admin access to OTA updates and app store assets buckets
  - Used by EAS builds in CI/CD pipeline

### 5. Cloud Monitoring
- **Alert: High Crash Rate**: Triggers if crash-free rate < 99%
- **Alert: High ANR Rate** (Android): Triggers if ANR rate > 0.5%
- **Log Sink**: Streams mobile app logs to Cloud Storage

## Usage

### Step 1: Add to your Terraform stack

```hcl
module "mobile_support" {
  source = "../../modules/mobile-support"
  
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  
  ios_bundle_id       = "com.waooaw.app"
  android_package_name = "com.waooaw.app"
  
  # Optional: Add after App Store submission
  ios_app_store_id = "123456789"
  
  # Optional: Notification channels for alerts
  alert_notification_channels = [
    "projects/${var.project_id}/notificationChannels/1234567890"
  ]
}
```

### Step 2: Populate secrets

After Terraform creates the secrets, populate them:

```bash
# Razorpay Test Key
echo -n "rzp_test_YOUR_KEY" | gcloud secrets versions add mobile-razorpay-test-key --data-file=-

# Razorpay Production Key
echo -n "rzp_live_YOUR_KEY" | gcloud secrets versions add mobile-razorpay-prod-key --data-file=-

# Google OAuth iOS Client ID
echo -n "YOUR_IOS_CLIENT_ID.apps.googleusercontent.com" | gcloud secrets versions add mobile-google-oauth-ios-client-id --data-file=-

# Google OAuth Android Client ID
echo -n "YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com" | gcloud secrets versions add mobile-google-oauth-android-client-id --data-file=-

# EAS Build Token (from https://expo.dev/accounts/[account]/settings/access-tokens)
echo -n "YOUR_EAS_TOKEN" | gcloud secrets versions add mobile-eas-build-token --data-file=-
```

### Step 3: Configure GitHub Actions

Add the service account key as a GitHub secret:

```bash
# Create and download service account key
gcloud iam service-accounts keys create mobile-cicd-key.json \
  --iam-account=mobile-cicd-sa@${PROJECT_ID}.iam.gserviceaccount.com

# Add to GitHub secrets as GCP_SA_KEY
# (Do this via GitHub UI: Settings > Secrets > Actions > New repository secret)
```

### Step 4: Update mobile app config

Use the outputs in your mobile app configuration:

```bash
# Get outputs
terraform output -json mobile_support > mobile_support_outputs.json

# Use in environment.config.ts
FIREBASE_IOS_APP_ID=$(terraform output -raw firebase_ios_app_id)
FIREBASE_ANDROID_APP_ID=$(terraform output -raw firebase_android_app_id)
```

## Outputs

- `firebase_ios_app_id`: Firebase iOS app ID (for google-services.json)
- `firebase_android_app_id`: Firebase Android app ID (for google-services.json)
- `ota_updates_bucket`: GCS bucket for OTA updates
- `app_store_assets_bucket`: GCS bucket for store assets
- `mobile_logs_bucket`: GCS bucket for logs
- `cicd_service_account_email`: Service account email for CI/CD
- `secret_ids`: Map of all secret IDs

## Cost Estimate

Monthly costs (approximate):

- Firebase Projects: **Free** (Spark plan includes 10GB bandwidth, 10K Analytics events/day)
- Secret Manager: **$0.60** (5 secrets × $0.06/month + $0.03/10K accesses)
- GCS Buckets:
  - OTA Updates (STANDARD, ~100MB): **$0.01**
  - Store Assets (NEARLINE, ~2GB): **$0.02**
  - Logs (COLDLINE, ~10GB): **$0.04**
- Cloud Monitoring: **Free** (within free tier limits)
- **Total: ~$0.67/month**

## Dependencies

- GCP project with billing enabled
- Terraform >= 1.5.0
- Google Provider >= 5.0
- Firebase API enabled: `gcloud services enable firebase.googleapis.com`
- Secret Manager API enabled: `gcloud services enable secretmanager.googleapis.com`

## Notes

- **Firebase Setup**: After Terraform creates Firebase apps, download `google-services.json` (Android) and `GoogleService-Info.plist` (iOS) from Firebase Console
- **EAS Secrets**: EAS Build can access GCP secrets via the service account during builds
- **Staging vs Production**: Use separate Terraform workspaces or projects for staging/production environments
- **App Store IDs**: Add `ios_app_store_id` after submitting to App Store (improves Firebase attribution)
