#!/usr/bin/env sh
# SPDX-License-Identifier: Apache-2.0
set -eu

# =====================================================
# Resolve script directory and workspace root
# =====================================================
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_PARENT="$(cd "$WORKSPACE_DIR/.." && pwd)"

# =====================================================
# Enforce execution from workspace root
# =====================================================
if [ "$(pwd)" != "$WORKSPACE_DIR" ]; then
  echo "ERROR: shell.sh must be run from the workspace root."
  echo
  echo "Workspace root:"
  echo "  $WORKSPACE_DIR"
  echo "Current directory:"
  echo "  $(pwd)"
  echo
  echo "Please run:"
  echo "  cd $WORKSPACE_DIR"
  echo "  scripts/shell.sh"
  exit 1
fi

# =====================================================
# Virtual environment
# =====================================================
VENV_DIR="$WORKSPACE_DIR/.venv"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
  echo "Virtual environment not found."
  echo "Run scripts/bootstrap.sh first."
  exit 1
fi

# shellcheck source=/dev/null
. "$VENV_DIR/bin/activate"

# =====================================================
# Ensure west-env module is importable
# =====================================================
WEST_ENV_MODULE_DIR="$WORKSPACE_PARENT/modules/west-env"

if [ ! -d "$WEST_ENV_MODULE_DIR/west_env" ]; then
  echo "ERROR: west-env module not found at:"
  echo "  $WEST_ENV_MODULE_DIR"
  echo
  echo "Expected layout:"
  echo "  example/"
  echo "    modules/west-env/"
  echo "    workspace/"
  exit 1
fi

export PYTHONPATH="$WEST_ENV_MODULE_DIR${PYTHONPATH:+:$PYTHONPATH}"

# =====================================================
# Extract versions
# =====================================================
PY_VER="$(python --version 2>&1 | awk '{print $2}')"
WEST_VER="$(west --version 2>/dev/null | awk '{print $3}')"

# =====================================================
# Banner
# =====================================================
echo
echo "west-env workspace shell activated."
echo
echo "Python: v$PY_VER"
echo "West:   $WEST_VER"
echo
echo "You are now in the workspace root."
echo "Type \"exit\" to leave."
echo

# =====================================================
# Enter interactive shell (stay in workspace)
# =====================================================
exec "${SHELL:-/bin/sh}"
