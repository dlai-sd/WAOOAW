#!/bin/bash

set -euo pipefail

echo "=== WAOOAW Codespaces Local Setup ==="
echo "Delegating to scripts/codespace-stack.sh up all"
echo ""

bash scripts/codespace-stack.sh up all
