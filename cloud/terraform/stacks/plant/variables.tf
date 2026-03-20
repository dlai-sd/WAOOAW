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

variable "plant_backend_image" {
  description = "Docker image for Plant backend"
  type        = string
}

variable "plant_gateway_image" {
  description = "Docker image for Plant gateway (FastAPI proxy)"
  type        = string
}

variable "plant_opa_image" {
  description = "Docker image for the Plant OPA policy engine service. Build once, promote demo \u2192 uat \u2192 prod by injecting a different tag."
  type        = string
}

variable "plant_migration_image" {
  description = "Docker image for Plant database migrations"
  type        = string
  default     = "gcr.io/waooaw-oauth/plant-migrations:latest"
}

variable "min_instances" {
  description = "Cloud Run minimum instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Cloud Run maximum instances"
  type        = number
  default     = 10
}

variable "attach_secret_manager_secrets" {
  description = "If true, attach Secret Manager-backed env vars (OAuth/JWT) to Cloud Run services."
  type        = bool
  default     = true
}

# Database Configuration
variable "private_network_id" {
  description = "VPC network ID for private IP (format: projects/PROJECT/global/networks/NETWORK)"
  type        = string
}

variable "vpc_connector_cidr" {
  description = "CIDR range for VPC Serverless Connector (must not overlap with Cloud SQL)"
  type        = string
  default     = "10.8.0.0/28" # Small range, avoids 10.19.0.0/16 used by Cloud SQL
}

variable "database_password" {
  description = "Database password for plant_app user"
  type        = string
  sensitive   = true
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-custom-2-8192"
}

variable "db_availability_type" {
  description = "REGIONAL for HA, ZONAL for single zone"
  type        = string
  default     = "ZONAL"
}

variable "db_disk_size_gb" {
  description = "Initial disk size in GB"
  type        = number
  default     = 50
}

variable "db_enable_pitr" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = false
}

variable "db_max_connections" {
  description = "Maximum database connections"
  type        = string
  default     = "100"
}

variable "db_enable_public_ip" {
  description = "Enable public IPv4 on the Plant Cloud SQL instance for environments that rely on the Codespaces Cloud SQL Auth Proxy path."
  type        = bool
  default     = false
}

variable "db_deletion_protection" {
  description = "Enable deletion protection on Cloud SQL instance"
  type        = bool
  default     = true
}

# ── OTP / Email delivery ───────────────────────────────────────────────────────

variable "smtp_host" {
  description = "SMTP server hostname for OTP email delivery"
  type        = string
  default     = "smtp.gmail.com" # Same across all envs; override here if needed
}

variable "smtp_port" {
  description = "SMTP server port (587 = STARTTLS)"
  type        = string
  default     = "587"
}

variable "smtp_from_email" {
  description = "From-address for OTP emails. Must be a verified sender on the SMTP account. Set per env in *.tfvars."
  type        = string
  # No default — Terraform plan will fail if not set, forcing explicit per-env value.
}

variable "smtp_username_secret" {
  description = "Secret Manager secret name (no version) for the SMTP username. Set per env in *.tfvars."
  type        = string
  # No default — must be set explicitly per env; secret may differ across demo/uat/prod.
}

variable "smtp_password_secret" {
  description = "Secret Manager secret name (no version) for the SMTP app-password. Set per env in *.tfvars."
  type        = string
  # No default — must be set explicitly per env.
}

variable "xai_api_key_secret_name" {
  description = "GCP Secret Manager secret name (no version suffix) for the Grok/XAI API key injected into Plant runtime."
  type        = string
  default     = "XAI_API_KEY"
}

# ---------------------------------------------------------------------------
# Payments configuration
# ---------------------------------------------------------------------------

variable "payments_mode" {
  description = "Payment processing mode for Plant backend. 'coupon' = in-memory stub (demo/uat). 'razorpay' = live Razorpay integration (prod). Never baked into the image — injected at deploy time."
  type        = string
  default     = "coupon" # Safe default: in-memory stub. Set to 'razorpay' in prod.tfvars.
  validation {
    condition     = contains(["razorpay", "coupon"], var.payments_mode)
    error_message = "payments_mode must be 'razorpay' or 'coupon'."
  }
}

variable "attach_razorpay_secrets" {
  description = "If true, inject RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET from GCP Secret Manager into plant_backend. Set to true only in environments where Razorpay secrets exist (typically prod and uat)."
  type        = bool
  default     = false # Demo: coupon mode, no Razorpay secrets needed.
}

variable "razorpay_key_id_secret" {
  description = "GCP Secret Manager secret name (no version suffix) for the Razorpay Key ID. Used only when attach_razorpay_secrets=true."
  type        = string
  default     = "RAZORPAY_KEY_ID"
}

variable "razorpay_key_secret_name" {
  description = "GCP Secret Manager secret name (no version suffix) for the Razorpay Key Secret. Used only when attach_razorpay_secrets=true."
  type        = string
  default     = "RAZORPAY_KEY_SECRET"
}
