---
name: office-docx-skills
description: Word docx 文件操作技能 - 提供 Word 文档读写、段落格式化 MCP 工具
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
