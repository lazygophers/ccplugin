---
name: plugin
description: 插件使用指南 - 当用户需要了解如何创建、使用或管理 Claude Code 插件时自动激活。覆盖插件的定义、目录结构、manifest 配置、组件组织和本地配置。
---

# 插件使用指南

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| **什么是插件** | 插件的定义和价值 | [definition.md](definition.md) |
| **目录结构** | 标准插件目录结构 | [structure.md](structure.md) |
| **Manifest 配置** | plugin.json 详解 | [manifest.md](manifest.md) |
| **本地配置** | 项目级插件配置 | [local-config.md](local-config.md) |

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
