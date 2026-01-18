variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "environment" {
  description = "Environment (demo, uat, prod)"
  type        = string
}

variable "instance_name" {
  description = "Cloud SQL instance name"
  type        = string
}

variable "database_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_15"
}

variable "tier" {
  description = "Machine tier (db-custom-2-8192, db-f1-micro, etc.)"
  type        = string
  default     = "db-custom-2-8192"
}

variable "availability_type" {
  description = "REGIONAL for HA, ZONAL for single zone"
  type        = string
  default     = "ZONAL"
}

variable "disk_size_gb" {
  description = "Initial disk size in GB"
  type        = number
  default     = 50
}

variable "enable_pitr" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = false
}

variable "max_connections" {
  description = "Maximum database connections"
  type        = string
  default     = "100"
}

variable "private_network_id" {
  description = "VPC network ID for private IP (format: projects/PROJECT/global/networks/NETWORK)"
  type        = string
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "plant"
}

variable "database_user" {
  description = "Database user"
  type        = string
  default     = "plant_app"
}

variable "database_password" {
  description = "Database password (use Secret Manager or GitHub secrets)"
  type        = string
  sensitive   = true
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}
