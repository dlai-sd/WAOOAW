# Outputs for mobile infrastructure

output "firebase_project_id" {
  description = "Firebase project ID"
  value       = google_firebase_project.waooaw_mobile.project
}

output "android_app_id" {
  description = "Firebase Android app ID"
  value       = google_firebase_android_app.waooaw_android.app_id
}

output "ios_app_id" {
  description = "Firebase iOS app ID"
  value       = google_firebase_apple_app.waooaw_ios.app_id
}

output "ota_updates_bucket" {
  description = "Cloud Storage bucket for OTA updates"
  value       = google_storage_bucket.ota_updates.name
}

output "app_assets_bucket" {
  description = "Cloud Storage bucket for app assets"
  value       = google_storage_bucket.app_assets.name
}

output " eas_builder_email" {
  description = "EAS builder service account email"
  value       = google_service_account.eas_builder.email
}

output "secret_ids" {
  description = "Map of secret IDs"
  value = {
    google_oauth = google_secret_manager_secret.google_oauth_client_id.secret_id
    razorpay_key_id = google_secret_manager_secret.razorpay_key_id.secret_id
    razorpay_key_secret = google_secret_manager_secret.razorpay_key_secret.secret_id
    sentry_dsn = google_secret_manager_secret.sentry_dsn.secret_id
  }
}
