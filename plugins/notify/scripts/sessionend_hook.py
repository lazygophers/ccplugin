#!/usr/bin/env python3
"""SessionEnd Hook wrapper"""
import sys
from pathlib import Path

script_path = Path(__file__).resolve().parent
plugin_path = script_path.parent
project_root = plugin_path.parent.parent

if not (project_root / 'lib').exists():
    current = script_path
    for _ in range(5):
        if (current / 'lib').exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

from lib.notify.simple_hook import main

if __name__ == "__main__":
    main("SessionEnd")
