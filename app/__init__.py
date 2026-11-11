"""AI-SHMC: AI-Based Self-Healing Mission Control Copilot for Autonomous Spacecraft Operations"""
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_deps_path = os.path.join(_project_root, ".deps")

# Only inject .deps if running on Python 3.8 (matching ABI)
if sys.version_info[:2] == (3, 8):
    if os.path.exists(_deps_path) and _deps_path not in sys.path:
        sys.path.insert(0, _deps_path)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

__version__ = "1.0.0"


