# Office PDF 插件文档

## 概述

Office PDF 插件基于 [SylphxAI/pdf-reader-mcp](https://github.com/SylphxAI/pdf-reader-mcp) 提供生产级 PDF 处理能力。

## 架构

```
┌─────────────────────────────────────┐
│   Office PDF Plugin                 │
├─────────────────────────────────────┤
│  Skills                              │
│  ├─ office-pdf-skills/              │
│  │   ├─ SKILL.md                    │
│  │   └─ examples.md                 │
├─────────────────────────────────────┤
│  MCP Server                          │
│  └─ pdf-reader                      │
│      (SylphxAI/pdf-reader-mcp)      │
│      - 文本提取                      │
│      - 图片提取                      │
│      - 元数据提取                    │
│      - 并行处理                      │
└─────────────────────────────────────┘
```

## 核心特性

### 1. 高性能处理

- **并行处理**：5-10x 更快的处理速度
- **生产级质量**：94%+ 测试覆盖
- **直接通信**：stdio 模式，无 HTTP 开销

### 2. 多种提取模式

- **文本提取**：提取 PDF 中的所有文本
- **图片提取**：提取 PDF 中的图片
- **元数据提取**：获取标题、作者、页数等信息

### 3. 灵活的输入

- **本地文件**：支持本地 PDF 文件
- **远程 URL**：支持 HTTP/HTTPS URL

## MCP 工具

### read_pdf

统一的 PDF 读取工具，支持多种提取模式。

详见 [API 文档](api.md)。

## 使用场景

1. **文档分析**：提取和分析 PDF 内容
2. **数据提取**：从发票、报告中提取结构化数据
3. **内容转换**：将 PDF 转换为其他格式
4. **批量处理**：批量处理多个 PDF 文件

## 技术栈

- **MCP 服务器**：SylphxAI/pdf-reader-mcp
- **运行环境**：Node.js 22+
- **协议**：MCP stdio

## 限制

- **只读**：仅支持读取，不支持 PDF 生成
- **Node.js 依赖**：需要 Node.js 22+ 环境

## 相关文档

- [API 文档](api.md)
- [使用示例](../skills/office-pdf-skills/examples.md)
