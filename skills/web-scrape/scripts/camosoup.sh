#!/usr/bin/env bash
set -euo pipefail

# Resolve script directory (works even if symlinked)
SCRIPT_DIR="$(cd "$(dirname -- "$0")" && pwd)"

# Use the hermes agent venv's Python so all deps are available
VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python3"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "ERROR: Hermes venv python not found at $VENV_PYTHON" >&2
  exit 1
fi

exec "$VENV_PYTHON" -m camosoup "$@"
