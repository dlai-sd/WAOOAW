#!/bin/bash
# Deploy Cost Guard Cloud Function
# Version: 1.0

set -e

echo "🚀 Deploying Cost Guard Cloud Function"
echo "======================================"

# Configuration
PROJECT_ID="${GCP_PROJECT:-waooaw-prod}"
REGION="${GCP_REGION:-us-central1}"
FUNCTION_NAME="cost-guard"
RUNTIME="python311"
ENTRY_POINT_PUBSUB="handle_pubsub_event"
ENTRY_POINT_HTTP="handle_http_request"
MEMORY="256Mi"
TIMEOUT="60s"

# Deploy Pub/Sub triggered function
echo "📦 Deploying Pub/Sub trigger (budget alerts)..."
gcloud functions deploy "${FUNCTION_NAME}-pubsub" \
  --gen2 \
  --runtime="${RUNTIME}" \
  --region="${REGION}" \
  --source=. \
  --entry-point="${ENTRY_POINT_PUBSUB}" \
  --trigger-topic="budget-alerts" \
  --memory="${MEMORY}" \
  --timeout="${TIMEOUT}" \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID}" \
  --set-secrets="REDIS_URL=redis-url:latest,REDIS_PASSWORD=redis-password:latest,SLACK_WEBHOOK_URL=slack-webhook-url:latest,SENDGRID_API_KEY=sendgrid-api-key:latest,PLANT_API_KEY=plant-api-key:latest" \
  --service-account="cost-guard@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}"

echo "✓ Pub/Sub function deployed"

# Deploy HTTP triggered function
echo "📦 Deploying HTTP trigger (manual checks, daily reports)..."
gcloud functions deploy "${FUNCTION_NAME}-http" \
  --gen2 \
  --runtime="${RUNTIME}" \
  --region="${REGION}" \
  --source=. \
  --entry-point="${ENTRY_POINT_HTTP}" \
  --trigger-http \
  --allow-unauthenticated \
  --memory="${MEMORY}" \
  --timeout="${TIMEOUT}" \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID},PLANT_API_URL=https://plant.waooaw.com,ALERT_EMAIL_RECIPIENTS=admin@waooaw.com,ops@waooaw.com" \
  --set-secrets="REDIS_URL=redis-url:latest,REDIS_PASSWORD=redis-password:latest,SLACK_WEBHOOK_URL=slack-webhook-url:latest,SENDGRID_API_KEY=sendgrid-api-key:latest,PLANT_API_KEY=plant-api-key:latest" \
  --service-account="cost-guard@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}"

echo "✓ HTTP function deployed"

# Get HTTP function URL
HTTP_URL=$(gcloud functions describe "${FUNCTION_NAME}-http" \
  --gen2 \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(serviceConfig.uri)")

echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo "Pub/Sub Function: ${FUNCTION_NAME}-pubsub (triggered by budget-alerts topic)"
echo "HTTP Function: ${FUNCTION_NAME}-http"
echo "HTTP URL: ${HTTP_URL}"
echo ""
echo "Test commands:"
echo "  curl \"${HTTP_URL}?action=check\""
echo "  curl \"${HTTP_URL}?action=report\""
echo "  curl -X POST \"${HTTP_URL}?action=pause\""
