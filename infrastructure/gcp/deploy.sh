#!/bin/bash
# Setup Custom Domain Mappings for WAOOAW Cloud Run Services
# Supports: demo, uat, production environments
# Usage: ./deploy.sh [demo|uat|production]

set -e

PROJECT_ID="waooaw-oauth"
REGION="asia-south1"
ENVIRONMENT="${1:-demo}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌐 WAOOAW Custom Domain Setup - ${ENVIRONMENT}${NC}"
echo "========================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not logged in to gcloud. Run: gcloud auth login${NC}"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID" --quiet

# ==============================================================================
# DOMAIN MAPPING FUNCTION
# ==============================================================================

setup_domain_mapping() {
    local service_name=$1
    local domain=$2

    echo ""
    echo -e "${BLUE}📍 Mapping ${domain} → ${service_name}${NC}"
    
    # Check if mapping already exists
    if gcloud run domain-mappings describe "$domain" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        echo -e "   ${YELLOW}ℹ️  Domain mapping already exists${NC}"
        
        # Get current mapping details
        current_service=$(gcloud run domain-mappings describe "$domain" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(spec.routeName)" 2>/dev/null || echo "unknown")
        
        if [ "$current_service" = "$service_name" ]; then
            echo -e "   ${GREEN}✅ Mapping is correct${NC}"
            return 0
        else
            echo -e "   ${YELLOW}⚠️  Mapped to different service: ${current_service}${NC}"
            echo -e "   ${YELLOW}   Delete and recreate if needed${NC}"
            return 1
        fi
    fi
    
    # Create domain mapping
    echo "   Creating mapping..."
    if gcloud run domain-mappings create \
        --service="$service_name" \
        --domain="$domain" \
        --region="$REGION" \
        --project="$PROJECT_ID" 2>&1 | tee /tmp/domain-mapping-output.txt; then
        echo -e "   ${GREEN}✅ Mapping created successfully${NC}"
        return 0
    else
        echo -e "   ${RED}❌ Failed to create mapping${NC}"
        cat /tmp/domain-mapping-output.txt
        return 1
    fi
}

# ==============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# ==============================================================================

case "$ENVIRONMENT" in
    demo)
        echo -e "${BLUE}Setting up DEMO environment domains...${NC}"
        echo ""
        
        # Demo services
        BACKEND_SERVICE="waooaw-api-demo"
        PORTAL_SERVICE="waooaw-portal-demo"
        PLATFORM_SERVICE="waooaw-platform-portal-demo"
        
        # Demo domains
        API_DOMAIN="demo-api.waooaw.com"
        WWW_DOMAIN="demo-www.waooaw.com"
        PP_DOMAIN="demo-pp.waooaw.com"
        ;;
    
    uat)
        echo -e "${BLUE}Setting up UAT environment domains...${NC}"
        echo ""
        
        # UAT services
        BACKEND_SERVICE="waooaw-api-uat"
        PORTAL_SERVICE="waooaw-portal-uat"
        PLATFORM_SERVICE="waooaw-platform-portal-uat"
        
        # UAT domains
        API_DOMAIN="uat-api.waooaw.com"
        WWW_DOMAIN="uat-www.waooaw.com"
        PP_DOMAIN="uat-pp.waooaw.com"
        ;;
    
    production|prod)
        echo -e "${BLUE}Setting up PRODUCTION environment domains...${NC}"
        echo ""
        
        # Production services
        BACKEND_SERVICE="waooaw-api"
        PORTAL_SERVICE="waooaw-portal"
        PLATFORM_SERVICE="waooaw-platform-portal"
        
        # Production domains
        API_DOMAIN="api.waooaw.com"
        WWW_DOMAIN="www.waooaw.com"
        PP_DOMAIN="pp.waooaw.com"
        ;;
    
    *)
        echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
        echo "Usage: $0 [demo|uat|production]"
        exit 1
        ;;
esac

# ==============================================================================
# MAP DOMAINS
# ==============================================================================

echo -e "${BLUE}🔗 Creating domain mappings...${NC}"

# Backend API
setup_domain_mapping "$BACKEND_SERVICE" "$API_DOMAIN"
api_status=$?

# Customer Portal (Marketplace)
setup_domain_mapping "$PORTAL_SERVICE" "$WWW_DOMAIN"
www_status=$?

# Platform Portal (Internal)
setup_domain_mapping "$PLATFORM_SERVICE" "$PP_DOMAIN"
pp_status=$?

# ==============================================================================
# RESULTS & NEXT STEPS
# ==============================================================================

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📊 Domain Mapping Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Status summary
if [ $api_status -eq 0 ]; then
    echo -e "${GREEN}✅ Backend API: $API_DOMAIN${NC}"
else
    echo -e "${RED}❌ Backend API: $API_DOMAIN${NC}"
fi

if [ $www_status -eq 0 ]; then
    echo -e "${GREEN}✅ Customer Portal: $WWW_DOMAIN${NC}"
else
    echo -e "${RED}❌ Customer Portal: $WWW_DOMAIN${NC}"
fi

if [ $pp_status -eq 0 ]; then
    echo -e "${GREEN}✅ Platform Portal: $PP_DOMAIN${NC}"
else
    echo -e "${RED}❌ Platform Portal: $PP_DOMAIN${NC}"
fi

echo ""
echo -e "${YELLOW}📋 DNS Configuration Required${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "Add these CNAME records to your DNS provider:"
echo ""
echo "  $API_DOMAIN → ghs.googlehosted.com"
echo "  $WWW_DOMAIN → ghs.googlehosted.com"
echo "  $PP_DOMAIN → ghs.googlehosted.com"
echo ""

echo -e "${YELLOW}⏱️  SSL Certificate Provisioning${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "Google will automatically provision SSL certificates."
echo "This can take 15 minutes to 24 hours."
echo ""

echo -e "${BLUE}🔍 Verify domain mappings:${NC}"
echo "  gcloud run domain-mappings list --region=$REGION"
echo ""
echo -e "${BLUE}📊 Check certificate status:${NC}"
echo "  gcloud run domain-mappings describe $API_DOMAIN --region=$REGION"
echo ""

echo -e "${YELLOW}🔐 OAuth Console Configuration${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "Update Google OAuth Console:"
echo ""
echo "Authorized JavaScript Origins:"
echo "  https://$WWW_DOMAIN"
echo "  https://$PP_DOMAIN"
echo ""
echo "Authorized Redirect URIs:"
echo "  https://$API_DOMAIN/auth/callback"
echo ""

# Exit with error if any mapping failed
if [ $api_status -ne 0 ] || [ $www_status -ne 0 ] || [ $pp_status -ne 0 ]; then
    echo -e "${RED}⚠️  Some domain mappings failed. Check errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All domain mappings created successfully!${NC}"
echo ""
