# Network Endpoint Groups for each Cloud Run service
resource "google_compute_region_network_endpoint_group" "api" {
  name                  = "waooaw-${var.environment}-api-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id
  
  cloud_run {
    service = var.services.api.name
  }
}

resource "google_compute_region_network_endpoint_group" "customer" {
  name                  = "waooaw-${var.environment}-customer-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id
  
  cloud_run {
    service = var.services.customer.name
  }
}

resource "google_compute_region_network_endpoint_group" "platform" {
  name                  = "waooaw-${var.environment}-platform-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id
  
  cloud_run {
    service = var.services.platform.name
  }
}
