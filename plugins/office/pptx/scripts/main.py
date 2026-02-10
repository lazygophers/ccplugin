"""Office Pptx CLI - PowerPoint operations and MCP server."""

import asyncio
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        from mcp_server import main as mcp_main
        asyncio.run(mcp_main())
    else:
        print("Office Pptx Plugin")
        print("Usage:")
        print("  uv run scripts/main.py mcp  # Start MCP server")
        print("Run 'uv sync' to install dependencies first.")


if __name__ == "__main__":
    main()
