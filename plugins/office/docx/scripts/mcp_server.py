"""MCP server for Office Docx plugin."""

import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from docx import Document


class DocxMCPServer:
    """MCP server for Word document operations."""

    def __init__(self):
        self.server = Server("office-docx")
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="read_docx",
                    description="Read Word document and extract text content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to docx file"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_docx",
                    description="Create a new Word document with content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Output docx file path"},
                            "content": {"type": "string", "description": "Text content to write"}
                        },
                        "required": ["path", "content"]
                    }
                ),
                Tool(
                    name="add_paragraph",
                    description="Add a paragraph to existing Word document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to docx file"},
                            "text": {"type": "string", "description": "Paragraph text to add"}
                        },
                        "required": ["path", "text"]
                    }
                ),
                Tool(
                    name="get_paragraphs",
                    description="Get all paragraphs from Word document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to docx file"}
                        },
                        "required": ["path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            if name == "read_docx":
                return await self._read_docx(arguments)
            elif name == "write_docx":
                return await self._write_docx(arguments)
            elif name == "add_paragraph":
                return await self._add_paragraph(arguments)
            elif name == "get_paragraphs":
                return await self._get_paragraphs(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _read_docx(self, args: dict) -> list[TextContent]:
        """Read Word document."""
        path = Path(args["path"])

        try:
            doc = Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

            result = {
                "path": str(path),
                "paragraphs": paragraphs,
                "paragraph_count": len(paragraphs),
                "full_text": "\n\n".join(paragraphs)
            }
            return [TextContent(type="text", text=f"Success: Read {len(paragraphs)} paragraphs")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error reading file: {str(e)}")]

    async def _write_docx(self, args: dict) -> list[TextContent]:
        """Create new Word document."""
        path = Path(args["path"])
        content = args.get("content", "")

        try:
            doc = Document()
            for para in content.split("\n\n"):
                if para.strip():
                    doc.add_paragraph(para.strip())

            doc.save(path)
            return [TextContent(type="text", text=f"Success: Created {path}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error writing file: {str(e)}")]

    async def _add_paragraph(self, args: dict) -> list[TextContent]:
        """Add paragraph to existing document."""
        path = Path(args["path"])
        text = args.get("text", "")

        try:
            doc = Document(path)
            doc.add_paragraph(text)
            doc.save(path)
            return [TextContent(type="text", text=f"Success: Added paragraph")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error adding paragraph: {str(e)}")]

    async def _get_paragraphs(self, args: dict) -> list[TextContent]:
        """Get all paragraphs from document."""
        path = Path(args["path"])

        try:
            doc = Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

            result = {
                "path": str(path),
                "paragraphs": paragraphs,
                "count": len(paragraphs)
            }
            return [TextContent(type="text", text=f"Found {len(paragraphs)} paragraphs")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error getting paragraphs: {str(e)}")]

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
    server = DocxMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
