---
name: skills-skills
description: Skills 使用指南 - 当需要了解如何创建、管理或使用 Claude Code Skills 时自动激活。覆盖 Skills 的定义、目录结构、YAML frontmatter、渐进披露模式和上下文隔离。
context: fork
agent: skill
---

# Skills 使用指南

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| **什么是 Skill** | Skills 的定义和价值 | [definition.md](definition.md) |
| **目录结构** | 标准 Skill 目录结构 | [structure.md](structure.md) |
| **Frontmatter** | YAML 前置元数据规范 | [frontmatter.md](frontmatter.md) |
| **渐进披露** | 多文件分层加载模式 | [progressive-disclosure.md](progressive-disclosure.md) |

## 什么是 Skill

Skill 是**扩展 Claude Code 能力的模块化知识单元**，以目录形式组织：

- **SKILL.md** - 必需入口文件（YAML frontmatter + 内容）
- **支持文件** - 可选的参考文档、模板等

### Skills vs Subagents

| 方面 | Skill | Subagent |
|------|-------|----------|
| **是什么** | 可重用的说明和知识 | 隔离执行上下文 |
| **上下文** | 加载到主对话 | 独立上下文窗口 |
| **结果** | 即时可用 | 返回摘要 |
| **适合** | 参考材料、可调用工作流 | 读取多文件、并行任务 |

### Skills 类型

| 类型 | 用途 | 示例 |
|------|------|------|
| **参考 Skill** | 提供知识（如代码规范） | python 规范 |
| **操作 Skill** | 执行工作流（如 /deploy） | git 提交 |

## 上下文模式（context）

### context: fork

在隔离的上下文中运行技能：

```yaml
---
name: my-skill
description: 我的技能
context: fork
---
```

**使用场景**：
- 需要上下文隔离的操作
- 不希望影响主对话历史
- 敏感操作

### context: inherit（默认）

继承主对话上下文：

```yaml
---
name: my-skill
description: 我的技能
---
```

**使用场景**：
- 需要访问当前上下文
- 与主对话协作

## Agent 字段

### 指定子代理

```yaml
---
name: my-skill
description: 我的技能
agent: Explore
---
```

### 可用 Agent 类型

| Agent | 用途 |
|-------|------|
| `Explore` | 代码探索、分析 |
| `general-purpose` | 通用任务 |
| `Plan` | 架构设计 |
| `Bash` | 命令执行 |

## Frontmatter 完整字段

```yaml
---
name: skill-name              # Skill 标识（小写+连字符）
description: 简短描述          # 1-2句话
# 可选字段
argument-hint: [arg]          # 参数提示
disable-model-invocation: true # 仅手动调用
user-invocable: false         # 仅 Claude 调用
allowed-tools: Read, Grep     # 允许的工具
context: fork                 # fork | inherit（默认）
agent: Explore               # 子代理类型
hooks: {...}                 # 限定钩子
---
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `name` | 技能标识 | 必需 |
| `description` | 简短描述 | 必需 |
| `argument-hint` | 参数提示 | 无 |
| `disable-model-invocation` | 仅手动调用 | false |
| `user-invocable` | 用户可调用 | true |
| `allowed-tools` | 允许的工具 | 全部 |
| `context` | 上下文模式 | inherit |
| `agent` | 指定子代理 | 无 |
| `hooks` | 限定钩子 | 无 |

## 渐进披露模式

Skills 支持**渐进披露（Progressive Disclosure）**：

1. **SKILL.md** - 提供概览和导航
2. **子文档** - 提供详细指南
3. **路径变量** - 使用 `${CLAUDE_PLUGIN_ROOT}` 引用

## 相关技能

- [plugin](../plugin-skills/SKILL.md) - 插件使用
- [commands](../commands/SKILL.md) - 命令使用
- [agents](../agents-skills/SKILL.md) - 代理使用
- [hooks](../hooks/SKILL.md) - 钩子使用