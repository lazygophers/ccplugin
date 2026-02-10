---
name: office-xlsx-skills
description: Excel xlsx 文件操作技能 - 提供 Excel 文件读写、数据分析 MCP 工具
---

# Office Xlsx 技能

## 快速导航

| 文档 | 内容 | 适用场景 |
| ---- | ---- | -------- |
| **SKILL.md** | 核心工具、使用方法 | 快速入门 |
| [examples.md](examples.md) | 完整使用示例 | 实践参考 |

## 核心工具

### read_xlsx
读取 Excel 文件，返回 JSON 格式数据。

```python
# Claude Code 中使用
result = await mcp.call_tool("read_xlsx", {
    "path": "/path/to/file.xlsx",
    "sheet": "Sheet1"  # 可选
})
```

### write_xlsx
写入数据到 Excel 文件。

```python
result = await mcp.call_tool("write_xlsx", {
    "path": "/path/to/output.xlsx",
    "data": [["Name", "Age"], ["Alice", 30], ["Bob", 25]],
    "headers": ["Name", "Age"]  # 可选
})
```

### analyze_xlsx
分析 Excel 文件，返回统计信息。

```python
result = await mcp.call_tool("analyze_xlsx", {
    "path": "/path/to/file.xlsx"
})
```

### list_sheets
列出 Excel 文件中的所有工作表。

```python
result = await mcp.call_tool("list_sheets", {
    "path": "/path/to/file.xlsx"
})
```

## 使用示例

### 读取并分析数据
```
1. read_xlsx 读取文件
2. analyze_xlsx 获取统计
3. write_xlsx 导出结果
```

## 注意事项

- 确保文件路径存在且有权限
- 大文件可能需要较长时间处理
- 使用 pandas 读取，支持多种数据格式
