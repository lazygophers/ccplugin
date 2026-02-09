---
name: plugin-skills
description: 插件使用指南 - 当用户需要了解如何创建、使用或管理 Claude Code 插件时自动激活。覆盖插件的定义、目录结构、manifest 配置、组件组织和本地配置。
context: fork
agent: plugin-agent
---

# 插件使用指南

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| **什么是插件** | 插件的定义和价值 | [definition.md](definition.md) |
| **目录结构** | 标准插件目录结构 | [structure.md](structure.md) |
| **Manifest 配置** | plugin.json 详解 | [manifest.md](manifest.md) |
| **本地配置** | 项目级插件配置 | [local-config.md](local-config.md) |

## 插件开发子技能

| 技能 | 作用 | Agent |
|------|------|-------|
| [插件开发](plugin-development/SKILL.md) | 创建新插件 | [plugin](../../agents/plugin) |
| [插件脚本开发](plugin-script-development/SKILL.md) | Python CLI 脚本 | [script](../../agents/script) |
| [插件命令开发](plugin-command-development/SKILL.md) | 自定义命令 | [command](../../agents/command) |
| [插件技能开发](plugin-skill-development/SKILL.md) | Skills 编写 | [skill](../../agents/skill) |
| [插件钩子开发](plugin-hook-development/SKILL.md) | 事件钩子 | [hook](../../agents/hook) |
| [插件 MCP 开发](plugin-mcp-development/SKILL.md) | MCP 服务器 | [mcp](../../agents/mcp) |
| [插件 LSP 开发](plugin-lsp-development/SKILL.md) | LSP 配置 | [lsp](../../agents/lsp) |
| [插件 AGENT.md 开发](plugin-agent-development/SKILL.md) | 系统提示注入 | [agent-doc](../../agents/agent-doc) |

## 什么是插件

插件是**扩展 Claude Code 功能的独立模块**，包含命令、代理、技能和钩子等组件。

### 插件组成

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # 插件清单（必需）
├── commands/                # 命令目录
│   └── *.md               # 命令文件
├── agents/                 # 代理目录
│   └── *.md               # 代理文件
├── skills/                 # 技能目录
│   └── skill-name/        # 技能目录
│       └── SKILL.md       # 技能入口
├── hooks/                  # 钩子目录
│   └── hooks.json         # 钩子配置
├── scripts/                # 脚本目录
│   └── main.py            # CLI 入口
├── .mcp.json             # MCP 配置（可选）
├── .lsp.json             # LSP 配置（可选）
├── AGENT.md               # 代理文档（可选）
└── README.md              # 插件文档（可选）
```

### 插件类型

| 类型 | 用途 | 示例 |
|------|------|------|
| **工具插件** | 提供特定工具能力 | git、semantic |
| **语言插件** | 语言开发支持 | python、golang |
| **框架插件** | 框架开发支持 | react、gin |
| **主题插件** | UI/输出样式 | style-dark |
| **功能插件** | 增强核心功能 | notify、version |

## 组件对比

| 组件 | 类型 | 作用 | 使用方式 |
|------|------|------|----------|
| **Command** | Skill | 可重用工作流 | `/command` |
| **Agent** | Subagent | 隔离执行上下文 | `@agent` |
| **Skill** | Skill | 参考知识和操作 | 上下文加载 |
| **Hook** | Hook | 事件驱动自动化 | 自动触发 |
| **MCP** | MCP | 外部服务连接 | 工具调用 |

## 插件使用

### 安装插件

```bash
# 从市场安装
/plugin install task@ccplugin-market
/plugin install semantic@ccplugin-market

# 从本地安装
/plugin install ./plugins/task

# 强制重新安装
/plugin install task@ccplugin-market --force
```

### 查看已安装插件

```bash
# 插件列表
ls ~/.claude/plugins/

# 查看插件清单
cat ~/.claude/plugins/cache/task@*/.claude-plugin/plugin.json
```

## 相关技能

- [skills](skills/SKILL.md) - Skills 使用
- [commands](commands/SKILL.md) - Commands 使用
- [agents](agents/SKILL.md) - Agents 使用
- [hooks](hooks/SKILL.md) - Hooks 使用