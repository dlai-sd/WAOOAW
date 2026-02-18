# WAOOAW Mobile App - Supporting Infrastructure (Terraform)
# 
# This Terraform configuration manages GCP infrastructure that supports the mobile app,
# but does NOT deploy the mobile app itself (that's handled by EAS).
#
# Managed Resources:
# - Firebase projects for each environment
# - Cloud Storage buckets for OTA update artifacts
# - Cloud Monitoring dashboards for mobile metrics
# - Secret Manager secrets for API keys
# - IAM roles for CI/CD service accounts

terraform {
  required_version = ">= 1.5.0"
  
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
    prefix = "mobile-infrastructure"
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

# Variables
variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "waooaw-production"
}

variable "gcp_region" {
  description = "GCP Region for resources"
  type        = string
  default     = "asia-south1"
}

variable "environments" {
  description = "Environments to provision"
  type        = list(string)
  default     = ["development", "staging", "production"]
}

variable "firebase_projects" {
  description = "Firebase project IDs for each environment"
  type        = map(string)
  default = {
    development = "waooaw-dev"
    staging     = "waooaw-staging"
    production  = "waooaw-prod"
  }
}

# ==========================================
# Cloud Storage Buckets for OTA Updates
# ==========================================

resource "google_storage_bucket" "mobile_ota_updates" {
  for_each = toset(var.environments)
  
  name          = "waooaw-mobile-ota-${each.key}"
  location      = var.gcp_region
  storage_class = "STANDARD"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90  # Delete OTA bundles older than 90 days
    }
    action {
      type = "Delete"
    }
  }
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  labels = {
    environment = each.key
    managed-by  = "terraform"
    app         = "waooaw-mobile"
  }
}

# Make OTA buckets publicly readable (for expo-updates)
resource "google_storage_bucket_iam_member" "mobile_ota_public_read" {
  for_each = toset(var.environments)
  
  bucket = google_storage_bucket.mobile_ota_updates[each.key].name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# ==========================================
# Secret Manager for Mobile App Secrets
# ==========================================

# Razorpay Keys
resource "google_secret_manager_secret" "razorpay_key_id" {
  for_each = toset(var.environments)
  
  secret_id = "mobile-razorpay-key-id-${each.key}"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = each.key
    app         = "waooaw-mobile"
  }
}

resource "google_secret_manager_secret" "razorpay_key_secret" {
  for_each = toset(var.environments)
  
  secret_id = "mobile-razorpay-key-secret-${each.key}"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = each.key
    app         = "waooaw-mobile"
  }
}

# Google OAuth Client IDs
resource "google_secret_manager_secret" "google_oauth_client_id" {
  for_each = toset(var.environments)
  
  secret_id = "mobile-google-oauth-client-id-${each.key}"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = each.key
    app         = "waooaw-mobile"
  }
}

# Sentry DSN
resource "google_secret_manager_secret" "sentry_dsn" {
  for_each = toset(var.environments)
  
  secret_id = "mobile-sentry-dsn-${each.key}"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = each.key
    app         = "waooaw-mobile"
  }
}

# Expo Token for CI/CD
resource "google_secret_manager_secret" "expo_token" {
  secret_id = "mobile-expo-token"
  
  replication {
    auto {}
  }
  
  labels = {
    app = "waooaw-mobile"
  }
}

# ==========================================
# Service Account for CI/CD
# ==========================================

resource "google_service_account" "mobile_cicd" {
  account_id   = "mobile-cicd"
  display_name = "Mobile CI/CD Service Account"
  description  = "Service account for mobile app CI/CD pipelines (GitHub Actions)"
}

# Grant CI/CD service account access to secrets
resource "google_secret_manager_secret_iam_member" "mobile_cicd_secrets_access" {
  for_each = toset([
    google_secret_manager_secret.expo_token.id,
  ])
  
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mobile_cicd.email}"
}

# Grant CI/CD service account access to OTA buckets
resource "google_storage_bucket_iam_member" "mobile_cicd_ota_access" {
  for_each = toset(var.environments)
  
  bucket = google_storage_bucket.mobile_ota_updates[each.key].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mobile_cicd.email}"
}

# ==========================================
# Cloud Monitoring Dashboard for Mobile App
# ==========================================

resource "google_monitoring_dashboard" "mobile_app_metrics" {
  dashboard_json = jsonencode({
    displayName = "WAOOAW Mobile App Metrics"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "App Crash Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"mobile_app\" metric.type=\"firebase.crashlytics/crash_free_rate\""
                  }
                }
                plotType = "LINE"
              }]
              yAxis = {
                label = "Crash-Free Rate (%)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "Active Users (DAU)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"mobile_app\" metric.type=\"firebase.analytics/daily_active_users\""
                  }
                }
                plotType = "LINE"
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "API Response Time (P95)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"global\" metric.type=\"custom.googleapis.com/mobile/api_response_time\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_PERCENTILE_95"
                    }
                  }
                }
                plotType = "LINE"
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "OTA Update Adoption Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"mobile_app\" metric.type=\"custom.googleapis.com/mobile/ota_adoption_rate\""
                  }
                }
                plotType = "STACKED_AREA"
              }]
            }
          }
        }
      ]
    }
  })
}

# ==========================================
# Alerting Policies
# ==========================================

# Alert on high crash rate
resource "google_monitoring_alert_policy" "mobile_high_crash_rate" {
  display_name = "Mobile App - High Crash Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Crash-free rate below 99%"
    
    condition_threshold {
      filter          = "resource.type=\"mobile_app\" metric.type=\"firebase.crashlytics/crash_free_rate\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 0.99
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.mobile_alerts_slack.id,
    google_monitoring_notification_channel.mobile_alerts_email.id
  ]
  
  alert_strategy {
    auto_close = "604800s"  # 7 days
  }
}

# Notification channels
resource "google_monitoring_notification_channel" "mobile_alerts_slack" {
  display_name = "Mobile Alerts - Slack"
  type         = "slack"
  
  labels = {
    channel_name = "#mobile-alerts"
  }
  
  sensitive_labels {
    auth_token = var.slack_webhook_token
  }
}

resource "google_monitoring_notification_channel" "mobile_alerts_email" {
  display_name = "Mobile Alerts - Email"
  type         = "email"
  
  labels = {
    email_address = "mobile-alerts@waooaw.com"
  }
}

# ==========================================
# Outputs
# ==========================================

output "ota_bucket_names" {
  description = "OTA update bucket names for each environment"
  value       = { for env, bucket in google_storage_bucket.mobile_ota_updates : env => bucket.name }
}

output "ota_bucket_urls" {
  description = "OTA update bucket URLs"
  value       = { for env, bucket in google_storage_bucket.mobile_ota_updates : env => "gs://${bucket.name}" }
}

output "cicd_service_account_email" {
  description = "CI/CD service account email"
  value       = google_service_account.mobile_cicd.email
}

output "monitoring_dashboard_url" {
  description = "URL to Cloud Monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.mobile_app_metrics.id}?project=${var.gcp_project_id}"
}

# Note: Secret values are NOT output for security reasons.
# Access them via: gcloud secrets versions access latest --secret=<secret-id>
