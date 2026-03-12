---
name: office-pptx-skills
description: PowerPoint pptx 文件操作技能 - 提供演示文稿读写、幻灯片操作 MCP 工具
user-invocable: true
context: fork
model: sonnet
memory: project
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

## 执行过程检查清单

### 文件读取检查（read_pptx）
- [ ] 文件路径存在且有权限访问
- [ ] 文件格式为 .pptx
- [ ] 文本内容成功提取
- [ ] 注意文本提取可能不完整

### 文件写入检查（write_pptx）
- [ ] 输出路径可写
- [ ] 标题和 slides 格式正确
- [ ] 演示文稿成功创建
- [ ] 标题页和内容页正确创建

### 幻灯片操作检查（add_slide, list_slides）
- [ ] 目标文件存在
- [ ] 幻灯片标题和内容格式正确
- [ ] 幻灯片成功添加/列出
- [ ] 幻灯片顺序正确

## 完成后检查清单

### 操作结果验证
- [ ] 文件操作成功完成
- [ ] 输出文件可正常打开
- [ ] 内容完整（注意文本提取限制）
- [ ] 格式符合预期

### 异常处理检查
- [ ] 文件不存在时有明确错误提示
- [ ] 权限不足时有明确错误提示
- [ ] 格式错误时有明确错误提示
