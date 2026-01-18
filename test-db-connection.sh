#!/bin/bash
set -euo pipefail

echo "=== Testing Cloud SQL Proxy + Database Connection ==="

# Get DATABASE_URL
echo "1. Fetching DATABASE_URL..."
DATABASE_URL=$(gcloud secrets versions access latest --secret="demo-plant-database-url" --project=waooaw-oauth 2>&1)

if [[ "$DATABASE_URL" == *"ERROR"* ]] || [[ -z "$DATABASE_URL" ]]; then
  echo "Failed: $DATABASE_URL"
  exit 1
fi
echo "DATABASE_URL fetched"

# Get connection name
echo "2. Getting connection name..."
CONNECTION_NAME=$(gcloud sql instances describe plant-sql-demo --format="value(connectionName)" --project=waooaw-oauth)
echo "CONNECTION_NAME: $CONNECTION_NAME"

# Download proxy
if [ ! -f "./cloud_sql_proxy" ]; then
  echo "3. Downloading proxy..."
  wget -q https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
  chmod +x cloud_sql_proxy
fi

# Start proxy
echo "4. Starting proxy..."
mkdir -p /tmp/cloudsql
./cloud_sql_proxy -dir=/tmp/cloudsql -instances=$CONNECTION_NAME &
PROXY_PID=$!
sleep 10

# Check socket
SOCKET_PATH="/tmp/cloudsql/$CONNECTION_NAME/.s.PGSQL.5432"
echo "5. Checking socket: $SOCKET_PATH"
if [ -S "$SOCKET_PATH" ]; then
  echo "Socket exists"
else
  echo "Socket NOT found"
  kill $PROXY_PID 2>/dev/null || true
  exit 1
fi

# Test with psql
echo "6. Testing psql..."
export DATABASE_URL
psql "$DATABASE_URL" -c "SELECT version();" || {
  echo "Connection failed"
  kill $PROXY_PID 2>/dev/null || true
  exit 1
}

echo "7. Testing tables..."
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" || echo "Query failed"

# Cleanup
kill $PROXY_PID 2>/dev/null || true
rm -rf /tmp/cloudsql
echo "=== SUCCESS ==="
