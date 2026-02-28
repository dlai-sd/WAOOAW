project_id    = "waooaw-oauth"
region        = "asia-south1"
environment   = "uat"
min_instances = 1
max_instances = 20

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
