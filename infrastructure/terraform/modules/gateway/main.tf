# API Gateway Infrastructure Module
# Version: 1.0
# Owner: Platform Team
# Last Updated: 2026-01-17

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (production, demo, staging)"
  type        = string
}

variable "cloud_sql_instance_name" {
  description = "Existing Cloud SQL instance name"
  type        = string
}

variable "redis_instance_name" {
  description = "Existing Redis instance name"
  type        = string
}

# Locals
locals {
  gateway_cp_name = "api-gateway-cp-${var.environment}"
  gateway_pp_name = "api-gateway-pp-${var.environment}"
  opa_service_name = "opa-service-${var.environment}"
  
  common_labels = {
    environment = var.environment
    component   = "api-gateway"
    managed_by  = "terraform"
  }
}

# Service Account for API Gateway CP
resource "google_service_account" "gateway_cp" {
  account_id   = "gateway-cp-${var.environment}"
  display_name = "API Gateway CP ${var.environment}"
  description  = "Service account for Customer Platform API Gateway"
}

# Service Account for API Gateway PP
resource "google_service_account" "gateway_pp" {
  account_id   = "gateway-pp-${var.environment}"
  display_name = "API Gateway PP ${var.environment}"
  description  = "Service account for Partner Platform API Gateway"
}

# Service Account for OPA Service
resource "google_service_account" "opa_service" {
  account_id   = "opa-service-${var.environment}"
  display_name = "OPA Policy Service ${var.environment}"
  description  = "Service account for OPA policy engine"
}

# Cloud Run Service - API Gateway CP
resource "google_cloud_run_service" "gateway_cp" {
  name     = local.gateway_cp_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.gateway_cp.email
      
      containers {
        image = "gcr.io/${var.project_id}/api-gateway-cp:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "OPA_SERVICE_URL"
          value = google_cloud_run_service.opa_service.status[0].url
        }

        env {
          name  = "PLANT_API_URL"
          value = "https://plant.${var.environment == "production" ? "" : "${var.environment}."}waooaw.com"
        }

        env {
          name = "JWT_SECRET_CP"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret_cp.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.database_url.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "REDIS_HOST"
          value = data.google_redis_instance.gateway_redis.host
        }

        env {
          name  = "REDIS_PORT"
          value = tostring(data.google_redis_instance.gateway_redis.port)
        }

        env {
          name = "REDIS_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.redis_password.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "AGENT_BUDGET_CAP_USD"
          value = "1.00"
        }

        env {
          name  = "PLATFORM_BUDGET_CAP_USD"
          value = "100.00"
        }

        env {
          name  = "TRIAL_TASK_LIMIT_PER_DAY"
          value = "10"
        }

        env {
          name  = "RATE_LIMIT_TRIAL"
          value = "100"
        }

        env {
          name  = "RATE_LIMIT_PAID"
          value = "1000"
        }

        env {
          name  = "RATE_LIMIT_ENTERPRISE"
          value = "10000"
        }

        env {
          name  = "FEATURE_FLAG_OPA_POLICY"
          value = "true"
        }

        env {
          name  = "FEATURE_FLAG_BUDGET_GUARD"
          value = "true"
        }

        env {
          name  = "FEATURE_FLAG_RATE_LIMITING"
          value = "true"
        }

        env {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "WARNING" : "INFO"
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
      }
    }

    metadata {
      labels = local.common_labels
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cloudsql-instances" = var.cloud_sql_instance_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
    ]
  }
}

