# GCP Deployment - Setup Requirements

**Purpose:** Checklist of what you need to set up on GCP for automated deployment  
**Date:** January 2, 2026  
**Status:** Ready for implementation

---

## Prerequisites

Before proceeding, you need:

- ✅ Active GCP project (with billing enabled)
- ✅ `gcloud` CLI installed locally
- ✅ Authenticated with your GCP account
- ✅ Owner or Editor permissions on the project

---

## 🎯 What I Need From You (Information)

Please provide these details after setting up GCP resources:

### 1. **GCP Project Information**
```
GCP_PROJECT_ID: (e.g., "waooaw-prod-2026")
GCP_REGION: (e.g., "us-central1", recommend: us-central1 or europe-west1)
GCP_ARTIFACT_REGISTRY_REPO: (e.g., "waooaw-containers")
GCP_ARTIFACT_REGISTRY_LOCATION: (e.g., "us-central1")
```

### 2. **Cloud Build Service Account**
```
CLOUD_BUILD_SERVICE_ACCOUNT_EMAIL: (auto-generated, e.g., "123456789@cloudbuild.gserviceaccount.com")
CLOUD_BUILD_SERVICE_ACCOUNT_KEY: (JSON key file - I'll store in GitHub Secrets)
```

### 3. **Cloud Run Service Account**
```
CLOUD_RUN_SERVICE_ACCOUNT_EMAIL: (e.g., "waooaw-cloud-run@PROJECT_ID.iam.gserviceaccount.com")
CLOUD_RUN_SERVICE_ACCOUNT_KEY: (JSON key file - I'll store in GitHub Secrets)
```

### 4. **Cloud SQL Database**
```
CLOUD_SQL_INSTANCE_NAME: (e.g., "waooaw-postgres-prod")
CLOUD_SQL_CONNECTION_NAME: (e.g., "PROJECT_ID:us-central1:waooaw-postgres-prod")
DATABASE_NAME: (e.g., "waooaw_platform_db")
DATABASE_USER: (e.g., "waooaw_app")
DATABASE_PASSWORD: (auto-generated or your choice)
```

### 5. **Cloud Memorystore (Redis)**
```
REDIS_INSTANCE_NAME: (e.g., "waooaw-redis-prod")
REDIS_HOST: (auto-assigned IP)
REDIS_PORT: (default: 6379)
```

### 6. **GitHub Secrets to Create**
```
GCP_PROJECT_ID
GCP_REGION
ARTIFACT_REGISTRY_REPO
CLOUD_BUILD_SA_KEY (base64 encoded)
CLOUD_RUN_SA_KEY (base64 encoded)
CLOUD_SQL_INSTANCE_NAME
CLOUD_SQL_CONNECTION_NAME
DATABASE_URL (full PostgreSQL connection string)
REDIS_URL (full Redis connection string)
```

---

## 📋 Step-by-Step GCP Setup

### Phase 1: GCP Project & Authentication

**1. Create GCP Project (if needed)**
```bash
# Set your desired project name
PROJECT_NAME="waooaw-platform"
PROJECT_ID="waooaw-platform-2026"  # Must be globally unique

# Create project
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# Set as active project
gcloud config set project $PROJECT_ID

# Enable billing (you must do this in Cloud Console)
# https://console.cloud.google.com/billing
```

**2. Enable Required APIs**
```bash
PROJECT_ID="waooaw-platform-2026"

gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  compute.googleapis.com \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudlogging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  cloudprofiler.googleapis.com \
  --project=$PROJECT_ID
```

**3. Set Default Region**
```bash
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

### Phase 2: Artifact Registry Setup

**1. Create Artifact Registry Repository**
```bash
PROJECT_ID="waooaw-platform-2026"
REPO_NAME="waooaw-containers"
REGION="us-central1"

gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID

# Verify
gcloud artifacts repositories list --project=$PROJECT_ID
```

**2. Configure Docker Authentication**
```bash
gcloud auth configure-docker $REGION-docker.pkg.dev

# Test with a tag (we'll push real images later)
docker tag alpine:latest $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/test:latest
```

### Phase 3: Service Accounts & IAM

**1. Cloud Build Service Account** (usually auto-created, but verify)
```bash
PROJECT_ID="waooaw-platform-2026"

