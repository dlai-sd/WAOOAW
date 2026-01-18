# Session Context: January 16, 2026 - Plant Database Migration Workflow

## Problem Summary

Attempted to create GitHub Actions workflow (`plant-db-migrations.yml`) to run Alembic migrations on Cloud SQL PostgreSQL database. **Workflow fails because Cloud SQL instance only has private IP and GitHub Actions runners cannot access it.**

### Error Chain

1. **Initial Error (Run 21074654676)**: Missing `-dir` flag for Cloud SQL Proxy
   ```
   must set -dir: using a unix socket for waooaw-oauth:asia-south1:plant-sql-demo
   ```
   - Fixed in PR #136: Added `-dir=/cloudsql` flag

2. **Permission Error (Run 21074981876)**: Cannot create root-level directory
   ```
   mkdir: cannot create directory '/cloudsql': Permission denied
   ```
   - Fixed in PR #137: Added `sudo mkdir -p /cloudsql` and `sudo chmod 777 /cloudsql`

3. **VPC/Private IP Error (Run 21075277151)**: Database unreachable from external runner
   ```
   connection to server on socket "/cloudsql/.../plant-sql-demo/.s.PGSQL.5432" failed: 
   server closed the connection unexpectedly
   This probably means the server terminated abnormally before or while processing the request.
   ```
   - **ROOT CAUSE**: Cloud SQL instance has `ipv4_enabled: false` (no public IP)
   - **Impact**: GitHub Actions runners are external and cannot reach private VPC network

---

## Architecture Analysis

### Cloud SQL Configuration (Terraform)

**File**: `cloud/terraform/modules/cloud-sql/main.tf`

```terraform
ip_configuration {
  ipv4_enabled    = false # No public IP
  private_network = var.private_network_id
  require_ssl     = true
}
```

- **IP Address**: 10.19.0.3 (PRIVATE only)
- **Network**: projects/waooaw-oauth/global/networks/default
- **SSL Mode**: TRUSTED_CLIENT_CERTIFICATE_REQUIRED

### Why Cloud SQL Proxy Failed

Cloud SQL Proxy **requires public IP or VPC access**:
- ✅ Works from Cloud Run (has VPC connector access)
- ✅ Works from Cloud Shell/Compute Engine (inside VPC)
- ❌ **Fails from GitHub Actions** (external runner, no VPC access)

### Current State

**Database**: Exists with 6 tables created manually during Session 5 (Jan 15)

From commit `6611295` (Jan 15):
```
Session 5 achievements:
- ✅ Plant deployed to Cloud Run (revision 00003-pww)
- ✅ 6 database tables initialized
- ✅ 13 API endpoints functional
```

Tables likely created from Cloud Shell using `create_tables.py` or Alembic migrations.

**Available Files**:
- SQLAlchemy Models: `src/Plant/BackEnd/models/` (7 files: base_entity, skill, job_role, team, agent, industry, trial)
- Alembic Migrations: `src/Plant/BackEnd/database/migrations/versions/` (7 migration files)
- Scripts: `migrate-db.sh`, `seed-db.sh`, `create_tables.py`

---

## What We Did (This Session)

### PRs Created

1. **PR #130** (closed): Attempted to use GitHub environment secrets for DATABASE_URL
   - ❌ Wrong approach: DATABASE_URL stored in GCP Secret Manager, not GitHub

2. **PR #131** (closed): Duplicate of #130

3. **PR #132** (merged): Fetch DATABASE_URL from GCP Secret Manager
   - ✅ Correct pattern: `gcloud secrets versions access latest --secret="demo-plant-database-url"`

4. **PR #133** (closed): Remove push trigger attempt 1

5. **PR #134** (merged): Consolidated fix
   - ✅ Remove push trigger (manual dispatch only)
   - ✅ Fix `migrate-db.sh` and `seed-db.sh` to check $DATABASE_URL env first
   - ✅ Add documentation to Deployment Agent

6. **PR #135** (closed): Duplicate

7. **PR #136** (merged): Add `-dir=/cloudsql` flag to Cloud SQL Proxy
   - ✅ Fixed proxy unix socket creation command
   - ✅ Applied to all 3 environments (demo/uat/prod)

8. **PR #137** (merged): Add sudo for /cloudsql directory creation
   - ✅ GitHub Actions runners need sudo for root-level directories
   - ✅ Added `sudo chmod 777 /cloudsql` for write access

### Workflow Evolution

**File**: `.github/workflows/plant-db-migrations.yml`

Final proxy setup (still fails due to private IP):
```yaml
- name: Set up Cloud SQL Proxy
  run: |
    wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
    chmod +x cloud_sql_proxy
    sudo mkdir -p /cloudsql
    sudo chmod 777 /cloudsql
    ./cloud_sql_proxy -dir=/cloudsql -instances=${{ env.CONNECTION_NAME }} &
    sleep 10
```

### Scripts Fixed

Both scripts now follow **env-first pattern**:

**`migrate-db.sh`** and **`seed-db.sh`**:
```bash
if [ -z "$DATABASE_URL" ]; then
  # Load from .env.$ENVIRONMENT file
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "✅ Using DATABASE_URL from environment"
fi
```

---

## Next Steps

### Option 1: Enable Public IP (NOT RECOMMENDED)

