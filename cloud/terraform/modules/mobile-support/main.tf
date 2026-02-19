# Mobile App Supporting Infrastructure Module
# Manages Firebase, GCS buckets for OTA updates, and monitoring for WAOOAW mobile apps

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# 1. Firebase Project for Analytics, Crashlytics, Performance Monitoring
# ============================================================================

resource "google_firebase_project" "mobile_app" {
  provider = google
  project  = var.project_id
}

# Firebase iOS App
resource "google_firebase_apple_app" "waooaw_ios" {
  provider     = google
  project      = var.project_id
  display_name = "WAOOAW iOS"
  bundle_id    = var.ios_bundle_id
  app_store_id = var.ios_app_store_id # Optional, add after App Store submission

  depends_on = [google_firebase_project.mobile_app]
}

# Firebase Android App
resource "google_firebase_android_app" "waooaw_android" {
  provider     = google
  project      = var.project_id
  display_name = "WAOOAW Android"
  package_name = var.android_package_name

  depends_on = [google_firebase_project.mobile_app]
}

# ============================================================================
# 2. GCS Bucket for Expo OTA Updates
# ============================================================================

resource "google_storage_bucket" "ota_updates" {
  name          = "${var.project_id}-mobile-ota-updates"
  location      = var.region
  storage_class = "STANDARD"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90 # Keep OTA updates for 90 days
    }
    action {
      type = "Delete"
    }
  }
  
  labels = {
    environment = var.environment
    app         = "mobile"
    managed_by  = "terraform"
  }
}

# ============================================================================
# 3. GCS Bucket for App Store Assets (Screenshots, Videos, Metadata)
# ============================================================================

resource "google_storage_bucket" "app_store_assets" {
  name          = "${var.project_id}-mobile-store-assets"
  location      = var.region
  storage_class = "NEARLINE" # Cost-effective for infrequent access
  
  uniform_bucket_level_access = true
  
  labels = {
    environment = var.environment
    app         = "mobile"
    managed_by  = "terraform"
  }
}

# ============================================================================
# 4. Secret Manager Secrets for Mobile App
# ============================================================================

# Razorpay Test Key
resource "google_secret_manager_secret" "razorpay_test_key" {
  secret_id = "mobile-razorpay-test-key"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.environment
    app         = "mobile"
  }
}

# Razorpay Production Key
resource "google_secret_manager_secret" "razorpay_prod_key" {
  secret_id = "mobile-razorpay-prod-key"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = "production"
    app         = "mobile"
  }
}

# Google OAuth Client ID (iOS)
resource "google_secret_manager_secret" "google_oauth_ios" {
  secret_id = "mobile-google-oauth-ios-client-id"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.environment
    app         = "mobile"
  }
}

# Google OAuth Client ID (Android)
resource "google_secret_manager_secret" "google_oauth_android" {
  secret_id = "mobile-google-oauth-android-client-id"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.environment
    app         = "mobile"
  }
}

# EAS Build Token (for CI/CD)
resource "google_secret_manager_secret" "eas_build_token" {
  secret_id = "mobile-eas-build-token"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.environment
    app         = "mobile"
  }
}

# ============================================================================
# 5. IAM Permissions for CI/CD Service Account
# ============================================================================

resource "google_service_account" "mobile_cicd" {
  account_id   = "mobile-cicd-sa"
  display_name = "Mobile CI/CD Service Account"
  description  = "Service account for mobile app CI/CD pipeline (GitHub Actions)"
}

# Grant access to secrets
resource "google_secret_manager_secret_iam_member" "cicd_secret_accessor" {
  for_each = {
    razorpay_test = google_secret_manager_secret.razorpay_test_key.id
    razorpay_prod = google_secret_manager_secret.razorpay_prod_key.id
    oauth_ios     = google_secret_manager_secret.google_oauth_ios.id
    oauth_android = google_secret_manager_secret.google_oauth_android.id
    eas_token     = google_secret_manager_secret.eas_build_token.id
  }
  
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mobile_cicd.email}"
}

# Grant access to OTA updates bucket
resource "google_storage_bucket_iam_member" "cicd_ota_admin" {
  bucket = google_storage_bucket.ota_updates.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mobile_cicd.email}"
}

# Grant access to app store assets bucket
resource "google_storage_bucket_iam_member" "cicd_assets_admin" {
  bucket = google_storage_bucket.app_store_assets.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mobile_cicd.email}"
}

# ============================================================================
# 6. Cloud Monitoring for Mobile App Performance
# ============================================================================

# Alert Policy: High crash rate
resource "google_monitoring_alert_policy" "mobile_crash_rate" {
  display_name = "Mobile App - High Crash Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Crash rate > 1%"
    
    condition_threshold {
      filter          = "resource.type = \"firebase_app\" AND metric.type = \"firebase.app/crash/free_rate\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 0.99 # Alert if crash-free rate < 99%
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = var.alert_notification_channels
  
  alert_strategy {
    auto_close = "604800s" # 7 days
  }
}

# Alert Policy: High ANR rate (Android)
resource "google_monitoring_alert_policy" "mobile_anr_rate" {
  display_name = "Mobile App - High ANR Rate (Android)"
  combiner     = "OR"
  
  conditions {
    display_name = "ANR rate > 0.5%"
    
    condition_threshold {
      filter          = "resource.type = \"firebase_app\" AND metric.type = \"firebase.app/anr/rate\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.005
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = var.alert_notification_channels
  
  alert_strategy {
    auto_close = "604800s"
  }
}

# ============================================================================
# 7. Log Sink for Mobile App Logs (iOS/Android app logs to Cloud Logging)
# ============================================================================

resource "google_logging_project_sink" "mobile_app_logs" {
  name        = "mobile-app-logs-sink"
  destination = "storage.googleapis.com/${google_storage_bucket.mobile_logs.name}"
  
  filter = <<-EOT
    resource.type = "firebase_app"
    OR logName = "projects/${var.project_id}/logs/mobile-app"
  EOT
  
  unique_writer_identity = true
}

# GCS bucket for mobile app logs
resource "google_storage_bucket" "mobile_logs" {
  name          = "${var.project_id}-mobile-app-logs"
  location      = var.region
  storage_class = "COLDLINE" # Cost-effective for archival logs
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 365 # Retain logs for 1 year
    }
    action {
      type = "Delete"
    }
  }
  
  labels = {
    environment = var.environment
    app         = "mobile"
    managed_by  = "terraform"
  }
}

# Grant log sink permission to write to bucket
resource "google_storage_bucket_iam_member" "log_sink_writer" {
  bucket = google_storage_bucket.mobile_logs.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.mobile_app_logs.writer_identity
}
