#!/usr/bin/env python3
"""Version management command for ccplugin

This script provides version information about the ccplugin package.
It's a simplified version of the version plugin for the standalone package.
"""
import sys
from pathlib import Path


def get_version() -> str:
    """Get the current version from .version file"""
    version_file = Path(__file__).parent.parent / ".version"
    if version_file.exists():
        return version_file.read_text().strip()
    return "unknown"


def show_version():
    """Show the current version"""
    version = get_version()
    print(f"ccplugin version {version}")


def show_info():
    """Show detailed version information"""
    version = get_version()
    print(f"Package: ccplugin")
    print(f"Version: {version}")
    print(f"Repository: https://github.com/lazygophers/ccplugin")


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        show_version()
        return 0

    command = sys.argv[1]

    if command == "show":
        show_version()
    elif command == "info":
        show_info()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Available commands: show, info", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
