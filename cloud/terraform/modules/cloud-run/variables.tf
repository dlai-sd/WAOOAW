variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "service_type" {
  description = "Type of service (backend, customer-portal, platform-portal)"
  type        = string
}

variable "image" {
  description = "Docker image URL"
  type        = string
}

variable "port" {
  description = "Container port"
  type        = number
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 5
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secret references (name = secret:version)"
  type        = map(string)
  default     = {}
}

variable "cloud_sql_connection_name" {
  description = "Cloud SQL connection name for Cloud SQL Proxy integration"
  type        = string
  default     = null
}

variable "vpc_connector_id" {
  description = "VPC Serverless Connector ID for private network access"
  type        = string
  default     = null
}
