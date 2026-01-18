#!/bin/bash
# WAOOAW Plant - Database Migration Script
# Runs Alembic migrations for specified environment
# Usage: ./migrate-db.sh <environment>
# Example: ./migrate-db.sh demo

set -e  # Exit on error

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
  echo "❌ Error: Environment not specified"
  echo "Usage: ./migrate-db.sh <local|demo|uat|prod>"
  exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(local|demo|uat|prod)$ ]]; then
  echo "❌ Error: Invalid environment '$ENVIRONMENT'"
  echo "Valid: local, demo, uat, prod"
  exit 1
fi

echo "🚀 Starting database migration for environment: $ENVIRONMENT"

# Load environment variables (skip if DATABASE_URL already set)
if [ -z "$DATABASE_URL" ]; then
  ENV_FILE=".env.$ENVIRONMENT"
  if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Environment file not found: $ENV_FILE"
    echo "❌ DATABASE_URL not set and .env file missing"
    exit 1
  fi

  set -a  # Export all variables
  source "$ENV_FILE"
  set +a

  echo "✅ Loaded environment from: $ENV_FILE"
else
  echo "✅ Using DATABASE_URL from environment"
fi

echo "   Database: ${DATABASE_URL:0:50}..." # Show first 50 chars only

# Check if Alembic is installed
if ! command -v alembic &> /dev/null; then
  echo "❌ Error: Alembic not installed"
  echo "Run: pip install alembic"
  exit 1
fi

# Check database connectivity (for non-local environments)
if [ "$ENVIRONMENT" != "local" ]; then
  echo "🔌 Checking Cloud SQL connectivity..."
  
  # Extract instance name from DATABASE_URL
  INSTANCE_NAME=$(echo "$CLOUD_SQL_CONNECTION_NAME" | cut -d':' -f3)
  
  # Check if Cloud SQL Proxy is running (optional for Cloud Run, required for local CI)
  # For Cloud Run, this uses Unix socket /cloudsql/PROJECT:REGION:INSTANCE
  echo "   Cloud SQL instance: $INSTANCE_NAME"
fi

# Run migration
echo "📦 Running Alembic migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
  echo "✅ Migration completed successfully for $ENVIRONMENT"
  
  # Log migration event (for audit trail)
  MIGRATION_LOG="database/migrations/migration_log.txt"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $ENVIRONMENT: alembic upgrade head - SUCCESS" >> "$MIGRATION_LOG"
  
  # Show current revision
  echo ""
  echo "📌 Current database revision:"
  alembic current
  
else
  echo "❌ Migration failed for $ENVIRONMENT"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $ENVIRONMENT: alembic upgrade head - FAILED" >> "$MIGRATION_LOG"
  exit 1
fi

echo ""
echo "🎉 Database migration complete!"
