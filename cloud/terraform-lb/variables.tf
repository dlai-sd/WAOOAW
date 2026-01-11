variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "Primary GCP region"
  type        = string
}

variable "environment" {
  description = "Environment (demo, uat, prod)"
  type        = string
}

variable "enable_backend_api" {
  description = "Enable backend API"
  type        = bool
}

variable "enable_customer_portal" {
  description = "Enable customer portal"
  type        = bool
}

variable "enable_platform_portal" {
  description = "Enable platform portal"
  type        = bool
}

variable "static_ip_name" {
  description = "Name of existing static IP"
  type        = string
}

variable "domains" {
  description = "Domain mapping per environment"
  type = map(object({
    customer_portal = string
    platform_portal = string
  }))
}
