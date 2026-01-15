#!/bin/bash
# Pre-deployment validation for Plant backend
# Tests locally before wasting time on GCP deployment

set -euo pipefail

PROJECT_ID="waooaw-oauth"
ENVIRONMENT="demo"
REGION="asia-south1"

echo "=== Plant Backend Deployment Pre-Check ==="
echo

# 1. Check Cloud SQL instance exists
echo "✓ Checking Cloud SQL instance..."
INSTANCE_NAME=$(/workspaces/WAOOAW/google-cloud-sdk/bin/gcloud sql instances describe plant-sql-${ENVIRONMENT} \
  --project=${PROJECT_ID} \
  --format="value(name)" 2>&1 || echo "NOT_FOUND")

if [ "$INSTANCE_NAME" == "NOT_FOUND" ]; then
  echo "❌ Cloud SQL instance plant-sql-${ENVIRONMENT} not found"
  exit 1
fi
echo "   Instance: $INSTANCE_NAME"

# 2. Check DATABASE_URL secret
echo "✓ Checking DATABASE_URL secret..."
DB_URL=$(/workspaces/WAOOAW/google-cloud-sdk/bin/gcloud secrets versions access latest \
  --secret=${ENVIRONMENT}-plant-database-url \
  --project=${PROJECT_ID} 2>&1 || echo "NOT_FOUND")

if [ "$DB_URL" == "NOT_FOUND" ]; then
  echo "❌ Secret ${ENVIRONMENT}-plant-database-url not found"
  exit 1
fi

# Validate format
if [[ ! "$DB_URL" =~ "?host=/cloudsql/" ]]; then
  echo "❌ DATABASE_URL format incorrect. Expected: ?host=/cloudsql/..."
  echo "   Got: $DB_URL"
  exit 1
fi
echo "   Format: ✓ Unix socket with ?host= parameter"

# 3. Build Docker image
echo "✓ Building Docker image..."
cd /workspaces/WAOOAW/src/Plant/BackEnd
docker build -q -t plant-backend-precheck:latest -f Dockerfile . >/dev/null
echo "   Image built successfully"

# 4. Check Terraform plan
echo "✓ Validating Terraform..."
cd /workspaces/WAOOAW/cloud/terraform/stacks/plant
/workspaces/WAOOAW/terraform init -backend=false -input=false >/dev/null 2>&1
/workspaces/WAOOAW/terraform validate >/dev/null
echo "   Terraform validates successfully"

# 5. Check Cloud Run service config
echo "✓ Checking Cloud Run module..."
TIMEOUT=$(grep "timeout" ../../modules/cloud-run/main.tf | grep -o '"[^"]*"' | tr -d '"')
echo "   Timeout: $TIMEOUT"

if [ "$TIMEOUT" != "300s" ]; then
  echo "⚠️  WARNING: Timeout is $TIMEOUT (expected 300s for Cloud SQL)"
fi

HAS_STARTUP_PROBE=$(grep -c "startup_probe" ../../modules/cloud-run/main.tf || echo 0)
if [ "$HAS_STARTUP_PROBE" -eq 0 ]; then
  echo "⚠️  WARNING: No startup probe configured"
else
  echo "   Startup probe: ✓ Configured"
fi

echo
echo "=== ✅ All pre-checks passed ==="
echo
echo "Ready to deploy with:"
echo "  gh workflow run \"WAOOAW Deploy\" -f environment=${ENVIRONMENT} -f terraform_action=apply"
