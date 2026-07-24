#!/usr/bin/env bash
set -e  # exit on error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Activating virtual environment..."
source "$SCRIPT_DIR/deez_venv/bin/activate"

echo "Loading environment variables from .env..."
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "ERROR: .env file not found. Create it with required env vars."
    exit 1
fi

echo "Running Python app..."
"$SCRIPT_DIR/deez_venv/bin/python" "$SCRIPT_DIR/deez_nutz.py"

echo "Deactivating virtual environment..."
deactivate