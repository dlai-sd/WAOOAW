#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="waooaw-plant-backend:loglevel-test"
CONTAINER_NAME="waooaw-plant-backend-loglevel-test"
HOST_PORT="18011"

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

pushd /workspaces/WAOOAW/src/Plant/BackEnd >/dev/null

echo "[1/3] Building image: $IMAGE_TAG"
docker build -t "$IMAGE_TAG" .

popd >/dev/null

echo "[2/3] Starting container with LOG_LEVEL=INFO (uppercase)"
docker run -d \
  --name "$CONTAINER_NAME" \
  -p "$HOST_PORT":8000 \
  -e PORT=8000 \
  -e WORKERS=1 \
  -e LOG_LEVEL=INFO \
  -e APP_MODULE=main_simple:app \
  "$IMAGE_TAG" >/dev/null

echo "[3/3] Waiting for /health"
for i in {1..30}; do
  if curl -fsS "http://127.0.0.1:${HOST_PORT}/health" >/dev/null 2>&1; then
    echo "OK: /health responded"
    exit 0
  fi
  sleep 1
  if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: container exited early"
    docker logs --tail 200 "$CONTAINER_NAME" || true
    exit 1
  fi
done

echo "ERROR: /health did not respond in time"
docker logs --tail 200 "$CONTAINER_NAME" || true
exit 1
