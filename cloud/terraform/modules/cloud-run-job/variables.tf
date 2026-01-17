variable "job_name" {
  description = "Name of the Cloud Run Job"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "image" {
  description = "Container image for the job"
  type        = string
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets from Secret Manager (key = env var name, value = secret:version)"
  type        = map(string)
  default     = {}
}

variable "vpc_connector_id" {
  description = "VPC Serverless Connector ID for private network access"
  type        = string
}

variable "cloud_sql_connection_name" {
  description = "Cloud SQL connection name (PROJECT:REGION:INSTANCE)"
  type        = string
  default     = ""
}

variable "service_account_email" {
  description = "Service account email for the job"
  type        = string
}

variable "cpu" {
  description = "CPU limit"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory limit"
  type        = string
  default     = "512Mi"
}

variable "timeout_seconds" {
  description = "Job execution timeout in seconds"
  type        = number
  default     = 600
}

variable "max_retries" {
  description = "Maximum number of retry attempts"
  type        = number
  default     = 0
}
