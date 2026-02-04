#!/usr/bin/env sh
set -eu

APP_MODULE="${APP_MODULE:-main:app}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"

# Uvicorn requires lowercase log levels. Normalize defensively.
LOG_LEVEL_RAW="${LOG_LEVEL:-info}"
LOG_LEVEL_LC="$(printf %s "$LOG_LEVEL_RAW" | tr '[:upper:]' '[:lower:]')"
if [ "$LOG_LEVEL_LC" = "warn" ]; then
  LOG_LEVEL_LC="warning"
fi

exec uvicorn "$APP_MODULE" \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WORKERS" \
  --loop uvloop \
  --http httptools \
  --log-level "$LOG_LEVEL_LC" "$@"
