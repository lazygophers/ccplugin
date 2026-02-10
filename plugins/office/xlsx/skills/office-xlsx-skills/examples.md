# Office Xlsx 使用示例

## 读取 Excel 文件

```python
# 读取整个文件
result = await mcp.call_tool("read_xlsx", {
    "path": "data.xlsx"
})

# 读取指定工作表
result = await mcp.call_tool("read_xlsx", {
    "path": "data.xlsx",
    "sheet": "Report"
})
```

## 写入 Excel 文件

```python
# 写入简单数据
result = await mcp.call_tool("write_xlsx", {
    "path": "output.xlsx",
    "data": [
        ["Name", "Score"],
        ["Alice", 95],
        ["Bob", 87]
    ]
})

# 写入带表头
result = await mcp.call_tool("write_xlsx", {
    "path": "output.xlsx",
    "data": [[1, 2, 3], [4, 5, 6]],
    "headers": ["A", "B", "C"]
})
```

## 分析数据

```python
# 获取完整统计
result = await mcp.call_tool("analyze_xlsx", {
    "path": "data.xlsx"
})
```

## 列出工作表

```python
# 查看所有工作表
result = await mcp.call_tool("list_sheets", {
    "path": "multi_sheet.xlsx"
})
```
