# Office PDF 使用示例

## 基础操作

### 读取 PDF 文本

```javascript
// 读取整个 PDF 的文本内容
const result = await mcp.call_tool("read_pdf", {
  "path": "document.pdf",
  "extract_text": true
});
```

### 提取 PDF 图片

```javascript
// 提取 PDF 中的所有图片
const result = await mcp.call_tool("read_pdf", {
  "path": "presentation.pdf",
  "extract_images": true
});
```

### 获取 PDF 元数据

```javascript
// 获取 PDF 的元数据信息
const result = await mcp.call_tool("read_pdf", {
  "path": "report.pdf",
  "extract_metadata": true
});
```

## 高级操作

### 完整提取

```javascript
// 同时提取文本、图片和元数据
const result = await mcp.call_tool("read_pdf", {
  "path": "document.pdf",
  "extract_text": true,
  "extract_images": true,
  "extract_metadata": true
});
```

### 处理 URL PDF

```javascript
// 从 URL 读取 PDF
const result = await mcp.call_tool("read_pdf", {
  "path": "https://example.com/document.pdf",
  "extract_text": true
});
```

## 批量处理

### 批量提取文本

```
从以下 PDF 文件中批量提取文本：
- report_2024.pdf
- summary_2024.pdf
- analysis_2024.pdf
```

### 批量提取图片

```
从 presentations/ 目录下的所有 PDF 中提取图片
```

## 实际应用场景

### 文档分析

```
分析 research_paper.pdf，提取摘要和关键信息
```

### 数据提取

```
从 invoice.pdf 中提取发票信息（金额、日期、供应商）
```

### 内容转换

```
将 document.pdf 转换为 Markdown 格式
```
