#!/bin/bash
set -e

# WAOOAW Monitoring Setup Script
# Sets up Prometheus, Grafana, and Alertmanager

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔍 Setting up WAOOAW monitoring infrastructure"
echo "================================================"

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

echo "✅ Docker is running"

# Create monitoring directories
echo "📁 Creating monitoring directories..."
mkdir -p "$PROJECT_ROOT/infrastructure/monitoring/prometheus/data"
mkdir -p "$PROJECT_ROOT/infrastructure/monitoring/grafana/data"
mkdir -p "$PROJECT_ROOT/infrastructure/monitoring/grafana/dashboards/json"
mkdir -p "$PROJECT_ROOT/infrastructure/monitoring/alertmanager/data"

# Set permissions
chmod 777 "$PROJECT_ROOT/infrastructure/monitoring/prometheus/data"
chmod 777 "$PROJECT_ROOT/infrastructure/monitoring/grafana/data"
chmod 777 "$PROJECT_ROOT/infrastructure/monitoring/alertmanager/data"

echo "✅ Directories created"

# Validate Prometheus configuration
echo "🔍 Validating Prometheus configuration..."
docker run --rm \
    -v "$PROJECT_ROOT/infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml" \
    prom/prometheus:latest \
    promtool check config /etc/prometheus/prometheus.yml

echo "✅ Prometheus configuration valid"

# Validate alert rules
echo "🔍 Validating alert rules..."
docker run --rm \
    -v "$PROJECT_ROOT/infrastructure/monitoring/rules:/etc/prometheus/rules" \
    prom/prometheus:latest \
    promtool check rules /etc/prometheus/rules/alerts.yml

echo "✅ Alert rules valid"

# Start monitoring stack
echo "🚀 Starting monitoring services..."

cat > "$PROJECT_ROOT/docker-compose.monitoring.yml" << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: waooaw-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./infrastructure/monitoring/rules:/etc/prometheus/rules:ro
      - ./infrastructure/monitoring/prometheus/data:/prometheus
    restart: unless-stopped
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: waooaw-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=redis-datasource,postgres-datasource
    ports:
      - "3001:3000"
    volumes:
      - ./infrastructure/monitoring/grafana:/etc/grafana/provisioning:ro
      - ./infrastructure/monitoring/grafana/data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: waooaw-alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    volumes:
      - ./infrastructure/monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - ./infrastructure/monitoring/alertmanager/data:/alertmanager
    restart: unless-stopped
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: waooaw-node-exporter
    command:
      - '--path.rootfs=/host'
    volumes:
      - '/:/host:ro,rslave'
    ports:
      - "9100:9100"
    restart: unless-stopped
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
EOF

docker compose -f "$PROJECT_ROOT/docker-compose.monitoring.yml" up -d

echo "✅ Monitoring services started"

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check Prometheus
echo "🔍 Checking Prometheus..."
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is healthy"
else
    echo "⚠️  Prometheus health check failed"
fi

# Check Grafana
echo "🔍 Checking Grafana..."
if curl -f http://localhost:3001/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is healthy"
else
    echo "⚠️  Grafana health check failed"
fi

# Check Alertmanager
echo "🔍 Checking Alertmanager..."
if curl -f http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "✅ Alertmanager is healthy"
else
    echo "⚠️  Alertmanager health check failed"
fi

echo ""
echo "================================================"
echo "✅ Monitoring setup complete!"
echo ""
echo "Access points:"
echo "• Prometheus: http://localhost:9090"
echo "• Grafana: http://localhost:3001 (admin:${GRAFANA_PASSWORD:-admin})"
echo "• Alertmanager: http://localhost:9093"
echo ""
echo "Next steps:"
echo "1. Configure alert receivers in alertmanager.yml"
echo "2. Import dashboards in Grafana"
echo "3. Set up Slack/PagerDuty integration"
echo ""
