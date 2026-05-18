#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "west-env setup (Linux/macOS)"
VENV_DIR="$PROJECT_ROOT/.venv"
command -v python3 &>/dev/null || { echo "ERROR: Python 3 not found." >&2; exit 1; }
[ -d "$VENV_DIR" ] || { echo "Creating virtual environment..."; python3 -m venv "$VENV_DIR"; }
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -e "$PROJECT_ROOT[dev]" 2>/dev/null || pip install -e "$PROJECT_ROOT"
echo "Setup complete."
