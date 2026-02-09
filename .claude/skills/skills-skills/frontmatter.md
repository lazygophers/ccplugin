# YAML Frontmatter

## 标准格式

```yaml
---
name: skill-name
description: Brief description of what this skill does and when to use it
---

# Skill Name

Skill instructions...
```

## 字段定义

### name（必需）

**要求：**
- 最多 64 个字符
- 仅小写字母，数字和连字符
- 不能包含 XML 标签
- 不能包含保留词："anthropic"、"claude"

```yaml
# ✅ 正确
name: python-coding
name: git-workflow
name: security-review-2025

# ❌ 错误
name: PythonCoding        # 大写
name: git_workflow        # 下划线
name: Python-Coding      # 驼峰
```

### description（必需）

**要求：**
- 不能为空
- 最多 1024 个字符
- 不能包含 XML 标签
- 应包含技能功能和触发条件

```yaml
# ✅ 良好
description: Python coding standards for this project. Use when writing Python code or when the user asks about coding conventions.

# ✅ 简洁
description: Explains code with visual diagrams. Use when explaining how code works.

# ❌ 避免
description: This is a skill.     # 太笼统
description: ""                   # 空值
```

### argument-hint（可选）

自动完成期间显示的参数提示：

```yaml
argument-hint: [issue-number]
argument-hint: [filename] [format]
argument-hint: [domain] [action]
```

### disable-model-invocation（可选）

仅手动调用（防止自动触发）：

```yaml
# 用于有副作用的工作流
disable-model-invocation: true

# 默认值：false
# 设置为 true 后，仅可通过 /skill-name 调用
```

### user-invocable（可选）

仅 Claude 调用（从菜单隐藏）：

```yaml
# 用于背景知识
user-invocable: false

# 默认值：true
# 设置为 false 后，仅 Claude 自动调用，不可手动调用
```

### allowed-tools（可选）

技能激活时允许的工具：

```yaml
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
```

**完整列表：**
```
Read, Write, Edit, Bash, Grep, Glob,
WebFetch, WebSearch, WebSearchLocal,
ReadMcpResourceTool, ListMcpResourcesTool,
Task, TaskList, TaskGet, TaskUpdate,
SendMessage
```

### context（可选）

分叉上下文运行：

```yaml
context: fork    # 在隔离子代理中运行
context: inherit # 继承主上下文（默认）
```

### agent（可选）

子代理类型（需要 `context: fork`）：

```yaml
context: fork
agent: Explore    # 探索代理
agent: Plan       # 规划代理
agent: general-purpose # 通用代理（默认）
```

### hooks（可选）

限定于此技能的钩子：

```yaml
hooks:
  PreToolUse:
    - type: prompt
      prompt: "Confirm before executing"
```

## 完整示例

### 手动工作流

```yaml
---
name: deploy
description: Deploy application to production
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Deploy Application

Deploy steps:
1. Run tests: `bash scripts/test.sh`
2. Build: `bash scripts/build.sh`
3. Deploy: `bash scripts/deploy.sh`
4. Verify: `bash scripts/verify.sh`
```

### 自动指导

```yaml
---
name: python-coding
description: Python coding standards for this project. Use when writing Python code.
user-invocable: false
context: inherit
---

# Python Coding Standards

## Type Hints
Always use type hints with Python 3.11+.

## Import Order
1. Standard library
2. Third-party packages
3. Local imports
```

### 子代理任务

```yaml
---
name: security-review
description: Conduct comprehensive security review
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
hooks:
  PostToolUse:
    - type: command
      command: "log_review_result.sh"
---

# Security Review Checklist

Review the codebase for security vulnerabilities:
1. Check authentication mechanisms
2. Verify input validation
3. Test for injection attacks
4. Examine data encryption
```
