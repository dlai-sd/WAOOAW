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

variable "customer_domain" {
  description = "Customer portal domain"
  type        = string
}

variable "platform_domain" {
  description = "Platform portal domain"
  type        = string
}

variable "backend_negs" {
  description = "Backend Network Endpoint Groups"
  type = map(object({
    name   = string
    region = string
  }))
}
