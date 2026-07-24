#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Load credentials from project .env
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "ERROR: .env file not found"
    exit 1
fi

# Set PYTHONPATH to venv site-packages so modules load without venv activation
# exec replaces the shell, so 'source' env vars would be lost
export PYTHONPATH="$SCRIPT_DIR/deez_venv/lib/python3.14/site-packages:$PYTHONPATH"

# Rename process in ps tree from 'python3' to 'deezbot' using exec -a
exec -a deezbot "$SCRIPT_DIR/deez_venv/bin/python3" "$SCRIPT_DIR/src/deez_nutz.py"