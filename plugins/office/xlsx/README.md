# Office Xlsx Plugin

> Excel xlsx 文件读写和数据分析插件。基于 MCP 协议提供 Excel 操作工具。

## Features

- Read xlsx files with pandas
- Write xlsx files with openpyxl
- Analyze data statistics
- Multi-sheet support

## Quick Start

```bash
# Install dependencies
uv sync

# Run MCP server
uv run scripts/main.py mcp
```

## MCP Tools

- `read_xlsx`: Read Excel file
- `write_xlsx`: Write Excel file
- `analyze_xlsx`: Analyze data
- `list_sheets`: List sheets

## Install

```bash
/plugin install ./plugins/office/xlsx
```
