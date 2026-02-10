# Office Docx 使用示例

## 读取文档

```python
# 读取整个文档
result = await mcp.call_tool("read_docx", {
    "path": "document.docx"
})
```

## 创建文档

```python
# 创建新文档
result = await mcp.call_tool("write_docx", {
    "path": "output.docx",
    "content": "这是一个测试文档。\n\n包含多个段落。"
})
```

## 添加段落

```python
# 添加段落
result = await mcp.call_tool("add_paragraph", {
    "path": "document.docx",
    "text": "这是新增的段落内容。"
})
```

## 获取段落

```python
# 获取所有段落
result = await mcp.call_tool("get_paragraphs", {
    "path": "document.docx"
})
```
