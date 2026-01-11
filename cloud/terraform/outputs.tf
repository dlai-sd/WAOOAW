output "static_ip" {
  description = "Static IP address for Load Balancer"
  value       = data.google_compute_global_address.static_ip.address
}

output "customer_portal_url" {
  description = "Customer Portal URL (only if enabled)"
  value       = var.enable_customer_portal ? "https://${var.domains[var.environment].customer_portal}" : null
}

output "platform_portal_url" {
  description = "Platform Portal URL (only if enabled)"
  value       = var.enable_platform_portal ? "https://${var.domains[var.environment].platform_portal}" : null
}

output "backend_api_url" {
  description = "Backend API URL (only if enabled)"
  value       = var.enable_backend_api ? "https://${var.domains[var.environment].customer_portal}/api" : null
}

output "cloud_run_services" {
  description = "Cloud Run service URLs (only enabled services)"
  value = {
    backend_api     = var.enable_backend_api ? module.backend_api[0].service_url : null
    customer_portal = var.enable_customer_portal ? module.customer_portal[0].service_url : null
    platform_portal = var.enable_platform_portal ? module.platform_portal[0].service_url : null
  }
}

output "ssl_certificates" {
  description = "SSL certificate status (only enabled services)"
  value = {
    customer = var.enable_customer_portal ? module.load_balancer[0].ssl_cert_customer : null
    platform = var.enable_platform_portal ? module.load_balancer[0].ssl_cert_platform : null
  }
}

output "dns_records_needed" {
  description = "DNS A records to configure (only for enabled domains)"
  value = merge(
    var.enable_customer_portal ? {
      customer_portal = "${var.domains[var.environment].customer_portal} → ${data.google_compute_global_address.static_ip.address}"
    } : {},
    var.enable_platform_portal ? {
      platform_portal = "${var.domains[var.environment].platform_portal} → ${data.google_compute_global_address.static_ip.address}"
    } : {}
  )
}

output "oauth_urls" {
  description = "URLs to add to Google OAuth Console (only for enabled services)"
  value = {
    authorized_origins = concat(
      var.enable_customer_portal ? ["https://${var.domains[var.environment].customer_portal}"] : [],
      var.enable_platform_portal ? ["https://${var.domains[var.environment].platform_portal}"] : []
    )
    redirect_uris = concat(
      var.enable_customer_portal ? ["https://${var.domains[var.environment].customer_portal}/api/auth/callback"] : [],
      var.enable_platform_portal ? ["https://${var.domains[var.environment].platform_portal}/api/auth/callback"] : []
    )
  }
}