# Get Cloud Build SA email
CLOUD_BUILD_SA=$(gcloud projects describe $PROJECT_ID \
  --format='value(projectNumber)')@cloudbuild.gserviceaccount.com

echo "Cloud Build Service Account: $CLOUD_BUILD_SA"

# Grant permissions to push to Artifact Registry
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$CLOUD_BUILD_SA \
  --role=roles/artifactregistry.writer

# Grant permissions to deploy to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$CLOUD_BUILD_SA \
  --role=roles/run.developer
```

**2. Create Cloud Run Service Account**
```bash
PROJECT_ID="waooaw-platform-2026"
SA_NAME="waooaw-cloud-run"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Create service account
gcloud iam service-accounts create $SA_NAME \
  --display-name="WAOOAW Cloud Run Service Account" \
  --project=$PROJECT_ID

# Grant Cloud SQL client role (for Postgres connection)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/cloudsql.client

# Grant Artifact Registry reader
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/artifactregistry.reader

# Grant Cloud Logging & Monitoring roles (observability)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/logging.logWriter

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/monitoring.metricWriter

# Grant Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/secretmanager.secretAccessor

echo "Cloud Run Service Account: $SA_EMAIL"
```

**3. Create and Download Service Account Keys**
```bash
PROJECT_ID="waooaw-platform-2026"
CLOUD_BUILD_SA=$(gcloud projects describe $PROJECT_ID \
  --format='value(projectNumber)')@cloudbuild.gserviceaccount.com
CLOUD_RUN_SA="waooaw-cloud-run@$PROJECT_ID.iam.gserviceaccount.com"

# Download Cloud Build SA key
gcloud iam service-accounts keys create /tmp/cloud-build-key.json \
  --iam-account=$CLOUD_BUILD_SA

# Download Cloud Run SA key
gcloud iam service-accounts keys create /tmp/cloud-run-key.json \
  --iam-account=$CLOUD_RUN_SA

# Display keys (for copying to GitHub Secrets)
echo "=== Cloud Build Key ==="
cat /tmp/cloud-build-key.json

echo -e "\n=== Cloud Run Key ==="
cat /tmp/cloud-run-key.json

# Base64 encode for GitHub Secrets
echo -e "\n=== Cloud Build Key (base64) ==="
base64 -w 0 /tmp/cloud-build-key.json && echo

echo -e "\n=== Cloud Run Key (base64) ==="
base64 -w 0 /tmp/cloud-run-key.json && echo
```

### Phase 4: Cloud SQL (PostgreSQL)

**1. Create Cloud SQL Instance**
```bash
PROJECT_ID="waooaw-platform-2026"
INSTANCE_NAME="waooaw-postgres-prod"
REGION="us-central1"
DB_VERSION="POSTGRES_15"  # Latest supported
TIER="db-f1-micro"  # Smallest, sufficient for dev/staging

gcloud sql instances create $INSTANCE_NAME \
  --database-version=$DB_VERSION \
  --tier=$TIER \
  --region=$REGION \
  --project=$PROJECT_ID \
  --availability-type=REGIONAL \
  --enable-bin-log \
  --backup-start-time=03:00 \
  --retained-backups-count=7 \
  --transaction-log-retention-days=7

# Verify
gcloud sql instances list --project=$PROJECT_ID
```

**2. Get Connection Name**
```bash
PROJECT_ID="waooaw-platform-2026"
INSTANCE_NAME="waooaw-postgres-prod"

CLOUD_SQL_CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --format='value(connectionName)')

echo "Cloud SQL Connection Name: $CLOUD_SQL_CONNECTION_NAME"
```

**3. Create Database & User**
```bash
PROJECT_ID="waooaw-platform-2026"
INSTANCE_NAME="waooaw-postgres-prod"
DB_NAME="waooaw_platform_db"
DB_USER="waooaw_app"
DB_PASSWORD=$(openssl rand -base64 32)  # Generate secure password

# Create database
gcloud sql databases create $DB_NAME \
  --instance=$INSTANCE_NAME \
  --project=$PROJECT_ID

# Create user
gcloud sql users create $DB_USER \
  --instance=$INSTANCE_NAME \
  --password=$DB_PASSWORD \
  --project=$PROJECT_ID

