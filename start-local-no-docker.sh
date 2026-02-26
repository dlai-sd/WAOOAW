#!/bin/bash
# Quick Start Script (Docker-first)

set -euo pipefail

echo "=== WAOOAW Local Setup (Docker) ==="
echo "Running Docker Compose using docker-compose.local.yml"
echo ""

docker compose -f docker-compose.local.yml up --build
