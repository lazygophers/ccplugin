---
description: Excel xlsx 文件操作技能 - 读写 Excel 文件、数据分析、格式转换、批量处理
triggers:
  - excel
  - xlsx
  - spreadsheet
  - 表格
  - 工作表
  - 单元格
  - csv转换
  - 数据分析
---

# Excel xlsx 操作技能

通过 MCP 工具和包装层操作 Excel 文件。

## MCP 基础工具（mcp-excel-server）

### 文件读取

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `read_excel` | 读取文件内容 | `file_path`（支持 xlsx/xls/csv/tsv/json） |
| `get_excel_info` | 获取文件元数据 | `file_path` |
| `get_sheet_names` | 列出所有工作表 | `file_path` |

### 数据分析

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `analyze_excel` | 统计分析 | `file_path`, `sheet_name?` |
| `filter_excel` | 条件过滤 | `file_path`, `conditions` |
| `pivot_table` | 透视表 | `file_path`, `rows`, `columns`, `values` |
| `data_summary` | 数据摘要 | `file_path`, `sheet_name?` |

### 文件操作

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `write_excel` | 创建新文件 | `file_path`, `data`, `sheet_name` |
| `update_excel` | 修改现有文件 | `file_path`, `updates`, `sheet_name` |
| `export_chart` | 生成图表 | `file_path`, `chart_type`, `x_column`, `y_column` |

## 包装层额外功能

通过 `scripts/wrapper.py` 提供，使用 `uv run` 执行：

### 格式转换

```bash
# xlsx -> CSV
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py convert data.xlsx output.csv

# CSV -> xlsx
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py convert data.csv output.xlsx

# xlsx -> JSON
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py convert data.xlsx output.json --sheet Sheet1

# JSON -> xlsx
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py convert data.json output.xlsx
```

### 批量处理

```bash
# 批量导入：将目录下所有 CSV 合并为一个 xlsx（每个文件一个工作表）
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py batch-import ./data_dir/ merged.xlsx --pattern "*.csv"

# 批量导出：将 xlsx 每个工作表导出为独立 CSV
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py batch-export data.xlsx ./output_dir/ --format csv

# 批量导出为 JSON
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py batch-export data.xlsx ./output_dir/ --format json
```

### 统计分析与图表

```bash
# 统计分析（输出 JSON）
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py analyze data.xlsx --sheet Sheet1

# 统计分析 + 生成柱状图
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py analyze data.xlsx --output chart.png --chart-type bar --x name --y score

# 图表类型：bar, line, scatter, histogram, pie, box
```

### 智能洞察

```bash
# 数据洞察（异常值检测、相关性分析、趋势判断）
uv run --directory ${CLAUDE_PLUGIN_ROOT} python scripts/wrapper.py insight data.xlsx --sheet Sheet1 --top 5
```

## 使用指南

1. 简单读写操作优先使用 MCP 工具（`read_excel`、`write_excel`）
2. 格式转换和批量操作使用包装层（`wrapper.py`）
3. 数据分析可组合使用 MCP 的 `analyze_excel` + 包装层的 `analyze`/`insight`
4. 图表生成：MCP 的 `export_chart` 适合简单图表，包装层支持更多类型（pie、box）
5. 编辑操作会直接修改文件，注意备份
