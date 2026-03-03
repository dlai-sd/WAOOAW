project_id    = "waooaw-oauth"
region        = "asia-south1"
environment   = "demo"
min_instances = 0
max_instances = 10

# plant_backend_image is ignored by lifecycle block in cloud-run module
# The actual deployed image will be preserved during reconciliation
plant_backend_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-backend:ignored-by-lifecycle"

# plant_opa_image is ignored by lifecycle block in cloud-run module
# The actual deployed image will be set by waooaw-deploy.yml: -var="plant_opa_image=<TAG>"
plant_opa_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-opa:ignored-by-lifecycle"

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
smtp_username_secret = "CP_OTP_SMTP_USERNAME" # Secret Manager secret name (no version suffix)
smtp_password_secret = "CP_OTP_SMTP_PASSWORD" # Secret Manager secret name (no version suffix)

# Payments — demo uses Razorpay test mode (rzp_test_* keys, no real money moves).
# Secrets RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must exist in GCP Secret Manager first.
payments_mode            = "razorpay"
attach_razorpay_secrets  = true
razorpay_key_id_secret   = "RAZORPAY_KEY_ID"
razorpay_key_secret_name = "RAZORPAY_KEY_SECRET"
