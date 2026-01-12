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

# ============================================================================
# Component Enable Flags
# ============================================================================

variable "enable_cp" {
  description = "Enable Customer Portal (CP) component - deploys 3 services"
  type        = bool
  default     = true
}

variable "enable_pp" {
  description = "Enable Platform Portal (PP) component - deploys 3 services"
  type        = bool
  default     = false
}

variable "enable_plant" {
  description = "Enable Plant (Core API) component - deploys 2 services"
  type        = bool
  default     = false
}

# ============================================================================
# Docker Images
# ============================================================================

variable "cp_frontend_image" {
  description = "Docker image for CP frontend"
  type        = string
  default     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp:latest"
}

variable "cp_backend_image" {
  description = "Docker image for CP backend"
  type        = string
  default     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:latest"
}

variable "pp_frontend_image" {
  description = "Docker image for PP frontend"
  type        = string
  default     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:latest"
}

variable "pp_backend_image" {
  description = "Docker image for PP backend"
  type        = string
  default     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-backend:latest"
}

variable "plant_backend_image" {
  description = "Docker image for Plant backend"
  type        = string
  default     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-backend:latest"
}

# ============================================================================
# Infrastructure Configuration
# ============================================================================

variable "static_ip_name" {
  description = "Name of the existing static IP"
  type        = string
  default     = "waooaw-lb-ip"
}

variable "domains" {
  description = "Domain mapping per environment and component"
  type = map(object({
    cp    = string
    pp    = string
    plant = string
  }))

  default = {
    demo = {
      cp    = "cp.demo.waooaw.com"
      pp    = "pp.demo.waooaw.com"
      plant = "plant.demo.waooaw.com"
    }
    uat = {
      cp    = "cp.uat.waooaw.com"
      pp    = "pp.uat.waooaw.com"
      plant = "plant.uat.waooaw.com"
    }
    prod = {
      cp    = "www.waooaw.com"
      pp    = "pp.waooaw.com"
      plant = "plant.waooaw.com"
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
