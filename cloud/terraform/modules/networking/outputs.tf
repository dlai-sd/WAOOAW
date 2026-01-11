output "neg_names" {
  description = "Network Endpoint Group names"
  value       = { for k, v in google_compute_region_network_endpoint_group.neg : k => v.name }
}

output "neg_ids" {
  description = "Network Endpoint Group IDs"
  value       = { for k, v in google_compute_region_network_endpoint_group.neg : k => v.id }
}
