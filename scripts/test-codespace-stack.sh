#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

bash -n scripts/codespace-stack.sh
CODESPACE_NAME=test-space bash scripts/codespace-stack.sh urls | grep 'app.github.dev'
