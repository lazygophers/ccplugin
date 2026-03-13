# Office PDF API 文档

## MCP 工具

### read_pdf

读取 PDF 文件，提取文本、图片和元数据。

**工具名称**：`read_pdf`

**参数**：

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `path` | string | 是 | - | PDF 文件路径（本地路径或 URL） |
| `extract_text` | boolean | 否 | true | 是否提取文本内容 |
| `extract_images` | boolean | 否 | false | 是否提取图片 |
| `extract_metadata` | boolean | 否 | true | 是否提取元数据 |

**返回值**：

```json
{
  "text": "提取的文本内容...",
  "images": [
    {
      "page": 1,
      "index": 0,
      "data": "base64_encoded_image_data",
      "format": "png"
    }
  ],
  "metadata": {
    "title": "文档标题",
    "author": "作者",
    "subject": "主题",
    "creator": "创建者",
    "producer": "生成器",
    "pages": 10,
    "creationDate": "2024-01-01T00:00:00Z",
    "modificationDate": "2024-01-02T00:00:00Z"
  }
}
```

**示例**：

```javascript
// 基础文本提取
const result = await mcp.call_tool("read_pdf", {
  "path": "/path/to/document.pdf",
  "extract_text": true
});

// 提取图片
const result = await mcp.call_tool("read_pdf", {
  "path": "/path/to/document.pdf",
  "extract_images": true
});

// 完整提取
const result = await mcp.call_tool("read_pdf", {
  "path": "https://example.com/document.pdf",
  "extract_text": true,
  "extract_images": true,
  "extract_metadata": true
});
```

**错误处理**：

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| `FileNotFound` | 文件不存在 | 检查文件路径 |
| `InvalidPDF` | 无效的 PDF 文件 | 确认文件格式 |
| `NetworkError` | URL 访问失败 | 检查网络连接 |
| `PermissionDenied` | 权限不足 | 检查文件权限 |

## 性能特性

### 并行处理

- 自动并行处理多页 PDF
- 5-10x 更快的处理速度
- 适合大型 PDF 文件

### 内存优化

- 流式处理，降低内存占用
- 支持大文件处理
- 自动资源清理

## 使用建议

### 最佳实践

1. **按需提取**：只提取需要的内容（text/images/metadata）
2. **本地优先**：本地文件处理速度更快
3. **批量处理**：使用并行处理提升效率
4. **错误处理**：始终处理可能的错误情况

### 性能优化

- 大文件：分批处理
- 只读文本：关闭图片提取
- 网络文件：考虑先下载到本地

## 限制说明

1. **只读限制**：仅支持读取，不支持 PDF 生成或编辑
2. **格式支持**：标准 PDF 格式，部分加密 PDF 可能无法读取
3. **依赖要求**：需要 Node.js 22+ 环境
