project_id    = "waooaw-oauth"
region        = "asia-south1"
environment   = "uat"
min_instances = 1
max_instances = 20

# plant_opa_image is ignored by lifecycle block in cloud-run module
# The actual deployed image will be set by waooaw-deploy.yml: -var="plant_opa_image=<TAG>"
plant_opa_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-opa:ignored-by-lifecycle"

# OTP email delivery — runtime-injected SMTP config (NOT baked into image)
# REQUIRED before promoting to UAT:
#   1. Create Secret Manager secrets (or reuse demo secrets for UAT):
#      gcloud secrets create UAT_OTP_SMTP_USERNAME --replication-policy=automatic
#      gcloud secrets create UAT_OTP_SMTP_PASSWORD --replication-policy=automatic
#   2. Add the Gmail/SMTP credentials as the latest version of each secret
#   3. Update smtp_from_email below (may use a different sender for UAT)
# smtp_host and smtp_port use module defaults (smtp.gmail.com:587)
smtp_from_email      = "CHANGE_ME@dlaisd.com"  # REQUIRED: set UAT sender address
smtp_username_secret = "UAT_OTP_SMTP_USERNAME" # REQUIRED: create this secret in GCP first
smtp_password_secret = "UAT_OTP_SMTP_PASSWORD" # REQUIRED: create this secret in GCP first

# Payments — UAT uses Razorpay test mode (same test keys as demo, no real money moves).
# Secrets RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must exist in GCP Secret Manager first.
payments_mode            = "razorpay"
attach_razorpay_secrets  = true
razorpay_key_id_secret   = "RAZORPAY_KEY_ID"
razorpay_key_secret_name = "RAZORPAY_KEY_SECRET"
