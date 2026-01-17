#!/bin/bash
set -euo pipefail

# Add gcloud to PATH
export PATH=/workspaces/WAOOAW/google-cloud-sdk/bin:$PATH

echo "1. Fetch DATABASE_URL"
DATABASE_URL=$(gcloud secrets versions access latest --secret="demo-plant-database-url" --project=waooaw-oauth)
echo "Got URL"

echo "2. Get connection name"
CONNECTION_NAME=$(gcloud sql instances describe plant-sql-demo --format="value(connectionName)" --project=waooaw-oauth)
echo "Connection: $CONNECTION_NAME"

echo "3. Download proxy if needed"
cd /workspaces/WAOOAW
if [ ! -f "cloud_sql_proxy" ]; then
  wget -q https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
  chmod +x cloud_sql_proxy
fi

echo "4. Start proxy with -dir flag"
mkdir -p /tmp/test-cloudsql
./cloud_sql_proxy -dir=/tmp/test-cloudsql -instances=$CONNECTION_NAME &
PROXY_PID=$!
echo "Proxy PID: $PROXY_PID"
sleep 12

echo "5. Check socket exists"
SOCKET="/tmp/test-cloudsql/$CONNECTION_NAME/.s.PGSQL.5432"
if [ -S "$SOCKET" ]; then
  echo "Socket exists: $SOCKET"
else
  echo "Socket missing: $SOCKET"
  ls -la /tmp/test-cloudsql/ || echo "No dir"
  kill $PROXY_PID 2>/dev/null || true
  exit 1
fi

echo "6. Test psql connection"
export DATABASE_URL
psql "$DATABASE_URL" -c "SELECT 1;" 2>&1 | head -5

echo "7. Cleanup"
kill $PROXY_PID
rm -rf /tmp/test-cloudsql
echo "SUCCESS"
