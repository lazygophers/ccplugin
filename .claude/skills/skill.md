---
name: skill
description: Skills 使用指南 - Skills 的定义、目录结构、YAML frontmatter 和渐进披露模式。
---

# Skills 使用指南

## 什么是 Skill

Skill 是**扩展 Claude Code 能力的模块化知识单元**，以目录形式组织。

## Skill 结构

```
skill-name/
├── SKILL.md                 # 入口文件（必需）
├── topic.md                 # 支持文件（可选）
└── subdir/
    └── detail.md            # 子目录文件（可选）
```

## Frontmatter 格式

```yaml
---
name: skill-name
description: 简短描述
context: fork
agent: agent-name
---
```

## 渐进披露模式

1. **SKILL.md** - 提供概览和导航
2. **子文档** - 提供详细指南
3. **路径变量** - 使用 `${CLAUDE_PLUGIN_ROOT}` 引用

## 相关技能

- [plugin](../skills/plugin/SKILL.md) - 插件使用
- [commands](../skills/commands/SKILL.md) - Commands 使用
- [agents](../skills/agents/SKILL.md) - Agents 使用
