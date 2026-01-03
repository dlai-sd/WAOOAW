output "url_map_id" {
  description = "URL Map ID"
  value       = google_compute_url_map.main.id
}

output "ssl_cert_customer" {
  description = "Customer SSL certificate name"
  value       = google_compute_managed_ssl_certificate.customer.name
}

output "ssl_cert_platform" {
  description = "Platform SSL certificate name"
  value       = google_compute_managed_ssl_certificate.platform.name
}

output "https_proxy_id" {
  description = "HTTPS Proxy ID"
  value       = google_compute_target_https_proxy.main.id
}

output "forwarding_rule_ip" {
  description = "Forwarding rule IP address"
  value       = var.static_ip_address
}
