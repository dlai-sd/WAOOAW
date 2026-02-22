# Variables for mobile infrastructure

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "android_package_name" {
  description = "Android app package name"
  type        = string
}

variable "ios_bundle_id" {
  description = "iOS app bundle identifier"
  type        = string
}

variable "ios_app_store_id" {
  description = "Apple App Store ID (optional, empty string if not yet published)"
  type        = string
  default     = ""
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}
