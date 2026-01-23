# Gateway Terraform Module Variables
# Version: 1.0

variable "project_id" {
  description = "GCP project ID where gateway resources will be created"
  type        = string
  validation {
    condition     = length(var.project_id) > 0
    error_message = "Project ID cannot be empty"
  }
}

variable "region" {
  description = "GCP region for deploying Cloud Run services"
  type        = string
  default     = "us-central1"
  validation {
    condition     = contains(["us-central1", "us-east1", "europe-west1", "asia-southeast1"], var.region)
    error_message = "Region must be a valid GCP region"
  }
}

variable "environment" {
  description = "Deployment environment (production, demo, staging, local)"
  type        = string
  validation {
    condition     = contains(["production", "demo", "staging", "local"], var.environment)
    error_message = "Environment must be production, demo, staging, or local"
  }
}

variable "cloud_sql_instance_name" {
  description = "Name of existing Cloud SQL instance for gateway audit logs"
  type        = string
  validation {
    condition     = length(var.cloud_sql_instance_name) > 0
    error_message = "Cloud SQL instance name cannot be empty"
  }
}

variable "redis_instance_name" {
  description = "Name of existing Redis Memorystore instance for rate limiting & budgets"
  type        = string
  validation {
    condition     = length(var.redis_instance_name) > 0
    error_message = "Redis instance name cannot be empty"
  }
}

variable "notification_channels" {
  description = "List of Cloud Monitoring notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

variable "gateway_cp_image" {
  description = "Docker image for API Gateway CP service"
  type        = string
  default     = ""
}

variable "gateway_pp_image" {
  description = "Docker image for API Gateway PP service"
  type        = string
  default     = ""
}

variable "opa_service_image" {
  description = "Docker image for OPA policy service"
  type        = string
  default     = ""
}

variable "gateway_min_instances" {
  description = "Minimum number of Gateway Cloud Run instances"
  type        = number
  default     = 1
  validation {
    condition     = var.gateway_min_instances >= 0 && var.gateway_min_instances <= 10
    error_message = "Min instances must be between 0 and 10"
  }
}

variable "gateway_max_instances" {
  description = "Maximum number of Gateway Cloud Run instances"
  type        = number
  default     = 10
  validation {
    condition     = var.gateway_max_instances >= 1 && var.gateway_max_instances <= 100
    error_message = "Max instances must be between 1 and 100"
  }
}

variable "opa_min_instances" {
  description = "Minimum number of OPA Cloud Run instances"
  type        = number
  default     = 1
  validation {
    condition     = var.opa_min_instances >= 0 && var.opa_min_instances <= 3
    error_message = "OPA min instances must be between 0 and 3"
  }
}

variable "opa_max_instances" {
  description = "Maximum number of OPA Cloud Run instances"
  type        = number
  default     = 3
  validation {
    condition     = var.opa_max_instances >= 1 && var.opa_max_instances <= 10
    error_message = "OPA max instances must be between 1 and 10"
  }
}

variable "enable_opa_policy" {
  description = "Feature flag to enable OPA policy enforcement"
  type        = bool
  default     = true
}

variable "enable_budget_guard" {
  description = "Feature flag to enable budget guard middleware"
  type        = bool
  default     = true
}

variable "enable_rate_limiting" {
  description = "Feature flag to enable rate limiting middleware"
  type        = bool
  default     = true
}

variable "enable_circuit_breaker" {
  description = "Feature flag to enable circuit breaker for Plant API"
  type        = bool
  default     = false
}

variable "enable_opentelemetry" {
  description = "Feature flag to enable OpenTelemetry tracing"
  type        = bool
  default     = true
}

variable "agent_budget_cap_usd" {
  description = "Daily budget cap per agent in USD"
  type        = number
  default     = 1.00
  validation {
    condition     = var.agent_budget_cap_usd > 0 && var.agent_budget_cap_usd <= 100
    error_message = "Agent budget cap must be between 0 and 100 USD"
  }
}

variable "platform_budget_cap_usd" {
  description = "Monthly budget cap for entire platform in USD"
  type        = number
  default     = 100.00
  validation {
    condition     = var.platform_budget_cap_usd >= 50 && var.platform_budget_cap_usd <= 1000
    error_message = "Platform budget cap must be between 50 and 1000 USD"
  }
}

variable "trial_task_limit_per_day" {
  description = "Maximum tasks per day for trial users"
  type        = number
  default     = 10
  validation {
    condition     = var.trial_task_limit_per_day >= 1 && var.trial_task_limit_per_day <= 100
    error_message = "Trial task limit must be between 1 and 100"
  }
}

variable "rate_limit_trial" {
  description = "Rate limit for trial users (requests per hour)"
  type        = number
  default     = 100
}

variable "rate_limit_paid" {
  description = "Rate limit for paid users (requests per hour)"
  type        = number
  default     = 1000
}

variable "rate_limit_enterprise" {
  description = "Rate limit for enterprise users (requests per hour)"
  type        = number
  default     = 10000
}

variable "log_level" {
  description = "Log level for Gateway services"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
  }
}

variable "tags" {
  description = "Additional tags/labels to apply to all resources"
  type        = map(string)
  default     = {}
}
