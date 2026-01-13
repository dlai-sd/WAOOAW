output "static_ip" {
  description = "Static IP address for the shared load balancer"
  value       = data.google_compute_global_address.static_ip.address
}

output "dns_records_needed" {
  description = "DNS A records to configure (host -> static IP)"
  value = {
    for host in local.all_domains : host => data.google_compute_global_address.static_ip.address
  }
}

output "oauth_urls" {
  description = "URLs to add to Google OAuth Console (CP/PP origins + callbacks)"
  value = {
    authorized_origins = concat(
      var.enable_cp ? ["https://${var.domains.demo.cp}", "https://${var.domains.uat.cp}", "https://${var.domains.prod.cp}"] : [],
      var.enable_pp ? ["https://${var.domains.demo.pp}", "https://${var.domains.uat.pp}", "https://${var.domains.prod.pp}"] : []
    )
    redirect_uris = concat(
      var.enable_cp ? [
        "https://${var.domains.demo.cp}/api/auth/callback",
        "https://${var.domains.uat.cp}/api/auth/callback",
        "https://${var.domains.prod.cp}/api/auth/callback"
      ] : [],
      var.enable_pp ? [
        "https://${var.domains.demo.pp}/api/auth/callback",
        "https://${var.domains.uat.pp}/api/auth/callback",
        "https://${var.domains.prod.pp}/api/auth/callback"
      ] : []
    )
  }
}
