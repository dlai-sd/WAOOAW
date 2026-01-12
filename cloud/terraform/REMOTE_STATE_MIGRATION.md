# Terraform Remote State Backend Migration

**Date**: January 12, 2026  
**Reason**: Eliminate state drift between GitHub Actions and local development

---

## What Changed

### Before (Local State)
- terraform.tfstate stored in repository
- GitHub Actions created its own state during runs
- State never synced back to repository
- Every run started with old state
- Caused Error 409: "Resource already exists"

### After (Remote State - GCS)
- State stored in GCS bucket: `gs://waooaw-terraform-state`
- All operations (GitHub Actions + local) use same remote state
- State updates automatically sync
- Concurrent runs blocked by state locking
- Environment-specific state files:
  - `env/demo/default.tfstate`
  - `env/uat/default.tfstate`
  - `env/prod/default.tfstate`

---

## GCS Bucket Configuration

**Bucket**: `waooaw-terraform-state`  
**Location**: asia-south1  
**Storage Class**: STANDARD  
**Versioning**: Enabled (state history + rollback)  
**Encryption**: Default encryption at rest  
**Access**: Service account permissions from GitHub Actions

---

## Migration Steps

### 1. Bucket Setup (Completed)
```bash
gsutil mb -p waooaw-oauth -l asia-south1 gs://waooaw-terraform-state
gsutil versioning set on gs://waooaw-terraform-state
```

### 2. Code Changes (Completed)
- **main.tf**: Enabled GCS backend configuration
- **cp-pipeline.yml**: Updated terraform init to use `-backend-config="prefix=env/${TARGET_ENV}"`

### 3. State Migration (Required)

**Option A: Fresh Start (Recommended)**
```bash
# Delete all GCP resources (except Static IP)
gcloud run services delete waooaw-cp-frontend-demo --region=asia-south1 --quiet
gcloud run services delete waooaw-cp-backend-demo --region=asia-south1 --quiet
gcloud run services delete waooaw-cp-health-demo --region=asia-south1 --quiet
gcloud compute ssl-certificates delete demo-cp-ssl --global --quiet
# Delete Load Balancer components...

# Run fresh deployment with cleanup checkbox = YES
# Terraform creates everything fresh with remote state
```

**Option B: Import Existing Resources**
```bash
cd /workspaces/WAOOAW/cloud/terraform

# Initialize with remote backend
terraform init -backend-config="prefix=env/demo" -reconfigure

# Import existing resources
terraform import 'module.load_balancer.google_compute_managed_ssl_certificate.cp[0]' \
  projects/waooaw-oauth/global/sslCertificates/demo-cp-ssl

terraform import 'module.cp_frontend[0].google_cloud_run_v2_service.service' \
  projects/waooaw-oauth/locations/asia-south1/services/waooaw-cp-frontend-demo

# Import all 17 resources...
```

---

## Current State

**Local State File**: `/workspaces/WAOOAW/cloud/terraform/terraform.tfstate`  
- Last updated: January 12, 07:21
- Contains: Old architecture (5 resources)
- Status: Obsolete

**GCP Runtime**:
- 17 resources deployed (run #104)
- Fully operational
- SSL: ACTIVE
- URL: https://cp.demo.waooaw.com

**Remote State File**: `gs://waooaw-terraform-state/env/demo/default.tfstate`
- Status: Empty (needs migration)

---

## Next Steps

1. **Decide Migration Strategy**: Fresh start vs import
2. **Run Migration**: Execute chosen option
3. **Verify Sync**: Run `terraform plan` - should show no changes
4. **Test Deployment**: Trigger workflow run
5. **Delete Local State**: Remove `terraform.tfstate*` from repository (add to .gitignore)

---

## Benefits After Migration

- No more Error 409 from state drift
- GitHub Actions and local dev stay in sync
- State versioning allows rollback if corrupted
- State locking prevents concurrent modification conflicts
- Cleaner git repository (no state files tracked)
- Industry standard approach

---

## Rollback Plan

If issues occur, can revert to local state:
```hcl
# In main.tf, comment out backend block:
# backend "gcs" {
#   bucket = "waooaw-terraform-state"
#   prefix = "env"
# }

# Re-initialize with local state
terraform init -migrate-state
```

---

## Documentation Updates

- ✅ PIPELINE.md: Added remote state backend section
- ✅ REMOTE_STATE_MIGRATION.md: This file
- ⏳ README.md: Update with remote state initialization instructions
- ⏳ PIPELINE_UPDATE_SUMMARY.md: Document migration in history
