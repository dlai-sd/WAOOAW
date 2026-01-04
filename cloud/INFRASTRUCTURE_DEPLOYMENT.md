# Infrastructure Deployment Summary

**Date**: 2025-01-03  
**Environment**: Demo  
**Status**: ✅ Fully Operational  
**Commit**: d38d8c3

---

## Deployment Overview

Successfully deployed WAOOAW demo environment using **Terraform** with YAML-driven configuration. All services are operational, SSL certificates are active, and both customer and platform portals are accessible via HTTPS.

### Live URLs

| Service | URL | Status |
|---------|-----|--------|
| **Customer Portal** | https://cp.demo.waooaw.com | ✅ 200 OK |
| **Platform Portal** | https://pp.demo.waooaw.com | ✅ 200 OK |
| **Backend API** | https://waooaw-api-demo-ryvhxvrdna-el.a.run.app | ✅ Running |
| **Load Balancer IP** | 35.190.6.91 | ✅ Preserved |

---

## Infrastructure Architecture

### Cloud Run Services (asia-south1)

1. **waooaw-api-demo**
   - Image: `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/backend-v2:latest`
   - Port: 8000
   - Min instances: 0
   - Max instances: 5
   - Direct URL: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app

2. **waooaw-portal-demo**
   - Image: `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/customer-portal-v2:latest`
   - Port: **80** (fixed from 8080)
   - Min instances: 0
   - Max instances: 5
   - Direct URL: https://waooaw-portal-demo-ryvhxvrdna-el.a.run.app

3. **waooaw-platform-portal-demo**
   - Image: `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-v2:latest`
   - Port: 8080
   - Min instances: 0
   - Max instances: 5
   - Direct URL: https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app

### Load Balancer Configuration

- **Type**: External Managed HTTP(S) Load Balancer
- **Static IP**: 35.190.6.91 (preserved from previous deployment)
- **Domains**:
  - cp.demo.waooaw.com → Customer Portal
  - pp.demo.waooaw.com → Platform Portal
  
- **SSL Certificates**: Managed by Google Cloud
  - demo-customer-ssl: ✅ ACTIVE
  - demo-platform-ssl: ✅ ACTIVE

- **URL Routing**:
  - `/api/*` → Backend API
  - `/auth/*` → Backend API (OAuth endpoints)
  - `/health` → Backend API
  - `/*` → Customer Portal (cp) / Platform Portal (pp)

### Networking

- **Serverless NEGs**: Automatically created for each Cloud Run service
- **Health Checks**: Managed internally by serverless NEGs (no explicit health checks needed)
- **Backend Services**: Three backend services (api, customer, platform) pointing to respective NEGs

---

## Key Technical Fixes

### 1. Customer Portal Port Fix

**Problem**: Customer portal container failed to start (timeout error code 9)
```
Cloud Run error: Container failed to start. Failed to start and then listen on the port defined by the PORT environment variable.
```

**Root Cause**: WaooawPortal nginx listens on port 80 by default, but Terraform was setting `PORT=8080`

