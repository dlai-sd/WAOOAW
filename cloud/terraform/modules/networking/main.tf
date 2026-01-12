# Network Endpoint Groups for each enabled Cloud Run service
resource "google_compute_region_network_endpoint_group" "neg" {
  for_each = var.services

  name                  = "waooaw-${var.environment}-${replace(each.key, "_", "-")}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = each.value.name
  }
}
