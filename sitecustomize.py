"""
Automatically adds .deps to sys.path when running on Python 3.8
so all pre-installed packages are available in standard sandboxed Python commands.
"""
import sys
import os

# Only inject .deps if running on Python 3.8 (the matching C-extension ABI)
if sys.version_info[:2] == (3, 8):
    deps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".deps"))
    if os.path.exists(deps_dir) and deps_dir not in sys.path:
        sys.path.insert(0, deps_dir)

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


