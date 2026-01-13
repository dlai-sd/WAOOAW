output "static_ip" {
  description = "Static IP address for Load Balancer"
  value       = data.google_compute_global_address.static_ip.address
}

# ==========================================================================
# Shared LB Foundation Inputs
# ==========================================================================

output "backend_negs" {
  description = "Serverless NEG info for enabled services (consumed by shared foundation load balancer stack)"
  value       = local.backend_negs
}

output "enabled_components" {
  description = "Which components are enabled in this environment"
  value = {
    cp    = var.enable_cp
    pp    = var.enable_pp
    plant = var.enable_plant
  }
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "region" {
  description = "Deployment region"
  value       = var.region
}

output "project_id" {
  description = "GCP project id"
  value       = var.project_id
}

# ============================================================================
# Component URLs
# ============================================================================

output "cp_url" {
  description = "Customer Portal URL (if enabled)"
  value       = var.enable_cp ? "https://${var.domains[var.environment].cp}" : null
}

output "pp_url" {
  description = "Platform Portal URL (if enabled)"
  value       = var.enable_pp ? "https://${var.domains[var.environment].pp}" : null
}

output "plant_url" {
  description = "Plant API URL (if enabled)"
  value       = var.enable_plant ? "https://${var.domains[var.environment].plant}" : null
}

# ============================================================================
# Cloud Run Service URLs (Direct Access)
# ============================================================================

output "cloud_run_services" {
  description = "Direct Cloud Run service URLs (only enabled services)"
  value = merge(
    var.enable_cp ? {
      cp_frontend = module.cp_frontend[0].service_url
      cp_backend  = module.cp_backend[0].service_url
    } : {},
    var.enable_pp ? {
      pp_frontend = module.pp_frontend[0].service_url
      pp_backend  = module.pp_backend[0].service_url
    } : {},
    var.enable_plant ? {
      plant_backend = module.plant_backend[0].service_url
    } : {}
  )
}

# ============================================================================
# Service Accounts
# ============================================================================

output "service_accounts" {
  description = "Service account emails for each service"
  value = merge(
    var.enable_cp ? {
      cp_frontend = module.cp_frontend[0].service_account
      cp_backend  = module.cp_backend[0].service_account
    } : {},
    var.enable_pp ? {
      pp_frontend = module.pp_frontend[0].service_account
      pp_backend  = module.pp_backend[0].service_account
    } : {},
    var.enable_plant ? {
      plant_backend = module.plant_backend[0].service_account
    } : {}
  )
}

# ============================================================================
# DNS Configuration
# ============================================================================

output "dns_records_needed" {
  description = "DNS A records to configure (only for enabled domains)"
  value = merge(
    var.enable_cp ? {
      cp = "${var.domains[var.environment].cp} → ${data.google_compute_global_address.static_ip.address}"
    } : {},
    var.enable_pp ? {
      pp = "${var.domains[var.environment].pp} → ${data.google_compute_global_address.static_ip.address}"
    } : {},
    var.enable_plant ? {
      plant = "${var.domains[var.environment].plant} → ${data.google_compute_global_address.static_ip.address}"
    } : {}
  )
}

# ============================================================================
# OAuth Configuration
# ============================================================================

output "oauth_urls" {
  description = "URLs to add to Google OAuth Console (only for enabled services)"
  value = {
    authorized_origins = concat(
      var.enable_cp ? ["https://${var.domains[var.environment].cp}"] : [],
      var.enable_pp ? ["https://${var.domains[var.environment].pp}"] : []
    )
    redirect_uris = concat(
      var.enable_cp ? ["https://${var.domains[var.environment].cp}/api/auth/callback"] : [],
      var.enable_pp ? ["https://${var.domains[var.environment].pp}/api/auth/callback"] : []
    )
  }
}

# ============================================================================
# Service Summary
# ============================================================================

output "deployed_services_count" {
  description = "Number of services deployed"
  value = (
    (var.enable_cp ? 3 : 0) +
    (var.enable_pp ? 3 : 0) +
    (var.enable_plant ? 2 : 0)
  )
}

output "deployment_summary" {
  description = "Summary of deployed components"
  value = {
    environment = var.environment
    components = {
      cp    = var.enable_cp ? "enabled (3 services)" : "disabled"
      pp    = var.enable_pp ? "enabled (3 services)" : "disabled"
      plant = var.enable_plant ? "enabled (2 services)" : "disabled"
    }
    total_services = (
      (var.enable_cp ? 3 : 0) +
      (var.enable_pp ? 3 : 0) +
      (var.enable_plant ? 2 : 0)
    )
  }
}
