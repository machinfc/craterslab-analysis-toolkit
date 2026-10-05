#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] Python executable not found: $PYTHON_BIN"
  exit 1
fi

echo "[INFO] Using Python: $($PYTHON_BIN -V)"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[INFO] Creating virtual environment in $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .

echo
echo "[OK] Environment ready. Recommended next steps:"
echo "  source $VENV_DIR/bin/activate"
echo "  python scripts/diagnostics/check_craterslab_env.py"
