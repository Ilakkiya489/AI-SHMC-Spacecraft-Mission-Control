#!/bin/bash
# AI-SHMC: Launch Mission Control Dashboard
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop any stale/old Streamlit instances for this project so fresh code loads cleanly
pkill -f "streamlit run.*dashboard.py" 2>/dev/null || true
sleep 1

# Detect python executable (prefer python3.8 if .deps is Python 3.8 ABI)
if command -v python3.8 &> /dev/null; then
    PY_BIN="python3.8"
    export PYTHONPATH="$SCRIPT_DIR/.deps:$SCRIPT_DIR:$PYTHONPATH"
else
    PY_BIN="python3"
fi

# Prevent Streamlit from entering developmentMode when loaded from local .deps directory
export STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Select preferred port (default 8501) or next available port if busy
START_PORT="${PORT:-8501}"
DASHBOARD_PORT="$($PY_BIN -c "
import socket
start = int('$START_PORT')
for p in range(start, start + 20):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', p))
        print(p)
        break
    except OSError:
        continue
    finally:
        s.close()
")"
DASHBOARD_PORT="${DASHBOARD_PORT:-$START_PORT}"

echo "=========================================================="
echo "Starting AI-SHMC Spacecraft Mission Control Dashboard..."
echo "Using interpreter: $($PY_BIN --version) ($PY_BIN)"
echo "Console URL: http://localhost:$DASHBOARD_PORT"
echo "=========================================================="

exec $PY_BIN -m streamlit run app/dashboard/dashboard.py --global.developmentMode=false --server.port "$DASHBOARD_PORT" --server.address 0.0.0.0 "$@"

