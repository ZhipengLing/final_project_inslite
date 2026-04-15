#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="$SCRIPT_DIR/layer.zip"

if [ -f "$OUTPUT" ]; then
    echo "Layer zip exists. Use --force to rebuild."
    [[ "${1:-}" != "--force" ]] && exit 0
fi

echo "Building Lambda Layer..."
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

pip3 install \
    -r "$SCRIPT_DIR/python/requirements.txt" \
    -t "$TMPDIR/python" \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 3.12 \
    --quiet

cp "$SCRIPT_DIR/python/"*.py "$TMPDIR/python/"

cd "$TMPDIR" && zip -r "$OUTPUT" python/ -q
echo "Layer built: $OUTPUT ($(du -h "$OUTPUT" | cut -f1))"
