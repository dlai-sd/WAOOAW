#!/bin/bash

# WAOOAW v2 Demo Infrastructure Setup Script
# Run this BEFORE GitHub Actions deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_ID="waooaw-oauth"
REGION="asia-south1"
DB_INSTANCE="waooaw-db"

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  WAOOAW v2 Demo Infrastructure Setup${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Check if gcloud is authenticated
echo -e "${YELLOW}1. Checking GCP Authentication${NC}"
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo -e "${GREEN}✓ Authenticated as: ${ACCOUNT}${NC}"
else
    echo -e "${RED}✗ Not authenticated. Run: gcloud auth login${NC}"
    exit 1
fi

# Set project
echo -e "\n${YELLOW}2. Setting Project${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set to: ${PROJECT_ID}${NC}"

# Create Artifact Registry
echo -e "\n${YELLOW}3. Creating Artifact Registry${NC}"
if gcloud artifacts repositories describe waooaw --location=$REGION &>/dev/null; then
    echo -e "${GREEN}✓ Artifact Registry already exists${NC}"
else
    echo "Creating Artifact Registry..."
    gcloud artifacts repositories create waooaw \
        --repository-format=docker \
        --location=$REGION \
        --description="WAOOAW Docker images" || true
    echo -e "${GREEN}✓ Artifact Registry created${NC}"
fi

# Create secrets in Secret Manager
echo -e "\n${YELLOW}4. Creating Secret Manager Secrets${NC}"
echo -e "${CYAN}You'll need to provide values for the following secrets:${NC}"

# DB_USER
if gcloud secrets describe DB_USER &>/dev/null; then
    echo -e "${GREEN}✓ DB_USER already exists${NC}"
else
    read -p "Enter DB_USER (default: postgres): " db_user
    db_user=${db_user:-postgres}
    echo -n "$db_user" | gcloud secrets create DB_USER --data-file=-
    echo -e "${GREEN}✓ DB_USER created${NC}"
fi

# DB_PASSWORD
if gcloud secrets describe DB_PASSWORD &>/dev/null; then
    echo -e "${GREEN}✓ DB_PASSWORD already exists${NC}"
else
    read -sp "Enter DB_PASSWORD: " db_password
    echo
    echo -n "$db_password" | gcloud secrets create DB_PASSWORD --data-file=-
    echo -e "${GREEN}✓ DB_PASSWORD created${NC}"
fi

# JWT_SECRET
if gcloud secrets describe JWT_SECRET &>/dev/null; then
    echo -e "${GREEN}✓ JWT_SECRET already exists${NC}"
else
    echo "Generating random JWT_SECRET..."
    jwt_secret=$(openssl rand -base64 32)
    echo -n "$jwt_secret" | gcloud secrets create JWT_SECRET --data-file=-
    echo -e "${GREEN}✓ JWT_SECRET created${NC}"
fi

# GOOGLE_CLIENT_ID
if gcloud secrets describe GOOGLE_CLIENT_ID &>/dev/null; then
    echo -e "${GREEN}✓ GOOGLE_CLIENT_ID already exists${NC}"
else
    echo -e "${YELLOW}Get this from Google Cloud Console > APIs & Services > Credentials${NC}"
    read -p "Enter GOOGLE_CLIENT_ID: " google_client_id
    echo -n "$google_client_id" | gcloud secrets create GOOGLE_CLIENT_ID --data-file=-
    echo -e "${GREEN}✓ GOOGLE_CLIENT_ID created${NC}"
fi

# GOOGLE_CLIENT_SECRET
if gcloud secrets describe GOOGLE_CLIENT_SECRET &>/dev/null; then
    echo -e "${GREEN}✓ GOOGLE_CLIENT_SECRET already exists${NC}"
else
    read -sp "Enter GOOGLE_CLIENT_SECRET: " google_client_secret
    echo
    echo -n "$google_client_secret" | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-
    echo -e "${GREEN}✓ GOOGLE_CLIENT_SECRET created${NC}"
fi

# Grant Cloud Run access to secrets
echo -e "\n${YELLOW}5. Granting Cloud Run Access to Secrets${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SA_EMAIL="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for secret in DB_USER DB_PASSWORD JWT_SECRET GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet || true
    echo -e "${GREEN}✓ Granted access to ${secret}${NC}"
done

# Database schema setup
echo -e "\n${YELLOW}6. Database Schema Setup${NC}"
echo -e "${CYAN}Run these commands manually in Cloud SQL:${NC}"
echo ""
echo "gcloud sql connect $DB_INSTANCE --user=postgres"
echo ""
echo "Then run:"
echo "CREATE SCHEMA IF NOT EXISTS demo;"
echo "SET search_path TO demo;"
echo "-- Create your tables here"
echo ""
echo -e "${YELLOW}⚠ Database schema creation requires manual setup${NC}"

# DNS Configuration
echo -e "\n${YELLOW}7. DNS Configuration${NC}"
echo -e "${CYAN}Add these DNS records in GoDaddy:${NC}"
echo ""
echo "Type: A"
echo "Name: demo-www"
echo "Value: 35.190.6.91"
echo "TTL: 600"
echo ""
echo "Type: A"
echo "Name: demo-pp"
echo "Value: 35.190.6.91"
echo "TTL: 600"
echo ""
echo "Type: A"
echo "Name: demo-api"
echo "Value: 35.190.6.91"
echo "TTL: 600"
echo ""
echo -e "${YELLOW}⚠ DNS configuration requires manual setup in GoDaddy${NC}"

# SSL Certificate
echo -e "\n${YELLOW}8. SSL Certificate${NC}"
echo -e "${CYAN}Create 6-domain SSL certificate:${NC}"
echo ""
echo "gcloud compute ssl-certificates create waooaw-ssl-cert-v2 \\"
echo "  --domains=www.waooaw.com,pp.waooaw.com,api.waooaw.com,demo-www.waooaw.com,demo-pp.waooaw.com,demo-api.waooaw.com \\"
echo "  --global"
echo ""
echo -e "${YELLOW}⚠ SSL certificate creation requires manual setup${NC}"

# OAuth Configuration
echo -e "\n${YELLOW}9. OAuth Configuration${NC}"
echo -e "${CYAN}Add these redirect URIs in Google Cloud Console:${NC}"
echo ""
echo "https://demo-api.waooaw.com/auth/callback"
echo "https://demo-www.waooaw.com/auth/callback"
echo "https://demo-pp.waooaw.com/auth/callback"
echo "http://localhost:8000/auth/callback (for development)"
echo ""
echo -e "${YELLOW}⚠ OAuth configuration requires manual setup in Google Console${NC}"

# GitHub Secrets
echo -e "\n${YELLOW}10. GitHub Secrets${NC}"
echo -e "${CYAN}Add these secrets to GitHub repository:${NC}"
echo ""
echo "GCP_SA_KEY - Service account JSON key with roles:"
echo "  - Cloud Run Admin"
echo "  - Artifact Registry Writer"
echo "  - Secret Manager Secret Accessor"
echo ""
echo "DB_HOST - Cloud SQL private IP (e.g., 10.x.x.x)"
echo "DB_NAME - waooaw"
echo ""
echo -e "${YELLOW}⚠ GitHub secrets require manual setup in repository settings${NC}"

# Summary
echo -e "\n${CYAN}============================================${NC}"
echo -e "${CYAN}  Setup Summary${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}✓ Completed:${NC}"
echo "  - GCP authentication verified"
echo "  - Artifact Registry created"
echo "  - Secret Manager secrets created"
echo "  - Cloud Run service account permissions granted"
echo ""
echo -e "${YELLOW}⚠ Manual steps required:${NC}"
echo "  - Database schema creation (Cloud SQL)"
echo "  - DNS records (GoDaddy)"
echo "  - SSL certificate (gcloud)"
echo "  - OAuth redirect URIs (Google Console)"
echo "  - GitHub secrets (repository settings)"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "1. Complete manual steps listed above"
echo "2. GitHub Actions will deploy on next push to feature/* branch"
echo "3. Run ./scripts/deployment/verify-demo.sh after deployment"
echo ""
echo -e "${GREEN}Setup script completed!${NC}"
