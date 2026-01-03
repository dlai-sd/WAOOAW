output "static_ip" {
  description = "Static IP address for Load Balancer"
  value       = data.google_compute_global_address.static_ip.address
}

output "customer_portal_url" {
  description = "Customer Portal URL"
  value       = "https://${var.domains[var.environment].customer_portal}"
}

output "platform_portal_url" {
  description = "Platform Portal URL"
  value       = "https://${var.domains[var.environment].platform_portal}"
}

output "backend_api_url" {
  description = "Backend API URL"
  value       = "https://${var.domains[var.environment].customer_portal}/api"
}

output "cloud_run_services" {
  description = "Cloud Run service URLs"
  value = {
    backend_api      = module.backend_api.service_url
    customer_portal  = module.customer_portal.service_url
    platform_portal  = module.platform_portal.service_url
  }
}

output "ssl_certificates" {
  description = "SSL certificate status"
  value = {
    customer = module.load_balancer.ssl_cert_customer
    platform = module.load_balancer.ssl_cert_platform
  }
}

output "dns_records_needed" {
  description = "DNS A records to configure"
  value = {
    customer_portal = "${var.domains[var.environment].customer_portal} → ${data.google_compute_global_address.static_ip.address}"
    platform_portal = "${var.domains[var.environment].platform_portal} → ${data.google_compute_global_address.static_ip.address}"
  }
}

output "oauth_urls" {
  description = "URLs to add to Google OAuth Console"
  value = {
    authorized_origins = [
      "https://${var.domains[var.environment].customer_portal}",
      "https://${var.domains[var.environment].platform_portal}"
    ]
    redirect_uris = [
      "https://${var.domains[var.environment].customer_portal}/api/auth/callback",
      "https://${var.domains[var.environment].platform_portal}/api/auth/callback"
    ]
  }
}