echo "Database User: $DB_USER"
echo "Database Password: $DB_PASSWORD"
echo "Keep the password safe - you'll need it for DATABASE_URL"

# Generate DATABASE_URL
echo "DATABASE_URL: postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CLOUD_SQL_CONNECTION_NAME"
```

**4. Configure Cloud SQL Proxy**
```bash
PROJECT_ID="waooaw-platform-2026"
INSTANCE_NAME="waooaw-postgres-prod"
CLOUD_RUN_SA="waooaw-cloud-run@$PROJECT_ID.iam.gserviceaccount.com"

# Create Cloud SQL client certificate
gcloud sql ssl-certs create prod-cert \
  --instance=$INSTANCE_NAME \
  --project=$PROJECT_ID

# Cloud Run will use Cloud SQL Proxy sidecar (configured in deployment)
```

### Phase 5: Cloud Memorystore (Redis)

**1. Create Redis Instance**
```bash
PROJECT_ID="waooaw-platform-2026"
REDIS_NAME="waooaw-redis-prod"
REGION="us-central1"
TIER="basic"
SIZE_GB=1

gcloud redis instances create $REDIS_NAME \
  --size=$SIZE_GB \
  --region=$REGION \
  --tier=$TIER \
  --redis-version=7.0 \
  --project=$PROJECT_ID

# Verify
gcloud redis instances list --project=$PROJECT_ID
```

**2. Get Redis Connection Info**
```bash
PROJECT_ID="waooaw-platform-2026"
REDIS_NAME="waooaw-redis-prod"
REGION="us-central1"

# Get host and port
gcloud redis instances describe $REDIS_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(host,port)'