# Cloud Run Service - API Gateway PP
resource "google_cloud_run_service" "gateway_pp" {
  name     = local.gateway_pp_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.gateway_pp.email
      
      containers {
        image = "gcr.io/${var.project_id}/api-gateway-pp:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "OPA_SERVICE_URL"
          value = google_cloud_run_service.opa_service.status[0].url
        }

        env {
          name  = "PLANT_API_URL"
          value = "https://plant.${var.environment == "production" ? "" : "${var.environment}."}waooaw.com"
        }

        env {
          name = "JWT_SECRET_PP"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret_pp.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.database_url.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "REDIS_HOST"
          value = data.google_redis_instance.gateway_redis.host
        }

        env {
          name  = "REDIS_PORT"
          value = tostring(data.google_redis_instance.gateway_redis.port)
        }

        env {
          name = "REDIS_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.redis_password.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "RBAC_ENABLED"
          value = "true"
        }

        env {
          name  = "GOVERNOR_APPROVAL_ENABLED"
          value = "true"
        }

        env {
          name  = "AGENT_BUDGET_CAP_USD"
          value = "1.00"
        }

        env {
          name  = "PLATFORM_BUDGET_CAP_USD"
          value = "100.00"
        }

        env {
          name  = "RATE_LIMIT_TRIAL"
          value = "1000"
        }

        env {
          name  = "RATE_LIMIT_PAID"
          value = "1000"
        }

        env {
          name  = "RATE_LIMIT_ENTERPRISE"
          value = "10000"
        }

        env {
          name  = "FEATURE_FLAG_OPA_POLICY"
          value = "true"
        }

        env {
          name  = "FEATURE_FLAG_BUDGET_GUARD"
          value = "true"
        }

        env {
          name  = "FEATURE_FLAG_RATE_LIMITING"
          value = "true"
        }

        env {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "WARNING" : "INFO"
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
      }
    }

    metadata {
      labels = local.common_labels
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cloudsql-instances" = var.cloud_sql_instance_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
    ]
  }
}

# Cloud Run Service - OPA Policy Engine
resource "google_cloud_run_service" "opa_service" {
  name     = local.opa_service_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.opa_service.email
      
      containers {
        image = "gcr.io/${var.project_id}/opa-service:latest"
        
        resources {
          limits = {
            cpu    = "100m"
            memory = "128Mi"
          }
        }

        ports {
          container_port = 8181
        }

        env {
          name  = "OPA_ADDR"
          value = ":8181"
        }

        env {
          name  = "OPA_LOG_LEVEL"
          value = var.environment == "production" ? "info" : "debug"
        }

        env {
          name  = "OPA_LOG_FORMAT"
          value = "json"
        }

        env {
          name  = "REDIS_HOST"
          value = data.google_redis_instance.gateway_redis.host
        }

        env {
          name  = "REDIS_PORT"
          value = tostring(data.google_redis_instance.gateway_redis.port)
        }

        env {
          name = "REDIS_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.redis_password.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "OPA_BUNDLE_SERVICE_URL"
          value = "https://storage.googleapis.com/${google_storage_bucket.opa_bundles.name}"
        }

        env {
          name  = "OPA_BUNDLE_NAME"
          value = "gateway-policies"
        }
      }
    }

    metadata {
      labels = local.common_labels
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "3"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
    ]
  }
}

# Data source for existing Cloud SQL instance
data "google_sql_database_instance" "gateway_db" {
  name = var.cloud_sql_instance_name
}

# Data source for existing Redis instance
data "google_redis_instance" "gateway_redis" {
  name = var.redis_instance_name
}

# Storage bucket for OPA policy bundles
resource "google_storage_bucket" "opa_bundles" {
  name     = "${var.project_id}-opa-bundles-${var.environment}"
  location = var.region
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  labels = local.common_labels
}

# IAM binding for OPA service to read bundles
resource "google_storage_bucket_iam_member" "opa_bundle_reader" {
  bucket = google_storage_bucket.opa_bundles.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.opa_service.email}"
}

# Outputs
output "gateway_cp_url" {
  description = "URL of API Gateway CP service"
  value       = google_cloud_run_service.gateway_cp.status[0].url
}

output "gateway_pp_url" {
  description = "URL of API Gateway PP service"
  value       = google_cloud_run_service.gateway_pp.status[0].url
}

output "opa_service_url" {
  description = "URL of OPA policy service"
  value       = google_cloud_run_service.opa_service.status[0].url
}

output "gateway_cp_service_account" {
  description = "Service account email for Gateway CP"
  value       = google_service_account.gateway_cp.email
}

output "gateway_pp_service_account" {
  description = "Service account email for Gateway PP"
  value       = google_service_account.gateway_pp.email
}

output "opa_service_account" {
  description = "Service account email for OPA service"
  value       = google_service_account.opa_service.email
}

output "opa_bundles_bucket" {
  description = "Storage bucket for OPA policy bundles"
  value       = google_storage_bucket.opa_bundles.name
}
