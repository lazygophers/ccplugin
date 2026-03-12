---
name: office-xlsx-skills
description: Excel xlsx 文件操作技能 - 提供 Excel 文件读写、数据分析 MCP 工具
user-invocable: true
context: fork
model: sonnet
memory: project
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

## 执行过程检查清单

### 文件读取检查（read_xlsx）
- [ ] 文件路径存在且有权限访问
- [ ] 文件格式为 .xlsx
- [ ] Sheet 名称正确（如指定）
- [ ] 数据成功读取为 JSON 格式
- [ ] 大文件处理时间合理

### 文件写入检查（write_xlsx）
- [ ] 输出路径可写
- [ ] 数据格式正确（二维数组）
- [ ] Headers 格式正确（如指定）
- [ ] Excel 文件成功创建
- [ ] 数据完整写入

### 数据分析检查（analyze_xlsx）
- [ ] 文件可正常读取
- [ ] 统计信息计算正确
- [ ] 分析结果包含有用信息（行数/列数/数据类型等）

### 工作表操作检查（list_sheets）
- [ ] 文件存在
- [ ] 所有工作表名称成功列出
- [ ] 工作表顺序正确

## 完成后检查清单

### 操作结果验证
- [ ] 文件操作成功完成
- [ ] 输出文件可正常打开
- [ ] 数据完整无丢失
- [ ] 格式符合预期（pandas 支持的格式）

### 性能检查
- [ ] 大文件处理时间可接受
- [ ] 内存使用合理

### 异常处理检查
- [ ] 文件不存在时有明确错误提示
- [ ] 权限不足时有明确错误提示
- [ ] 数据格式错误时有明确错误提示