# This will output: [HOST] 6379
# REDIS_URL will be: redis://[HOST]:6379
```

---

## 🔐 GitHub Secrets Setup

Once you have all GCP information, create GitHub Secrets:

**Navigate to:** Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value | Source |
|---|---|---|
| `GCP_PROJECT_ID` | Project ID | gcloud config get-value project |
| `GCP_REGION` | us-central1 | Your choice |
| `ARTIFACT_REGISTRY_REPO` | waooaw-containers | Created in Phase 2 |
| `ARTIFACT_REGISTRY_LOCATION` | us-central1 | Same as region |
| `CLOUD_BUILD_SA_KEY` | Base64 encoded key | From /tmp/cloud-build-key.json |
| `CLOUD_RUN_SA_KEY` | Base64 encoded key | From /tmp/cloud-run-key.json |
| `CLOUD_RUN_SA_EMAIL` | Service account email | Cloud Run SA email |
| `CLOUD_SQL_INSTANCE_NAME` | waooaw-postgres-prod | Created in Phase 4 |
| `CLOUD_SQL_CONNECTION_NAME` | PROJECT_ID:REGION:INSTANCE | From Phase 4.2 |
| `DATABASE_URL` | postgresql://user:pass@... | From Phase 4.3 |
| `REDIS_URL` | redis://HOST:6379 | From Phase 5.2 |

---

## ✅ Verification Checklist

After completing all GCP setup:

- [ ] GCP Project created and billing enabled
- [ ] All required APIs enabled
- [ ] Artifact Registry repository created
- [ ] Cloud Build service account configured
- [ ] Cloud Run service account created with roles
- [ ] Service account keys downloaded and base64 encoded
- [ ] Cloud SQL instance running (PostgreSQL 15)
- [ ] Database and user created
- [ ] Cloud SQL connection name obtained
- [ ] Cloud Memorystore Redis instance running
- [ ] All 11 GitHub Secrets created
- [ ] Tested `gcloud auth login` with Cloud Run SA key
- [ ] Tested Docker push to Artifact Registry

---

## 🚀 What I'll Do With This Information

Once you provide the GCP setup details and GitHub Secrets:

1. **Create Cloud Build Pipeline** (`cloudbuild.yaml`)
   - Auto-build backend & frontend Docker images
   - Push to Artifact Registry
   - Run tests in Cloud Build environment
   - Deploy to Cloud Run

2. **Create Cloud Deploy Configuration** (`clouddeploy.yaml`)
   - Staging → Production deployment targets
   - Automated approval gates
   - Blue-green deployment strategy
   - Rollback triggers

3. **Create GitHub Actions Workflows**
   - `deploy-to-gcp.yml` → Trigger Cloud Build
   - `cloud-run-deploy.yml` → Deploy to staging/prod
   - `image-security-scan.yml` → Scan Docker images before deployment

4. **Create Cloud Run Service Definitions**
   - Backend service (port 8000)
   - Frontend service (port 3000)
   - Environment variables
   - Cloud SQL proxy sidecar
   - Redis connection configuration

5. **Create Infrastructure as Code (Terraform)**
   - Idempotent resource definitions
   - Multi-environment support
   - Secrets management

6. **Create Deployment Runbooks**
   - Manual deployment steps
   - Rollback procedures
   - Troubleshooting guides

---

## 📊 Resource Estimates & Costs

### Monthly Cost Estimate (Development/Staging)

| Service | Config | Est. Monthly Cost |
|---|---|---|
| Cloud Run | 2 services, 2 vCPU, 4GB RAM | $50-80 |
| Cloud SQL | db-f1-micro (shared core) | $3-5 |
| Cloud Memorystore | 1GB basic tier | $10-15 |
| Artifact Registry | 5GB storage | $0.10 |
| Cloud Build | 120 minutes/month included | Free |
| Cloud Logging | <50GB/month | ~$10 |
| **Total** | | **~$75-110** |

### For Production

| Service | Config | Est. Monthly Cost |
|---|---|---|
| Cloud Run | 2 services, 4 vCPU, 8GB RAM | $150-250 |
| Cloud SQL | db-n1-standard-1 (1 vCPU) | $50-80 |
| Cloud Memorystore | 2GB standard tier | $30-40 |
| Artifact Registry | 10GB storage | $0.25 |
| Cloud Build | Auto-triggered on push | $0.30/build (usually <$20) |
| Cloud Logging | <200GB/month | ~$40 |
| Cloud Monitoring | Custom dashboards | ~$30 |
| **Total** | | **~$300-450** |

---

## ⚠️ Important Notes

1. **Keep Service Account Keys Safe**
   - Never commit to git
   - Never share publicly
   - Store in GitHub Secrets only
   - Rotate periodically

2. **Database Password**
   - Generate with `openssl rand -base64 32`
   - Store in GitHub Secrets and GCP Secret Manager
   - Don't commit to repository

3. **Network Security**
   - Cloud SQL requires Cloud SQL proxy for Cloud Run
   - Redis is VPC-peered (no auth by default)
   - Consider VPC Service Controls for production

4. **Monitoring**
   - Enable Cloud Logging for application logs
   - Setup Cloud Monitoring dashboards
   - Configure alerting for key metrics

5. **Backups**
   - Cloud SQL: Automated daily backups (7-day retention)
   - Application data: Back up Redis separately
   - Consider disaster recovery plan

---

## 🆘 Troubleshooting Commands

```bash
# Verify GCP project setup
gcloud config list
gcloud services list --enabled

# Check service account permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --format='value(bindings.role)' \
  --filter="bindings.members:serviceAccount:*"

# Test Cloud SQL connectivity
gcloud sql connect INSTANCE_NAME --user=postgres

# Check Redis instance status
gcloud redis instances describe INSTANCE_NAME --region=REGION

# List deployed Cloud Run services
gcloud run services list

# View Cloud Build logs
gcloud builds log BUILD_ID --stream
```

---

## 📞 Next Steps

1. **Run all GCP setup commands** in phases 1-5
2. **Collect all required information** from the checklist above
3. **Create GitHub Secrets** with the values
4. **Reply with the following:**
   ```
   GCP_PROJECT_ID: [value]
   GCP_REGION: [value]
   CLOUD_SQL_CONNECTION_NAME: [value]
   DATABASE_URL: [value]
   REDIS_URL: [value]
   ARTIFACT_REGISTRY_REPO: [value]
   ```
5. **I will then:**
   - Create all deployment pipelines
   - Generate Cloud Build & Cloud Deploy configs
   - Create GitHub Actions workflows
   - Setup infrastructure-as-code (Terraform)
   - Provide deployment runbooks

---

**Estimated Setup Time:** 30-45 minutes  
**Automated Deployment Time:** 5-10 minutes per deployment
