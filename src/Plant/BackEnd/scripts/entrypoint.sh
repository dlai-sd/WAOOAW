#!/bin/bash
# Entrypoint script for Plant database migration Cloud Run Job
# Handles different migration operations: baseline, migrate, seed

set -e

OPERATION=${1:-migrate}

echo "🚀 Starting migration operation: $OPERATION"

case "$OPERATION" in
  baseline)
    echo "📍 Marking existing schema as migrated..."
    python -m alembic stamp 005_rls_policies
    echo "✅ Baseline complete - migrations 001-005 marked as applied"
    ;;
  
  migrate)
    echo "🔄 Running database migrations..."
    python -m alembic upgrade head
    echo "✅ Migrations complete"
    ;;
  
  seed)
    echo "🌱 Seeding Genesis data..."
    python database/seed_data.py
    echo "✅ Seed complete"
    ;;
  
  both)
    echo "🔄 Running migrations..."
    python -m alembic upgrade head
    echo "🌱 Seeding Genesis data..."
    python database/seed_data.py
    echo "✅ Both operations complete"
    ;;
  
  *)
    echo "❌ Unknown operation: $OPERATION"
    echo "Valid operations: baseline, migrate, seed, both"
    exit 1
    ;;
esac

echo "🎉 Operation $OPERATION completed successfully"
