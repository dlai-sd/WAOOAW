/**
 * Cloud Run Job Module
 * Creates a Cloud Run Job for one-time or scheduled tasks (e.g., database migrations)
 * Runs inside VPC with access to private Cloud SQL
 */

resource "google_cloud_run_v2_job" "job" {
  name     = var.job_name
  location = var.region
  project  = var.project_id

  template {
    template {
      containers {
        image = var.image

        # Environment variables
        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        # Secrets from Secret Manager
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

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }
      }

      # VPC connector for private Cloud SQL access
      vpc_access {
        connector = var.vpc_connector_id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      # Cloud SQL connection
      dynamic "volumes" {
        for_each = var.cloud_sql_connection_name != "" ? [1] : []
        content {
          name = "cloudsql"
          cloud_sql_instance {
            instances = [var.cloud_sql_connection_name]
          }
        }
      }

      service_account = var.service_account_email
      timeout         = "${var.timeout_seconds}s"
      max_retries     = var.max_retries
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }
}

# IAM binding for invoking the job
resource "google_cloud_run_v2_job_iam_member" "invoker" {
  name   = google_cloud_run_v2_job.job.name
  location = var.region
  project  = var.project_id
  role   = "roles/run.invoker"
  member = "serviceAccount:${var.service_account_email}"
}
