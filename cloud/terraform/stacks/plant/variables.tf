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

variable "db_deletion_protection" {
  description = "Enable deletion protection on Cloud SQL instance"
  type        = bool
  default     = true
}
