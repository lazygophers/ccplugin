# API 文档

## MCP 工具（mcp-excel-server）

通过 plugin.json 中的 `mcpServers` 配置自动注册。

### read_excel

读取 Excel 文件内容。

- **参数**: `file_path` (str) - 文件路径，支持 xlsx/xls/csv/tsv/json
- **返回**: 文件内容（表格数据）

### get_excel_info

获取文件元数据和结构信息。

- **参数**: `file_path` (str) - 文件路径
- **返回**: 工作表列表、行列数、数据类型等元信息

### get_sheet_names

列出所有工作表名。

- **参数**: `file_path` (str) - 文件路径
- **返回**: 工作表名称列表

### analyze_excel

统计分析（均值、中位数、标准差等）。

- **参数**: `file_path` (str), `sheet_name` (str, 可选)
- **返回**: 各列的统计指标

### filter_excel

按条件过滤数据。

- **参数**: `file_path` (str), `conditions` (object) - 过滤条件
- **返回**: 满足条件的数据行

### pivot_table

创建透视表。

- **参数**: `file_path` (str), `rows` (array), `columns` (array), `values` (array)
- **返回**: 透视表结果

### data_summary

综合数据摘要。

- **参数**: `file_path` (str), `sheet_name` (str, 可选)
- **返回**: 数据概览、分布、统计

### write_excel

创建新 Excel 文件。

- **参数**: `file_path` (str), `data` (object), `sheet_name` (str)
- **返回**: 创建状态

### update_excel

修改现有 Excel 文件。

- **参数**: `file_path` (str), `updates` (object), `sheet_name` (str)
- **返回**: 更新状态

### export_chart

生成图表（line/bar/scatter/histogram）。

- **参数**: `file_path` (str), `chart_type` (str), `x_column` (str), `y_column` (str)
- **返回**: 图表文件路径

## 包装层 API（scripts/wrapper.py）

通过 `uv run` 调用，所有命令输出 JSON 格式结果。

### convert

格式转换，根据输入输出文件扩展名自动判断方向。

```bash
uv run python scripts/wrapper.py convert <input> <output> [--sheet SHEET]
```

支持的转换：
- `.xlsx` -> `.csv`
- `.csv` -> `.xlsx`
- `.xlsx` -> `.json`
- `.json` -> `.xlsx`

**返回示例**:
```json
{"status": "ok", "output": "data.csv"}
```

### batch-import

批量导入文件到一个 xlsx 工作簿。

```bash
uv run python scripts/wrapper.py batch-import <directory> <output> [--pattern PATTERN]
```

- `directory`: 源文件目录
- `output`: 输出 xlsx 路径
- `--pattern`: 文件匹配模式，默认 `*.csv`

**返回示例**:
```json
{
  "output": "merged.xlsx",
  "sheets": {"sales_jan": 100, "sales_feb": 120},
  "total_files": 2
}
```

### batch-export

将 xlsx 每个工作表导出为独立文件。

```bash
uv run python scripts/wrapper.py batch-export <input> <directory> [--format csv|json]
```

**返回示例**:
```json
{
  "input": "data.xlsx",
  "exported": {"Sheet1": "./out/Sheet1.csv"},
  "total_sheets": 1
}
```

### analyze

统计分析，可选生成图表。

```bash
uv run python scripts/wrapper.py analyze <input> [--sheet SHEET] [--output CHART_PATH] [--chart-type TYPE] [--x COL] [--y COL]
```

图表类型：`bar`, `line`, `scatter`, `histogram`, `pie`, `box`

**返回示例**:
```json
{
  "shape": {"rows": 100, "columns": 5},
  "columns": ["name", "age", "score"],
  "numeric_stats": {"age": {"mean": 25.5, "std": 5.2}},
  "correlations": {"age": {"score": 0.72}}
}
```

### insight

智能数据洞察和趋势分析。

```bash
uv run python scripts/wrapper.py insight <input> [--sheet SHEET] [--top N]
```

**返回示例**:
```json
{
  "overview": {"total_rows": 500, "total_columns": 8},
  "data_quality": {"completeness_pct": 98.5, "duplicate_rows": 3},
  "outliers": {"price": 12},
  "high_correlations": [{"col1": "revenue", "col2": "units", "correlation": 0.95}],
  "trends": {"revenue": "rising", "cost": "stable"}
}
```

## 配置

MCP 服务通过 plugin.json 中的 `mcpServers` 配置：

```json
{
  "mcpServers": {
    "excel": {
      "command": "uvx",
      "args": ["mcp-excel-server"]
    }
  }
}
```
