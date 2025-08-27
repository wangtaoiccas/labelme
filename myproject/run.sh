#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN=${PYTHON_BIN:-python3}
VENV_DIR=".venv"
VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

use_venv=true
if [[ ! -x "$VENV_PY" ]]; then
	set +e
	"$PYTHON_BIN" -m venv "$VENV_DIR"
	status=$?
	set -e
	if [[ $status -ne 0 ]]; then
		echo "[run.sh] Warning: venv creation failed; falling back to system Python." >&2
		use_venv=false
	fi
fi

if $use_venv && [[ -x "$VENV_PIP" ]]; then
	"$VENV_PIP" install --upgrade pip >/dev/null || true
	"$VENV_PIP" install -r requirements.txt >/dev/null
	export PYTHONPATH=$(pwd)
	exec "$VENV_PY" -m backend.app
else
	# Fallback: system Python
	# Try python -m pip first; if not available, try pip3
	if "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
		PIP_CMD=("$PYTHON_BIN" -m pip)
	elif command -v pip3 >/dev/null 2>&1; then
		PIP_CMD=(pip3)
	else
		echo "[run.sh] Error: pip for Python3 is not available. Please install python3-pip." >&2
		exit 1
	fi
	"${PIP_CMD[@]}" install --user -r requirements.txt >/dev/null
	export PYTHONPATH=$(pwd)
	exec "$PYTHON_BIN" -m backend.app
fi