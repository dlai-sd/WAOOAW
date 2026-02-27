#!/bin/bash
# Note: Using 'set -e' removed - will handle errors gracefully instead

echo "🚀 WAOOAW Development Environment Setup"
echo ""

# Install additional system packages (non-critical)
echo "📦 Installing optional system dependencies..."
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq \
    build-essential \
    curl \
    wget \
    vim \
    jq \
    tree \
    postgresql-server-dev-15 \
    libpq-dev \
    2>/dev/null || echo "⚠️ Some packages unavailable (non-critical)"

echo "✅ System setup attempted"
echo "ℹ️  Google Cloud SDK is installed via devcontainer feature (google-cloud-cli)"

# Wait for PostgreSQL to be ready
echo ""
echo "⏳ Waiting for PostgreSQL to start..."
RETRY_COUNT=0
MAX_RETRIES=30
until pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; do
  RETRY_COUNT=$((RETRY_COUNT+1))
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "⚠️  PostgreSQL did not start in time. Continuing anyway..."
    break
  fi
  sleep 1
done

if pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
  echo "✅ PostgreSQL is ready"
else
  echo "⚠️  PostgreSQL may not be fully ready yet - will initialize on first use"
fi

# Simple database setup (if PostgreSQL is ready)
if pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
    echo "🗄️  Initializing databases..."
    
    # Create development database (ignore errors if already exists)
    psql -h localhost -U postgres -d postgres -c "CREATE DATABASE waooaw_plant_dev;" 2>/dev/null || true
    psql -h localhost -U postgres -d postgres -c "CREATE DATABASE waooaw_plant_test;" 2>/dev/null || true
    
    # Enable extensions (ignore errors if already enabled)
    psql -h localhost -U postgres -d waooaw_plant_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true
    psql -h localhost -U postgres -d waooaw_plant_dev -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" 2>/dev/null || true
    psql -h localhost -U postgres -d waooaw_plant_test -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true
    psql -h localhost -U postgres -d waooaw_plant_test -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" 2>/dev/null || true
    
    echo "✅ Database initialization attempted"
else
    echo "⏳ PostgreSQL will initialize on next manual start"
fi

# Install Python dependencies for Plant backend (optional, can be done manually)
echo "📦 Python dependencies can be installed with: bash scripts/init-local-db.sh"

# Create local .env file
echo "📝 Creating local environment file..."
cat > /workspaces/WAOOAW/src/Plant/BackEnd/.env.local << 'ENVEOF'
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=waooaw_dev_password
ENVEOF

echo "✅ Setup complete! Next steps:"
echo ""
echo "1. Initialize database: bash scripts/init-local-db.sh"
echo "2. Start server: bash scripts/start-local-server.sh"
echo "3. Run tests: bash scripts/run-local-tests.sh"
echo ""
echo "   Database: $POSTGRES_DB @ $POSTGRES_HOST:$POSTGRES_PORT"
echo "   API Docs: http://localhost:8000/docs"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
SERVEREOF

chmod +x /workspaces/WAOOAW/scripts/start-local-server.sh

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ WAOOAW Development Environment Ready!                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 PostgreSQL 15 with pgvector installed"
echo "   • Dev Database:  waooaw_plant_dev"
echo "   • Test Database: waooaw_plant_test"
echo "   • Connection:    postgresql://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev"
echo ""
echo "🛠️  Quick Commands:"
echo "   • Initialize DB:    bash scripts/init-local-db.sh"
echo "   • Run Tests:        bash scripts/run-local-tests.sh"
echo "   • Start Server:     bash scripts/start-local-server.sh"
echo "   • Connect to DB:    psql -h localhost -U postgres waooaw_plant_dev"
echo ""
echo "📝 Environment file: src/Plant/BackEnd/.env.local"
echo ""
