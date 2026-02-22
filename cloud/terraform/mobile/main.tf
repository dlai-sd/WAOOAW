# Terraform Mobile Infrastructure
# Manages Firebase, Cloud Storage, Secrets, and Monitoring for WAOOAW mobile app

terraform {
  required_version = ">= 1.3.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "waooaw-terraform-state"
    prefix = "mobile"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Local variables
locals {
  environment = terraform.workspace
  app_name    = "waooaw-mobile"

  common_labels = {
    app         = "waooaw"
    component   = "mobile"
    environment = local.environment
    managed_by  = "terraform"
  }
}

# Firebase Project
resource "google_firebase_project" "waooaw_mobile" {
  provider = google-beta
  project  = var.gcp_project_id
}

# Firebase Android App
resource "google_firebase_android_app" "waooaw_android" {
  provider     = google-beta
  project      = var.gcp_project_id
  display_name = "WAOOAW Android ${title(local.environment)}"
  package_name = var.android_package_name

  depends_on = [google_firebase_project.waooaw_mobile]
}

# Firebase iOS App
resource "google_firebase_apple_app" "waooaw_ios" {
  provider     = google-beta
  project      = var.gcp_project_id
  display_name = "WAOOAW iOS ${title(local.environment)}"
  bundle_id    = var.ios_bundle_id
  app_store_id = var.ios_app_store_id

  depends_on = [google_firebase_project.waooaw_mobile]
}

# Cloud Storage bucket for OTA updates
resource "google_storage_bucket" "ota_updates" {
  name          = "${var.gcp_project_id}-mobile-ota-${local.environment}"
  location      = var.gcp_region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90 # Keep old OTA updates for 90 days
    }
    action {
      type = "Delete"
    }
  }

  labels = local.common_labels
}

# Cloud Storage bucket for app assets (screenshots, videos, etc.)
resource "google_storage_bucket" "app_assets" {
  name          = "${var.gcp_project_id}-mobile-assets-${local.environment}"
  location      = var.gcp_region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = local.common_labels
}

# Secret Manager secrets for mobile app
resource "google_secret_manager_secret" "google_oauth_client_id" {
  secret_id = "mobile-google-oauth-client-id-${local.environment}"

  replication {
    auto {}
  }

  labels = local.common_labels
}

resource "google_secret_manager_secret" "razorpay_key_id" {
  secret_id = "mobile-razorpay-key-id-${local.environment}"

  replication {
    auto {}
  }

  labels = local.common_labels
}

resource "google_secret_manager_secret" "razorpay_key_secret" {
  secret_id = "mobile-razorpay-key-secret-${local.environment}"

  replication {
    auto {}
  }

  labels = local.common_labels
}

resource "google_secret_manager_secret" "sentry_dsn" {
  secret_id = "mobile-sentry-dsn-${local.environment}"

  replication {
    auto {}
  }

  labels = local.common_labels
}

# IAM - Service Account for EAS builds
resource "google_service_account" "eas_builder" {
  account_id   = "mobile-eas-builder-${local.environment}"
  display_name = "EAS Mobile Builder (${local.environment})"
  description  = "Service account for Expo Application Services builds"
}

# IAM - Grant EAS builder access to secrets
resource "google_secret_manager_secret_iam_member" "eas_secrets_access" {
  for_each = toset([
    google_secret_manager_secret.google_oauth_client_id.id,
    google_secret_manager_secret.razorpay_key_id.id,
    google_secret_manager_secret.razorpay_key_secret.id,
    google_secret_manager_secret.sentry_dsn.id,
  ])

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.eas_builder.email}"
}

# IAM - Grant EAS builder access to storage buckets
resource "google_storage_bucket_iam_member" "eas_ota_access" {
  bucket = google_storage_bucket.ota_updates.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.eas_builder.email}"
}

resource "google_storage_bucket_iam_member" "eas_assets_access" {
  bucket = google_storage_bucket.app_assets.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.eas_builder.email}"
}

# Cloud Monitoring - Alert policy for crash rate
resource "google_monitoring_alert_policy" "high_crash_rate" {
  display_name = "Mobile App - High Crash Rate (${local.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Crash-free rate below 99%"

    condition_threshold {
      filter          = "resource.type=\"firebase_domain\" AND metric.type=\"firebase.com/crashlytics/crash_free_rate\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 0.99

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "604800s" # 7 days
  }

  documentation {
    content   = "Crash-free rate has dropped below 99%. Check Firebase Crashlytics for details."
    mime_type = "text/markdown"
  }
}

# Cloud Monitoring - Alert policy for high error rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "Mobile App - High Error Rate (${local.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Error rate above 5%"

    condition_threshold {
      filter          = "resource.type=\"firebase_domain\" AND metric.type=\"firebase.com/crashlytics/error_rate\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "Error rate has exceeded 5%. Check Firebase Crashlytics for details."
    mime_type = "text/markdown"
  }
}
