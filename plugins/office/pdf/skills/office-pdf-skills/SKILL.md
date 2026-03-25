---
description: PDF 文件操作技能 - 提供 PDF 读取、文本提取、图片提取 MCP 工具
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Office PDF 技能

## 快速导航

| 文档 | 内容 | 适用场景 |
| ---- | ---- | -------- |
| **SKILL.md** | 核心工具、使用方法 | 快速入门 |
| [examples.md](examples.md) | 完整使用示例 | 实践参考 |

## 核心工具

### read_pdf

读取 PDF 文件，提取文本、图片和元数据。

**参数**：
- `path` (string, 必需): PDF 文件路径（本地路径或 URL）
- `extract_text` (boolean, 可选): 是否提取文本，默认 true
- `extract_images` (boolean, 可选): 是否提取图片，默认 false
- `extract_metadata` (boolean, 可选): 是否提取元数据，默认 true

**返回值**：
- `text`: 提取的文本内容
- `images`: 提取的图片列表
- `metadata`: PDF 元数据（标题、作者、页数等）

**示例**：
```javascript
// 读取 PDF 文本
mcp.call_tool("read_pdf", {
  "path": "/path/to/document.pdf",
  "extract_text": true
})

// 提取 PDF 图片
mcp.call_tool("read_pdf", {
  "path": "/path/to/document.pdf",
  "extract_images": true
})

// 获取 PDF 元数据
mcp.call_tool("read_pdf", {
  "path": "/path/to/document.pdf",
  "extract_metadata": true
})
```

## 使用场景

### 文本提取
```
提取 report.pdf 中的所有文本内容
```

### 图片提取
```
从 presentation.pdf 中提取所有图片并保存
```

### 元数据获取
```
获取 document.pdf 的作者、标题和页数信息
```

## 注意事项

- 基于 SylphxAI/pdf-reader-mcp，生产级质量
- 支持并行处理，5-10x 更快
- 支持本地文件和 URL
- 94%+ 测试覆盖

## 执行过程检查清单

### 文件读取检查
- [ ] 文件路径正确且可访问
- [ ] PDF 文件格式有效
- [ ] 成功提取所需内容

### 文本提取检查
- [ ] 文本内容完整
- [ ] 编码正确（支持中文）
- [ ] 格式保留合理

### 图片提取检查
- [ ] 图片提取完整
- [ ] 图片质量保持
- [ ] 保存路径正确

## 完成后检查清单

### 操作结果验证
- [ ] 提取操作成功完成
- [ ] 输出内容符合预期
- [ ] 数据格式正确
- [ ] 无错误或警告

### 性能检查
- [ ] 处理速度符合预期
- [ ] 并行处理正常工作
- [ ] 内存使用合理
