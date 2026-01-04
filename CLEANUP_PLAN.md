# Repository Cleanup Plan - Infrastructure Compliance

**Date**: 2025-01-04
**Current State**: Terraform-based deployment operational
**Goal**: Remove obsolete Deployment Manager and old scripts

---

## Summary

Remove all Deployment Manager artifacts and obsolete scripts. Retain:
- Terraform infrastructure (cloud/terraform/)
- Codespace-specific testing tools
- YAML-driven configuration
- Environment-specific documentation

---

## Items to Remove

### 1. cloud/ Directory

**Obsolete Deployment Manager Files**:
- ❌ `cloud/templates/` - .jinja templates for Deployment Manager
  - cloud-run.jinja
  - load-balancer.jinja
  - networking.jinja
- ❌ `cloud/deploy.py` - Deployment Manager Python script (439 lines)
- ❌ `cloud/deploy.py.backup` - Backup of obsolete script
- ❌ `cloud/deploy-simple.sh` - Wrapper for deploy.py
- ❌ `cloud/deploy-gcloud.sh` - Old gcloud-based deployment (354 lines)

**Obsolete Documentation**:
- ❌ `cloud/gcp/` - Old architecture and planning docs
  - BUDGET_ESCALATION_GUIDE.md
  - CICD_ENVIRONMENTS_ANALYSIS.md
  - CODE_REVIEW_SUMMARY.md
  - CURRENT_STATE.md
  - FRESH_START_PLAN.md
  - IMPLEMENTATION_STRATEGY.md
  - TARGET_ARCHITECTURE.md
  - deployment/
  - monitoring/
  - oauth/
  - runbooks/

**Reason**: These are pre-Terraform planning documents. Current state is documented in root-level docs (INFRASTRUCTURE_DEPLOYMENT.md, V2_CURRENT_STATUS.md).

### 2. templates/ Directory (Root Level)

**Agent Templates** (Not infrastructure-related):
- ❌ `templates/event_bus_template.py` - Agent event bus template
- ❌ `templates/new_coe_agent_template.py` - CoE agent template
- ❌ `templates/output_generation_template.py` - Agent output template

**Reason**: These are for WAOOAW agent development (Week 15-18 implementation), not related to cloud infrastructure. Should be in `docs/agents/templates/` if needed.

### 3. scripts/ Directory

**Obsolete Deployment Scripts**:
- ❌ `scripts/deploy_production.sh` - Old production deployment
- ❌ `scripts/rollback_production.sh` - Old rollback mechanism
- ❌ `scripts/setup.sh` - Old setup script
- ❌ `scripts/setup_environment.sh` - Obsolete environment setup
- ❌ `scripts/setup_project.sh` - Old project initialization
- ❌ `scripts/setup_credentials.py` - Replaced by terraform-admin service account
- ❌ `scripts/setup_github_secrets.sh` - Manual secret setup (use GitHub UI)
- ❌ `scripts/setup_monitoring.sh` - Old monitoring setup
- ❌ `scripts/setup_ssl_certificate.sh` - Managed by Terraform now
- ❌ `scripts/update_alb_certificate.sh` - Managed by Terraform now
- ❌ `scripts/configure_dns.sh` - Manual DNS (do via Cloud Console)
- ❌ `scripts/check_deployment_status.sh` - Use `gcloud run services describe`
- ❌ `scripts/check_certificate_status.sh` - Use `gcloud compute ssl-certificates list`

**Obsolete Database Scripts**:
- ❌ `scripts/init_database.py` - Old DB initialization
- ❌ `scripts/init_schema.py` - Old schema setup
- ❌ `scripts/backup_database.sh` - Manual backup (use Cloud SQL automated backups)
- ❌ `scripts/restore_database.sh` - Manual restore
- ❌ `scripts/backup_agent_data.sh` - Agent-specific backup
- ❌ `scripts/disaster_recovery.sh` - Old DR script

