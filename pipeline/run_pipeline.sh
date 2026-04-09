#!/usr/bin/env bash
# Run the full preprocessing pipeline: download -> extract -> aggregate
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Step 1: Download PPTX files ==="
python3 download.py "$@"

echo ""
echo "=== Step 2: Extract style profiles ==="
python3 extract.py --all

echo ""
echo "=== Step 3: Aggregate into style library ==="
python3 aggregate.py

echo ""
echo "=== Pipeline complete ==="
