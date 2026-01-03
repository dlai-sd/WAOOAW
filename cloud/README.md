# WAOOAW Infrastructure as Code

Single-file infrastructure management for all GCP resources using Deployment Manager + Jinja templates.

## 📁 Structure

```
cloud/
├── deploy.py                    # Main deployment script
├── infrastructure.yaml          # Documentation (original comprehensive config)
├── templates/
│   ├── cloud-run.jinja         # Cloud Run service template
│   ├── load-balancer.jinja     # Load Balancer template
│   └── networking.jinja        # Networking (IPs, VPC) template
├── demo/                        # Legacy demo scripts
├── uat/                         # Legacy UAT scripts
└── prod/                        # Legacy prod scripts
```

## 🚀 Quick Start

### Deploy Demo Environment

```bash
cd /workspaces/WAOOAW/cloud

# Create new infrastructure
./deploy.py --environment demo --action create

# Update existing infrastructure
./deploy.py --environment demo --action update

# Preview changes before applying
./deploy.py --environment demo --action update --preview

# Delete infrastructure
./deploy.py --environment demo --action delete
```

### Deploy with Specific Version

```bash
# Deploy specific Docker image version
./deploy.py --environment uat --action create --version v1.0.0

# Deploy from commit SHA
./deploy.py --environment prod --action update --version abc123
```

## 🔧 What Gets Deployed

### Demo Environment
- ✅ Cloud Run services (backend, platform portal)
- ✅ Static external IP
- ✅ Google-managed SSL certificate
- ✅ Load Balancer with URL routing
  - `/api/*` → Backend
  - `/*` → Platform Portal
- ✅ HTTP → HTTPS redirect
- ✅ Health checks
- ✅ Logging enabled

**Scaling**: 0-5 instances (scale-to-zero)

### UAT Environment
- Same as demo, plus:
- ✅ Minimum 1 instance (always warm)
- ✅ Up to 10 instances

**Scaling**: 1-10 instances

### Prod Environment
- Same as UAT, plus:
- ✅ Minimum 2 instances (HA)
- ✅ Up to 100 instances
- ✅ Multi-region support (optional)
- ✅ Lower log sampling (10%)

**Scaling**: 2-100 instances

## 📋 Post-Deployment Configuration

After successful deployment, configure:

### 1. DNS (GoDaddy)

```
Type:       A
Host:       demo (or uat, prod)
Points to:  [IP from deployment output]
TTL:        600
```

### 2. Google OAuth Console

https://console.cloud.google.com/apis/credentials

**Authorized JavaScript origins:**
- `https://demo.waooaw.com`

**Authorized redirect URIs:**
- `https://demo.waooaw.com/api/auth/callback`

## 🔍 Verification

### Check SSL Certificate Status

```bash
gcloud compute ssl-certificates describe demo-ssl-cert \
  --global \
  --project=waooaw-oauth
```

**Note**: SSL provisioning takes 10-15 minutes after DNS is configured.

### Test Endpoints

```bash
# Health check
curl https://demo.waooaw.com/api/health

# Platform Portal
curl https://demo.waooaw.com
```

### View Logs

```bash
# Backend logs
gcloud logging read \
  'resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-api-demo' \
  --limit=20 \
  --project=waooaw-oauth

# Platform Portal logs
gcloud logging read \
  'resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-platform-portal-demo' \
  --limit=20 \
  --project=waooaw-oauth
```

## 🎛️ Configuration

All configuration is in `deploy.py`:

### Regions

```python
REGIONS = {
    "demo": ["asia-south1"],
    "uat": ["asia-south1"],
    "prod": ["asia-south1", "us-central1"]  # Multi-region
}
```

### Scaling

```python
SCALING = {
    "demo": {
        "minInstances": 0,
        "maxInstances": 5,
        "concurrency": 80,
        "cpuThrottling": True
    },
    # ... uat, prod
}
```

### Docker Images

```python
# In deploy.py, generate_config() function
"image": f"asia-south1-docker.pkg.dev/{PROJECT}/waooaw/backend-v2:{version}"
```

## 🔄 Update Workflow

### Make Changes

1. Edit `deploy.py` (configuration)
2. Edit templates (infrastructure)
3. Preview changes:

```bash
./deploy.py --environment demo --action update --preview
```

### Apply Changes

```bash
./deploy.py --environment demo --action update
```

### Rollback

Deployment Manager tracks all deployments:

```bash
# List deployments
gcloud deployment-manager deployments list --project=waooaw-oauth

# Describe deployment
gcloud deployment-manager deployments describe waooaw-demo-infra --project=waooaw-oauth

# Rollback (delete and recreate from previous config)
./deploy.py --environment demo --action delete
./deploy.py --environment demo --action create
```

## 🏗️ Architecture

```
demo.waooaw.com (Static IP: xxx.xxx.xxx.xxx)
         ↓
   Load Balancer
         ↓
    ┌─────────────┴─────────────┐
    │                           │
/api/*                       /*
    ↓                           ↓
Backend Service        Platform Portal Service
    ↓                           ↓
waooaw-api-demo      waooaw-platform-portal-demo
(Cloud Run)                (Cloud Run)
asia-south1              asia-south1
```

## 🔐 Security

### Service Accounts

Each service has dedicated service account:
- `waooaw-backend-{env}@waooaw-oauth.iam.gserviceaccount.com`
- `waooaw-platform-{env}@waooaw-oauth.iam.gserviceaccount.com`

### Secrets

Stored in GCP Secret Manager:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `JWT_SECRET`

### IAM Roles

Backend service account needs:
- `roles/secretmanager.secretAccessor`
- `roles/logging.logWriter`
- `roles/cloudtrace.agent`

## 💰 Cost Estimate

### Demo (scale-to-zero, minimal traffic)
- Cloud Run: $0-5/month
- Load Balancer: $18/month
- **Total: ~$20/month**

### UAT (always warm, moderate traffic)
- Cloud Run: $20-30/month
- Load Balancer: $18/month
- **Total: ~$40-50/month**

### Prod (HA, high traffic)
- Cloud Run: $100-300/month
- Load Balancer: $18/month
- **Total: ~$120-320/month**

## 🆘 Troubleshooting

### Deployment fails with "resource already exists"

```bash
# Delete existing deployment first
./deploy.py --environment demo --action delete

# Then create new
./deploy.py --environment demo --action create
```

### SSL certificate stuck in "PROVISIONING"

1. Check DNS is configured correctly
2. Wait 10-15 minutes for Google to verify domain
3. Check certificate status:

```bash
gcloud compute ssl-certificates describe demo-ssl-cert --global
```

### Service not accessible

1. Check Load Balancer backend health:

```bash
gcloud compute backend-services get-health demo-api-backend-service --global
```

2. Check Cloud Run service is running:

```bash
gcloud run services describe waooaw-api-demo --region=asia-south1
```

3. Check logs for errors:

```bash
gcloud logging read 'resource.type=cloud_run_revision' --limit=50
```

## 📚 Reference

- [GCP Deployment Manager Docs](https://cloud.google.com/deployment-manager/docs)
- [Jinja Template Reference](https://cloud.google.com/deployment-manager/docs/configuration/templates/create-basic-template)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Load Balancing Docs](https://cloud.google.com/load-balancing/docs)

## 🔗 Related Files

- Backend config: `/backend-v2/app/config.py`
- Platform Portal config: `/PlatformPortal-v2/PlatformPortal_v2/PlatformPortal_v2.py`
- OAuth setup: `/cloud/gcp/oauth/google-oauth-config.md`
