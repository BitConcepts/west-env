#!/usr/bin/env sh
set -eu

# =====================================================
# Configuration
# =====================================================
PYTHON_MIN_MINOR=10
PYTHON_MAX_MINOR=12

# =====================================================
# Resolve script directory and workspace root
# =====================================================
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# =====================================================
# Hard guards
# =====================================================
if [ ! -f "$WORKSPACE_DIR/west.yml" ]; then
  echo "ERROR: west.yml not found in workspace root."
  echo "Expected: $WORKSPACE_DIR/west.yml"
  exit 1
fi

if [ -d "$WORKSPACE_DIR/.git" ]; then
  echo "ERROR: Workspace must not be inside a git repository."
  exit 1
fi

if [ -f "$WORKSPACE_DIR/pyproject.toml" ]; then
  echo "ERROR: bootstrap.sh must NOT be run inside the west-env repository."
  exit 1
fi

# =====================================================
# Python availability
# =====================================================
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH"
  exit 1
fi

# =====================================================
# Python version check (Zephyr requirement)
# =====================================================
PYMAJOR="$(python3 - <<'EOF'
import sys
print(sys.version_info.major)
EOF
)"

PYMINOR="$(python3 - <<'EOF'
import sys
print(sys.version_info.minor)
EOF
)"

PYVER="${PYMAJOR}.${PYMINOR}"

if [ "$PYMAJOR" -ne 3 ]; then
  echo "ERROR: Unsupported Python version $PYVER"
  echo "Zephyr requires Python 3.$PYTHON_MIN_MINOR-3.$PYTHON_MAX_MINOR"
  exit 1
fi

if [ "$PYMINOR" -lt "$PYTHON_MIN_MINOR" ]; then
  echo "ERROR: Unsupported Python version $PYVER"
  echo "Zephyr requires Python 3.$PYTHON_MIN_MINOR-3.$PYTHON_MAX_MINOR"
  exit 1
fi

if [ "$PYMINOR" -gt "$PYTHON_MAX_MINOR" ]; then
  echo "ERROR: Unsupported Python version $PYVER"
  echo "Zephyr requires Python 3.$PYTHON_MIN_MINOR-3.$PYTHON_MAX_MINOR"
  echo "Python 3.$PYTHON_MAX_MINOR+ is not yet supported"
  exit 1
fi

echo
echo "=== Bootstrapping west-env workspace ==="
echo "Workspace root:"
echo "  $WORKSPACE_DIR"
echo "Python version:"
echo "  $PYVER"
echo

# =====================================================
# Virtual environment
# =====================================================
VENV_DIR="$WORKSPACE_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
. "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install west

# =====================================================
# WEST OPERATIONS (forced CWD)
# =====================================================
cd "$WORKSPACE_DIR"

if [ ! -d ".west" ]; then
  echo "Initializing west workspace..."
  python -m west init -l .
fi

echo "Updating workspace..."
python -m west update

if ! python -m west list west-env >/dev/null 2>&1; then
  echo "ERROR: west-env project not found."
  echo "The active manifest is not west.yml."
  exit 1
fi

# =====================================================
# Install Zephyr Python dependencies (CRITICAL)
# =====================================================
ZEPHYR_REQS="$WORKSPACE_DIR/../zephyr/scripts/requirements.txt"

if [ ! -f "$ZEPHYR_REQS" ]; then
  echo "ERROR: Zephyr requirements file not found:"
  echo "  $ZEPHYR_REQS"
  exit 1
fi

echo
echo "Installing Zephyr Python dependencies..."
python -m pip install -r "$ZEPHYR_REQS"

# =====================================================
# Done
# =====================================================
echo
echo "=== Bootstrap complete ==="
echo "Workspace:"
echo "  $WORKSPACE_DIR"
echo
echo "Next steps:"
echo "  scripts/shell.sh"
echo "  west env doctor"
