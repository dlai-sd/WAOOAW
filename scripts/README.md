# Scripts Directory

Utility scripts for WAOOAW platform development and testing.

## Active Scripts

### Codespace Development

**test-codespace-oauth.sh**
- Test OAuth configuration in GitHub Codespaces environment
- Verifies CODESPACE_NAME and PORT_FORWARDING_DOMAIN variables
- Checks backend, customer portal, and platform portal URLs
- Validates CORS configuration for Codespace domains
- Provides code snippets for environment detection

**test-oauth-locally.sh**
- Test OAuth flow locally before cloud deployment
- Fetches OAuth secrets from GCP Secret Manager
- Creates .env.local file with credentials
- Starts backend with proper environment variables
- Tests localhost OAuth endpoints

Usage:
```bash
# Test Codespace OAuth
./test-codespace-oauth.sh

# Test local OAuth
./test-oauth-locally.sh
```

### Infrastructure Verification

**verify-platform-portal.sh**
- Verifies platform portal deployment is operational
- Checks HTTP status codes
- Validates response content
- Useful after Terraform deployments

Usage:
```bash
# Verify demo environment
./verify-platform-portal.sh https://pp.demo.waooaw.com

# Verify UAT environment
./verify-platform-portal.sh https://pp.uat.waooaw.com
```

## Deployment

Infrastructure deployment is managed via **Terraform**, not scripts.

See:
- `cloud/terraform/` - Terraform configuration
- `cloud/infrastructure.yaml` - Environment definitions
- [INFRASTRUCTURE_DEPLOYMENT.md](../INFRASTRUCTURE_DEPLOYMENT.md) - Deployment guide

## Removed Scripts

The following obsolete scripts have been archived in `archive/cleanup-2025-01-04/`:

### Deployment & Setup
- deploy_production.sh
- rollback_production.sh
- setup.sh
- setup_environment.sh
- setup_project.sh
- setup_credentials.py
- setup_github_secrets.sh
- setup_monitoring.sh
- setup_ssl_certificate.sh
- update_alb_certificate.sh
- configure_dns.sh
- check_deployment_status.sh
- check_certificate_status.sh

### Database Management
- init_database.py
- init_schema.py
- backup_database.sh
- restore_database.sh
- backup_agent_data.sh
- disaster_recovery.sh

### Testing & Agents
- agent_roll_call.py
- demo_roll_call.py
- full_platform_test.py
- platform_smoke_test.py
- quick_platform_test.sh
- debug_delivery.py
- generate_training_dataset.py

### Validation & Utilities
- validate_config.py
- verify_backups.sh
- verify_infrastructure.py
- issue_capabilities.py
- create_story_1_4_issues.py
- post_to_issue_101.sh
- provision_dids.py
- maintenance_portal_text.py
- deployment/ (directory)

**Reason for Removal**: These scripts are obsolete due to:
1. Migration to Terraform for infrastructure
2. Simplified deployment process
3. Focus on Codespace development workflow
4. Reduced manual intervention

## Development Workflow

### Local Development (Codespace)

```bash
# 1. Test OAuth configuration
./test-codespace-oauth.sh

# 2. Run backend locally
cd ../backend-v2
uvicorn app.main:app --reload --port 8000

# 3. Run customer portal
cd ../frontend
python -m http.server 8080

# 4. Run platform portal
cd ../PlatformPortal-v2
reflex run --port 3000
```

### Cloud Deployment

```bash
# 1. Build Docker images
docker build -t backend-v2:latest backend-v2/
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/backend-v2:latest

# 2. Deploy via Terraform
cd cloud/terraform
terraform apply -var-file=environments/demo.tfvars

# 3. Verify deployment
./verify-platform-portal.sh https://pp.demo.waooaw.com
```

---

**Repository Cleanup**: 2025-01-04  
**Retained Scripts**: 3 (Codespace testing + verification)  
**Archived Scripts**: 30+ (obsolete deployment/setup/testing)
