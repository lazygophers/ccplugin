# Agent 与 Skill 功能边界定义文档

## 文档概述

本文档明确定义 Task 插件中 Agent 和 Skill 的职责边界，消除功能重叠，统一实现路径。

**核心定义**：
- **Agent** = 多步骤有状态流程执行者（Stateful Multi-Step Orchestrator）
- **Skill** = 单步无状态原子能力规范（Stateless Atomic Capability Specification）

**文档导航**：
- **模块详细分析** → [AGENT_SKILL_BOUNDARY-ANALYSIS.md](./AGENT_SKILL_BOUNDARY-ANALYSIS.md)

---

## 一、核心差异矩阵

| 维度 | Agent | Skill |
|------|-------|-------|
| **职责** | 编排执行流程，调用工具和其他 agents | 定义规范和标准，提供知识和指导 |
| **状态** | 有状态（维护执行上下文、历史记录） | 无状态（纯文档，不执行代码） |
| **步骤数** | 多步骤（阶段 1 → 阶段 2 → ... → 输出） | 单步骤（调用即返回结果） |
| **输出** | JSON 结构化结果 + 执行副作用 | Markdown 文档（规范、指南、最佳实践） |
| **调用方式** | `Agent(agent="task:xxx", prompt=...)` | `Skills(task:xxx)` 或被 agent 引用 |
| **生命周期** | 运行时创建 → 执行 → 销毁 | 编译时加载 → 常驻内存 |
| **典型内容** | 工作流定义、决策逻辑、工具调用序列 | 概念解释、字段定义、输出格式、最佳实践 |
| **使用场景** | Loop 流程中的各个阶段 | 为 agent 提供知识支持 |

---

## 二、模块评估总结

详细分析参见 [AGENT_SKILL_BOUNDARY-ANALYSIS.md](./AGENT_SKILL_BOUNDARY-ANALYSIS.md#二现有模块分析)

### 边界清晰的模块（✅）

| 模块 | Agent | Skill | 说明 |
|------|-------|-------|------|
| **planner** | 执行计划设计流程 | 定义MECE分解原则和输出格式 | 无重叠 |
| **verifier** | 执行任务验收流程 | 定义验收测试最佳实践 | 导航型架构 |
| **adjuster** | 执行失败调整流程 | 定义升级策略和Circuit Breaker | 无重叠 |
| **finalizer** | 执行资源清理流程 | 定义防御性清理原则 | 无重叠 |
| **plan-formatter** | 执行JSON→Markdown转换 | 定义模板格式规范 | 单一职责 |
| **loop** | 无（特殊） | PDCA编排引擎 | 特殊情况 |

### 需优化的模块（⚠️）

| 模块 | 问题 | 影响 | 优化方案 |
|------|------|------|---------|
| **prompt-optimizer** | Skill包含执行逻辑 | 文件过大（320行），违反单一职责 | 移除阶段1-4执行步骤，保留6项原则和评分标准 |
| **execute** | 缺少对应Agent | 执行逻辑散落在loop中 | 方案A：创建agent / 方案B：简化为纯规范 |

---

## 二、现有模块分析（精简版）

完整分析参见 [AGENT_SKILL_BOUNDARY-ANALYSIS.md](./AGENT_SKILL_BOUNDARY-ANALYSIS.md)

**关键示例**: 详见 [AGENT_SKILL_BOUNDARY-ANALYSIS.md](./AGENT_SKILL_BOUNDARY-ANALYSIS.md#21-planner-模块)

---

## 三、优化建议

详细优化方案参见 [AGENT_SKILL_BOUNDARY-ANALYSIS.md](./AGENT_SKILL_BOUNDARY-ANALYSIS.md#四优化方案)

### prompt-optimizer 模块
- **问题**: Skill 包含执行逻辑（阶段 1-4 步骤、伪代码）
- **方案**: 保留 6 项原则、5W1H 框架、评分标准；移除执行步骤到 Agent

### execute 模块
- **问题**: 有 Skill 但无对应 Agent
- **方案A**: 创建 `task:execute` agent（推荐复杂编排）
- **方案B**: 简化 Skill 为纯规范（推荐简单场景）

---

## 四、统一实现路径

完整规范参见 [AGENT_SKILL_BOUNDARY-ANALYSIS.md](./AGENT_SKILL_BOUNDARY-ANALYSIS.md#五统一实现路径)

### Agent 标准模式
```yaml
---
skills: [task:xxx]
---
<role>你是 XXX agent</role>
<workflow>阶段 1 → 阶段 2 → ...</workflow>
```

### Skill 标准结构
```markdown
<scope>适用场景</scope>
<core_principles>核心原则</core_principles>
<output_format>输出格式</output_format>
```

**禁止内容**: ❌ 执行步骤编号 ❌ 流程伪代码 ❌ 状态转换逻辑

---

## 五、验收标准

详细检查清单参见 [AGENT_SKILL_BOUNDARY-ANALYSIS.md](./AGENT_SKILL_BOUNDARY-ANALYSIS.md#六验收标准)

### 边界清晰度
- [ ] Agent 包含多步骤工作流
- [ ] Skill 只包含概念和格式定义
- [ ] Agent 前置声明引用对应 Skill

### 功能完整性
- [ ] 执行逻辑在 Agent
- [ ] 规范定义在 Skill
- [ ] 无重复定义

### 文档质量
- [ ] Agent < 300 行
- [ ] Skill < 400 行（主文件，采用导航型架构）

---

## 六、总结

| 职责 | Agent | Skill |
|------|-------|-------|
| **本质** | 执行者（Executor） | 规范（Specification） |
| **内容** | 工作流、状态、工具调用 | 原则、格式、字段定义 |
| **生命周期** | 运行时 | 编译时 |

### 发现的问题
- **prompt-optimizer**: Skill 包含执行逻辑 → 需重构
- **execute**: 缺少对应 Agent → 需创建或简化

### 优化收益
- ✅ 职责单一 ✅ 易于维护 ✅ 易于理解 ✅ 减少冗余 ✅ 提升质量

---

**文档版本**: v1.0
**创建日期**: 2026-03-21
**负责人**: Task Plugin Team
