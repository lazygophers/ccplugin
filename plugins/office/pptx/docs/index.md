# office-pptx 插件文档

## 概述

office-pptx 是一个基于 MCP 协议的 PowerPoint 文件操作插件，提供对 .pptx 文件的完整读写支持。

## 架构

```
plugins/office/pptx/
├── .claude-plugin/
│   └── plugin.json          # 插件配置和 MCP 服务定义
├── skills/
│   └── office-pptx-skills/
│       ├── SKILL.md          # 技能定义
│       └── examples.md       # 使用示例
├── docs/
│   ├── index.md              # 文档首页
│   └── api.md                # API 文档
├── README.md
└── llms.txt
```

## MCP 服务

使用 [Office-PowerPoint-MCP-Server](https://github.com/GongRzhe/Office-PowerPoint-MCP-Server) 提供 PowerPoint 操作能力，通过 `uvx --from office-powerpoint-mcp-server ppt_mcp_server` 启动。

## 相关链接

- [API 文档](api.md)
- [Office-PowerPoint-MCP-Server GitHub](https://github.com/GongRzhe/Office-PowerPoint-MCP-Server)
