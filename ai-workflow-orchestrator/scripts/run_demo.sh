#!/usr/bin/env bash
# Run the demo against the sample data (no API key needed).
set -euo pipefail
cd "$(dirname "$0")/.."
python -m workflow_orchestrator.cli data/sample_items.json
