variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "environment" {
  description = "Environment (demo, uat, prod)"
  type        = string

  validation {
    condition     = contains(["demo", "uat", "prod"], var.environment)
    error_message = "Environment must be demo, uat, or prod."
  }
}

variable "pp_frontend_image" {
  description = "Docker image for PP frontend"
  type        = string
}

variable "pp_backend_image" {
  description = "Docker image for PP backend"
  type        = string
}

variable "min_instances" {
  description = "Cloud Run minimum instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Cloud Run maximum instances"
  type        = number
  default     = 5
}

variable "attach_secret_manager_secrets" {
  description = "If true, attach Secret Manager-backed env vars (OAuth/JWT) to Cloud Run services."
  type        = bool
  default     = true
}

variable "enable_db_updates" {
  description = "Enable break-glass DB update endpoints (true for demo/uat, false for prod)"
  type        = string
  default     = "false"
}

variable "allowed_email_domains" {
  description = "Comma-separated list of allowed email domains for PP admin login"
  type        = string
  default     = "dlaisd.com,waooaw.com"
}

variable "enable_dev_token" {
  description = "Enable /auth/dev-token endpoint (development only — always false in UAT/prod)"
  type        = string
  default     = "false"
}

variable "enable_metering_debug" {
  description = "Enable /metering/debug endpoints (development only — always false in UAT/prod)"
  type        = string
  default     = "false"
}
variable "private_network_id" {
  description = "VPC network ID for the Serverless Connector (format: projects/PROJECT/global/networks/NETWORK)"
  type        = string
}

variable "vpc_connector_cidr" {
  description = "CIDR range for PP VPC Serverless Connector. Must not overlap with Cloud SQL (10.19.0.0/16) or other connectors."
  type        = string
  default     = "10.8.0.32/28" # Plant uses 10.8.0.0/28; CP uses 10.8.0.16/28
}