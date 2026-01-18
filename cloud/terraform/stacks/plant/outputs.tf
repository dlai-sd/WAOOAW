locals {
  backend_negs = {
    for k, v in module.networking.neg_names : k => {
      name   = v
      region = var.region
    }
  }
}

output "backend_negs" {
  description = "Serverless NEG info for Plant services (consumed by shared foundation load balancer stack)"
  value       = local.backend_negs
}

output "enabled_components" {
  description = "Which components are enabled in this stack"
  value = {
    cp    = false
    pp    = false
    plant = true
  }
}

output "cloud_run_services" {
  description = "Direct Cloud Run service URLs"
  value = {
    plant_backend = module.plant_backend.service_url
  }
}

output "service_accounts" {
  description = "Service account emails for each service"
  value = {
    plant_backend = module.plant_backend.service_account
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

# Database Outputs
output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = module.plant_database.instance_name
}

output "database_connection_name" {
  description = "Instance connection name for Cloud SQL Proxy (use in migrations)"
  value       = module.plant_database.instance_connection_name
}

output "database_name" {
  description = "Database name"
  value       = module.plant_database.database_name
}

output "database_user" {
  description = "Database user"
  value       = module.plant_database.database_user
}

output "database_url_secret_id" {
  description = "Secret Manager secret ID containing DATABASE_URL"
  value       = module.plant_database.database_url_secret_id
}

output "local_proxy_command" {
  description = "Command to run Cloud SQL Proxy locally"
  value       = "cloud-sql-proxy ${module.plant_database.instance_connection_name}=tcp:5432"
}
