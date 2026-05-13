"""pytest conftest — adds content-os plugin directory to path"""
import sys
from pathlib import Path

# Add content-os directory to sys.path so direct module import works
plugin_dir = str(Path(__file__).resolve().parent)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)
