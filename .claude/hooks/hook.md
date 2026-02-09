---
name: hook
description: 钩子使用指南 - 钩子的定义、事件类型、配置格式和输入输出。
---

# 钩子使用指南

## 什么是钩子

钩子是**事件驱动的自动化机制**，在特定事件发生时自动执行自定义逻辑。

## 钩子结构

```
hooks/
└── hooks.json         # 钩子配置文件
```

## 配置格式

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          { "type": "command", "command": "..." },
          { "type": "prompt", "prompt": "..." }
        ]
      }
    ]
  }
}
```

## 事件类型

| 事件 | 触发时机 |
|------|----------|
| `PreToolUse` | 工具使用前 |
| `PostToolUse` | 工具使用后 |
| `SessionStart` | 会话开始时 |
| `SessionEnd` | 会话结束时 |

## 相关技能

- [plugin](../skills/plugin/SKILL.md) - 插件使用
- [skills](../skills/skills/SKILL.md) - Skills 使用
- [commands](../skills/commands/SKILL.md) - Commands 使用
