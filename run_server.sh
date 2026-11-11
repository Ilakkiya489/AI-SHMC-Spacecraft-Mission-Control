#!/bin/bash
# AI-SHMC: Launch FastAPI Backend Server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3.8 &> /dev/null; then
    PY_BIN="python3.8"
    export PYTHONPATH="$SCRIPT_DIR/.deps:$SCRIPT_DIR:$PYTHONPATH"
else
    PY_BIN="python3"
fi

echo "=========================================================="
echo "Starting AI-SHMC FastAPI REST Server on port 8000..."
echo "Swagger Docs: http://localhost:8000/docs"
echo "=========================================================="

$PY_BIN app/main.py