**Solution**: Changed container port in [cloud/terraform/main.tf](cloud/terraform/main.tf#L66)
```hcl
# OLD
port = 8080

# NEW
port = 80
```

### 2. Serverless NEG Health Checks

**Problem**: Terraform apply failed with 400 error
```
Error: Error creating Backend Service: googleapi: Error 400: INVALID_ARGUMENT
Health checks are not supported for Serverless Network Endpoint Groups.
```

**Root Cause**: Serverless NEGs (Cloud Run) manage health internally; explicit health checks cause conflicts

**Solution**: Removed `health_checks` from all three backend services in [cloud/terraform/modules/load-balancer/main.tf](cloud/terraform/modules/load-balancer/main.tf)
```hcl
resource "google_compute_backend_service" "api" {
  # ... other config ...
  # REMOVED: health_checks = [google_compute_health_check.api.id]
}
```

### 3. IAM Permissions

**Problem**: Terraform service account couldn't apply IAM policy
```
Error: Error setting IAM policy for service: googleapi: Error 403
Permission 'run.services.setIamPolicy' denied
```

**Solution**: Granted `roles/run.admin` to terraform-admin service account
```bash
gcloud projects add-iam-policy-binding waooaw-oauth \
  --member="serviceAccount:terraform-admin@waooaw-oauth.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

---

## Terraform Configuration

### YAML-Driven Infrastructure

Created [cloud/infrastructure.yaml](cloud/infrastructure.yaml) as single source of truth:
```yaml
project_id: waooaw-oauth
region: asia-south1

environments:
  demo:
    customer_portal_domain: cp.demo.waooaw.com
    platform_portal_domain: pp.demo.waooaw.com
    image_tag: latest
    scaling:
      min_instances: 0
      max_instances: 5
```

### Terraform Modules

1. **[cloud-run](cloud/terraform/modules/cloud-run/)**: Cloud Run v2 service creation with IAM bindings
2. **[networking](cloud/terraform/modules/networking/)**: Serverless NEG creation
3. **[load-balancer](cloud/terraform/modules/load-balancer/)**: External HTTP(S) load balancer with SSL

### Generated tfvars

[generate_tfvars.py](cloud/terraform/generate_tfvars.py) converts infrastructure.yaml to environment-specific tfvars:
```bash
python generate_tfvars.py
# Generates:
# - environments/demo.tfvars
# - environments/uat.tfvars
# - environments/prod.tfvars
```

---

## Docker Images

Built locally and pushed to Artifact Registry:
```bash
# Backend API
docker build -t backend-v2:latest WaooawPortal/backend/
docker tag backend-v2:latest asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/backend-v2:latest
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/backend-v2:latest

# Customer Portal
docker build -t customer-portal-v2:latest WaooawPortal/
docker tag customer-portal-v2:latest asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/customer-portal-v2:latest
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/customer-portal-v2:latest

# Platform Portal
docker build -t platform-portal-v2:latest PlatformPortal/
docker tag platform-portal-v2:latest asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-v2:latest
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-v2:latest
```

---

## Deployment Commands

### Apply Infrastructure
```bash
cd cloud/terraform

# Initialize Terraform
terraform init

# Generate tfvars from YAML
python generate_tfvars.py

# Plan deployment
terraform plan -var-file=environments/demo.tfvars

# Apply changes
terraform apply -var-file=environments/demo.tfvars
```

### Verify Deployment
```bash
# Check SSL certificates
gcloud compute ssl-certificates describe demo-customer-ssl --global
gcloud compute ssl-certificates describe demo-platform-ssl --global

# Test endpoints
curl -I https://cp.demo.waooaw.com
curl -I https://pp.demo.waooaw.com
curl -I https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/health

# Check DNS
getent hosts cp.demo.waooaw.com
getent hosts pp.demo.waooaw.com
```

### Destroy Infrastructure
```bash
terraform destroy -var-file=environments/demo.tfvars
```

---

## Resources Created

Terraform apply created **23 resources**:

### Cloud Run (6 resources)
- 3 Cloud Run v2 services
- 3 IAM policy bindings (allUsers invoker)

### Networking (3 resources)
- 3 Serverless NEGs (api, customer, platform)

### Load Balancer (14 resources)
- 1 Global forwarding rule (HTTPS)
- 1 Global forwarding rule (HTTP redirect)
- 1 Target HTTPS proxy
- 1 Target HTTP proxy
- 1 URL map
- 2 Managed SSL certificates
- 3 Backend services
- 4 Other LB components

---

## Security Considerations

### Credentials Management

⚠️ **Important**: Service account keys must never be committed to git

Files excluded in [.gitignore](.gitignore):
```gitignore
# Credentials
terraform-admin-key.json
github-actions-key.json
credential_registry.json
google-cloud-sdk/platform/bq/.gcloud_credentials

# Terraform cache
cloud/terraform/.terraform/
*.tfstate
*.tfstate.backup

# Large files
google-cloud-sdk/
```

### IAM Service Account

- **Name**: terraform-admin@waooaw-oauth.iam.gserviceaccount.com
- **Roles**:
  - `roles/editor` (project-wide)
  - `roles/run.admin` (Cloud Run IAM management)

### Public Access

All Cloud Run services are publicly accessible (`allUsers` invoker role) - this is intentional for the demo environment.

---

## Next Steps

### OAuth Implementation

With infrastructure deployed, next iteration focuses on Google OAuth integration:

1. **Configure OAuth Consent Screen**
   - Add authorized domains: cp.demo.waooaw.com, pp.demo.waooaw.com
   - Set redirect URIs in Google Cloud Console

2. **Update OAuth Credentials**
   - Backend: Ensure CLIENT_ID and CLIENT_SECRET in environment variables
   - Frontend: Update auth.js with new backend URLs (already done in OAUTH_IMPLEMENTATION.md)

3. **Test OAuth Flow**
   - Customer Portal: Sign In → OAuth → Callback → Marketplace
   - Platform Portal: Sign In → OAuth → Callback → Dashboard

4. **Verify Token Exchange**
   - Backend receives authorization code
   - Exchanges for access/refresh tokens
   - Returns JWT to frontend
   - Frontend stores token in localStorage

### Reference Documents

- [OAUTH_IMPLEMENTATION.md](OAUTH_IMPLEMENTATION.md) - OAuth code changes (commit caf60b2)
- [cloud/infrastructure.yaml](cloud/infrastructure.yaml) - Infrastructure configuration
- [cloud/terraform/README.md](cloud/terraform/README.md) - Terraform usage guide

---

## Lessons Learned

1. **Serverless NEGs don't need explicit health checks** - They manage health internally via Cloud Run
2. **Container ports must match application listen ports** - nginx defaults to 80, not 8080
3. **Service accounts need run.admin for IAM bindings** - Editor role alone is insufficient
4. **Static IPs can be preserved** - Use data sources instead of resources to avoid recreation
5. **YAML-driven infrastructure** - Single source of truth simplifies multi-environment management
6. **Local Docker builds** - Faster than Cloud Build for small images during development

---

## Troubleshooting

### SSL Certificate Not Active

If SSL certs show status `PROVISIONING`:
```bash
# Wait 10-15 minutes for Google to provision
gcloud compute ssl-certificates describe demo-customer-ssl --global

# Check domain ownership
gcloud compute ssl-certificates list
```

### Container Start Timeout

If Cloud Run service fails to start:
```bash
# Check logs
gcloud run services logs read waooaw-portal-demo --region=asia-south1 --limit=50

# Common causes:
# - Wrong PORT value (must match nginx/app listen port)
# - Missing environment variables
# - Image pull errors
```

### 404 Not Found on Domain

If curl returns 404:
```bash
# Check URL map routing
gcloud compute url-maps describe waooaw-demo-lb --global

# Verify backend services
gcloud compute backend-services list

# Check NEG health
gcloud compute network-endpoint-groups describe waooaw-demo-customer-neg --region=asia-south1
```

---

**Deployment completed successfully!** 🚀  
Infrastructure is ready for OAuth testing and production rollout.
