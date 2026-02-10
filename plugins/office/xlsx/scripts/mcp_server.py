"""MCP server for Office Xlsx plugin."""

import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import pandas as pd


class XlsxMCPServer:
    """MCP server for Excel file operations."""

    def __init__(self):
        self.server = Server("office-xlsx")
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="read_xlsx",
                    description="Read Excel file and return data as JSON",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to xlsx file"},
                            "sheet": {"type": "string", "description": "Sheet name (optional, reads first sheet if not specified)"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_xlsx",
                    description="Write data to Excel file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Output xlsx file path"},
                            "data": {"type": "array", "description": "Data to write as array of arrays"},
                            "headers": {"type": "array", "description": "Optional column headers"}
                        },
                        "required": ["path", "data"]
                    }
                ),
                Tool(
                    name="analyze_xlsx",
                    description="Analyze Excel file and return statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to xlsx file"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="list_sheets",
                    description="List all sheet names in an Excel file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to xlsx file"}
                        },
                        "required": ["path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            if name == "read_xlsx":
                return await self._read_xlsx(arguments)
            elif name == "write_xlsx":
                return await self._write_xlsx(arguments)
            elif name == "analyze_xlsx":
                return await self._analyze_xlsx(arguments)
            elif name == "list_sheets":
                return await self._list_sheets(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _read_xlsx(self, args: dict) -> list[TextContent]:
        """Read Excel file."""
        path = Path(args["path"])
        sheet = args.get("sheet")

        try:
            if sheet:
                df = pd.read_excel(path, sheet_name=sheet)
            else:
                df = pd.read_excel(path)

            result = {
                "path": str(path),
                "rows": len(df),
                "columns": len(df.columns),
                "headers": df.columns.tolist(),
                "data": df.to_dict(orient="records")
            }
            return [TextContent(type="text", text=f"Success: {result}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error reading file: {str(e)}")]

    async def _write_xlsx(self, args: dict) -> list[TextContent]:
        """Write data to Excel file."""
        path = Path(args["path"])
        data = args.get("data", [])
        headers = args.get("headers", [])

        try:
            df = pd.DataFrame(data, columns=headers) if headers else pd.DataFrame(data)
            df.to_excel(path, index=False)
            return [TextContent(type="text", text=f"Success: Written {len(data)} rows to {path}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error writing file: {str(e)}")]

    async def _analyze_xlsx(self, args: dict) -> list[TextContent]:
        """Analyze Excel file statistics."""
        path = Path(args["path"])

        try:
            df = pd.read_excel(path)

            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

            result = {
                "path": str(path),
                "sheets": pd.ExcelFile(path).sheet_names,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "numeric_columns": numeric_cols,
                "statistics": df.describe().to_dict() if numeric_cols else {}
            }
            return [TextContent(type="text", text=f"Analysis: {result}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing file: {str(e)}")]

    async def _list_sheets(self, args: dict) -> list[TextContent]:
        """List sheets in Excel file."""
        path = Path(args["path"])

        try:
            sheets = pd.ExcelFile(path).sheet_names
            return [TextContent(type="text", text=f"Sheets: {sheets}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error listing sheets: {str(e)}")]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Entry point."""
    server = XlsxMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
