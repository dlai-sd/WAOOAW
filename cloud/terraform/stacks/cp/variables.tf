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

variable "cp_frontend_image" {
  description = "Docker image for CP frontend"
  type        = string
}

variable "cp_backend_image" {
  description = "Docker image for CP backend"
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
