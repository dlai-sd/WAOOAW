output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "instance_connection_name" {
  description = "Instance connection name for Cloud SQL Proxy"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "database_user" {
  description = "Database user"
  value       = google_sql_user.user.name
}

output "private_ip_address" {
  description = "Private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "database_url_secret_id" {
  description = "Secret Manager secret ID containing DATABASE_URL"
  value       = google_secret_manager_secret.database_url.secret_id
}

output "connection_string" {
  description = "Database connection string (for local proxy)"
  value       = "postgresql+asyncpg://${var.database_user}:${var.database_password}@127.0.0.1:5432/${var.database_name}"
  sensitive   = true
}
