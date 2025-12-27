#!/bin/bash
set -e

# WAOOAW Database Restore Script
# Restores PostgreSQL database from RDS snapshot

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DB_INSTANCE="waooaw-postgres-${ENVIRONMENT}"

echo -e "${YELLOW}⚠️  WAOOAW Database Restore${NC}"
echo "================================================"
echo -e "${RED}WARNING: This will replace the current database!${NC}"
echo ""

# Get snapshot ID
SNAPSHOT_ID="$1"

if [ -z "${SNAPSHOT_ID}" ]; then
    echo "Usage: $0 <snapshot-id> [new-db-instance-name]"
    echo ""
    echo "Available snapshots:"
    aws rds describe-db-snapshots \
        --db-instance-identifier ${DB_INSTANCE} \
        --region ${AWS_REGION} \
        --query 'reverse(sort_by(DBSnapshots, &SnapshotCreateTime))[:10].[DBSnapshotIdentifier,SnapshotCreateTime,AllocatedStorage]' \
        --output table
    exit 1
fi

# New instance name (optional)
NEW_DB_INSTANCE="${2:-${DB_INSTANCE}-restored-$(date +%Y%m%d-%H%M%S)}"

echo "Snapshot: ${SNAPSHOT_ID}"
echo "Target Instance: ${NEW_DB_INSTANCE}"
echo ""

# Verify snapshot exists
echo "🔍 Verifying snapshot..."
if ! aws rds describe-db-snapshots \
    --db-snapshot-identifier ${SNAPSHOT_ID} \
    --region ${AWS_REGION} \
    > /dev/null 2>&1; then
    echo -e "${RED}❌ Snapshot not found: ${SNAPSHOT_ID}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Snapshot found${NC}"

# Get original DB configuration
echo "📋 Getting DB configuration..."

DB_CLASS=$(aws rds describe-db-instances \
    --db-instance-identifier ${DB_INSTANCE} \
    --region ${AWS_REGION} \
    --query 'DBInstances[0].DBInstanceClass' \
    --output text)

DB_SUBNET_GROUP=$(aws rds describe-db-instances \
    --db-instance-identifier ${DB_INSTANCE} \
    --region ${AWS_REGION} \
    --query 'DBInstances[0].DBSubnetGroup.DBSubnetGroupName' \
    --output text)

SECURITY_GROUPS=$(aws rds describe-db-instances \
    --db-instance-identifier ${DB_INSTANCE} \
    --region ${AWS_REGION} \
    --query 'DBInstances[0].VpcSecurityGroups[*].VpcSecurityGroupId' \
    --output text)

echo "Instance Class: ${DB_CLASS}"
echo "Subnet Group: ${DB_SUBNET_GROUP}"
echo ""

# Confirmation
read -p "Continue with restore? This will create a new DB instance. (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Restore from snapshot
echo ""
echo "📦 Restoring database from snapshot..."

aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier ${NEW_DB_INSTANCE} \
    --db-snapshot-identifier ${SNAPSHOT_ID} \
    --db-instance-class ${DB_CLASS} \
    --db-subnet-group-name ${DB_SUBNET_GROUP} \
    --vpc-security-group-ids ${SECURITY_GROUPS} \
    --publicly-accessible false \
    --multi-az true \
    --storage-encrypted true \
    --enable-cloudwatch-logs-exports postgresql upgrade \
    --tags Key=Environment,Value=${ENVIRONMENT} Key=RestoredFrom,Value=${SNAPSHOT_ID} \
    --region ${AWS_REGION} \
    > /dev/null

echo "⏳ Waiting for database to be available (this may take 10-15 minutes)..."

aws rds wait db-instance-available \
    --db-instance-identifier ${NEW_DB_INSTANCE} \
    --region ${AWS_REGION}

echo -e "${GREEN}✅ Database restored successfully${NC}"

# Get new endpoint
NEW_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier ${NEW_DB_INSTANCE} \
    --region ${AWS_REGION} \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo ""
echo "================================================"
echo -e "${GREEN}✅ Restore completed!${NC}"
echo ""
echo "New Instance: ${NEW_DB_INSTANCE}"
echo "Endpoint: ${NEW_ENDPOINT}"
echo ""
echo "Next steps:"
echo "1. Test the restored database"
echo "2. Update application configuration with new endpoint"
echo "3. Switch over when ready"
echo "4. Delete old instance when confirmed working"
echo ""
echo "Switch over:"
echo "  # Update ECS task definitions with new endpoint"
echo "  # Or rename instances (requires downtime)"
echo ""
echo "Delete old instance (when ready):"
echo "  aws rds delete-db-instance --db-instance-identifier ${DB_INSTANCE} --skip-final-snapshot"
echo ""
