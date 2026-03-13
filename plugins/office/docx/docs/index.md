# office-docx 插件文档

## 概述

office-docx 是一个基于 MCP 协议的 Word 文件操作插件，提供对 .docx 文件的完整读写支持。包含 37+ MCP 基础工具和额外的包装层功能。

## 架构

```
plugins/office/docx/
├── .claude-plugin/
│   └── plugin.json          # 插件配置和 MCP 服务定义
├── scripts/
│   ├── __init__.py
│   └── wrapper.py           # 包装层（格式转换、批量处理、模板、分析）
├── skills/
│   └── office-docx-skills/
│       ├── SKILL.md          # 技能定义
│       └── examples.md       # 使用示例
├── docs/
│   ├── index.md              # 文档首页
│   └── api.md                # API 文档
├── pyproject.toml            # 依赖配置
├── README.md
└── llms.txt
```

## 功能层次

### 第一层：MCP 基础工具（37+ 工具）
通过 office-word-mcp-server 提供的原生 Word 操作：文档管理、内容编辑、表格操作、格式化等。

### 第二层：包装层额外功能
通过 scripts/wrapper.py 提供：
- **格式转换**：docx <-> Markdown、docx -> PDF
- **批量处理**：批量读取信息、批量格式转换
- **模板生成**：创建模板、基于模板生成文档
- **智能分析**：文档结构分析、关键信息提取

## 相关链接

- [API 文档](api.md)
- [office-word-mcp-server GitHub](https://github.com/GongRzhe/Office-Word-MCP-Server)
