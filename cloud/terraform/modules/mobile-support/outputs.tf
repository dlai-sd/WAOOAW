# Outputs for Mobile App Supporting Infrastructure

output "firebase_ios_app_id" {
  description = "Firebase iOS app ID"
  value       = google_firebase_apple_app.waooaw_ios.app_id
}

output "firebase_android_app_id" {
  description = "Firebase Android app ID"
  value       = google_firebase_android_app.waooaw_android.app_id
}

output "ota_updates_bucket" {
  description = "GCS bucket name for OTA updates"
  value       = google_storage_bucket.ota_updates.name
}

output "app_store_assets_bucket" {
  description = "GCS bucket name for app store assets"
  value       = google_storage_bucket.app_store_assets.name
}

output "mobile_logs_bucket" {
  description = "GCS bucket name for mobile app logs"
  value       = google_storage_bucket.mobile_logs.name
}

output "cicd_service_account_email" {
  description = "Service account email for CI/CD pipeline"
  value       = google_service_account.mobile_cicd.email
}

output "secret_ids" {
  description = "Map of secret IDs for mobile app configuration"
  value = {
    razorpay_test_key  = google_secret_manager_secret.razorpay_test_key.secret_id
    razorpay_prod_key  = google_secret_manager_secret.razorpay_prod_key.secret_id
    google_oauth_ios   = google_secret_manager_secret.google_oauth_ios.secret_id
    google_oauth_android = google_secret_manager_secret.google_oauth_android.secret_id
    eas_build_token    = google_secret_manager_secret.eas_build_token.secret_id
  }
}
