# Office Pptx Plugin

> PowerPoint pptx 文件读写和幻灯片操作插件。基于 MCP 协议提供 PowerPoint 操作工具。

## Features

- Read pptx files
- Write pptx files
- Add slides
- List slide structure

## Quick Start

```bash
# Install dependencies
uv sync

# Run MCP server
uv run scripts/main.py mcp
```

## MCP Tools

- `read_pptx`: Read PowerPoint presentation
- `write_pptx`: Create PowerPoint presentation
- `add_slide`: Add slide
- `list_slides`: List slides

## Install

```bash
/plugin install ./plugins/office/pptx
```
