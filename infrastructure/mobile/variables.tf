variable "gcp_project_id" {
  description = "GCP Project ID for WAOOAW"
  type        = string
  default     = "waooaw-production"
}

variable "gcp_region" {
  description = "Primary GCP region"
  type        = string
  default     = "asia-south1"  # Mumbai region for Indian users
}

variable "environments" {
  description = "List of environments to provision infrastructure for"
  type        = list(string)
  default     = ["development", "staging", "production"]
}

variable "firebase_projects" {
  description = "Firebase project IDs mapped to environments"
  type        = map(string)
  default = {
    development = "waooaw-dev"
    staging     = "waooaw-staging"
    production  = "waooaw-prod"
  }
}

variable "slack_webhook_token" {
  description = "Slack webhook token for mobile alerts"
  type        = string
  sensitive   = true
  default     = ""  # Set via TF_VAR_slack_webhook_token environment variable
}

variable "enable_monitoring" {
  description = "Enable Cloud Monitoring and alerting"
  type        = bool
  default     = true
}

variable "ota_bucket_retention_days" {
  description = "Number of days to retain OTA update bundles"
  type        = number
  default     = 90
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    project    = "waooaw"
    component  = "mobile"
    managed_by = "terraform"
    team       = "mobile-engineering"
  }
}
