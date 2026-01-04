#!/bin/bash
# Simple deployment script that generates config and calls gcloud directly

set -e

ENVIRONMENT=${1:-demo}
ACTION=${2:-create}
PROJECT="waooaw-oauth"

echo "🚀 Deploying $ENVIRONMENT environment"
echo "   Action: $ACTION"
echo "   Project: $PROJECT"
echo

# Generate config using Python
python3 /workspaces/WAOOAW/cloud/deploy.py --environment $ENVIRONMENT --action $ACTION
