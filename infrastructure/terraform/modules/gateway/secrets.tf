# Secret Manager Resources
# Version: 1.0
# Owner: Platform Team

# JWT Secret for CP
resource "google_secret_manager_secret" "jwt_secret_cp" {
  secret_id = "jwt-secret-cp-${var.environment}"
  
  replication {
    automatic = true
  }
  
  labels = local.common_labels
}

# JWT Secret for PP
resource "google_secret_manager_secret" "jwt_secret_pp" {
  secret_id = "jwt-secret-pp-${var.environment}"
  
  replication {
    automatic = true
  }
  
  labels = local.common_labels
}

# Database URL (connection string)
resource "google_secret_manager_secret" "database_url" {
  secret_id = "gateway-database-url-${var.environment}"
  
  replication {
    automatic = true
  }
  
  labels = local.common_labels
}

# Redis Password
resource "google_secret_manager_secret" "redis_password" {
  secret_id = "gateway-redis-password-${var.environment}"
  
  replication {
    automatic = true
  }
  
  labels = local.common_labels
}

# OPA Bundle Encryption Key
resource "google_secret_manager_secret" "opa_bundle_key" {
  secret_id = "opa-bundle-key-${var.environment}"
  
  replication {
    automatic = true
  }
  
  labels = local.common_labels
}

# Note: Secret values must be added manually or via separate process
# Example using gcloud:
# gcloud secrets versions add jwt-secret-cp-production --data-file=secret.txt

# Outputs
output "secret_jwt_cp_id" {
  description = "Secret Manager ID for JWT CP secret"
  value       = google_secret_manager_secret.jwt_secret_cp.id
}

output "secret_jwt_pp_id" {
  description = "Secret Manager ID for JWT PP secret"
  value       = google_secret_manager_secret.jwt_secret_pp.id
}

output "secret_database_url_id" {
  description = "Secret Manager ID for database URL"
  value       = google_secret_manager_secret.database_url.id
}

output "secret_redis_password_id" {
  description = "Secret Manager ID for Redis password"
  value       = google_secret_manager_secret.redis_password.id
}

output "secret_opa_bundle_key_id" {
  description = "Secret Manager ID for OPA bundle key"
  value       = google_secret_manager_secret.opa_bundle_key.id
}
