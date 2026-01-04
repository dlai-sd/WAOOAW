# 🚀 Final Setup Checklist - WAOOAW v2 Demo Deployment

**Date**: January 3, 2026  
**Status**: ✅ **80% COMPLETE** | ⏳ **20% MANUAL STEPS REMAINING**

---

## ✅ Completed Automatically

- [x] **Artifact Registry** created in Mumbai (asia-south1)
- [x] **Secret Manager** secrets created:
  - DB_USER (postgres)
  - DB_PASSWORD
  - JWT_SECRET (auto-generated)
  - GOOGLE_CLIENT_ID (270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq)
  - GOOGLE_CLIENT_SECRET
- [x] **Cloud Run service account** granted access to all secrets
- [x] **GitHub Actions service account** created with roles:
  - Cloud Run Admin
  - Artifact Registry Writer
  - Secret Manager Secret Accessor
  - Service Account User
- [x] **Service account key** generated: `/workspaces/WAOOAW/github-actions-key.json`
- [x] **Database schema SQL** created: `scripts/deployment/setup-demo-database.sql`

---

## ⏳ Manual Steps Required (6 items)

### 1. Create Cloud SQL Instance ⚠️ CRITICAL
**Status**: Not found - needs to be created

```bash
# Create Cloud SQL instance in Mumbai
gcloud sql instances create waooaw-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --root-password=YOUR_ROOT_PASSWORD_HERE \
  --storage-type=SSD \
  --storage-size=10GB \
  --availability-type=ZONAL

# Wait for creation (~5 minutes)
gcloud sql instances list

# Get connection info
gcloud sql instances describe waooaw-db --format='value(ipAddresses[0].ipAddress)'
```

**After creation, run database setup**:
```bash
# Create demo schema and tables
gcloud sql connect waooaw-db --user=postgres --quiet < scripts/deployment/setup-demo-database.sql
```

---

### 2. Add GitHub Secrets ⚠️ CRITICAL
**URL**: https://github.com/dlai-sd/WAOOAW/settings/secrets/actions

Click "New repository secret" for each:

**GCP_SA_KEY**:
```bash
# Copy entire contents of this file:
cat /workspaces/WAOOAW/github-actions-key.json

# Paste into GitHub secret (it's a JSON object starting with {"type":"service_account"...})
```

**DB_HOST**:
```bash
# After Cloud SQL is created, get the private IP:
gcloud sql instances describe waooaw-db --format='value(ipAddresses[0].ipAddress)'

# If no private IP, use connection name:
gcloud sql instances describe waooaw-db --format='value(connectionName)'
# Format: waooaw-oauth:asia-south1:waooaw-db
```

**DB_NAME**:
```
waooaw
```

---

### 3. DNS Configuration (GoDaddy) ⏳
**URL**: https://dcc.godaddy.com/control/waooaw.com/dns

Add 3 A records pointing to **35.190.6.91**:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | demo-www | 35.190.6.91 | 600 |
| A | demo-pp | 35.190.6.91 | 600 |
| A | demo-api | 35.190.6.91 | 600 |

**Note**: DNS propagation takes 5-10 minutes

---

### 4. SSL Certificate (GCP) ⏳
```bash
gcloud compute ssl-certificates create waooaw-ssl-cert-v2 \
  --domains=www.waooaw.com,pp.waooaw.com,api.waooaw.com,demo-www.waooaw.com,demo-pp.waooaw.com,demo-api.waooaw.com \
  --global

# Verify creation
gcloud compute ssl-certificates list
```

**Note**: SSL provisioning takes 15-30 minutes after DNS is configured

---

### 5. OAuth Configuration (Google Console) ⏳
**URL**: https://console.cloud.google.com/apis/credentials/oauthclient/270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq

Click "Edit" on your OAuth client, then add these **Authorized redirect URIs**:

```
https://demo-api.waooaw.com/auth/callback
https://demo-www.waooaw.com/auth/callback
https://demo-pp.waooaw.com/auth/callback
http://localhost:8000/auth/callback
```

Click "Save"

---

### 6. Load Balancer Configuration ⏳
**Do this AFTER first GitHub Actions deployment succeeds**

