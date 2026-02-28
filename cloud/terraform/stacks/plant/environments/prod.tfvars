project_id    = "waooaw-oauth"
region        = "asia-south1"
environment   = "prod"
min_instances = 2
max_instances = 200

# OTP email delivery — runtime-injected SMTP config (NOT baked into image)
# REQUIRED before promoting to prod:
#   1. Create Secret Manager secrets for production credentials:
#      gcloud secrets create PROD_OTP_SMTP_USERNAME --replication-policy=automatic
#      gcloud secrets create PROD_OTP_SMTP_PASSWORD --replication-policy=automatic
#   2. Use a production-grade sender (e.g. no-reply@waooaw.com via Workspace)
#   3. Verify sender domain in Google Workspace Admin before deploying
# smtp_host and smtp_port use module defaults (smtp.gmail.com:587)
smtp_from_email      = "CHANGE_ME@waooaw.com"   # REQUIRED: set production sender address
smtp_username_secret = "PROD_OTP_SMTP_USERNAME" # REQUIRED: create this secret in GCP first
smtp_password_secret = "PROD_OTP_SMTP_PASSWORD" # REQUIRED: create this secret in GCP first
