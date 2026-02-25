# Office Docx 插件

> Word docx 文件读写和文档操作插件。基于 MCP 协议提供 Word 操作工具。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin office-docx@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install office-docx@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **读取 docx 文件** - 读取 Word 文档内容
- **写入 docx 文件** - 创建 Word 文档
- **添加段落** - 添加格式化段落
- **获取文档结构** - 获取文档结构信息

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Skill | `office-docx-skills` | Word 操作技能 |
| MCP Server | `docx` | Word MCP 服务器 |

## MCP 工具

| 工具名称 | 描述 |
|---------|------|
| `read_docx` | 读取 Word 文档 |
| `write_docx` | 创建 Word 文档 |
| `add_paragraph` | 添加段落 |
| `get_paragraphs` | 列出段落 |

## 快速开始

### 读取 Word 文档

```
读取 report.docx 文件的内容
```

### 创建 Word 文档

```
创建一个新的 Word 文档，标题为"项目报告"...
```

### 添加段落

```
在文档中添加一个新段落，内容为...
```

## 许可证

MIT
