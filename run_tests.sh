#!/bin/bash
# AI-SHMC: Run Pytest Test Suite
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3.8 &> /dev/null; then
    PY_BIN="python3.8"
    export PYTHONPATH="$SCRIPT_DIR/.deps:$SCRIPT_DIR:$PYTHONPATH"
else
    PY_BIN="python3"
fi

$PY_BIN -m pytest tests/ -v "$@"

