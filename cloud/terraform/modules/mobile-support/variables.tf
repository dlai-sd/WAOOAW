# Variables for Mobile App Supporting Infrastructure

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "ios_bundle_id" {
  description = "iOS app bundle identifier"
  type        = string
  default     = "com.waooaw.app"
}

variable "ios_app_store_id" {
  description = "iOS App Store ID (optional, add after submission)"
  type        = string
  default     = null
}

variable "android_package_name" {
  description = "Android app package name"
  type        = string
  default     = "com.waooaw.app"
}

variable "alert_notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}
