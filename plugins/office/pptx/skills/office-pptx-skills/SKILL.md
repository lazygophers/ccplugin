---
name: office-pptx-skills
description: PowerPoint pptx 文件操作技能 - 提供演示文稿读写、幻灯片操作 MCP 工具
---

# Office Pptx 技能

## 快速导航

| 文档 | 内容 | 适用场景 |
| ---- | ---- | -------- |
| **SKILL.md** | 核心工具、使用方法 | 快速入门 |
| [examples.md](examples.md) | 完整使用示例 | 实践参考 |

## 核心工具

### read_pptx
读取 PowerPoint 演示文稿，提取文本内容。

```python
result = await mcp.call_tool("read_pptx", {
    "path": "/path/to/presentation.pptx"
})
```

### write_pptx
创建新的 PowerPoint 演示文稿。

```python
result = await mcp.call_tool("write_pptx", {
    "path": "/path/to/output.pptx",
    "title": "演示标题",
    "slides": [
        {"title": "第一页", "content": "内容..."}
    ]
})
```

### add_slide
向现有演示文稿添加幻灯片。

```python
result = await mcp.call_tool("add_slide", {
    "path": "/path/to/presentation.pptx",
    "title": "新幻灯片",
    "content": "幻灯片内容"
})
```

### list_slides
列出演示文稿中的所有幻灯片。

```python
result = await mcp.call_tool("list_slides", {
    "path": "/path/to/presentation.pptx"
})
```

## 使用示例

### 读取并处理演示文稿
```
1. read_pptx 读取文件
2. list_slides 查看结构
3. add_slide 添加幻灯片
```

## 注意事项

- 使用 python-pptx 库
- 支持标题页和内容页
- 文本内容提取可能不完整
