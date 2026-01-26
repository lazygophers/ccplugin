"""Version plugin proxy package

This package redirects to the actual version plugin in plugins/version.
"""
import sys
from pathlib import Path

# Redirect package path to plugins/version
__path__ = [str(Path(__file__).parent.parent / "plugins" / "version")]