**Obsolete Agent/Testing Scripts**:
- ❌ `scripts/agent_roll_call.py` - Agent system test (not infrastructure)
- ❌ `scripts/demo_roll_call.py` - Demo script
- ❌ `scripts/full_platform_test.py` - Platform test (not infra)
- ❌ `scripts/platform_smoke_test.py` - Smoke test
- ❌ `scripts/quick_platform_test.sh` - Quick test
- ❌ `scripts/debug_delivery.py` - Delivery debugging
- ❌ `scripts/generate_training_dataset.py` - ML training data
- ❌ `scripts/issue_capabilities.py` - GitHub issue helper
- ❌ `scripts/create_story_1_4_issues.py` - Story creation
- ❌ `scripts/post_to_issue_101.sh` - Issue posting
- ❌ `scripts/provision_dids.py` - DID provisioning
- ❌ `scripts/maintenance_portal_text.py` - Portal maintenance

**Obsolete Validation**:
- ❌ `scripts/validate_config.py` - Old config validation
- ❌ `scripts/verify_backups.sh` - Backup verification
- ❌ `scripts/verify_infrastructure.py` - Old infra verification

**Obsolete Deployment Directory**:
- ❌ `scripts/deployment/` - Old deployment utilities

---

## Items to Retain

### cloud/ Directory ✅

- ✅ `cloud/terraform/` - Current Terraform infrastructure
  - main.tf, variables.tf, outputs.tf
  - modules/cloud-run/, modules/networking/, modules/load-balancer/
  - environments/demo.tfvars, uat.tfvars, prod.tfvars
  - generate_tfvars.py
- ✅ `cloud/infrastructure.yaml` - YAML configuration source
- ✅ `cloud/cleanup.sh` - Utility to clean up GCP resources
- ✅ `cloud/README.md` - Cloud directory overview
- ✅ `cloud/demo/` - Demo environment docs
  - deploy-demo.sh
  - verify-platform-portal.sh
- ✅ `cloud/uat/` - UAT environment docs
- ✅ `cloud/prod/` - Production environment docs
- ✅ `cloud/test/` - Test scripts

### scripts/ Directory ✅

**Codespace-Specific** (RETAIN):
- ✅ `scripts/test-codespace-oauth.sh` - Tests OAuth in Codespace environment
- ✅ `scripts/test-oauth-locally.sh` - Local OAuth testing

**Infrastructure Verification** (RETAIN):
- ✅ `scripts/verify-platform-portal.sh` - Verifies platform portal deployment

**Documentation**:
- ✅ `scripts/README.md` - Should be updated to reflect retained scripts only

### Root Templates Directory

- ❌ Remove entire `templates/` directory (not infrastructure-related)

---

## Execution Plan

### Phase 1: Create Archive (Safety)

```bash
# Create archive of items to be removed
cd /workspaces/WAOOAW
mkdir -p archive/cleanup-2025-01-04
cp -r cloud/templates archive/cleanup-2025-01-04/
cp -r cloud/gcp archive/cleanup-2025-01-04/
cp -r templates archive/cleanup-2025-01-04/root-templates
cp cloud/deploy*.py cloud/deploy*.sh archive/cleanup-2025-01-04/
```

### Phase 2: Remove Obsolete Files

```bash
# Remove Deployment Manager artifacts
rm -rf cloud/templates/
rm -f cloud/deploy.py cloud/deploy.py.backup
rm -f cloud/deploy-simple.sh cloud/deploy-gcloud.sh

# Remove old planning docs
rm -rf cloud/gcp/

# Remove agent templates
rm -rf templates/

# Remove obsolete scripts
cd scripts/
rm -f deploy_production.sh rollback_production.sh
rm -f setup.sh setup_environment.sh setup_project.sh
rm -f setup_credentials.py setup_github_secrets.sh
rm -f setup_monitoring.sh setup_ssl_certificate.sh
rm -f update_alb_certificate.sh configure_dns.sh
rm -f check_deployment_status.sh check_certificate_status.sh
rm -f init_database.py init_schema.py
rm -f backup_database.sh restore_database.sh
rm -f backup_agent_data.sh disaster_recovery.sh
rm -f agent_roll_call.py demo_roll_call.py
rm -f full_platform_test.py platform_smoke_test.py quick_platform_test.sh
rm -f debug_delivery.py generate_training_dataset.py
rm -f issue_capabilities.py create_story_1_4_issues.py
rm -f post_to_issue_101.sh provision_dids.py
rm -f maintenance_portal_text.py
rm -f validate_config.py verify_backups.sh verify_infrastructure.py
rm -rf deployment/
```

