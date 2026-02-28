# MCP 工具

Office Xlsx 插件提供的 MCP 工具。

## 工具列表

| 工具 | 描述 |
|------|------|
| `read_xlsx` | 读取 Excel 文件 |
| `write_xlsx` | 写入 Excel 文件 |
| `analyze_xlsx` | 分析数据 |
| `list_sheets` | 列出工作表 |

## read_xlsx

### 功能

读取 Excel 文件内容。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |
| `sheet_name` | string | 工作表名称（可选） |

### 示例

```python
result = read_xlsx(
    file_path="data.xlsx",
    sheet_name="Sheet1"
)
```

## write_xlsx

### 功能

写入 Excel 文件。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |
| `data` | array | 数据内容 |
| `sheet_name` | string | 工作表名称 |

### 示例

```python
write_xlsx(
    file_path="output.xlsx",
    data=[
        ["Name", "Age"],
        ["Alice", 30],
        ["Bob", 25]
    ],
    sheet_name="Sheet1"
)
```

## analyze_xlsx

### 功能

分析 Excel 数据。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |
| `analysis_type` | string | 分析类型 |

### 示例

```python
result = analyze_xlsx(
    file_path="sales.xlsx",
    analysis_type="summary"
)
```

## list_sheets

### 功能

列出 Excel 文件中的所有工作表。

### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 文件路径 |

### 示例

```python
sheets = list_sheets(file_path="data.xlsx")
```
