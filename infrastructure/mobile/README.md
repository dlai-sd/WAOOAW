# WAOOAW Mobile Infrastructure Deployment Guide

## Overview

This directory contains Terraform configurations for managing GCP infrastructure that **supports** the WAOOAW mobile app. 

**IMPORTANT**: Terraform manages supporting infrastructure (Firebase, storage, monitoring), but **does NOT deploy the mobile app itself**. Mobile app builds and deployments are handled by **Expo EAS** and **GitHub Actions**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MOBILE APP STACK                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │   EAS Build  │────────▶│  App Stores  │ (Actual Apps)      │
│  │   Service    │         │ iOS/Android  │                    │
│  └──────────────┘         └──────────────┘                    │
│         │                                                       │
│         │ Uses infrastructure provisioned by Terraform ▼       │
│         │                                                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │            GCP Infrastructure (Terraform)                 │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ • Cloud Storage (OTA Updates)                            │ │
│  │ • Secret Manager (API Keys, Credentials)                 │ │
│  │ • Cloud Monitoring (Dashboards, Alerts)                  │ │
│  │ • IAM (Service Accounts for CI/CD)                       │ │
│  │ • Firebase (Analytics, Crashlytics)                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Terraform Manages

✅ **Cloud Storage Buckets**: For Expo OTA update artifacts  
✅ **Secret Manager**: API keys (Razorpay, Google OAuth, Sentry, Expo)  
✅ **Cloud Monitoring**: Dashboards and alerting for mobile metrics  
✅ **IAM**: Service accounts for CI/CD pipelines  
✅ **Firebase Projects**: Analytics, Crashlytics, Performance Monitoring  

❌ **What Terraform Does NOT Manage**: Mobile app binary builds, TestFlight/Play Store submissions, OTA JS updates (handled by EAS)

---

## Prerequisites

### 1. Install Tools

```bash
# Terraform
brew install terraform  # macOS
# OR
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip

# Google Cloud SDK
brew install google-cloud-sdk  # macOS
# OR
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth application-default login
gcloud config set project waooaw-production
```

### 2. Create GCS Bucket for Terraform State

```bash
# One-time setup
gcloud storage buckets create gs://waooaw-terraform-state \
  --location=asia-south1 \
  --uniform-bucket-level-access

gsutil versioning set on gs://waooaw-terraform-state
```

### 3. Set Environment Variables

```bash
export TF_VAR_gcp_project_id="waooaw-production"
export TF_VAR_slack_webhook_token="xoxb-your-slack-token"
```

---

## Deployment

### Initialize Terraform

```bash
cd /workspaces/WAOOAW/infrastructure/mobile
terraform init
```

### Plan Changes

```bash
terraform plan -out=tfplan
```

**Review the plan carefully!** This shows what will be created/modified.

### Apply Changes

```bash
# Development environment only
terraform apply -target=google_storage_bucket.mobile_ota_updates[\"development\"]

# All environments
terraform apply tfplan
```

### Destroy Resources (USE WITH CAUTION)

```bash
# Destroy specific environment
terraform destroy -target=google_storage_bucket.mobile_ota_updates[\"staging\"]

# Destroy everything (DANGEROUS)
terraform destroy
```

---

## Environment Management

### Add New Environment

1. Update `variables.tf`:
   ```hcl
   variable "environments" {
     default = ["development", "staging", "production", "hotfix"]
   }
   ```

2. Apply changes:
   ```bash
   terraform apply
   ```

### Update Secrets

Secrets are managed in GCP Secret Manager. To update:

```bash
# Example: Update Razorpay production key
echo -n "rzp_live_NEW_KEY" | gcloud secrets versions add mobile-razorpay-key-id-production --data-file=-

# Verify
gcloud secrets versions access latest --secret=mobile-razorpay-key-id-production
```

---

## Monitoring & Alerts

### Access Dashboard

After applying Terraform, get the dashboard URL:

```bash
terraform output monitoring_dashboard_url
```

Open in browser to view:
- App crash rate
- Daily active users (DAU)
- API response times (P95)
- OTA update adoption rate

### Configure Alerts

Alerts trigger when:
- Crash-free rate drops below 99%
- API response time P95 > 2 seconds
- OTA adoption rate < 80% after 7 days

Notifications sent to:
- Slack: `#mobile-alerts`
- Email: `mobile-alerts@waooaw.com`

---

## Integration with CI/CD

GitHub Actions workflows automatically use the infrastructure provisioned by Terraform.

### Service Account Setup

1. Generate key for CI/CD service account:
   ```bash
   gcloud iam service-accounts keys create mobile-cicd-key.json \
     --iam-account=mobile-cicd@waooaw-production.iam.gserviceaccount.com
   ```

2. Add to GitHub Secrets:
   ```bash
   gh secret set GCP_SA_KEY < mobile-cicd-key.json
   gh secret set EXPO_TOKEN --body "your-expo-token"
   ```

3. Workflows in `.github/workflows/mobile-*.yml` will use these credentials.

---

## Cost Estimation

| Resource | Environment | Monthly Cost (Approx) |
|----------|-------------|----------------------|
| Cloud Storage (OTA) | Development | $0.10 |
| Cloud Storage (OTA) | Staging | $1.00 |
| Cloud Storage (OTA) | Production | $5.00 |
| Secret Manager | All | $0.06 (6 secrets × $0.01) |
| Cloud Monitoring | All | $2.00 |
| **Total** | | **~$8.16/month** |

Firebase (Analytics, Crashlytics) has generous free tier; paid plans start at $25/month if needed.

---

## Troubleshooting

### Issue: Terraform state locked

```bash
# Force unlock (use carefully)
terraform force-unlock <LOCK_ID>
```

### Issue: Permission denied errors

```bash
# Verify authentication
gcloud auth list
gcloud auth application-default login

# Check IAM roles
gcloud projects get-iam-policy waooaw-production
```

### Issue: OTA bucket access denied

```bash
# Make bucket public
gsutil iam ch allUsers:objectViewer gs://waooaw-mobile-ota-production
```

---

## Best Practices

1. **Always run `terraform plan` before `apply`** — Preview changes
2. **Use workspaces for environments** — Isolate state
3. **Store state remotely (GCS)** — Team collaboration
4. **Version control Terraform files** — Track infrastructure changes
5. **Use variables for secrets** — Never hardcode credentials
6. **Tag all resources** — Cost tracking and organization
7. **Enable versioning on buckets** — Rollback capability
8. **Review IAM permissions regularly** — Principle of least privilege

---

## Useful Commands

```bash
# Show current state
terraform show

# List all resources
terraform state list

# Get specific output
terraform output ota_bucket_names

# Import existing resource
terraform import google_storage_bucket.mobile_ota_updates[\"production\"] waooaw-mobile-ota-production

# Refresh state
terraform refresh

# Format .tf files
terraform fmt -recursive

# Validate configuration
terraform validate
```

---

## Support

For infrastructure issues:
- **Slack**: `#infrastructure`
- **On-call**: Check PagerDuty rotation
- **Documentation**: [WAOOAW Infrastructure Wiki](https://wiki.waooaw.com/infrastructure)

For mobile app deployment issues (EAS, app stores):
- **Slack**: `#mobile-engineering`
- **Documentation**: `/docs/mobile/deployment_guide.md`

---

## Related Documentation

- [Mobile Deployment Guide](../../docs/mobile/deployment_guide.md)
- [EAS Build Configuration](../../src/mobile/eas.json)
- [GitHub Actions Workflows](../../.github/workflows/mobile-*.yml)
- [GCP Architecture Overview](../README.md)
