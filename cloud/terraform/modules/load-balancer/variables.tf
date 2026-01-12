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

# Component Enable Flags
variable "enable_cp" {
  description = "Whether to enable CP component routing"
  type        = bool
  default     = true
}

variable "enable_pp" {
  description = "Whether to enable PP component routing"
  type        = bool
  default     = false
}

variable "enable_plant" {
  description = "Whether to enable Plant component routing"
  type        = bool
  default     = false
}

# Component Domains
variable "cp_domain" {
  description = "CP domain"
  type        = string
}

variable "pp_domain" {
  description = "PP domain"
  type        = string
}

variable "plant_domain" {
  description = "Plant domain"
  type        = string
}

variable "backend_negs" {
  description = "Backend Network Endpoint Groups (map with enabled services only)"
  type = map(object({
    name   = string
    region = string
  }))
}
