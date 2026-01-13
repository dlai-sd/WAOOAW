locals {
  backend_negs = {
    for k, v in module.networking.neg_names : k => {
      name   = v
      region = var.region
    }
  }
}

output "backend_negs" {
  description = "Serverless NEG info for PP services (consumed by shared foundation load balancer stack)"
  value       = local.backend_negs
}

output "enabled_components" {
  description = "Which components are enabled in this stack"
  value = {
    cp    = false
    pp    = true
    plant = false
  }
}

output "cloud_run_services" {
  description = "Direct Cloud Run service URLs"
  value = {
    pp_frontend = module.pp_frontend.service_url
    pp_backend  = module.pp_backend.service_url
  }
}

output "service_accounts" {
  description = "Service account emails for each service"
  value = {
    pp_frontend = module.pp_frontend.service_account
    pp_backend  = module.pp_backend.service_account
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
