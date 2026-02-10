# Office Docx Plugin

> Word docx 文件读写和文档操作插件。基于 MCP 协议提供 Word 操作工具。

## Features

- Read docx files
- Write docx files
- Add paragraphs
- Get document structure

## Quick Start

```bash
# Install dependencies
uv sync

# Run MCP server
uv run scripts/main.py mcp
```

## MCP Tools

- `read_docx`: Read Word document
- `write_docx`: Create Word document
- `add_paragraph`: Add paragraph
- `get_paragraphs`: List paragraphs

## Install

```bash
/plugin install ./plugins/office/docx
```
