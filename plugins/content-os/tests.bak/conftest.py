"""
pytest conftest — adds content-os plugin directory to sys.path
so that tests can import content_os_core directly.
"""
import sys
from pathlib import Path

# Add plugin root directory to sys.path so direct module import works
plugin_dir = str(Path(__file__).resolve().parent.parent)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)
