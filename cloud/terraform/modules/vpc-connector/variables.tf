variable "connector_name" {
  description = "Name of the VPC connector"
  type        = string
}

variable "region" {
  description = "Region for the VPC connector"
  type        = string
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "network_id" {
  description = "VPC network ID (full resource ID)"
  type        = string
}

variable "ip_cidr_range" {
  description = "CIDR range for connector (e.g., 10.8.0.0/28). Must not overlap with existing ranges."
  type        = string
}

variable "min_instances" {
  description = "Minimum number of connector instances"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of connector instances"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Machine type for connector instances"
  type        = string
  default     = "e2-micro"
}