Change Terraform to allow external connections:
```terraform
ip_configuration {
  ipv4_enabled    = true  # Enable public IP
  authorized_networks = [
    {
      name  = "github-actions"
      value = "CIDR_RANGE"  # GitHub Actions IP ranges
    }
  ]
  private_network = var.private_network_id
  require_ssl     = true
}
```

**Why NOT recommended**: Security risk, opens database to internet.

### Option 2: Cloud Run Job for Migrations (RECOMMENDED)

Create Cloud Run Job that runs inside VPC (same as backend):

**Benefits**:
- ✅ Has VPC connector access to private Cloud SQL
- ✅ Same security model as backend
- ✅ Can be triggered from GitHub Actions via `gcloud run jobs execute`
- ✅ No public IP needed

**Implementation**:
1. Create Dockerfile for migration job
2. Add Terraform module for Cloud Run Job
3. Configure with same VPC connector as backend
4. Update workflow to trigger job instead of running migrations directly

### Option 3: Run Migrations Locally (TEMPORARY)

For immediate needs, run migrations from Cloud Shell:

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project waooaw-oauth

# Activate Cloud Shell

# Clone repo
git clone https://github.com/dlai-sd/WAOOAW.git
cd WAOOAW/src/Plant/BackEnd

# Get DATABASE_URL from Secret Manager
export DATABASE_URL=$(gcloud secrets versions access latest --secret="demo-plant-database-url")

# Run migrations
python -m alembic upgrade head

# Or create tables
python create_tables.py

# Seed data
python seed_genesis_data.py
```

---

## Technical Details

### Secret Management Pattern

**Flow**: Terraform → GCP Secret Manager → GitHub Actions → Scripts

1. **Terraform creates database** (plant-db-infra.yml workflow)
   - Reads `PLANT_DB_PASSWORD` from GitHub environment secret
   - Creates Cloud SQL instance with user/database
   - Stores `DATABASE_URL` in GCP Secret Manager as `{env}-plant-database-url`

2. **GitHub Actions fetches at runtime** (plant-db-migrations.yml workflow)
   ```yaml
   - name: Fetch DATABASE_URL from Secret Manager
     run: |
       DATABASE_URL=$(gcloud secrets versions access latest \
         --secret="${{ inputs.environment }}-plant-database-url" \
         --project=waooaw-oauth)
       echo "DATABASE_URL=$DATABASE_URL" >> $GITHUB_ENV
   ```

3. **Scripts use environment variable**
   ```bash
   if [ -z "$DATABASE_URL" ]; then
     source .env.$ENVIRONMENT  # Fallback for local dev
   fi
   ```

### DATABASE_URL Format

```
postgresql+asyncpg://plant_app:PASSWORD@/plant?host=/cloudsql/waooaw-oauth:asia-south1:plant-sql-demo
```

- Driver: `asyncpg` (async PostgreSQL driver)
- User: `plant_app`
- Database: `plant`
- Host: Unix socket via Cloud SQL Proxy

### Cloud SQL Proxy Requirements

**For external runners** (GitHub Actions):
- ✅ `-dir` flag for unix socket directory
- ✅ sudo access for /cloudsql creation
- ❌ **Public IP on Cloud SQL instance** (missing)

**For internal services** (Cloud Run):
- ✅ VPC Serverless Connector
- ✅ Private IP access (10.19.0.0/16 range)
- ✅ Cloud SQL Proxy sidecar annotation

---

## Repository Files Referenced

### Workflows
- `.github/workflows/plant-db-migrations.yml` - Migration workflow (fails)
- `.github/workflows/plant-db-infra.yml` - Terraform database provisioning (works)

### Scripts
- `src/Plant/BackEnd/scripts/migrate-db.sh` - Alembic migration runner
- `src/Plant/BackEnd/scripts/seed-db.sh` - Genesis data seeder
- `src/Plant/BackEnd/create_tables.py` - SQLAlchemy table creation
- `src/Plant/BackEnd/migrate_db.py` - Direct migration helper

### Terraform
- `cloud/terraform/stacks/plant/main.tf` - Plant stack orchestration
- `cloud/terraform/modules/cloud-sql/main.tf` - Database module (ipv4_enabled: false)
- `cloud/terraform/modules/vpc-connector/main.tf` - VPC connector for Cloud Run

### Models & Migrations
- `src/Plant/BackEnd/models/` - SQLAlchemy models (7 entities)
- `src/Plant/BackEnd/database/migrations/versions/` - Alembic migrations (7 files)

### Documentation
- `infrastructure/CI_Pipeline/Waooaw Cloud Deployment Agent.md` - Updated with DB script pattern

---

## Recommendations

**Immediate (Today)**:
- Use Cloud Shell to run migrations manually (Option 3)
- Document the process for team reference

**Short-term (This Week)**:
- Implement Cloud Run Job for migrations (Option 2)
- Update workflows to trigger job via gcloud

**Long-term**:
- Consider self-hosted runner in GCP for CI/CD
- Evaluate Workload Identity Federation for better auth

---

## Session Notes

**Duration**: ~3 hours  
**PRs Created**: 8 (5 merged, 3 closed)  
**Workflow Runs**: 5+ failed attempts  
**Root Cause Identified**: Private-only Cloud SQL instance incompatible with external GitHub runners  
**Status**: Blocked on infrastructure decision (public IP vs Cloud Run Job)
