project_id    = "waooaw-oauth"
region        = "asia-south1"
environment   = "demo"
min_instances = 0
max_instances = 10

# plant_backend_image is ignored by lifecycle block in cloud-run module
# The actual deployed image will be preserved during reconciliation
plant_backend_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-backend:ignored-by-lifecycle"

# Database Configuration
private_network_id = "projects/waooaw-oauth/global/networks/default"
# database_password provided via -var or TF_VAR_database_password env var (not committed)

db_tier                = "db-f1-micro" # Cost-effective for demo
db_availability_type   = "ZONAL"
db_disk_size_gb        = 20
db_enable_pitr         = false
db_max_connections     = "50"
db_deletion_protection = false # Allow easy cleanup for demo

# OTP email delivery — runtime-injected SMTP config (NOT baked into image)
# smtp_host and smtp_port use module defaults (smtp.gmail.com:587)
smtp_from_email      = "customersupport@dlaisd.com"
smtp_username_secret = "CP_OTP_SMTP_USERNAME"  # Secret Manager secret name (no version suffix)
smtp_password_secret = "CP_OTP_SMTP_PASSWORD"  # Secret Manager secret name (no version suffix)
