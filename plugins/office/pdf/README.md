# Office PDF 插件

> PDF 文件读取和内容提取插件。基于 MCP 协议提供 PDF 操作工具。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin office-pdf@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install office-pdf@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **读取 PDF 文件** - 提取 PDF 文本内容
- **元数据提取** - 获取 PDF 文档信息
- **图片提取** - 提取 PDF 中的图片
- **并行处理** - 5-10x 更快的处理速度

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Skill | `office-pdf-skills` | PDF 操作技能 |
| MCP Server | `pdf-reader` | PDF MCP 服务器（SylphxAI/pdf-reader-mcp） |

## MCP 工具

| 工具名称 | 描述 |
|---------|------|
| `read_pdf` | 读取 PDF 文件，提取文本、图片和元数据 |

## 快速开始

### 读取 PDF 文件

```
读取 document.pdf 文件的内容
```

### 提取 PDF 元数据

```
提取 report.pdf 的元数据信息
```

### 提取 PDF 图片

```
从 presentation.pdf 中提取所有图片
```

## 许可证

AGPL-3.0-or-later
