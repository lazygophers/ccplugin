---
name: command
description: 命令使用指南 - 命令的定义、frontmatter、参数处理和交互模式。
---

# 命令使用指南

## 什么是命令

命令是**以 `/` 开头的可执行功能入口**，用于触发特定操作。

## 命令结构

```
commands/
└── command-name.md    # 命令文件
```

## Frontmatter 格式

```yaml
---
name: command-name
description: 简短描述
argument-hint: [arg]
allowed-tools: Bash(...)
---
```

## 使用命令

```bash
/command-name
/command-name arg1
```

## 相关技能

- [plugin](../skills/plugin/SKILL.md) - 插件使用
- [skills](../skills/skills/SKILL.md) - Skills 使用
- [agents](../skills/agents/SKILL.md) - Agents 使用
