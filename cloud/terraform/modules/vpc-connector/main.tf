/**
 * VPC Serverless Connector Module
 * Enables Cloud Run to access resources on private VPC (like Cloud SQL)
 */

resource "google_vpc_access_connector" "connector" {
  name          = var.connector_name
  region        = var.region
  project       = var.project_id
  network       = var.network_id
  ip_cidr_range = var.ip_cidr_range

  # Scale configuration
  min_instances = var.min_instances
  max_instances = var.max_instances
  machine_type  = var.machine_type
}
