#!/usr/bin/env bash
# run-dev.sh — run AirCheck directly from the cloned repo.
# Passes any extra arguments through to the CLI (e.g. --list-devices).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$REPO_DIR/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: virtual environment not found at $REPO_DIR/.venv" >&2
    echo "Run scripts/install.sh first." >&2
    exit 1
fi

exec "$VENV_PYTHON" -m aircheck.main --config "$REPO_DIR/config.yaml" "$@"
