---
name: plugin
description: 插件使用指南 - 插件的定义、目录结构、manifest 配置和组件组织。
---

# 插件使用指南

## 什么是插件

插件是**扩展 Claude Code 功能的独立模块**，包含命令、代理、技能和钩子等组件。

## 插件结构

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # 插件清单（必需）
├── commands/                 # 命令目录
├── agents/                  # 代理目录
├── skills/                  # 技能目录
├── hooks/                   # 钩子目录
└── scripts/                 # 脚本目录
```

## plugin.json 配置

```json
{
  "name": "plugin-name",
  "version": "0.0.1",
  "description": "插件描述",
  "commands": ["./commands/"],
  "agents": ["./agents/"],
  "skills": "./skills/"
}
```

## 安装插件

```bash
# 从市场安装
/plugin install plugin-name@ccplugin-market

# 从本地安装
/plugin install ./plugins/plugin-name
```

## 相关技能

- [skills](../skills/skills/SKILL.md) - Skills 使用
- [commands](../skills/commands/SKILL.md) - Commands 使用
- [agents](../skills/agents/SKILL.md) - Agents 使用
