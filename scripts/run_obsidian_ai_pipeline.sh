#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo ".venv not found. Please create the virtual environment first." >&2
  exit 3
fi

if [ ! -x ".venv/bin/python" ]; then
  echo ".venv/bin/python not found or not executable." >&2
  exit 3
fi

if [ ! -f "config/obsidian_ai.yaml" ]; then
  echo "config/obsidian_ai.yaml not found. Copy config/obsidian_ai.example.yaml first." >&2
  exit 4
fi

if [ -z "${NVIDIA_API_KEY:-}" ]; then
  echo "NVIDIA_API_KEY is not set" >&2
  exit 2
fi

mkdir -p logs
timestamp="$(date +%Y%m%d_%H%M%S)"
log_file="logs/obsidian_ai_pipeline_${timestamp}.log"

.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --stats \
  "$@" 2>&1 | tee "$log_file"

exit "${PIPESTATUS[0]}"
