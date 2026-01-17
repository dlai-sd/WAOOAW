# Cloud Run Service Configuration for PP Gateway

resource "google_cloud_run_service" "pp_gateway" {
  name     = "pp-gateway"
  location = var.region
  project  = var.project_id

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"      = "1"
        "autoscaling.knative.dev/maxScale"      = "10"
        "run.googleapis.com/cpu-throttling"     = "false"
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }

    spec {
      container_concurrency = 80
      timeout_seconds       = 300
      service_account_name  = google_service_account.pp_gateway.email

      containers {
        image = "${var.artifact_registry}/${var.project_id}/waooaw/pp-gateway:${var.image_tag}"

        resources {
          limits = {
            cpu    = "2000m"
            memory = "1Gi"
          }
        }

        ports {
          container_port = 8001
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "PORT"
          value = "8001"
        }

        env {
          name  = "GATEWAY_TYPE"
          value = "PP"
        }

        env {
          name  = "PLANT_SERVICE_URL"
          value = var.plant_service_url
        }

        env {
          name  = "OPA_SERVICE_URL"
          value = var.opa_service_url
        }

        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
        }

        env {
          name  = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.database_url.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "APPROVAL_UI_URL"
          value = var.approval_ui_url
        }

        env {
          name  = "JWT_PUBLIC_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_public_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name  = "JWT_ISSUER"
          value = "waooaw.com"
        }

        env {
          name  = "LAUNCHDARKLY_SDK_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.launchdarkly_sdk_key.secret_id
              key  = "latest"
            }
          }
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 8001
          }
          initial_delay_seconds = 10
          timeout_seconds       = 5
          period_seconds        = 10
          failure_threshold     = 3
        }

        liveness_probe {
          http_get {
            path = "/health"
            port = 8001
          }
          initial_delay_seconds = 15
          timeout_seconds       = 5
          period_seconds        = 10
          failure_threshold     = 3
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.run_api,
    google_service_account.pp_gateway
  ]
}

# IAM Policy for PP Gateway (Authenticated users only)
resource "google_cloud_run_service_iam_member" "pp_gateway_authenticated" {
  service  = google_cloud_run_service.pp_gateway.name
  location = google_cloud_run_service.pp_gateway.location
  role     = "roles/run.invoker"
  member   = "allUsers"  # In production, restrict to authenticated users
}

# Service Account for PP Gateway
resource "google_service_account" "pp_gateway" {
  account_id   = "pp-gateway"
  display_name = "PP Gateway Service Account"
  project      = var.project_id
}

# Grant permissions to PP Gateway service account
resource "google_project_iam_member" "pp_gateway_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.pp_gateway.email}"
}

resource "google_project_iam_member" "pp_gateway_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.pp_gateway.email}"
}

resource "google_project_iam_member" "pp_gateway_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.pp_gateway.email}"
}

# Output
output "pp_gateway_url" {
  value       = google_cloud_run_service.pp_gateway.status[0].url
  description = "URL of the PP Gateway Cloud Run service"
}
