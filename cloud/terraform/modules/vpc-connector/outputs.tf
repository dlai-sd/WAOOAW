output "connector_id" {
  description = "Full resource ID of the VPC connector"
  value       = google_vpc_access_connector.connector.id
}

output "connector_name" {
  description = "Name of the VPC connector"
  value       = google_vpc_access_connector.connector.name
}

output "self_link" {
  description = "Self link of the VPC connector"
  value       = google_vpc_access_connector.connector.self_link
}
