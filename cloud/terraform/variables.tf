variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "waooaw-oauth"
}

variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "Environment (demo, uat, prod)"
  type        = string

  validation {
    condition     = contains(["demo", "uat", "prod"], var.environment)
    error_message = "Environment must be demo, uat, or prod."
  }
}

variable "at_least_one_service_enabled" {
  description = "Validation variable - ensures at least one service is enabled"
  type        = bool
  default     = true

  validation {
    condition     = var.enable_backend_api || var.enable_customer_portal || var.enable_platform_portal
    error_message = "At least one service must be enabled (enable_backend_api, enable_customer_portal, or enable_platform_portal)."
  }
}

variable "enable_backend_api" {
  description = "Whether to deploy the backend API Cloud Run service"
  type        = bool
  default     = true
}

variable "enable_customer_portal" {
  description = "Whether to deploy the customer portal Cloud Run service"
  type        = bool
  default     = true
}

variable "enable_platform_portal" {
  description = "Whether to deploy the platform portal Cloud Run service"
  type        = bool
  default     = true
}

variable "static_ip_name" {
  description = "Name of the existing static IP"
  type        = string
  default     = "waooaw-lb-ip"
}

variable "backend_image" {
  description = "Docker image for backend API"
  type        = string
  default     = "gcr.io/waooaw-oauth/waooaw-api:latest"
}

variable "customer_portal_image" {
  description = "Docker image for customer portal"
  type        = string
  default     = "gcr.io/waooaw-oauth/waooaw-portal:latest"
}

variable "platform_portal_image" {
  description = "Docker image for platform portal"
  type        = string
  default     = "gcr.io/waooaw-oauth/waooaw-platform-portal:latest"
}

variable "domains" {
  description = "Domain mapping per environment"
  type = map(object({
    customer_portal = string
    platform_portal = string
  }))

  default = {
    demo = {
      customer_portal = "cp.demo.waooaw.com"
      platform_portal = "pp.demo.waooaw.com"
    }
    uat = {
      customer_portal = "cp.uat.waooaw.com"
      platform_portal = "pp.uat.waooaw.com"
    }
    prod = {
      customer_portal = "www.waooaw.com"
      platform_portal = "pp.waooaw.com"
    }
  }
}

variable "scaling" {
  description = "Scaling configuration per environment"
  type = map(object({
    min = number
    max = number
  }))

  default = {
    demo = {
      min = 0
      max = 5
    }
    uat = {
      min = 1
      max = 10
    }
    prod = {
      min = 2
      max = 100
    }
  }
}
