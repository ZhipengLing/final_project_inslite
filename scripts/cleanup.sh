#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "========================================="
echo "  InstaLite — Cleanup"
echo "========================================="
echo ""

# Restore config.js placeholder if it was replaced
if grep -q "execute-api" frontend/js/config.js 2>/dev/null; then
  sed -i.bak 's|https://[^"]*execute-api[^"]*|PLACEHOLDER_API_URL|g' frontend/js/config.js
  rm -f frontend/js/config.js.bak
  echo "Restored frontend/js/config.js placeholder"
fi

echo "Destroying all CDK stacks..."
cdk destroy --all --force

echo ""
echo "Cleanup complete."