### Phase 3: Update Documentation

**Update scripts/README.md**:
```markdown
# Scripts Directory

## Active Scripts

### Codespace Development
- `test-codespace-oauth.sh` - Test OAuth configuration in GitHub Codespaces
- `test-oauth-locally.sh` - Test OAuth flow locally before cloud deployment

### Infrastructure Verification
- `verify-platform-portal.sh` - Verify platform portal is operational

## Deployment

Infrastructure deployment is managed via Terraform:
- See `cloud/terraform/` for Terraform configuration
- See `cloud/infrastructure.yaml` for environment definitions
- See [INFRASTRUCTURE_DEPLOYMENT.md](../INFRASTRUCTURE_DEPLOYMENT.md) for deployment guide

## Removed Scripts

All obsolete deployment, setup, and testing scripts have been archived.
See `archive/cleanup-2025-01-04/` for historical reference.
```

**Update cloud/README.md**:
```markdown
# Cloud Infrastructure

## Current Implementation

WAOOAW uses **Terraform** for infrastructure as code.

### Key Files

- `infrastructure.yaml` - Single source of truth for all environments
- `terraform/` - Terraform configuration and modules
- `{demo,uat,prod}/` - Environment-specific documentation

### Deployment

See [INFRASTRUCTURE_DEPLOYMENT.md](../INFRASTRUCTURE_DEPLOYMENT.md) for complete deployment guide.

Quick start:
```bash
cd terraform
python generate_tfvars.py
terraform apply -var-file=environments/demo.tfvars
```

### Removed Files

Deployment Manager artifacts (templates/, deploy.py) have been archived.
Terraform is the only supported deployment method.
```

### Phase 4: Commit Changes

```bash
git add -A
git commit -m "chore: remove obsolete Deployment Manager and scripts

- Removed cloud/templates/ (Deployment Manager .jinja files)
- Removed cloud/deploy.py, deploy-simple.sh, deploy-gcloud.sh
- Removed cloud/gcp/ (old planning docs, moved to archive)
- Removed templates/ (agent templates, not infrastructure-related)
- Removed 30+ obsolete scripts from scripts/
- Retained Terraform infrastructure and codespace testing tools
- Updated README files to reflect current state

All removed files archived in archive/cleanup-2025-01-04/"
```

---

## Risk Assessment

**Low Risk**:
- All removed files are obsolete (replaced by Terraform)
- Current infrastructure is fully operational
- Files archived before deletion
- No impact on running services

**Validation**:
- Demo environment continues to serve traffic
- Terraform configuration unchanged
- Codespace development tools retained

---

## Post-Cleanup Verification

```bash
# Verify Terraform still works
cd cloud/terraform
terraform validate
terraform plan -var-file=environments/demo.tfvars

# Verify codespace testing still works
./scripts/test-codespace-oauth.sh

# Verify services operational
curl https://cp.demo.waooaw.com
curl https://pp.demo.waooaw.com
```

---

## Files Removed Summary

- **cloud/**: 6 files/directories (Deployment Manager, old docs)
- **templates/**: 3 Python files (agent templates)
- **scripts/**: 30+ files (obsolete deployment/setup/testing scripts)

**Total**: ~40 files/directories removed

**Retained**:
- cloud/terraform/ (complete)
- cloud/infrastructure.yaml
- scripts/test-codespace-oauth.sh
- scripts/test-oauth-locally.sh
- scripts/verify-platform-portal.sh

