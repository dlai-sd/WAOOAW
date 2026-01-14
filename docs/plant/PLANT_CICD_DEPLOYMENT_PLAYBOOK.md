# Plant Phase - CI/CD Deployment Playbook
**Version**: 1.0  
**Created**: January 14, 2026  
**Status**: Ready for Demo Deployment  
**Audience**: DevOps Engineers, Platform Engineers

---

## Key Learning Points (Start Here)

Before executing this playbook, understand these critical patterns:

### 1. Shared Infrastructure Pattern (Cost-Optimized)
- **One static IP, one HTTPS LB, one grouped SSL cert** serves CP, PP, and Plant
- **Reason**: Cost optimization ($18-25/month vs $54-75 for 3 separate LBs)
- **Implication**: SSL cert updates affect all three when domains change

### 2. Terraform State Isolation (Deployment Safety)
- **Separate stacks** = separate state files = independent deployments
- `foundation` stack: LB, SSL cert, routing (changes rarely)
- `plant` stack: Cloud SQL, Cloud Run, NEG (changes often)
- `cp`/`pp` stacks: Unaffected by Plant deployments
- **Guardrail**: Never use `terraform -target` in CI

### 3. Bootstrap Sequence (Chicken-and-Egg Prevention)
**CRITICAL ORDER** (cannot be reversed):
1. Deploy **Plant app stack FIRST** (creates NEG, writes output to state)
2. Enable `enable_plant = true` in foundation tfvars
3. Apply **foundation SECOND** (reads Plant NEG from remote state, adds routing)

**Why?** Foundation uses `terraform_remote_state.plant.outputs.backend_negs`. If you enable before Plant exists, foundation plan fails with "object has no attribute backend_negs".

### 4. SSL Certificate Recreation (Graceful, No Downtime)
When we add Plant domains to foundation:
- **New cert** created (PROVISIONING status) while **old cert** remains ACTIVE
- **Old cert** serves CP/PP traffic during 15-60 min provisioning window
- **Terraform guarantee**: `create_before_destroy` prevents orphaned certs
- **Result**: Zero downtime, CP/PP uninterrupted
- **Proven**: PP deployment (Jan 13, 2026) validated this pattern

### 5. Database Isolation from LB/SSL
- Cloud SQL instance creation is **completely independent** from LB changes
- Database can be deployed anytime without affecting CP/PP
- **Best practice**: Deploy DB first (Batch 2), LB changes last (Batch 4)

### 6. Environment Variables and Secrets Management
- Database password stored in GitHub secrets per environment
- Never commit passwords or connection strings
- Use GitHub environment-specific secrets for sensitive data
- Terraform reads from secrets at apply time

---

## Deployment Checklist (Pre-Flight)

- [ ] Plant backend code complete (`src/Plant/BackEnd/`)
- [ ] Alembic migrations ready (`database/migrations/versions/0001_initial_plant_schema.py`)
- [ ] Seed data script ready (`database/seed_data.py`)
- [ ] Terraform code ready (`cloud/terraform/stacks/plant/`, modules)
- [ ] Workflows ready (`.github/workflows/plant-db-*.yml`)
- [ ] GitHub demo environment created with `PLANT_DB_PASSWORD` secret
- [ ] GCP project `waooaw-oauth` verified, region `asia-south1` confirmed
- [ ] Have copy of strong password in secure location
- [ ] CP/PP currently operational on shared LB (baseline established)

---

## BATCH 1: Prepare Infrastructure Code (No GCP Changes)

### Objective
Prepare all code changes needed before touching infrastructure. This batch creates scripts, updates Terraform configs, and commits changes.

### Step 1.1: Create Migration Scripts

**What**: Create shell scripts that will be called by `plant-db-migrations.yml` workflow

**Files to Create**:
- `src/Plant/BackEnd/scripts/migrate-db.sh`
- `src/Plant/BackEnd/scripts/seed-db.sh`

**Script: migrate-db.sh**
```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-demo}
PYTHONPATH=. alembic -c alembic.ini upgrade head
echo "✅ Database migration completed for $ENVIRONMENT"
```

