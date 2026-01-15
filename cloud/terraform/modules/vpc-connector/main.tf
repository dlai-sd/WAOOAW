/**
 * VPC Serverless Connector Module
 * Enables Cloud Run to access resources on private VPC (like Cloud SQL)
 */

locals {
  # Extract network name from full resource ID if provided
  # Input: "projects/PROJECT/global/networks/NETWORK" or "NETWORK"
  # Output: "NETWORK"
  network_name = can(regex("/networks/(.+)$", var.network_id)) ? regex("/networks/(.+)$", var.network_id)[0] : var.network_id
}

resource "google_vpc_access_connector" "connector" {
  name          = var.connector_name
  region        = var.region
  project       = var.project_id
  network       = local.network_name
  ip_cidr_range = var.ip_cidr_range

  # Scale configuration
  min_instances = var.min_instances
  max_instances = var.max_instances
  machine_type  = var.machine_type
}
