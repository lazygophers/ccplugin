# Planner 参考指南

本文档是 Planner Agent 和 Skills 选择指南的索引。

<navigation>

Agent 选择指南在 [planner-agents-guide.md](planner-agents-guide.md) 中，包括可用 Agents 列表、Agent 选择原则、多角色协作和自定义 Agent。当你需要为任务选择合适的执行 Agent 时参考此文档。

Skills 选择指南在 [planner-skills-guide.md](planner-skills-guide.md) 中，包括通用 Skills（Python、Go、TypeScript、JavaScript）、专用 Skills、Skills 选择原则、选择示例、常见组合模式和自定义 Skills。当你需要为任务选择合适的技能集时参考此文档。

</navigation>

<agent_skills_quick_ref>

## Agent 和 Skills 快速参考

### 必填性

| 场景 | Agent | Skills |
|------|-------|--------|
| tasks 不为空 | **必填** | **必填**（至少1个） |
| tasks 为空 | 不需要 | 不需要 |

### 格式

- **带来源**：`name（中文注释）@source`
  - 示例：`golang:dev（Go开发专家）@golang`

- **不带来源**：`name（中文注释）`
  - 示例：`coder（开发者）`

### 来源选择

| Agent 类型 | 来源示例 | 使用场景 |
|-----------|---------|---------|
| Task 内置 | `task:planner`、`task:explorer-frontend` | Loop 内部、探索任务 |
| 语言插件 | `golang:dev`、`python:test` | 专业开发/测试 |
| 通用 | `coder（开发者）`、`tester（测试员）` | 通用开发/测试 |
| 项目自定义 | `ml-engineer（机器学习工程师）` | 项目特定角色 |

### 验证检查

1. ✓ agent 非空字符串
2. ✓ agent 包含 "（" 字符
3. ✓ skills 为非空数组
4. ✓ 每个 skill 包含 "（" 字符

</agent_skills_quick_ref>
