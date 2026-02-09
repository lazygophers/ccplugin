---
name: hooks
description: 钩子使用指南 - 当用户需要创建、使用或管理 Claude Code 钩子时自动激活。覆盖钩子的定义、事件类型、配置格式、输入输出和完整示例。
---

# 钩子使用指南

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| **什么是钩子** | 钩子的定义和用途 | [definition.md](definition.md) |
| **事件类型** | 可用事件列表 | [events.md](events.md) |
| **配置格式** | hooks.json 详解 | [config.md](config.md) |
| **钩子输入** | stdin JSON 输入格式 | [input.md](input.md) |
| **钩子输出** | 退出代码和 JSON 输出 | [output.md](output.md) |
| **插件钩子** | 插件集成钩子 | [plugin.md](plugin.md) |
| **MCP 工具** | MCP 工具钩子配置 | [mcp.md](mcp.md) |
| **示例集合** | 完整示例参考 | [examples.md](examples.md) |

## 什么是钩子

钩子是**事件驱动的自动化机制**，在特定事件发生时自动执行自定义逻辑：

- 工具使用前后验证
- 会话开始/结束处理
- 用户提交前确认
- 子进程停止处理

### 钩子特点

| 特性 | 说明 |
|------|------|
| **触发方式** | 事件驱动 |
| **类型** | command / prompt |
| **作用时机** | 事前/事后/替代 |
| **配置位置** | settings.json / 插件 / skills / agents |

## 钩子结构

```
hooks/
└── hooks.json         # 钩子配置文件

# 或在以下位置配置
~/.claude/settings.json     # 用户设置
.claude/settings.json       # 项目设置
.claude/plugin-name.local.md # 本地配置
```

### 标准配置格式

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

## 使用钩子

钩子自动触发，无需手动调用：

| 事件 | 触发时机 |
|------|----------|
| `PreToolUse` | 工具使用前 |
| `PostToolUse` | 工具使用后 |
| `SessionStart` | 会话开始时 |
| `SessionEnd` | 会话结束时 |
| `Stop` | 停止执行时 |
| `SubagentStop` | 子进程停止时 |
| `UserPromptSubmit` | 用户提交输入前 |
| `PreCompact` | 上下文压缩前 |
| `Notification` | 发送通知时 |
| `PermissionRequest` | 权限请求时 |

## 相关技能

- [plugin](../plugin/SKILL.md) - 插件使用
- [commands](../commands/SKILL.md) - 命令使用
- [agents](../agents/SKILL.md) - 代理使用
- [skills](../skills/SKILL.md) - Skills 使用
