variable "environment" {
  description = "Environment name"
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

variable "services" {
  description = "Map of services to create NEGs for"
  type = map(object({
    name   = string
    region = string
  }))
}

variable "alert_p95_latency" {
  description = "Alert for P95 latency"
  type        = number
  default     = 200
}

variable "alert_error_rate" {
  description = "Alert for error rate"
  type        = number
  default     = 1
}
