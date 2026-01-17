# IAM Roles and Permissions
# Version: 1.0
# Owner: Platform Team

# Gateway CP Service Account IAM

# Cloud SQL Client (connect to database)
resource "google_project_iam_member" "gateway_cp_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.gateway_cp.email}"
}

# Secret Manager Accessor (read JWT secrets)
resource "google_secret_manager_secret_iam_member" "gateway_cp_jwt_secret" {
  secret_id = google_secret_manager_secret.jwt_secret_cp.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_cp.email}"
}

resource "google_secret_manager_secret_iam_member" "gateway_cp_database_secret" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_cp.email}"
}

resource "google_secret_manager_secret_iam_member" "gateway_cp_redis_secret" {
  secret_id = google_secret_manager_secret.redis_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_cp.email}"
}

# Redis Editor (connect to Redis instance)
resource "google_project_iam_member" "gateway_cp_redis" {
  project = var.project_id
  role    = "roles/redis.editor"
  member  = "serviceAccount:${google_service_account.gateway_cp.email}"
}

# Cloud Logging Writer (write logs)
resource "google_project_iam_member" "gateway_cp_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gateway_cp.email}"
}

# Cloud Monitoring Metric Writer (write metrics)
resource "google_project_iam_member" "gateway_cp_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gateway_cp.email}"
}

# Cloud Run Invoker (call OPA service)
resource "google_cloud_run_service_iam_member" "gateway_cp_opa_invoker" {
  service  = google_cloud_run_service.opa_service.name
  location = google_cloud_run_service.opa_service.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.gateway_cp.email}"
}

# Gateway PP Service Account IAM (same permissions as CP)

resource "google_project_iam_member" "gateway_pp_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.gateway_pp.email}"
}

resource "google_secret_manager_secret_iam_member" "gateway_pp_jwt_secret" {
  secret_id = google_secret_manager_secret.jwt_secret_pp.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_pp.email}"
}

resource "google_secret_manager_secret_iam_member" "gateway_pp_database_secret" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_pp.email}"
}

resource "google_secret_manager_secret_iam_member" "gateway_pp_redis_secret" {
  secret_id = google_secret_manager_secret.redis_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_pp.email}"
}

resource "google_project_iam_member" "gateway_pp_redis" {
  project = var.project_id
  role    = "roles/redis.editor"
  member  = "serviceAccount:${google_service_account.gateway_pp.email}"
}

resource "google_project_iam_member" "gateway_pp_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gateway_pp.email}"
}

resource "google_project_iam_member" "gateway_pp_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gateway_pp.email}"
}

resource "google_cloud_run_service_iam_member" "gateway_pp_opa_invoker" {
  service  = google_cloud_run_service.opa_service.name
  location = google_cloud_run_service.opa_service.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.gateway_pp.email}"
}

# OPA Service Account IAM

resource "google_project_iam_member" "opa_redis" {
  project = var.project_id
  role    = "roles/redis.editor"
  member  = "serviceAccount:${google_service_account.opa_service.email}"
}

resource "google_secret_manager_secret_iam_member" "opa_redis_secret" {
  secret_id = google_secret_manager_secret.redis_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.opa_service.email}"
}

resource "google_secret_manager_secret_iam_member" "opa_bundle_key_secret" {
  secret_id = google_secret_manager_secret.opa_bundle_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.opa_service.email}"
}

resource "google_project_iam_member" "opa_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.opa_service.email}"
}

resource "google_project_iam_member" "opa_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.opa_service.email}"
}

# Allow public access to Gateway services (controlled by gateway auth)
resource "google_cloud_run_service_iam_member" "gateway_cp_public" {
  service  = google_cloud_run_service.gateway_cp.name
  location = google_cloud_run_service.gateway_cp.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "gateway_pp_public" {
  service  = google_cloud_run_service.gateway_pp.name
  location = google_cloud_run_service.gateway_pp.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Note: OPA service is NOT publicly accessible, only called by gateway services
