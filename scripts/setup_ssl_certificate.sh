#!/bin/bash
set -e

# WAOOAW SSL/TLS Certificate Setup
# Request and configure SSL certificate using AWS ACM

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

AWS_REGION="${AWS_REGION:-us-east-1}"
DOMAIN="${DOMAIN:-waooaw.ai}"

echo -e "${GREEN}🔒 WAOOAW SSL Certificate Setup${NC}"
echo "================================================"
echo "Domain: ${DOMAIN}"
echo "Region: ${AWS_REGION}"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi

# Request certificate
echo "📋 Requesting SSL certificate..."

CERT_ARN=$(aws acm request-certificate \
    --domain-name ${DOMAIN} \
    --subject-alternative-names "*.${DOMAIN}" \
    --validation-method DNS \
    --region ${AWS_REGION} \
    --query 'CertificateArn' \
    --output text)

echo -e "${GREEN}✅ Certificate requested: ${CERT_ARN}${NC}"
echo ""

# Wait for validation options
echo "⏳ Waiting for DNS validation records..."
sleep 10

# Get validation records
VALIDATION_RECORDS=$(aws acm describe-certificate \
    --certificate-arn ${CERT_ARN} \
    --region ${AWS_REGION} \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord')

echo "DNS Validation Record:"
echo "${VALIDATION_RECORDS}" | jq '.'
echo ""

# Extract values
RECORD_NAME=$(echo ${VALIDATION_RECORDS} | jq -r '.Name')
RECORD_TYPE=$(echo ${VALIDATION_RECORDS} | jq -r '.Type')
RECORD_VALUE=$(echo ${VALIDATION_RECORDS} | jq -r '.Value')

echo "================================================"
echo -e "${YELLOW}⚠️  ACTION REQUIRED${NC}"
echo ""
echo "Add the following DNS record to validate certificate:"
echo ""
echo "  Type:  ${RECORD_TYPE}"
echo "  Name:  ${RECORD_NAME}"
echo "  Value: ${RECORD_VALUE}"
echo ""
echo "Instructions:"
echo "1. Log in to your DNS provider (Route53, Cloudflare, etc.)"
echo "2. Create a CNAME record with the values above"
echo "3. Wait for DNS propagation (5-30 minutes)"
echo "4. Run: ./scripts/check_certificate_status.sh"
echo ""

# Save certificate ARN
mkdir -p infrastructure/ssl
echo ${CERT_ARN} > infrastructure/ssl/certificate-arn.txt

echo "Certificate ARN saved to: infrastructure/ssl/certificate-arn.txt"
echo ""

# If using Route53, offer automatic creation
read -p "Are you using Route53 for DNS? (yes/no): " USE_ROUTE53

if [ "${USE_ROUTE53}" = "yes" ]; then
    echo ""
    echo "🔍 Looking for hosted zone..."
    
    HOSTED_ZONE_ID=$(aws route53 list-hosted-zones \
        --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
        --output text | cut -d'/' -f3)
    
    if [ -z "${HOSTED_ZONE_ID}" ]; then
        echo -e "${RED}❌ Hosted zone not found for ${DOMAIN}${NC}"
        exit 1
    fi
    
    echo "Found hosted zone: ${HOSTED_ZONE_ID}"
    
    # Create validation record
    echo "📝 Creating DNS validation record..."
    
    cat > /tmp/route53-change.json << EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${RECORD_NAME}",
      "Type": "${RECORD_TYPE}",
      "TTL": 300,
      "ResourceRecords": [{"Value": "${RECORD_VALUE}"}]
    }
  }]
}
EOF
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id ${HOSTED_ZONE_ID} \
        --change-batch file:///tmp/route53-change.json \
        > /dev/null
    
    echo -e "${GREEN}✅ DNS record created${NC}"
    echo ""
    echo "⏳ Waiting for certificate validation (this may take 5-30 minutes)..."
    
    aws acm wait certificate-validated \
        --certificate-arn ${CERT_ARN} \
        --region ${AWS_REGION} || true
    
    # Check status
    STATUS=$(aws acm describe-certificate \
        --certificate-arn ${CERT_ARN} \
        --region ${AWS_REGION} \
        --query 'Certificate.Status' \
        --output text)
    
    if [ "${STATUS}" = "ISSUED" ]; then
        echo -e "${GREEN}✅ Certificate validated successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️  Certificate status: ${STATUS}${NC}"
        echo "Run ./scripts/check_certificate_status.sh to check progress"
    fi
fi

echo ""
echo "================================================"
echo "Next steps:"
echo "1. Wait for certificate to be validated"
echo "2. Update Terraform with certificate ARN"
echo "3. Configure ALB HTTPS listener"
echo "4. Set up DNS A record pointing to ALB"
echo ""
