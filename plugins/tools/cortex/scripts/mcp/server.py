#!/usr/bin/env python3
"""Cortex MCP server — stdio transport.

Registers `cortex_search` and `cortex_save` so cortex skills can drive vault
operations through a typed API instead of orchestrating bash/CLI fallbacks.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow `python3 server.py` without 包安装.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import TextContent, Tool  # noqa: E402

from tools.deep_search import DEEP_SEARCH_TOOL, handle_deep_search  # noqa: E402
from tools.ingest_file import INGEST_FILE_TOOL, handle_ingest_file  # noqa: E402
from tools.ingest_url import INGEST_URL_TOOL, handle_ingest_url  # noqa: E402
from tools.save import SAVE_TOOL, handle_save  # noqa: E402
from tools.search import SEARCH_TOOL, handle_search  # noqa: E402

from cortex_mcp import HANDLERS as MEMORY_HANDLERS  # noqa: E402
from cortex_mcp import MEMORY_TOOLS  # noqa: E402

app: Server = Server("cortex")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        SEARCH_TOOL,
        SAVE_TOOL,
        INGEST_URL_TOOL,
        INGEST_FILE_TOOL,
        DEEP_SEARCH_TOOL,
        *MEMORY_TOOLS,
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == SEARCH_TOOL.name:
        return await handle_search(arguments)
    if name == SAVE_TOOL.name:
        return await handle_save(arguments)
    if name == INGEST_URL_TOOL.name:
        return await handle_ingest_url(arguments)
    if name == INGEST_FILE_TOOL.name:
        return await handle_ingest_file(arguments)
    if name == DEEP_SEARCH_TOOL.name:
        return await handle_deep_search(arguments)
    handler = MEMORY_HANDLERS.get(name)
    if handler is not None:
        return await handler(arguments)
    raise ValueError(f"cortex-mcp: unknown tool {name!r}")


def main() -> None:
    async def _run() -> None:
        async with stdio_server() as (reader, writer):
            await app.run(reader, writer, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
