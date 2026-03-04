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

# Payments — demo uses in-memory coupon stub (no Razorpay keys required).
# "WAOOAW100" coupon grants a free 7-day trial, zero payment.
# Razorpay secrets are NOT required in this mode; attach_razorpay_secrets=false
# keeps the Cloud Run service startable without Secret Manager Razorpay entries.
payments_mode            = "coupon"
attach_razorpay_secrets  = false
razorpay_key_id_secret   = "RAZORPAY_KEY_ID"      # unused in coupon mode
razorpay_key_secret_name = "RAZORPAY_KEY_SECRET"   # unused in coupon mode