```bash
# After Cloud Run services are deployed, get their URLs
gcloud run services describe waooaw-api-demo --region=asia-south1 --format='value(status.url)'
gcloud run services describe waooaw-portal-demo --region=asia-south1 --format='value(status.url)'
gcloud run services describe waooaw-platform-portal-demo --region=asia-south1 --format='value(status.url)'

# Update Load Balancer backend services to point demo-* domains to these services
# This requires Load Balancer reconfiguration - see cloud/gcp/TARGET_ARCHITECTURE.md
```

---

## 🚀 Deployment Timeline

| Step | Task | Time | Status |
|------|------|------|--------|
| 1 | Run infrastructure script | 5 min | ✅ Done |
| 2 | Create Cloud SQL instance | 5 min | ⏳ **Next** |
| 3 | Setup database schema | 2 min | ⏳ Pending |
| 4 | Add GitHub secrets | 3 min | ⏳ **Critical** |
| 5 | Configure DNS (GoDaddy) | 2 min | ⏳ Pending |
| 6 | Create SSL certificate | 1 min | ⏳ Pending |
| 7 | Update OAuth (Google) | 2 min | ⏳ Pending |
| 8 | Trigger GitHub Actions | 1 min | ⏳ Pending |
| 9 | Wait for deployment | 10 min | ⏳ Pending |
| 10 | Configure Load Balancer | 5 min | ⏳ Pending |
| 11 | Wait for DNS/SSL propagation | 10 min | ⏳ Pending |
| 12 | Verify deployment | 5 min | ⏳ Pending |
| **Total** | | **~50 min** | **80% done** |

---

## ⚡ Quick Start Commands

Run these in order:

```bash
# 1. Create Cloud SQL instance (5 min wait)
gcloud sql instances create waooaw-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --root-password=ChangeMe123! \
  --storage-type=SSD \
  --storage-size=10GB \
  --availability-type=ZONAL

# 2. Setup database (after Cloud SQL is ready)
gcloud sql connect waooaw-db --user=postgres --quiet < scripts/deployment/setup-demo-database.sql

# 3. Get DB host for GitHub secret
gcloud sql instances describe waooaw-db --format='value(ipAddresses[0].ipAddress)'

# 4. Get service account key for GitHub secret
cat /workspaces/WAOOAW/github-actions-key.json

# 5. Create SSL certificate
gcloud compute ssl-certificates create waooaw-ssl-cert-v2 \
  --domains=www.waooaw.com,pp.waooaw.com,api.waooaw.com,demo-www.waooaw.com,demo-pp.waooaw.com,demo-api.waooaw.com \
  --global

# 6. After GitHub secrets are added, trigger deployment
git commit --allow-empty -m "chore: trigger deployment"
git push

# 7. Monitor deployment
# https://github.com/dlai-sd/WAOOAW/actions

# 8. After deployment, verify
./scripts/deployment/verify-demo.sh
```

---

## 🔍 Verification Steps

After all steps complete:

```bash
# Check Cloud SQL
gcloud sql instances list

# Check Artifact Registry
gcloud artifacts repositories list --location=asia-south1

# Check Secret Manager
gcloud secrets list

# Check Cloud Run services (after deployment)
gcloud run services list --region=asia-south1

# Check DNS
dig +short demo-www.waooaw.com
dig +short demo-pp.waooaw.com
dig +short demo-api.waooaw.com

# Check SSL certificate
gcloud compute ssl-certificates describe waooaw-ssl-cert-v2

# Test endpoints (after deployment)
curl https://demo-api.waooaw.com/health
curl https://demo-www.waooaw.com/
```

---

## 📞 Support

**GitHub Actions Logs**: https://github.com/dlai-sd/WAOOAW/actions  
**GCP Console**: https://console.cloud.google.com/  
**Documentation**: See [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)

---

## ✅ Success Criteria

Deployment is complete when:

- [ ] Cloud SQL instance running
- [ ] Database schema created with 7 agents
- [ ] GitHub secrets configured (GCP_SA_KEY, DB_HOST, DB_NAME)
- [ ] DNS records added in GoDaddy
- [ ] SSL certificate created
- [ ] OAuth redirect URIs configured
- [ ] GitHub Actions workflow succeeds (green checkmark)
- [ ] All 3 Cloud Run services deployed
- [ ] Load Balancer configured
- [ ] DNS resolves to 35.190.6.91
- [ ] `curl https://demo-api.waooaw.com/health` returns success
- [ ] Browser loads https://demo-www.waooaw.com/
- [ ] OAuth flow works end-to-end

---

**Current Status**: Ready for Cloud SQL creation and GitHub secrets configuration 🚀
