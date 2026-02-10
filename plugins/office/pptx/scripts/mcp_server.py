"""MCP server for Office Pptx plugin."""

import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from pptx import Presentation
from pptx.util import Inches, Pt


class PptxMCPServer:
    """MCP server for PowerPoint presentation operations."""

    def __init__(self):
        self.server = Server("office-pptx")
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="read_pptx",
                    description="Read PowerPoint presentation and extract text content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to pptx file"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_pptx",
                    description="Create a new PowerPoint presentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Output pptx file path"},
                            "title": {"type": "string", "description": "Presentation title"},
                            "slides": {"type": "array", "description": "Array of slide contents"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="add_slide",
                    description="Add a slide to existing presentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to pptx file"},
                            "title": {"type": "string", "description": "Slide title"},
                            "content": {"type": "string", "description": "Slide content"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="list_slides",
                    description="List all slides in presentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to pptx file"}
                        },
                        "required": ["path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            if name == "read_pptx":
                return await self._read_pptx(arguments)
            elif name == "write_pptx":
                return await self._write_pptx(arguments)
            elif name == "add_slide":
                return await self._add_slide(arguments)
            elif name == "list_slides":
                return await self._list_slides(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _read_pptx(self, args: dict) -> list[TextContent]:
        """Read PowerPoint presentation."""
        path = Path(args["path"])

        try:
            prs = Presentation(path)
            slides_data = []

            for i, slide in enumerate(prs.slides):
                slide_data = {"index": i, "text": []}

                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_data["text"].append(shape.text.strip())

                slides_data.append(slide_data)

            result = {
                "path": str(path),
                "slide_count": len(prs.slides),
                "slides": slides_data
            }
            return [TextContent(type="text", text=f"Success: Read {len(prs.slides)} slides")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error reading file: {str(e)}")]

    async def _write_pptx(self, args: dict) -> list[TextContent]:
        """Create new PowerPoint presentation."""
        path = Path(args["path"])
        title = args.get("title", "Presentation")
        slides = args.get("slides", [])

        try:
            prs = Presentation()
            prs.slide_layouts[0].name = title

            # Title slide
            if slides:
                title_slide_layout = prs.slide_layouts[0]
                slide = prs.slides.add_slide(title_slide_layout)
                slide.shapes.title.text = title
                if len(slides[0].get("content", "")) > 0:
                    slide.placeholders[1].text = slides[0]["content"]

            # Content slides
            for slide_data in slides[1:]:
                slide_layout = prs.slide_layouts[1]
                slide = prs.slides.add_slide(slide_layout)
                slide.shapes.title.text = slide_data.get("title", f"Slide {len(slides)}")

                if slide_data.get("content"):
                    body = slide.placeholders[1]
                    body.text = slide_data["content"]

            prs.save(path)
            return [TextContent(type="text", text=f"Success: Created {path} with {len(slides)} slides")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error writing file: {str(e)}")]

    async def _add_slide(self, args: dict) -> list[TextContent]:
        """Add slide to existing presentation."""
        path = Path(args["path"])
        title = args.get("title", "")
        content = args.get("content", "")

        try:
            prs = Presentation(path)
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)

            if title:
                slide.shapes.title.text = title
            if content:
                slide.placeholders[1].text = content

            prs.save(path)
            return [TextContent(type="text", text=f"Success: Added slide")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error adding slide: {str(e)}")]

    async def _list_slides(self, args: dict) -> list[TextContent]:
        """List all slides in presentation."""
        path = Path(args["path"])

        try:
            prs = Presentation(path)
            slides_info = []

            for i, slide in enumerate(prs.slides):
                text_preview = ""
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        text_preview = shape.text.strip()[:50]
                        break
                slides_info.append({
                    "index": i,
                    "preview": text_preview
                })

            result = {
                "path": str(path),
                "count": len(prs.slides),
                "slides": slides_info
            }
            return [TextContent(type="text", text=f"Found {len(prs.slides)} slides")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error listing slides: {str(e)}")]

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
    server = PptxMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
