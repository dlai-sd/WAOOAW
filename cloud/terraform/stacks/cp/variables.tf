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

variable "plant_gateway_url" {
  description = "Override for PLANT_GATEWAY_URL used by CP backend (e.g., direct Cloud Run URL). Leave empty to use the environment's plant.<env>.waooaw.com domain."
  type        = string
  default     = ""
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

variable "otp_delivery_mode" {
  description = "OTP delivery mode for CP: 'disabled' (echo OTP to logs, local dev only) or 'provider' (attempt delivery via smtp etc). Set explicitly in each environment tfvars — never inferred from ENVIRONMENT at runtime."
  type        = string
  default     = "provider" # Safe default: attempt delivery. Override to 'disabled' in local-only tfvars if needed.
}

variable "cp_otp_delivery_provider" {
  description = "OTP delivery provider for CP when otp_delivery_mode=provider (e.g. smtp)."
  type        = string
  default     = "smtp"
}

variable "payments_mode" {
  description = "Payment mode for CP Backend config endpoint. 'razorpay' = show both Razorpay and coupon options. 'coupon' = coupon only. Injected at deploy time — never baked into the image. Same image is promoted demo → uat → prod."
  type        = string
  default     = "razorpay"
  validation {
    condition     = contains(["razorpay", "coupon"], var.payments_mode)
    error_message = "payments_mode must be 'razorpay' or 'coupon'."
  }
}
