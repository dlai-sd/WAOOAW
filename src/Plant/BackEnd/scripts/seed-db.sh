#!/bin/bash
# WAOOAW Plant - Database Seeding Script
# Seeds Genesis baseline data (4 skills) for specified environment
# Usage: ./seed-db.sh <environment>
# Example: ./seed-db.sh demo

set -e

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
  echo "❌ Error: Environment not specified"
  echo "Usage: ./seed-db.sh <local|demo|uat|prod>"
  exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(local|demo|uat|prod)$ ]]; then
  echo "❌ Error: Invalid environment '$ENVIRONMENT'"
  exit 1
fi

echo "🌱 Starting database seeding for environment: $ENVIRONMENT"

# Load environment variables (skip if DATABASE_URL already set in CI)
if [ -z "$DATABASE_URL" ]; then
  ENV_FILE=".env.$ENVIRONMENT"
  if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Environment file not found: $ENV_FILE"
    exit 1
  fi

  set -a
  source "$ENV_FILE"
  set +a

  echo "✅ Loaded environment: $ENV_FILE"
else
  echo "✅ Using DATABASE_URL from environment (CI mode)"
fi

# Run seeding script
echo "🌱 Seeding Genesis baseline data..."
python -c "
import sys
sys.path.insert(0, '.')
from database.init_db import seed_genesis_data
from core.database import SessionLocal

db = SessionLocal()
try:
    seed_genesis_data(db)
    print('✅ Genesis data seeded successfully')
except Exception as e:
    print(f'❌ Seeding failed: {e}')
    sys.exit(1)
finally:
    db.close()
"

if [ $? -eq 0 ]; then
  echo "✅ Seeding completed for $ENVIRONMENT"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $ENVIRONMENT: seed_genesis_data - SUCCESS" >> "database/migrations/migration_log.txt"
else
  echo "❌ Seeding failed for $ENVIRONMENT"
  exit 1
fi

echo "🎉 Database seeding complete!"
