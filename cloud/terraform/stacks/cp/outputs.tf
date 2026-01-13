locals {
  backend_negs = {
    for k, v in module.networking.neg_names : k => {
      name   = v
      region = var.region
    }
  }
}

output "backend_negs" {
  description = "Serverless NEG info for CP services (consumed by shared foundation load balancer stack)"
  value       = local.backend_negs
}

output "enabled_components" {
  description = "Which components are enabled in this stack"
  value = {
    cp    = true
    pp    = false
    plant = false
  }
}

output "cloud_run_services" {
  description = "Direct Cloud Run service URLs"
  value = {
    cp_frontend = module.cp_frontend.service_url
    cp_backend  = module.cp_backend.service_url
  }
}

output "service_accounts" {
  description = "Service account emails for each service"
  value = {
    cp_frontend = module.cp_frontend.service_account
    cp_backend  = module.cp_backend.service_account
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
