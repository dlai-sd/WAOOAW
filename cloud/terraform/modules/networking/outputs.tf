output "neg_names" {
  description = "Network Endpoint Group names"
  value = {
    api      = google_compute_region_network_endpoint_group.api.name
    customer = google_compute_region_network_endpoint_group.customer.name
    platform = google_compute_region_network_endpoint_group.platform.name
  }
}

output "neg_ids" {
  description = "Network Endpoint Group IDs"
  value = {
    api      = google_compute_region_network_endpoint_group.api.id
    customer = google_compute_region_network_endpoint_group.customer.id
    platform = google_compute_region_network_endpoint_group.platform.id
  }
}
