#!/bin/bash
set -e

# WAOOAW Database Backup Script
# Creates automated backups of RDS PostgreSQL database

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DB_INSTANCE="waooaw-postgres-${ENVIRONMENT}"
BACKUP_BUCKET="${BACKUP_BUCKET:-waooaw-backups-${ENVIRONMENT}}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

echo -e "${GREEN}💾 WAOOAW Database Backup${NC}"
echo "================================================"
echo "Environment: ${ENVIRONMENT}"
echo "DB Instance: ${DB_INSTANCE}"
echo "Backup Bucket: ${BACKUP_BUCKET}"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi

# Create S3 bucket if not exists
echo "🪣 Checking S3 bucket..."
if ! aws s3 ls "s3://${BACKUP_BUCKET}" 2>/dev/null; then
    echo "Creating backup bucket..."
    aws s3 mb "s3://${BACKUP_BUCKET}" --region ${AWS_REGION}
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket ${BACKUP_BUCKET} \
        --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket ${BACKUP_BUCKET} \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }'
    
    # Set lifecycle policy
    aws s3api put-bucket-lifecycle-configuration \
        --bucket ${BACKUP_BUCKET} \
        --lifecycle-configuration '{
            "Rules": [{
                "Id": "DeleteOldBackups",
                "Status": "Enabled",
                "Prefix": "postgres/",
                "Expiration": {"Days": '${RETENTION_DAYS}'}
            }]
        }'
    
    echo -e "${GREEN}✅ Backup bucket created${NC}"
else
    echo -e "${GREEN}✅ Backup bucket exists${NC}"
fi

# Create RDS snapshot
SNAPSHOT_ID="waooaw-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

echo ""
echo "📸 Creating RDS snapshot..."
echo "Snapshot ID: ${SNAPSHOT_ID}"

aws rds create-db-snapshot \
    --db-instance-identifier ${DB_INSTANCE} \
    --db-snapshot-identifier ${SNAPSHOT_ID} \
    --region ${AWS_REGION} \
    --tags Key=Environment,Value=${ENVIRONMENT} Key=Type,Value=Manual \
    > /dev/null

echo "⏳ Waiting for snapshot to complete..."

aws rds wait db-snapshot-completed \
    --db-snapshot-identifier ${SNAPSHOT_ID} \
    --region ${AWS_REGION}

echo -e "${GREEN}✅ Snapshot created: ${SNAPSHOT_ID}${NC}"

# Get snapshot details
SNAPSHOT_ARN=$(aws rds describe-db-snapshots \
    --db-snapshot-identifier ${SNAPSHOT_ID} \
    --region ${AWS_REGION} \
    --query 'DBSnapshots[0].DBSnapshotArn' \
    --output text)

SNAPSHOT_SIZE=$(aws rds describe-db-snapshots \
    --db-snapshot-identifier ${SNAPSHOT_ID} \
    --region ${AWS_REGION} \
    --query 'DBSnapshots[0].AllocatedStorage' \
    --output text)

echo "Snapshot ARN: ${SNAPSHOT_ARN}"
echo "Size: ${SNAPSHOT_SIZE} GB"

# Export to S3 (optional - for cross-region backup)
if [ "${EXPORT_TO_S3}" = "true" ]; then
    echo ""
    echo "📤 Exporting snapshot to S3..."
    
    EXPORT_TASK_ID="waooaw-export-$(date +%Y%m%d-%H%M%S)"
    
    aws rds start-export-task \
        --export-task-identifier ${EXPORT_TASK_ID} \
        --source-arn ${SNAPSHOT_ARN} \
        --s3-bucket-name ${BACKUP_BUCKET} \
        --s3-prefix "postgres/${SNAPSHOT_ID}/" \
        --iam-role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/rds-s3-export-role" \
        --kms-key-id "alias/aws/rds" \
        --region ${AWS_REGION} \
        > /dev/null || echo -e "${YELLOW}⚠️  S3 export failed (IAM role may not exist)${NC}"
fi

# Create metadata file
METADATA_FILE="/tmp/backup-metadata-${SNAPSHOT_ID}.json"

cat > ${METADATA_FILE} << EOF
{
  "snapshot_id": "${SNAPSHOT_ID}",
  "snapshot_arn": "${SNAPSHOT_ARN}",
  "db_instance": "${DB_INSTANCE}",
  "environment": "${ENVIRONMENT}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "size_gb": ${SNAPSHOT_SIZE},
  "type": "manual"
}
EOF

# Upload metadata
aws s3 cp ${METADATA_FILE} \
    "s3://${BACKUP_BUCKET}/postgres/${SNAPSHOT_ID}/metadata.json" \
    --region ${AWS_REGION}

echo ""
echo "================================================"
echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo ""
echo "Snapshot: ${SNAPSHOT_ID}"
echo "Metadata: s3://${BACKUP_BUCKET}/postgres/${SNAPSHOT_ID}/metadata.json"
echo ""
echo "Restore with:"
echo "  ./scripts/restore_database.sh ${SNAPSHOT_ID}"
echo ""

# Clean old snapshots (keep last N)
KEEP_SNAPSHOTS=7

echo "🧹 Cleaning old snapshots (keeping last ${KEEP_SNAPSHOTS})..."

OLD_SNAPSHOTS=$(aws rds describe-db-snapshots \
    --db-instance-identifier ${DB_INSTANCE} \
    --snapshot-type manual \
    --region ${AWS_REGION} \
    --query "reverse(sort_by(DBSnapshots[?starts_with(DBSnapshotIdentifier, 'waooaw-${ENVIRONMENT}-')], &SnapshotCreateTime))[${KEEP_SNAPSHOTS}:].DBSnapshotIdentifier" \
    --output text)

if [ -n "${OLD_SNAPSHOTS}" ]; then
    for snapshot in ${OLD_SNAPSHOTS}; do
        echo "Deleting old snapshot: ${snapshot}"
        aws rds delete-db-snapshot \
            --db-snapshot-identifier ${snapshot} \
            --region ${AWS_REGION} \
            > /dev/null
    done
    echo -e "${GREEN}✅ Old snapshots cleaned${NC}"
else
    echo "No old snapshots to clean"
fi

echo ""
