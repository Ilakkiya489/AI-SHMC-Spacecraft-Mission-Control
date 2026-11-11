"""
Master Application Entry Point for AI-SHMC.
Launches the FastAPI mission control backend server with Uvicorn.
"""

import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_deps_path = os.path.join(_project_root, ".deps")
if sys.version_info[:2] == (3, 8):
    if os.path.exists(_deps_path) and _deps_path not in sys.path:
        sys.path.insert(0, _deps_path)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import uvicorn
from app.backend.api import app
from app.backend.database import init_db


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    print("=" * 65)
    print("AI-SHMC: Initializing Spacecraft Mission Control Copilot Backend")
    print(f"API Server listening on: http://{host}:{port}")
    print(f"Interactive Swagger Docs: http://localhost:{port}/docs")
    print("=" * 65)
    init_db()
    uvicorn.run("app.backend.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    start_server(host="0.0.0.0", port=8000)