**Script: seed-db.sh**
```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-demo}
python -m database.seed_data
echo "✅ Seed data completed for $ENVIRONMENT"
```

**Make executable**:
```bash
chmod +x src/Plant/BackEnd/scripts/migrate-db.sh
chmod +x src/Plant/BackEnd/scripts/seed-db.sh
```

**Verification**:
```bash
ls -lh src/Plant/BackEnd/scripts/
# Both files should have -rwxr-xr-x permissions
```

### Step 1.2: Update Foundation Stack for Plant

**What**: Modify foundation Terraform to prepare for Plant routing (don't apply yet)

**Files to Update**:

**1. `cloud/terraform/stacks/foundation/variables.tf`** - Add Plant enable flag:
```hcl
variable "enable_plant" {
  description = "Enable Plant backend component and routing"
  type        = bool
  default     = false
}
```

**2. `cloud/terraform/stacks/foundation/main.tf`** - Add Plant remote state + backend service + routing:
```hcl
# Read Plant backend NEG from remote state
data "terraform_remote_state" "plant" {
  count   = var.enable_plant ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/${var.environment}/plant"
  }
}

# Create Plant backend service (reads NEG from remote state)
resource "google_compute_backend_service" "plant_backend" {
  count = var.enable_plant ? 1 : 0
  name  = "waooaw-plant-backend-${var.environment}"
  
  backend {
    group = data.terraform_remote_state.plant[0].outputs.backend_negs.plant_backend.self_link
  }
  
  health_checks = [google_compute_health_check.https_hc.id]
  port_name     = "http"
}

# Add Plant to URL map
resource "google_compute_url_map_path_rule" "plant" {
  count     = var.enable_plant ? 1 : 0
  url_map   = google_compute_url_map.main.name
  path_rule = "plant.${var.environment}.waooaw.com/*"
  service   = google_compute_backend_service.plant_backend[0].self_link
}
```

**3. `cloud/terraform/stacks/foundation/main.tf`** - Extend SSL cert domains:
```hcl
# Modify ssl_certificates to include Plant domains
locals {
  all_domains = concat(
    ["cp.${var.environment}.waooaw.com", "pp.${var.environment}.waooaw.com"],
    var.enable_plant ? ["plant.${var.environment}.waooaw.com"] : []
  )
  
  domain_hash = substr(md5(join(",", sort(local.all_domains))), 0, 8)
}

resource "google_compute_managed_ssl_certificate" "shared" {
  name = "waooaw-shared-ssl-${local.domain_hash}"
  
  managed {
    domains = local.all_domains
  }
  
  lifecycle {
    create_before_destroy = true
  }
}
```

**Verification**:
```bash
cd cloud/terraform/stacks/foundation
terraform fmt -check
terraform init -backend=false
terraform validate
# All checks should pass
```

### Step 1.3: Commit All Changes

**What**: Save all code changes to git for tracking

**Command**:
```bash
git add src/Plant/BackEnd/scripts/
git add cloud/terraform/stacks/foundation/
git add docs/plant/PLANT_BLUEPRINT.yaml

git commit -m "feat(plant): prepare infrastructure for demo deployment

- Add migrate-db.sh and seed-db.sh scripts
- Update foundation stack to conditionally support Plant routing
- Extend SSL cert domains to include plant.demo.waooaw.com
- Reference: PLANT_CICD_DEPLOYMENT_PLAYBOOK.md"

git push origin feature/plant-frontend-backend-scaffold
```

**Expected Output**:
- Commit hash displayed
- Branch updated on GitHub
- CI checks run (should be green: fmt, validate)

**Verification**:
```bash
git log --oneline -1
# Should show your commit message
```

---

## BATCH 2: Deploy Plant App Stack (Creates DB + Backend Service)

### Objective
Create Cloud SQL instance, Plant backend Cloud Run service, and NEG. This is infrastructure creation with zero impact on CP/PP.

### Step 2.1: Set GitHub Secrets

**What**: Store database password in GitHub demo environment

**Actions**:
1. Go to GitHub repo: https://github.com/dlai-sd/WAOOAW
2. Settings → Secrets and variables → Actions
3. Under "Environments" select `demo`
4. Click "Add environment secret"
5. Name: `PLANT_DB_PASSWORD`
6. Value: `Waooaw!2026_Plant#demo` (or your preferred strong password)
7. Save

**Verification**:
- Secret appears in demo environment secrets list
- Value shows as masked `***` in UI

**Security Note**: Store password copy in secure location (password manager, 1Password, etc.)

### Step 2.2: Run Plant DB Infrastructure Workflow - PLAN

**What**: Preview infrastructure changes before creating them

**Actions**:
1. Go to GitHub repo → Actions tab
2. Select "Plant - Database Infrastructure" workflow
3. Click "Run workflow"
4. Fill in:
   - `environment`: `demo`
   - `terraform_action`: `plan`
5. Click "Run workflow"

**Expected Output**:
```
Terraform Plan Summary:
  + google_sql_database_instance.postgres (plant-sql-demo)
  + google_sql_database.database (plant DB)
  + google_sql_user.user (plant_app user)
  + google_secret_manager_secret.database_url
  + google_cloud_run_v2_service (waooaw-plant-backend-demo)
  + google_compute_region_network_endpoint_group (plant_backend NEG)

Plan: 6 to add, 0 to change, 0 to destroy
Time: ~2 min
```

**Verification**:
- Workflow completes with green checkmark ✅
- Plan artifact uploaded: `plant-demo-tfplan`
- Resource count shows "Plan: 6 to add"
- No errors in logs

**⚠️ CP/PP Status**: Still fully operational, no changes

### Step 2.3: Review Plan (Optional but Recommended)

**What**: Download and review the Terraform plan to ensure resources are correct

**Actions**:
1. In workflow run, download artifact `plant-demo-tfplan`
2. Review locally:
   ```bash
   terraform show plant-demo-tfplan | grep -E "^(resource|#)"
   ```

**Verification**: Plan shows only Plant resources, no CP/PP changes

### Step 2.4: Apply Plant Stack

**What**: Actually create Cloud SQL + Plant backend in GCP

**Actions**:
1. Go to GitHub Actions → "Plant - Database Infrastructure"
2. Click "Run workflow"
3. Fill in:
   - `environment`: `demo`
   - `terraform_action`: `apply`
4. Click "Run workflow"

**Expected Output** (~10-15 min for Cloud SQL creation):
```
Terraform Apply Summary:
  + google_sql_database_instance.postgres (plant-sql-demo)
    CREATED - Instance state: RUNNABLE
  + google_sql_database.database
    CREATED - Database: plant
  + google_sql_user.user
    CREATED - User: plant_app
  + google_secret_manager_secret.database_url
    CREATED - Secret stored in Secret Manager
  + google_cloud_run_v2_service (waooaw-plant-backend-demo)
    CREATED - Service URL: https://waooaw-plant-backend-demo-<hash>.a.run.app
  + google_compute_region_network_endpoint_group
    CREATED - NEG for load balancer integration

Apply complete! Resources: 6 added

Outputs:
  database_instance_name: plant-sql-demo
  database_connection_name: waooaw-oauth:asia-south1:plant-sql-demo
  database_url_secret_id: demo-plant-database-url
  plant_backend_url: https://waooaw-plant-backend-demo-<hash>.a.run.app
  local_proxy_command: cloud-sql-proxy waooaw-oauth:asia-south1:plant-sql-demo=tcp:5432
```

**Verification**:
```bash
# Check Cloud SQL instance
gcloud sql instances describe plant-sql-demo --project=waooaw-oauth
# Status should be: RUNNABLE

# Check Cloud Run service
gcloud run services describe waooaw-plant-backend-demo \
  --region=asia-south1 --project=waooaw-oauth
# Status should be: Active

# Check NEG exists
gcloud compute network-endpoint-groups list --project=waooaw-oauth | grep plant
# Should show: plant_backend NEG
```

**⚠️ Auto-Trigger**: Workflow automatically triggers `plant-db-migrations.yml` for demo env

---

## BATCH 3: Run Database Migrations + Seed Data

### Objective
Apply schema migrations to Cloud SQL and seed with sample data (50 agents, industries, skills, etc.)

### Step 3.1: Verify Migration Workflow Auto-Triggered

**What**: Confirm that database migrations started automatically from Step 2.4

**Actions**:
1. Go to GitHub Actions tab
2. Look for "Plant Backend - Database Migrations" workflow
3. Should be running or recently completed

**Expected Output**:
```
Workflow: Plant Backend - Database Migrations
  Job: migrate-demo
  Steps:
    ✅ Checkout code
    ✅ Set up Python (3.11)
    ✅ Install dependencies
    ✅ Authenticate to Google Cloud
    ✅ Set up Cloud SQL Proxy
    ✅ Run migrations (alembic upgrade head)
    ✅ Seed Genesis data (python -m database.seed_data)
    ✅ Verify migration

Duration: ~5 min
Status: ✅ All steps green
```

**Verification** (in workflow logs):
```
2026-01-14 15:45:32 INFO: Running migration 0001_initial_plant_schema...
2026-01-14 15:45:38 INFO: ✅ Migration successful
2026-01-14 15:45:40 INFO: Starting seed data insertion...
2026-01-14 15:45:42 INFO: Inserted 3 industries
2026-01-14 15:45:43 INFO: Inserted 19 skills
2026-01-14 15:45:44 INFO: Inserted 10 job roles
2026-01-14 15:45:45 INFO: Inserted 6 teams
2026-01-14 15:45:47 INFO: Inserted 50 agents
2026-01-14 15:45:50 INFO: ✅ Demo database migration verified
```

**⚠️ CP/PP Status**: Still unaffected, database internal to Plant

### Step 3.2: Verify Database Tables and Data

**What**: Manually check that schema and seed data are correct

**Actions**:
```bash
# Start Cloud SQL Proxy (if not running)
cloud-sql-proxy waooaw-oauth:asia-south1:plant-sql-demo=tcp:5432 &

# Connect to database
export PGPASSWORD='<password>'
psql -h 127.0.0.1 -U plant_app -d plant

# Check tables exist
\dt
# Expected output:
# base_entity, skill_entity, job_role_entity, team_entity, agent_entity, industry_entity

# Check data counts
SELECT COUNT(*) FROM agent_entity;
# Expected: 50

SELECT COUNT(*) FROM industry_entity;
# Expected: 3

SELECT COUNT(*) FROM skill_entity;
# Expected: 19

# View sample agent
SELECT id, name, status FROM agent_entity LIMIT 3;
# Expected: 3 rows with agent names and status='active'
```

**Verification**:
- All 6 tables exist
- agent_entity has 50 records
- industry_entity has 3 records
- All records have status='active'

---

## BATCH 4: Wire Plant to Shared Load Balancer (Affects SSL)

### Objective
Connect Plant backend to the shared HTTPS load balancer and expand SSL certificate. This is where we modify shared infrastructure, so extra care needed.

### ⚠️ Critical Notes Before Proceeding
- This is the **only batch** that affects CP/PP infrastructure
- SSL cert will be recreated (cert replacement, not downtime)
- Old cert remains valid during provisioning (15-60 min)
- CP/PP traffic uninterrupted
- **Do not** run this during peak traffic hours if possible

### Step 4.1: Enable Plant in Foundation

**What**: Update foundation configuration to include Plant routing

**File**: `cloud/terraform/stacks/foundation/environments/default.tfvars`

**Change**:
```hcl
# Before
enable_plant = false

# After
enable_plant = true
```

**Command**:
```bash
cd cloud/terraform/stacks/foundation

# Edit the file
nano environments/default.tfvars
# Change enable_plant = false to enable_plant = true

# Commit change
git add environments/default.tfvars
git commit -m "feat(foundation): enable Plant routing for demo

- Add plant.demo.waooaw.com to LB routing
- Extend SSL cert to include Plant domain"

git push
```

**Verification**:
```bash
grep "enable_plant" cloud/terraform/stacks/foundation/environments/default.tfvars
# Should show: enable_plant = true
```

### Step 4.2: Foundation PLAN (Review Only)

**What**: Preview all LB/SSL changes before applying

**Actions**:
1. Go to GitHub Actions → "WAOOAW Deploy - Foundation (Shared LB)"
2. Click "Run workflow"
3. Fill in: `terraform_action: plan`
4. Click "Run workflow"

**Expected Output**:
```
Terraform Plan Summary:
  + google_compute_backend_service.plant_backend (new)
    CREATED - Backend service for Plant
  
  +/- google_compute_managed_ssl_certificate.shared (recreate)
    Old: waooaw-shared-ssl-779b788b (cp.demo, pp.demo)
    New: waooaw-shared-ssl-<new-hash> (cp.demo, pp.demo, plant.demo)
  
  ~ google_compute_target_https_proxy (update)
    ssl_certificates: [old cert] → [new cert]
  
  ~ google_compute_url_map (update)
    + host_rule: plant.demo.waooaw.com

Plan: 1 to add, 2 to change, 1 to destroy
Time: ~2 min
```

**Review Checklist**:
- [ ] Only Plant-related changes shown
- [ ] CP/PP backend services have NO changes
- [ ] SSL cert name different (hash changed)
- [ ] URL map adds plant.demo.waooaw.com rule
- [ ] Create-before-destroy lifecycle on SSL cert

**Verification**:
- Workflow completes green ✅
- Plan shows correct resource changes
- No CP/PP backend service changes

### Step 4.3: Foundation APPLY (Live Infrastructure Change)

**What**: Apply LB/SSL changes, add Plant routing, create new cert

**⚠️ WARNING**: This modifies shared infrastructure. Have CP/PP monitoring ready.

**Actions**:
1. Go to GitHub Actions → "WAOOAW Deploy - Foundation (Shared LB)"
2. Click "Run workflow"
3. Fill in: `terraform_action: apply`
4. Click "Run workflow"

**Expected Output** (~5-10 min):
```
Terraform Apply Summary:
  + google_compute_backend_service.plant_backend
    CREATED - Plant backend service registered
  
  +/- google_compute_managed_ssl_certificate.shared
    Creating: waooaw-shared-ssl-<new-hash> (status: PROVISIONING)
    Updating: HTTPS proxy references new cert
    Destroying: waooaw-shared-ssl-779b788b (old cert)
    Status: create_before_destroy lifecycle ensures safety

Apply complete! Resources: 1 added, 2 changed, 1 destroyed

Summary:
  ✅ Plant backend service added to LB
  ✅ New SSL cert created (PROVISIONING)
  ✅ Old SSL cert deleted (safe)
  ✅ URL map updated (plant.demo.waooaw.com routing added)
```

**Verification** (Immediate, after apply):
```bash
# Check SSL cert status
gcloud compute ssl-certificates list --project=waooaw-oauth
# Should show:
# - waooaw-shared-ssl-<new-hash> (PROVISIONING)
# - waooaw-shared-ssl-779b788b (should be gone or deleting)

# Check URL map
gcloud compute url-maps describe waooaw-shared-lb-url-map --global --project=waooaw-oauth | grep -A 5 "hostRule"
# Should show new rule for plant.demo.waooaw.com

# Test CP/PP still work (critical!)
curl -s -I https://cp.demo.waooaw.com/health | head -1
# Expected: HTTP/2 200
curl -s -I https://pp.demo.waooaw.com/health | head -1
# Expected: HTTP/2 200
```

**⚠️ Expected Behavior During Cert Provisioning**:
- New cert status: `PROVISIONING`
- Old cert: Deleted (but was active until new cert ready)
- CP/PP traffic: **Continues uninterrupted**
- Plant traffic: **Not yet accessible** (cert still provisioning)

---

## BATCH 5: Verify Plant Accessibility via Load Balancer

### Objective
Wait for SSL cert to become ACTIVE, then verify all three portals work together.

### Step 5.1: Wait for SSL Certificate ACTIVE Status

**What**: Monitor SSL cert provisioning (15-60 min typically)

**Actions**:
```bash
# Check status every 5 minutes
watch -n 300 'gcloud compute ssl-certificates describe waooaw-shared-ssl-<new-hash> --global --project=waooaw-oauth | grep -E "(name|status|managed.status)"'
```

**Expected Output**:
```
Initial (5 min): status: PROVISIONING
After 15-30 min: status: PROVISIONING (still provisioning)
Final (15-60 min): status: ACTIVE ← Ready!
```

**Verification**:
```bash
# Query once
gcloud compute ssl-certificates describe waooaw-shared-ssl-<new-hash> \
  --global --project=waooaw-oauth --format="value(status)"
# When output shows: ACTIVE
# Then proceed to Step 5.2
```

**🎯 Key Point**: You can do other work during this wait. CP/PP remain fully operational.

### Step 5.2: Test Plant via Load Balancer Domain

**What**: Verify Plant is accessible through shared LB via public domain

**Actions**:
```bash
# Test Plant health endpoint
curl -i https://plant.demo.waooaw.com/health

# Test Plant agents API
curl -i https://plant.demo.waooaw.com/api/v1/agents/ | jq . | head -20

# Test Plant backend directly (should also work)
PLANT_BACKEND_URL="https://waooaw-plant-backend-demo-<hash>.a.run.app"
curl -i $PLANT_BACKEND_URL/health
```

**Expected Output**:
```
HTTP/2 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "database": "connected",
  "version": "0.1.0"
}
```

**Verification**:
- Health endpoint returns 200 OK
- Response includes database connection status
- Agent list returns JSON array of 50 agents

### Step 5.3: Final Verification - All Three Portals

**What**: Confirm CP, PP, and Plant all work simultaneously on shared LB

**Actions**:
```bash
# Test all three portals
echo "Testing CP..."
curl -I https://cp.demo.waooaw.com/health

echo "Testing PP..."
curl -I https://pp.demo.waooaw.com/health

echo "Testing Plant..."
curl -I https://plant.demo.waooaw.com/health
```

**Expected Output**:
```
Testing CP...
HTTP/2 200 OK

Testing PP...
HTTP/2 200 OK

Testing Plant...
HTTP/2 200 OK
```

**Verification**:
- [ ] CP health endpoint: 200 OK
- [ ] PP health endpoint: 200 OK
- [ ] Plant health endpoint: 200 OK
- [ ] All domains resolve via single IP (35.190.6.91)
- [ ] All use same SSL certificate

**Final Status**:
```
✅ Plant Phase Demo Deployment COMPLETE
✅ 50 agents seeded in database
✅ Plant backend accessible via https://plant.demo.waooaw.com
✅ CP/PP uninterrupted throughout deployment
✅ Shared LB routing all three components
```

---

## Post-Deployment Actions

### 1. Document Completion
```bash
# Create a deployment log
cat > PLANT_DEPLOYMENT_LOG_DEMO.md << 'EOF'
# Plant Demo Deployment - Completed
Date: $(date)
Deployed by: <your-name>
Status: ✅ SUCCESS

## Outcomes
- Cloud SQL instance: plant-sql-demo (RUNNABLE)
- Plant backend service: waooaw-plant-backend-demo (ACTIVE)
- Database schema: 0001_initial_plant_schema (applied)
- Seed data: 50 agents, 3 industries, 19 skills, 10 job roles (inserted)
- Load balancer: plant.demo.waooaw.com routing (ACTIVE)
- SSL certificate: includes plant.demo.waooaw.com (ACTIVE)

## URLs
- Plant direct: https://waooaw-plant-backend-demo-<hash>.a.run.app
- Plant via LB: https://plant.demo.waooaw.com
- Database connection: waooaw-oauth:asia-south1:plant-sql-demo
EOF

git add PLANT_DEPLOYMENT_LOG_DEMO.md
git commit -m "docs(plant): log demo deployment completion"
git push
```

### 2. Update Foundation Documentation
Update `/infrastructure/CI_Pipeline/UNIFIED_ARCHITECTURE.md` with Plant integration details

### 3. Create UAT/Prod Deployment Plans
Repeat this playbook for UAT and production environments (when ready)

---

## Troubleshooting Guide

### Issue: SSL Certificate Stuck in PROVISIONING

**Symptom**: After 2+ hours, cert status still PROVISIONING

**Cause**: Domain validation issue or DNS propagation delay

**Fix**:
```bash
# Check cert validation status
gcloud compute ssl-certificates describe waooaw-shared-ssl-<new-hash> \
  --global --project=waooaw-oauth --format="value(managed.status)"

# If validation not progressing, consider:
# - Ensure DNS A records point to load balancer IP
# - Wait additional 30-60 minutes (GCP can take 1-2 hours)
# - Check GCP Cloud Console for SSL cert validation details
```

### Issue: Plant Backend Returns 503 Service Unavailable

**Symptom**: `curl https://plant.demo.waooaw.com` returns 503

**Likely Cause**: Cloud SQL Proxy connection failed, database unreachable

**Fix**:
```bash
# Check Cloud Run service logs
gcloud run services describe waooaw-plant-backend-demo \
  --region=asia-south1 --project=waooaw-oauth \
  --format="value(status.conditions[].message)"

# Check if Cloud SQL instance is RUNNABLE
gcloud sql instances describe plant-sql-demo --project=waooaw-oauth

# Verify DATABASE_URL secret is accessible
gcloud secrets versions access latest --secret=demo-plant-database-url --project=waooaw-oauth
```

### Issue: CP/PP Traffic Interrupted During Batch 4

**Symptom**: `curl cp.demo.waooaw.com` returns connection error during SSL update

**Likely Cause**: Proxy updated before new cert fully active

**Prevention**: This should not happen due to `create_before_destroy` lifecycle, but if it does:
```bash
# Revert SSL cert to old one temporarily
gcloud compute ssl-certificates list --project=waooaw-oauth
# Find the old cert (before it was deleted)
# If available, update target proxy to reference it
gcloud compute target-https-proxies update waooaw-shared-https-proxy \
  --ssl-certificates=<old-cert-name> \
  --global \
  --project=waooaw-oauth
```

---

## Success Criteria Checklist

- [ ] Cloud SQL instance `plant-sql-demo` is RUNNABLE
- [ ] Plant backend service `waooaw-plant-backend-demo` is ACTIVE
- [ ] Database has 50 agents, 3 industries, 19 skills, 10 job roles
- [ ] SSL cert includes `plant.demo.waooaw.com` and is ACTIVE
- [ ] `https://plant.demo.waooaw.com/health` returns 200 OK
- [ ] `https://plant.demo.waooaw.com/api/v1/agents/` returns JSON array
- [ ] `https://cp.demo.waooaw.com/health` still returns 200 OK
- [ ] `https://pp.demo.waooaw.com/health` still returns 200 OK
- [ ] All three portals share single IP (35.190.6.91)
- [ ] All traffic is HTTPS via grouped SSL cert

---

## Timeline Summary

| Batch | Description | Duration | CP/PP Impact |
|-------|-------------|----------|--------------|
| 1 | Prepare code | 30 min | None |
| 2 | Deploy Plant stack | 15 min | None |
| 3 | Migrate DB + seed | 5 min | None |
| 4 | Wire to LB + SSL | 10 min | Cert recreation (safe) |
| 5 | Verify | 60+ min wait | None |
| **Total** | **Full deployment** | **~2 hours** | **Zero downtime** |

---

## References

- [PLANT_BLUEPRINT.md](./PLANT_BLUEPRINT.yaml) - Architecture and design decisions
- [UNIFIED_ARCHITECTURE.md](/infrastructure/CI_Pipeline/UNIFIED_ARCHITECTURE.md) - Shared LB pattern
- [Terraform Stacks](../../cloud/terraform/stacks/) - Infrastructure as code
- [Workflows](./.github/workflows/) - CI/CD automation

---

**Document Version**: 1.0  
**Last Updated**: January 14, 2026  
**Status**: Ready for Deployment  
**Next Review**: After Plant demo deployment completes
