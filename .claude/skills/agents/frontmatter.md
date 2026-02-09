# 代理 Frontmatter

## 标准格式

```yaml
---
name: agent-name
description: 简短描述

# 核心字段
tools: [...]
model: inherit
context: fork
color: "#FF6B6B"

# 权限控制
permissionMode: default
disallowedTools: [...]

# 功能扩展
skills: [...]
hooks: [...]

# 持久化
memory: local
---

# 代理标题

系统提示词...
```

## 字段详解

### name（必需）

代理标识符：

```yaml
---
name: dev          # ✅ 正确
name: code-review   # ✅ 正确
name: Dev          # ❌ 大写
name: dev_agent    # ❌ 下划线
---
```

**要求：**
- 小写字母+连字符
- 最多 64 字符
- 唯一性

### description（必需）

简短描述，用于决定何时委托：

```yaml
---
description: Python 开发专家
description: "代码审查和重构建议"
description: 代码审查专家。主动审查代码质量、安全性和最佳实践。
---
```

**要求：**
- 1-2 句话
- 包含职责关键词
- 最多 1024 字符
- 建议包含 "proactively" 以鼓励主动使用

### tools（可选）

允许的工具列表：

```yaml
---
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### disallowedTools（可选）

要拒绝的工具：

```yaml
---
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
---
```

### model（可选）

使用的模型：

```yaml
---
model: sonnet   # 使用 Sonnet
model: opus     # 使用 Opus
model: haiku    # 使用 Haiku（快速）
model: inherit  # 继承主对话（默认）
---
```

| 值 | 说明 |
|------|------|
| `sonnet` | 平衡能力和速度 |
| `opus` | 最强能力 |
| `haiku` | 快速、低延迟 |
| `inherit` | 使用主对话相同模型 |

### context（可选）

上下文隔离模式：

```yaml
---
context: fork      # 独立上下文（推荐）
context: inherit   # 继承上下文
---
```

### color（可选）

UI 颜色（十六进制）：

```yaml
---
color: "#FF6B6B"   # 红色
color: "#4CAF50"   # 绿色
color: "#2196F3"   # 蓝色
color: "#9C27B0"   # 紫色
---

**颜色选择建议：**
- 绿色（#4CAF50）：开发/构建类
- 橙色（#FF9800）：审查/质量类
- 蓝色（#2196F3）：探索/研究类
- 红色（F44336）：安全/危险类
```

### permissionMode（可选）

权限模式：

```yaml
---
permissionMode: default           # 标准权限检查
permissionMode: acceptEdits      # 自动接受编辑
permissionMode: dontAsk         # 自动拒绝
permissionMode: bypassPermissions # 跳过所有检查
permissionMode: plan            # Plan mode
---

| 模式 | 行为 |
|------|------|
| `default` | 标准权限检查和提示 |
| `acceptEdits` | 自动接受文件编辑 |
| `dontAsk` | 自动拒绝权限提示 |
| `bypassPermissions` | 跳过所有权限检查 |

### skills（可选）

预加载的 skills：

```yaml
---
skills:
  - api-conventions
  - error-handling-patterns
---

**说明：**
- Skills 完整内容注入 subagent 上下文
- 不继承父对话的 skills
- 参考 [Skills](../skills/SKILL.md)
```

### hooks（可选）

限定于此 subagent 的 hooks：

```yaml
---
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
---

参考 [Hooks](../hooks/SKILL.md)
```

### memory（可选）

持久内存范围：

```yaml
---
memory: user     # 用户级（推荐）
memory: project  # 项目级
memory: local    # 本地
---

| 范围 | 位置 | 用途 |
|------|------|------|
| `user` | `~/.claude/agent-memory/<name>/` | 跨项目记忆 |
| `project` | `.claude/agent-memory/<name>/` | 项目共享记忆 |
| `local` | `.claude/agent-memory-local/<name>/` | 本地记忆 |

## 完整示例

```yaml
---
name: code-reviewer
description: 代码审查专家。主动审查代码质量、安全性和最佳实践。
context: fork
tools: Read, Grep, Glob, Bash
model: inherit
color: "#FF9800"
permissionMode: default
skills:
  - python-coding
  - security-best-practices
memory: user
---

# 代码审查专家

你是高级代码审查专家，确保代码质量和安全的高标准。

## 工作流程

1. 运行 git diff 查看最近更改
2. 专注于修改的文件
3. 立即开始审查

## 审查清单

- 代码清晰可读
- 函数和变量命名良好
- 无重复代码
- 适当的错误处理
- 无暴露的密钥或 API 密钥
- 实现输入验证
- 良好的测试覆盖

按优先级组织反馈：
- 严重问题（必须修复）
- 警告（应该修复）
- 建议（考虑改进）

包含具体的修复示例。
```

## 字段速查表

| 字段 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | 是 | - | 唯一标识符 |
| `description` | 是 | - | 委托触发条件 |
| `tools` | 否 | 全部 | 允许的工具 |
| `disallowedTools` | 否 | 无 | 要拒绝的工具 |
| `model` | 否 | inherit | 使用的模型 |
| `context` | 否 | fork | 上下文模式 |
| `color` | 否 | - | UI 颜色 |
| `permissionMode` | 否 | default | 权限模式 |
| `skills` | 否 | 无 | 预加载 skills |
| `hooks` | 否 | 无 | 生命周期 hooks |
| `memory` | 否 | 无 | 持久内存 |
