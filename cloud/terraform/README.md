# WAOOAW Infrastructure - Terraform

Complete Infrastructure as Code using Terraform for all environments.

## Architecture

**Single Static IP (35.190.6.91)** routes to ALL environments:
- Demo: `cp.demo.waooaw.com`, `pp.demo.waooaw.com`
- UAT: `cp.uat.waooaw.com`, `pp.uat.waooaw.com`
- Prod: `www.waooaw.com`, `pp.waooaw.com`

**Three Services per Environment:**
1. Backend API (shared by both portals)
2. Customer Portal (marketplace)
3. Platform Portal (internal ops)

## Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
# OR
sudo apt install terraform  # Linux

# Initialize GCP authentication
gcloud auth application-default login

# Create state bucket (one-time)
gsutil mb -p waooaw-oauth -l asia-south1 gs://waooaw-terraform-state
gsutil versioning set on gs://waooaw-terraform-state
```

## Quick Start

### Deploy Demo Environment

```bash
cd /workspaces/WAOOAW/cloud/terraform

# Initialize Terraform
terraform init

# Review changes
terraform plan -var-file=environments/demo.tfvars

# Apply infrastructure
terraform apply -var-file=environments/demo.tfvars

# View outputs
terraform output
```

### Deploy UAT Environment

```bash
terraform workspace new uat  # Create workspace
terraform workspace select uat

terraform plan -var-file=environments/uat.tfvars
terraform apply -var-file=environments/uat.tfvars
```

### Deploy Production

```bash
terraform workspace new prod
terraform workspace select prod

terraform plan -var-file=environments/prod.tfvars
terraform apply -var-file=environments/prod.tfvars
```

## Project Structure

```
terraform/
├── main.tf                    # Root module (orchestrates everything)
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── backend.tf                 # State backend configuration
│
├── environments/
│   ├── demo.tfvars            # Demo environment config
│   ├── uat.tfvars             # UAT environment config
│   └── prod.tfvars            # Production config
│
└── modules/
    ├── cloud-run/             # Cloud Run service module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── load-balancer/         # Load Balancer module
    │   ├── main.tf            # Backend services, URL map, SSL, proxies
    │   ├── variables.tf
    │   └── outputs.tf
    │
    └── networking/            # Network Endpoint Groups
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Key Features

### State Management
- **Remote state**: GCS bucket `waooaw-terraform-state`
- **Workspaces**: Separate state per environment
- **Locking**: Prevents concurrent modifications
- **Versioning**: Can rollback if needed

### Modular Design
- Reusable modules for Cloud Run, LB, Networking
- Environment-specific tfvars files
- DRY principle (Don't Repeat Yourself)

### Safety Features
- `terraform plan` shows changes before applying
- `lifecycle` blocks prevent accidental deletions
- `ignore_changes` allows manual image updates

### Cost Optimization
- Single static IP shared across environments ($5/month total)
- Scale-to-zero for demo (0 min instances)
- Always-warm for production (2 min instances)

## Common Commands

```bash
# Initialize (first time or after adding modules)
terraform init

# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes (dry run)
terraform plan -var-file=environments/demo.tfvars

# Apply changes
terraform apply -var-file=environments/demo.tfvars

# Apply with auto-approval (CI/CD)
terraform apply -var-file=environments/demo.tfvars -auto-approve

# Show current state
terraform show

# List resources
terraform state list

# View specific resource
terraform state show google_cloud_run_v2_service.backend_api

# Destroy everything (CAREFUL!)
terraform destroy -var-file=environments/demo.tfvars

# Import existing resource
terraform import google_compute_global_address.static_ip waooaw-lb-ip
```

## Outputs

After `terraform apply`, you'll see:

```
Outputs:

static_ip = "35.190.6.91"

customer_portal_url = "https://cp.demo.waooaw.com"
platform_portal_url = "https://pp.demo.waooaw.com"
backend_api_url = "https://cp.demo.waooaw.com/api"

dns_records_needed = {
  customer_portal = "cp.demo.waooaw.com → 35.190.6.91"
  platform_portal = "pp.demo.waooaw.com → 35.190.6.91"
}

oauth_urls = {
  authorized_origins = [
    "https://cp.demo.waooaw.com",
    "https://pp.demo.waooaw.com"
  ]
  redirect_uris = [
    "https://cp.demo.waooaw.com/api/auth/callback",
    "https://pp.demo.waooaw.com/api/auth/callback"
  ]
}

ssl_certificates = {
  customer = {
    name   = "demo-customer-ssl"
    status = "PROVISIONING"
  }
  platform = {
    name   = "demo-platform-ssl"
    status = "PROVISIONING"
  }
}
```

## Post-Deployment

### 1. Configure DNS (One-time for all environments)

In GoDaddy, add these A records:

| Name | Type | Value | TTL |
|------|------|-------|-----|
| cp.demo | A | 35.190.6.91 | 600 |
| pp.demo | A | 35.190.6.91 | 600 |
| cp.uat | A | 35.190.6.91 | 600 |
| pp.uat | A | 35.190.6.91 | 600 |
| www | A | 35.190.6.91 | 600 |
| pp | A | 35.190.6.91 | 600 |

### 2. Update OAuth Console

https://console.cloud.google.com/apis/credentials

Use the `oauth_urls` output to add origins and redirect URIs.

### 3. Wait for SSL Provisioning

```bash
# Check SSL certificate status
gcloud compute ssl-certificates list --global

# Usually takes 10-15 minutes
```

### 4. Test Deployment

```bash
# Check health
curl https://cp.demo.waooaw.com/api/health

# Visit portals
open https://cp.demo.waooaw.com  # Customer Portal
open https://pp.demo.waooaw.com  # Platform Portal
```

## Troubleshooting

### SSL Certificate Stuck in PROVISIONING

- Ensure DNS is configured correctly
- Wait up to 60 minutes for first-time provisioning
- Check domain ownership verification

### Cloud Run Service Not Found

- Verify Docker images exist in Artifact Registry
- Check IAM permissions for Cloud Run
- Review service logs: `gcloud run services logs read waooaw-api-demo`

### Backend Service Unhealthy

- Check health check path is correct
- Verify Cloud Run service is responding
- Review NEG connections to Cloud Run

### State Lock Errors

```bash
# Force unlock (if process was killed)
terraform force-unlock LOCK_ID
```

## Cleanup

```bash
# Delete demo environment
chmod +x cleanup-demo.sh
./cleanup-demo.sh

# OR use Terraform
terraform destroy -var-file=environments/demo.tfvars
```

## Benefits Over Deployment Manager

| Feature | Deployment Manager | Terraform |
|---------|-------------------|-----------|
| Cloud Run Support | ❌ No | ✅ Yes |
| State Management | ❌ No | ✅ Yes |
| Plan before apply | ❌ No | ✅ Yes |
| Module reusability | ⚠️ Limited | ✅ Excellent |
| Community support | ⚠️ Small | ✅ Large |
| Multi-cloud | ❌ No | ✅ Yes |
| Error messages | ⚠️ Poor | ✅ Good |
| Import existing | ⚠️ Difficult | ✅ Easy |

## Next Steps

1. ✅ Deploy demo with Terraform
2. Test OAuth flow on new infrastructure
3. Create UAT environment
4. Add monitoring and alerting (future)
5. Implement blue-green deployments (future)
6. Add Terraform Cloud for team collaboration (future)
