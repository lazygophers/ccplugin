---
name: agents
description: 代理使用指南 - 当用户需要创建、使用或管理 Claude Code 子代理时自动激活。覆盖代理的定义、内置代理、完整配置选项、使用模式和示例。
context: fork
agent: agent
---

# 代理使用指南

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| **什么是代理** | 代理的定义和价值 | [definition.md](definition.md) |
| **内置代理** | Explore/Plan/General-purpose | [builtin.md](builtin.md) |
| **Frontmatter** | YAML 前置元数据详解 | [frontmatter.md](frontmatter.md) |
| **使用代理** | 代理调用和管理 | [usage.md](usage.md) |
| **代理协作** | 多代理协作模式 | [collaboration.md](collaboration.md) |
| **示例集合** | 完整示例参考 | [examples.md](examples.md) |

## 什么是代理

代理是**自主执行复杂任务的子进程**，具有独立的上下文和工具集：

```
@dev          # 自主开发代理
@review       # 代码审查代理
@explore      # 代码探索代理
```

### 代理特点

| 特性 | 说明 |
|------|------|
| **触发方式** | 以 `@` 开头 |
| **自主性** | 多步骤自主决策 |
| **工具集** | 可配置的权限 |
| **上下文** | 可隔离（fork）或继承 |

## 代理核心价值

1. **保留上下文** - 将探索和实现保持在主对话之外
2. **强制约束** - 限制 subagent 可以使用的工具
3. **跨项目复用** - 用户级 subagents 在所有项目中可用
4. **专门化行为** - 为特定领域使用专注的系统提示
5. **控制成本** - 将任务路由到更快、更便宜的模型

## 代理结构

```
agents/
└── agent-name.md    # 代理文件

# 文件内容
---
name: agent-name
description: 简短描述
tools: [...]
model: inherit
---

# 代理标题

系统提示词...
```

## 使用代理

```bash
@dev              # 使用默认配置
@dev "任务描述"    # 带任务描述
```

## 相关技能

- [plugin](../plugin-skills/SKILL.md) - 插件使用
- [commands](../commands/SKILL.md) - 命令使用
- [skills](../skills/SKILL.md) - Skills 使用
- [hooks](../hooks/SKILL.md) - Hooks 使用