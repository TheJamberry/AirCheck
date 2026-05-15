#!/usr/bin/env bash
# install.sh — set up AirCheck on a production or development machine.
# Safe to re-run; will not overwrite an existing config.yaml or venv.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$REPO_DIR/.venv"

# Require Python 3.10+
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" || {
    echo "Error: Python 3.10 or newer is required." >&2
    exit 1
}

echo "==> Creating virtual environment at $VENV_DIR"
python3 -m venv "$VENV_DIR"

echo "==> Installing AirCheck and dependencies"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -e "$REPO_DIR" --quiet

if [ ! -f "$REPO_DIR/config.yaml" ]; then
    echo "==> Copying config.example.yaml → config.yaml"
    cp "$REPO_DIR/config.example.yaml" "$REPO_DIR/config.yaml"
    echo "    Edit $REPO_DIR/config.yaml before running AirCheck."
else
    echo "==> config.yaml already exists — skipping copy."
fi

echo ""
echo "Installation complete."
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml:  nano $REPO_DIR/config.yaml"
echo "  2. List audio devices: $VENV_DIR/bin/python -m aircheck.main --list-devices"
echo "  3. Run manually:       bash $REPO_DIR/scripts/run-dev.sh"
echo ""
echo "To install as a systemd service:"
echo "  sudo cp $REPO_DIR/systemd/aircheck.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable aircheck"
echo "  sudo systemctl start aircheck"
