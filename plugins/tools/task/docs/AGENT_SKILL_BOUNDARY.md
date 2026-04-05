# Agent 与 Skill 功能边界定义

## 核心差异

| 维度 | Agent | Skill |
|------|-------|-------|
| **本质** | 执行者（Stateful Multi-Step Orchestrator） | 规范（Stateless Atomic Capability Specification） |
| **状态** | 有状态（维护执行上下文、历史记录） | 无状态（纯文档，不执行代码） |
| **步骤数** | 多步骤（阶段 1 → 阶段 2 → ... → 输出） | 单步骤（调用即返回结果） |
| **输出** | JSON 结构化结果 + 执行副作用 | Markdown 文档（规范、指南、最佳实践） |
| **调用方式** | `Agent(subagent_type="task:xxx", prompt=...)` | `Skills(task:xxx)` 或被 agent 引用 |
| **生命周期** | 运行时创建 → 执行 → 销毁 | 编译时加载 → 常驻内存 |
| **典型内容** | 工作流定义、决策逻辑、工具调用序列 | 概念解释、字段定义、输出格式、最佳实践 |

---

## 模块边界

| 模块 | Agent 职责 | Skill 职责 |
|------|-----------|-----------|
| **planner** | 执行计划设计 + 格式化写文件 + 用户确认 | 定义 MECE 分解原则和输出格式 |
| **verifier** | 执行任务验收流程 | 定义验收测试最佳实践 |
| **adjuster** | 执行失败调整流程 | 定义升级策略和 Circuit Breaker |
| **prompt-optimizer** | 执行规格说明生成（DCG 方法论） | 定义验收标准设计原则 |
| **loop** | 无（特殊） | PDCA 编排引擎 |
| **explorer-\*** | 执行代码库/架构探索 | 定义探索策略和输出规范 |

---

## 标准模式

### Agent

```yaml
---
skills: [task:xxx]
---
<role>你是 XXX agent</role>
<workflow>阶段 1 → 阶段 2 → ...</workflow>
```

### Skill

```markdown
<scope>适用场景</scope>
<core_principles>核心原则</core_principles>
<output_format>输出格式</output_format>
```

**禁止内容**: 执行步骤编号、流程伪代码、状态转换逻辑

---

## 验收标准

- Agent 包含多步骤工作流，Skill 只包含概念和格式定义
- Agent 前置声明引用对应 Skill
- 执行逻辑在 Agent，规范定义在 Skill，无重复定义
- Agent < 300 行，Skill < 400 行
