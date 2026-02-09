---
name: agent-template
description: Agent 模板 - 演示 Sub-Agent 的标准格式和用法
---

# Agent Template

## 快速参考

| 字段 | 说明 |
|------|------|
| `name` | Agent 名（小写） |
| `description` | 简短描述 |
| `context` | fork 或 inherit |
| `allowed-tools` | 允许的工具列表 |
| `auto-activate` | 自动激活规则 |

## Frontmatter 完整格式

```yaml
---
name: agent-name
description: Agent 简短描述（1-2句话）

# 可选字段
context: fork                    # fork（独立）或 inherit（继承）
allowed-tools:                   # 工具权限列表
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
color: "#FF6B6B"                # UI 颜色
auto-activate:
  when: "用户需要XXX"           # 激活条件
---

# Agent 标题

Agent 系统提示词...

## 能力
- 能力 1
- 能力 2

## 约束
- 约束 1
- 约束 2

## 工作流程
1. 步骤 1
2. 步骤 2
3. 步骤 3
```

## 完整示例

```markdown
---
name: dev
description: Python 开发专家
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
color: "#4CAF50"
---

# Python 开发专家

你是 Python 开发专家，帮助用户编写高质量的 Python 代码。

## 能力
- 代码审查和重构建议
- 单元测试编写指导
- 性能优化建议
- 错误排查和修复

## 约束
- 使用 Python 3.11+ 类型注解
- 遵循 PEP 8 规范
- 优先使用 lib.logging

## 工作流程
1. 理解用户需求
2. 分析代码问题
3. 提供解决方案
4. 生成修复代码
```

## 工具权限

| 类别 | 工具 |
|------|------|
| 文件操作 | `Read`, `Write`, `Edit`, `Glob` |
| 命令执行 | `Bash` |
| 搜索 | `Grep`, `Glob` |
| 网络 | `WebFetch`, `WebSearch` |
| 任务 | `Task`, `TaskList`, `TaskUpdate` |

## 注意事项

1. **明确职责**：一个 Agent 只做一件事
2. **限制工具**：只授予必要的权限
3. **使用 context: fork**：避免上下文污染
4. **提供 AGENT.md**：注入详细文档

## 相关资源

- [Agents Skill](../../.claude/skills/agents/SKILL.md)
- [AGENT.md](../../AGENT.md)
