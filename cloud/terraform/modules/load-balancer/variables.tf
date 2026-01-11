variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "static_ip_address" {
  description = "Static IP address (existing)"
  type        = string
}

variable "static_ip_name" {
  description = "Static IP name"
  type        = string
}

variable "enable_api" {
  description = "Whether to route to backend API"
  type        = bool
  default     = true
}

variable "enable_customer" {
  description = "Whether to route to customer portal"
  type        = bool
  default     = true
}

variable "enable_platform" {
  description = "Whether to route to platform portal"
  type        = bool
  default     = true
}

variable "customer_domain" {
  description = "Customer portal domain"
  type        = string
}

variable "platform_domain" {
  description = "Platform portal domain"
  type        = string
}

variable "backend_negs" {
  description = "Backend Network Endpoint Groups (map with enabled services only)"
  type = map(object({
    name   = string
    region = string
  }))
}
