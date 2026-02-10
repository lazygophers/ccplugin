# Office Pptx 使用示例

## 读取演示文稿

```python
# 读取整个演示文稿
result = await mcp.call_tool("read_pptx", {
    "path": "presentation.pptx"
})
```

## 创建演示文稿

```python
# 创建新演示文稿
result = await mcp.call_tool("write_pptx", {
    "path": "output.pptx",
    "title": "我的演示",
    "slides": [
        {"title": "封面", "content": "演示标题"},
        {"title": "第一页", "content": "内容介绍"}
    ]
})
```

## 添加幻灯片

```python
# 添加幻灯片
result = await mcp.call_tool("add_slide", {
    "path": "presentation.pptx",
    "title": "新幻灯片",
    "content": "这是新幻灯片的内容。"
})
```

## 列出幻灯片

```python
# 列出所有幻灯片
result = await mcp.call_tool("list_slides", {
    "path": "presentation.pptx"
})
```
