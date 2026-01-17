resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  labels = {
    environment  = var.environment
    service-type = var.service_type
    managed-by   = "terraform"
  }

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # Cloud SQL Proxy annotation
    annotations = var.cloud_sql_connection_name != null ? {
      "run.googleapis.com/cloudsql-instances" = var.cloud_sql_connection_name
    } : {}

    # VPC Connector for private network access
    dynamic "vpc_access" {
      for_each = var.vpc_connector_id != null ? [1] : []
      content {
        connector = var.vpc_connector_id
        egress    = "PRIVATE_RANGES_ONLY" # Only route private IPs through VPC
      }
    }

    containers {
      image = var.image

      ports {
        name           = "http1"
        container_port = var.port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }

        cpu_idle          = true
        startup_cpu_boost = true
      }

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = split(":", env.value)[0]
              version = split(":", env.value)[1]
            }
          }
        }
      }

      # Startup probe for services with database initialization
      dynamic "startup_probe" {
        for_each = var.cloud_sql_connection_name != null ? [1] : []
        content {
          initial_delay_seconds = 0
          timeout_seconds       = 240
          period_seconds        = 240
          failure_threshold     = 1
          tcp_socket {
            port = var.port
          }
        }
      }
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }
}

# Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
