output "url_map_id" {
  description = "URL Map ID"
  value       = google_compute_url_map.main.id
}

output "ssl_cert_cp" {
  description = "CP SSL certificate name (or empty if disabled)"
  value       = length(google_compute_managed_ssl_certificate.cp) > 0 ? google_compute_managed_ssl_certificate.cp[0].name : ""
}

output "ssl_cert_pp" {
  description = "PP SSL certificate name (or empty if disabled)"
  value       = length(google_compute_managed_ssl_certificate.pp) > 0 ? google_compute_managed_ssl_certificate.pp[0].name : ""
}

output "ssl_cert_plant" {
  description = "Plant SSL certificate name (or empty if disabled)"
  value       = length(google_compute_managed_ssl_certificate.plant) > 0 ? google_compute_managed_ssl_certificate.plant[0].name : ""
}

output "https_proxy_id" {
  description = "HTTPS Proxy ID (or empty if no SSL certs)"
  value       = length(google_compute_target_https_proxy.main) > 0 ? google_compute_target_https_proxy.main[0].id : ""
}

output "forwarding_rule_ip" {
  description = "Forwarding rule IP address"
  value       = var.static_ip_address
}
