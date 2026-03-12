---
name: office-docx-skills
description: Word docx 文件操作技能 - 提供 Word 文档读写、段落格式化 MCP 工具
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Office Docx 技能

## 快速导航

| 文档 | 内容 | 适用场景 |
| ---- | ---- | -------- |
| **SKILL.md** | 核心工具、使用方法 | 快速入门 |
| [examples.md](examples.md) | 完整使用示例 | 实践参考 |

## 核心工具

### read_docx
读取 Word 文档，提取文本内容。

```python
result = await mcp.call_tool("read_docx", {
    "path": "/path/to/document.docx"
})
```

### write_docx
创建新 Word 文档。

```python
result = await mcp.call_tool("write_docx", {
    "path": "/path/to/output.docx",
    "content": "文档内容..."
})
```

### add_paragraph
向现有文档添加段落。

```python
result = await mcp.call_tool("add_paragraph", {
    "path": "/path/to/document.docx",
    "text": "新段落内容"
})
```

### get_paragraphs
获取文档所有段落。

```python
result = await mcp.call_tool("get_paragraphs", {
    "path": "/path/to/document.docx"
})
```

## 使用示例

### 读取并处理文档
```
1. read_docx 读取文档
2. get_paragraphs 获取段落
3. add_paragraph 添加内容
```

## 注意事项

- 使用 python-docx 库
- 支持中英文混排
- 段落以空行分隔

## 执行过程检查清单

### 文件读取检查（read_docx）
- [ ] 文件路径存在且有权限访问
- [ ] 文件格式为 .docx
- [ ] 文本内容成功提取
- [ ] 中英文混排正确处理

### 文件写入检查（write_docx）
- [ ] 输出路径可写
- [ ] 内容格式正确
- [ ] 文档成功创建
- [ ] 段落以空行正确分隔

### 段落操作检查（add_paragraph, get_paragraphs）
- [ ] 目标文档存在
- [ ] 段落内容格式正确
- [ ] 段落成功添加/获取
- [ ] 段落顺序正确

## 完成后检查清单

### 操作结果验证
- [ ] 文件操作成功完成
- [ ] 输出文件可正常打开
- [ ] 内容完整无丢失
- [ ] 格式符合预期

### 异常处理检查
- [ ] 文件不存在时有明确错误提示
- [ ] 权限不足时有明确错误提示
- [ ] 格式错误时有明确错误提示
