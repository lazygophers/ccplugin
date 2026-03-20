---
status: pending
created_at: 2026-03-20T00:00:00
title: Task 插件优化实施计划
total_tasks: 7
completed_tasks: 0
source: deep-research
---

# Task 插件优化实施计划

## 1. 概览

基于深度研究结果，本计划覆盖 8 个优化方向中的 7 个（T8 多编排器延后评估），分 6 批次实施。所有改动基于现有 task 插件 v0.0.180 的 PDCA 循环架构，保持 loop 入口不变。

### 现状分析

| 维度 | 现状 |
|------|------|
| 插件版本 | v0.0.180 |
| Agents | 5 个（planner / verifier / adjuster / finalizer / prompt-optimizer） |
| Skills | 9 个目录（loop / planner / verifier / adjuster / finalizer / execute / deep-iteration / plan-formatter / prompt-optimizer） |
| 已完成优化 | P0-0 深度迭代模式 |
| 外部依赖 | memory 插件（SQLite + URI 寻址，已独立部署） |

### 约束条件

1. **入口不变**：loop 仍然是唯一入口，不改变用户接口
2. **单一职责**：每个 skill 目录只负责一个功能域
3. **并行上限**：最多 2 个任务并行执行
4. **审批前置**：每个文件级别的改动必须由用户批准后才能执行
5. **质量验证**：所有新建/修改的 skill 文件必须通过 AI 理解性检查

---

## 2. 执行优先级

### 优先级评估矩阵

| 优先级 | 功能 | ROI | 合规风险 | 实施难度 | 建议批次 |
|--------|------|-----|----------|----------|----------|
| **P0-1** | HITL 审批机制 | 高 | **EU AI Act 2026/8/2 截止** | 中 | 第1批 |
| **P0-2** | 可观测性仪表板 | 高 | 成本控制必需 | 低 | 第1批 |
| **P0-3** | 记忆工程 | 高 | 无 | 高 | 第2批 |
| **P1-1** | 智能并行调度 | 中 | 无 | 中 | 第3批 |
| **P1-2** | 检查点恢复 | 中 | 无 | 中 | 第3批 |
| **P1-3** | 自愈机制 | 中 | 无 | 低 | 第4批 |
| **P2-1** | 上下文版本化 | 低 | 无 | 低 | 第5批 |
| **P2-2** | 多编排器架构 | 低 | 无 | 高 | 第6批（延后） |

### 优先级调整说明

- **HITL 提前至第1批**：EU AI Act 合规截止日期 2026/8/2，距今仅 4.5 个月，最紧迫
- **记忆工程降至第2批**：设计复杂度高，且需要 T2 可观测性的指标数据来丰富记忆内容
- **自愈机制降至第4批**：依赖 T1（审批日志）和 T5（检查点恢复上下文），需前置完成

---

## 3. 依赖关系图

```
                    ┌─────────────────┐
                    │     开始         │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐       ┌──────────▼──────────┐
    │  T1: HITL 审批     │       │  T2: 可观测性仪表板  │
    │  (P0-1)            │       │  (P0-2)              │
    └─────────┬─────────┘       └──────────┬──────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  T3: 记忆工程      │
                   │  (P0-3)            │
                   │  依赖: T2          │
                   └─────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐       ┌──────────▼──────────┐
    │  T4: 智能并行调度  │       │  T5: 检查点恢复      │
    │  (P1-1)            │       │  (P1-2)              │
    └─────────┬─────────┘       └──────────┬──────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  T6: 自愈机制      │
                   │  (P1-3)            │
                   │  依赖: T1, T5      │
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │  T7: 上下文版本化  │
                   │  (P2-1)            │
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │  T8: 多编排器      │
                   │  (P2-2, 延后)      │
                   └─────────┬─────────┘
                             │
                    ┌────────▼────────┐
                    │     完成         │
                    └─────────────────┘
```

### 依赖关系表

| 任务 | 前置依赖 | 说明 |
|------|----------|------|
| T1 | 无 | 独立实施 |
| T2 | 无 | 独立实施 |
| T3 | T2 | 使用 T2 的指标数据丰富记忆内容 |
| T4 | 无 | 独立实施（建议 T3 后） |
| T5 | 无 | 独立实施（建议 T3 后） |
| T6 | T1, T5 | 自愈操作需审批日志（T1），恢复需检查点（T5） |
| T7 | 无 | 独立实施（建议 T3 后） |
| T8 | 全部 | 延后评估 |

### 并行分组

| 批次 | 并行组 | 最大并行度 |
|------|--------|-----------|
| 第1批 | [T1, T2] | 2 |
| 第2批 | [T3] | 1 |
| 第3批 | [T4, T5] | 2 |
| 第4批 | [T6] | 1 |
| 第5批 | [T7] | 1 |
| 第6批 | [T8] | 延后 |

---

## 4. 详细任务分解

---

### 第1批：P0 合规 + 成本（T1 与 T2 并行）

---

#### T1: HITL 审批机制（Human-in-the-Loop）

**优先级**：P0-1 | **难度**：中 | **预估时间**：2-3 小时

**任务描述**：在 loop 关键决策点插入人工审批机制，实现风险分级审批策略（auto / review / mandatory 三级），满足 EU AI Act 2026 合规要求。

**输入**：
- 现有 loop 流程：`skills/loop/detailed-flow.md`（7 个阶段的伪代码）
- 现有计划确认：`skills/loop/flows/plan.md`（已有 AskUserQuestion 基础）
- EU AI Act 要求：高风险 AI 系统必须有人工监督机制

**输出**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/hitl/SKILL.md` | 新建 | HITL 审批主技能，定义审批流程和 API |
| `skills/hitl/risk-classifier.md` | 新建 | 风险分级规则定义 |
| `skills/hitl/approval-policies.md` | 新建 | 审批策略（三级审批阈值和行为） |
| `skills/loop/detailed-flow.md` | 修改 | 在执行阶段和调整阶段插入审批检查点 |
| `skills/loop/flows/plan.md` | 修改 | 增强计划确认，增加风险评估摘要 |

**子任务分解**：

| ID | 子任务 | 文件 | 依赖 |
|----|--------|------|------|
| T1.1 | 定义风险分级规则（auto/review/mandatory 三级分类） | `skills/hitl/risk-classifier.md` | 无 |
| T1.2 | 实现审批策略和审批流程（超时处理、记录追溯） | `skills/hitl/SKILL.md`, `skills/hitl/approval-policies.md` | T1.1 |
| T1.3 | 集成到 loop 流程（计划确认增强、执行前审批、危险操作拦截） | 修改 `detailed-flow.md`, `flows/plan.md` | T1.2 |

**风险分级规则设计**：

| 风险等级 | 操作类型 | 审批策略 | 示例 |
|---------|---------|---------|------|
| **auto**（自动通过） | 只读/生成类操作 | 无需用户确认 | 代码生成、测试运行、文件读取 |
| **review**（需审查） | 写入/修改类操作 | 展示摘要后用户确认 | 文件修改、依赖安装、配置变更 |
| **mandatory**（强制审批） | 破坏性/不可逆操作 | 详细展示后强制用户确认 | 文件删除、数据库变更、git force push、生产部署 |

**验收标准**：

| ID | 类型 | 描述 | 验证方法 |
|----|------|------|---------|
| AC1.1 | exact_match | 风险操作（文件删除、git force push）100% 触发 mandatory 审批 | 模拟测试 |
| AC1.2 | exact_match | 低风险操作（代码生成、测试运行）自动通过，无用户干扰 | 模拟测试 |
| AC1.3 | exact_match | 审批超时（可配置，默认 5 分钟）自动阻塞并提醒用户 | 流程验证 |
| AC1.4 | exact_match | 审批记录追溯：每次审批决策记录在计划文件的审批日志中 | 输出检查 |
| AC1.5 | exact_match | 通过质量检查命令验证 AI 可正确理解 HITL 技能 | 命令验证 |

**审批点设计**：
- 用户审批 T1.1 风险分级规则定义（决定哪些操作需要审批）
- 用户审批 T1.2 审批策略（决定审批超时和行为）
- 用户审批 T1.3 对 `detailed-flow.md` 的修改 diff

---

#### T2: 可观测性仪表板（Observability Dashboard）

**优先级**：P0-2 | **难度**：低 | **预估时间**：1.5-2 小时

**任务描述**：增强现有 `monitoring.md` 的基础监控框架，构建结构化可观测系统，实时输出 token 消耗、agent 并行度、任务耗时、失败率等指标，并在任务完成时生成成本报告。

**输入**：
- 现有监控框架：`skills/loop/monitoring.md`（已有 MonitoringCollector 类、KPI 定义、日志格式）
- 现有状态前缀格式：`[MindFlow·${任务}·${步骤}/${迭代}·${状态}]`
- loop 执行流程中的关键事件点

**输出**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/observability/SKILL.md` | 新建 | 可观测性主技能，定义收集/报告/查询 API |
| `skills/observability/metrics-collector.md` | 新建 | 指标体系定义和收集规范 |
| `skills/observability/cost-report.md` | 新建 | 成本报告模板和生成逻辑 |
| `skills/loop/monitoring.md` | 修改 | 集成可观测性技能调用 |

**子任务分解**：

| ID | 子任务 | 文件 | 依赖 |
|----|--------|------|------|
| T2.1 | 定义指标体系（token 消耗、agent 并行度、任务耗时、失败率、成功率） | `skills/observability/metrics-collector.md` | 无 |
| T2.2 | 实现成本报告生成逻辑（每迭代/每任务/总计三级） | `skills/observability/cost-report.md` | T2.1 |
| T2.3 | 实现可观测性主技能并集成到 loop 监控 | `skills/observability/SKILL.md`, 修改 `monitoring.md` | T2.2 |

**指标体系设计**：

| 指标类别 | 指标名称 | 数据类型 | 采集点 |
|---------|---------|---------|--------|
| **成本** | token_input / token_output | integer | 每次 Agent 调用 |
| **成本** | estimated_cost_usd | float | 每次迭代结束 |
| **效率** | task_duration_ms | integer | 任务开始/结束 |
| **效率** | parallel_utilization | float (0-1) | 执行阶段 |
| **质量** | task_success_rate | float (0-1) | 验证阶段 |
| **质量** | iteration_count | integer | 每次迭代 |
| **稳定性** | failure_count | integer | 失败调整阶段 |
| **稳定性** | stall_count | integer | 停滞检测 |

**成本报告格式**：

```json
{
  "summary": {
    "total_iterations": 3,
    "total_tasks": 5,
    "total_duration_ms": 480000,
    "total_tokens": { "input": 125000, "output": 45000 },
    "estimated_cost_usd": 0.85,
    "success_rate": 0.8
  },
  "per_iteration": [...],
  "per_task": [...]
}
```

**验收标准**：

| ID | 类型 | 描述 | 验证方法 |
|----|------|------|---------|
| AC2.1 | exact_match | 每次迭代结束输出结构化指标摘要（JSON 格式） | 输出检查 |
| AC2.2 | exact_match | 任务完成时输出总成本报告（包含 token、耗时、成功率） | 输出检查 |
| AC2.3 | exact_match | 并行度监控实时可查（当前/最大/平均三个维度） | 流程验证 |
| AC2.4 | exact_match | 指标格式为 JSON，字段定义清晰，可被外部工具解析 | 格式验证 |
| AC2.5 | exact_match | 通过质量检查命令验证 AI 可正确理解可观测性技能 | 命令验证 |

**审批点设计**：
- 用户审批 T2.1 指标体系定义（决定收集哪些数据）
- 用户审批 T2.3 对 `monitoring.md` 的修改 diff

---

### 第2批：P0 记忆工程（串行）

---

#### T3: 记忆工程（Memory Engineering）

**优先级**：P0-3 | **难度**：高 | **预估时间**：3-4 小时

**任务描述**：通过 memory-bridge 适配层集成现有 memory 插件（SQLite + URI 寻址），实现三层记忆系统（短期/情节/语义），支持跨会话知识复用。在任务完成后自动保存经验，新任务规划时自动检索相似历史经验。

**输入**：
- memory 插件能力：URI 结构化记忆、SQLite 存储、版本控制、智能推荐、Hooks 自动化
- memory 插件 URI 命名空间：`project://`、`workflow://`、`system://`
- planner 上下文学习系统：`skills/planner/planner-context-learning.md`（三层 ACE 策略）
- T2 可观测性的指标收集能力（用于丰富记忆内容）

**输出**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/memory-bridge/SKILL.md` | 新建 | 记忆桥接主技能，连接 task 与 memory 插件 |
| `skills/memory-bridge/memory-schema.md` | 新建 | 三层记忆数据模型定义 |
| `skills/memory-bridge/retrieval-strategy.md` | 新建 | 记忆检索策略（相似任务、失败模式） |
| `skills/planner/planner-context-learning.md` | 修改 | 在 Tier 3 冷记忆层集成 memory-bridge |
| `skills/loop/detailed-flow.md` | 修改 | 初始化阶段加载记忆、完成阶段保存记忆 |

**子任务分解**：

| ID | 子任务 | 文件 | 依赖 |
|----|--------|------|------|
| T3.1 | 设计三层记忆数据模型（短期=当前会话上下文、情节=成功/失败经验、语义=项目知识图谱） | `skills/memory-bridge/memory-schema.md` | 无 |
| T3.2 | 实现记忆桥接技能（适配 memory 插件 URI 接口） | `skills/memory-bridge/SKILL.md` | T3.1 |
| T3.3 | 定义检索策略（相似任务匹配、失败模式匹配、项目知识关联） | `skills/memory-bridge/retrieval-strategy.md` | T3.1 |
| T3.4 | 集成到 planner 上下文学习（Tier 3）和 loop 初始化/完成阶段 | 修改现有文件 | T3.2, T3.3 |

**三层记忆模型设计**：

| 层级 | 名称 | 生命周期 | URI 路径 | 内容 |
|------|------|---------|---------|------|
| **短期** | Working Memory | 当前会话 | `task://session/{id}/context` | 当前任务上下文、中间状态 |
| **情节** | Episodic Memory | 跨会话持久 | `task://episodes/{hash}` | 成功方案、失败经验、耗时/成本指标 |
| **语义** | Semantic Memory | 长期持久 | `task://knowledge/{domain}` | 项目架构知识、技术栈约定、团队偏好 |

**记忆写入时机**：
- **短期记忆**：每个阶段转换时自动更新
- **情节记忆**：任务完成/失败时自动保存（含指标数据，来自 T2）
- **语义记忆**：用户确认有价值的知识时保存

**记忆检索时机**：
- **规划阶段**：检索相似任务的历史方案
- **失败调整阶段**：检索相同错误的历史解决方案
- **初始化阶段**：加载项目语义记忆

**验收标准**：

| ID | 类型 | 描述 | 验证方法 |
|----|------|------|---------|
| AC3.1 | exact_match | 任务完成后自动保存成功经验（任务描述 + 方案 + 结果 + 指标） | 流程验证 |
| AC3.2 | exact_match | 新任务规划时自动检索相似历史经验并展示给 planner | 流程验证 |
| AC3.3 | exact_match | 失败模式记录并在后续规划中预警（匹配错误签名） | 模拟测试 |
| AC3.4 | exact_match | 跨会话记忆可持久化和恢复（通过 memory 插件 URI） | 读写验证 |
| AC3.5 | exact_match | memory-bridge 作为适配层隔离版本差异，不直接依赖 memory 内部实现 | 代码审查 |
| AC3.6 | exact_match | 通过质量检查命令验证 AI 可正确理解记忆桥接技能 | 命令验证 |

**审批点设计**：
- 用户审批 T3.1 三层记忆数据模型（决定跨会话共享的数据结构，最关键）
- 用户审批 T3.2 记忆桥接 API 设计
- 用户审批 T3.4 对 `planner-context-learning.md` 和 `detailed-flow.md` 的修改 diff

---

### 第3批：P1 效率 + 稳定（T4 与 T5 并行）

---

#### T4: 智能并行调度（Intelligent Parallelism）

**优先级**：P1-1 | **难度**：中 | **预估时间**：2-3 小时

**任务描述**：基于任务复杂度和资源占用动态调整并行度（2-5 个槽位），替代当前固定 2 并行的策略。自动分析任务的文件依赖、预估复杂度，智能决定并行/串行执行。

**研究依据**：Google Research (2026) 显示可并行任务并行执行提升 +81%，顺序任务错误并行执行降低 -70%。

**输入**：
- 现有执行流程：`skills/execute/SKILL.md`
- 现有改进规划：`docs/IMPROVEMENTS-2026.md`（P0-1 智能并行调度优化）
- loop 中的任务调度逻辑（`detailed-flow.md` 执行阶段）

**输出**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/parallel-scheduler/SKILL.md` | 新建 | 并行调度主技能 |
| `skills/parallel-scheduler/complexity-analyzer.md` | 新建 | 任务复杂度分析器 |
| `skills/loop/detailed-flow.md` | 修改 | 执行阶段使用智能调度替代固定并行 |

**子任务分解**：

| ID | 子任务 | 文件 | 依赖 |
|----|--------|------|------|
| T4.1 | 实现任务复杂度分析器（文件数、依赖深度、预估耗时、文件冲突检测） | `skills/parallel-scheduler/complexity-analyzer.md` | 无 |
| T4.2 | 实现动态并行度计算和调度策略（槽位管理、优先级队列） | `skills/parallel-scheduler/SKILL.md` | T4.1 |
| T4.3 | 集成到 loop 执行阶段（替换固定并行逻辑） | 修改 `skills/loop/detailed-flow.md` | T4.2 |

**复杂度评估维度**：

| 维度 | 权重 | 低复杂度 | 高复杂度 |
|------|------|---------|---------|
| 涉及文件数 | 30% | 1-2 个文件 | 5+ 个文件 |
| 依赖深度 | 25% | 无前置依赖 | 3+ 层依赖链 |
| 预估 token | 20% | < 10K tokens | > 50K tokens |
| 文件冲突 | 25% | 无共享文件 | 有共享文件（禁止并行） |

**并行度计算规则**：

| 场景 | 并行度 | 条件 |
|------|--------|------|
| 全部低复杂度 | 最大（可配置，默认 2，最大 5） | 无文件冲突 |
| 混合复杂度 | 2 | 高复杂度任务独占 1 槽位 |
| 存在文件冲突 | 1（串行） | 冲突任务必须串行 |
| 用户配置覆盖 | 用户指定值 | 尊重用户约束 |

**验收标准**：

| ID | 类型 | 描述 | 验证方法 |
|----|------|------|---------|
| AC4.1 | exact_match | 可并行任务自动识别并并行执行（基于文件冲突检测） | 模拟测试 |
| AC4.2 | exact_match | 并行度动态调整（简单任务多并行、复杂任务少并行） | 场景验证 |
| AC4.3 | exact_match | 资源冲突检测：同文件写入的任务禁止并行 | 冲突测试 |
| AC4.4 | quantitative_threshold | 并行度上限可配置（默认 2，最大 5） | 配置验证 |
| AC4.5 | exact_match | 通过质量检查命令验证 AI 可正确理解并行调度技能 | 命令验证 |

**审批点设计**：
- 用户审批 T4.2 并行度上限配置（用户约束 vs 性能优化的权衡）
- 用户审批 T4.3 对 `detailed-flow.md` 的修改 diff

---

#### T5: 检查点恢复（Checkpoint Recovery）

**优先级**：P1-2 | **难度**：中 | **预估时间**：2-3 小时

**任务描述**：在 loop 的每个阶段转换时自动保存检查点状态，支持任务中断后从断点恢复，避免重复已完成的工作。

**研究依据**：长时间运行的 agent 在 35 分钟后成功率显著下降，检查点恢复可有效缓解此问题。

**输入**：
- loop 执行流程：`skills/loop/detailed-flow.md`（7 个阶段转换）
- 计划文件格式：`.claude/plans/*.md`（YAML frontmatter + Markdown）
- 现有改进规划：`docs/IMPROVEMENTS-2026.md`（P1-1 长任务检查点恢复）

**输出**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/checkpoint/SKILL.md` | 新建 | 检查点主技能 |
| `skills/checkpoint/state-serializer.md` | 新建 | 状态序列化/反序列化规范 |
| `skills/loop/detailed-flow.md` | 修改 | 每阶段转换时保存检查点，初始化时检测恢复 |

**子任务分解**：

| ID | 子任务 | 文件 | 依赖 |
|----|--------|------|------|
| T5.1 | 设计检查点状态模型（迭代号、已完成任务列表、当前阶段、planner 结果、执行上下文） | `skills/checkpoint/state-serializer.md` | 无 |
| T5.2 | 实现检查点保存/恢复/清理逻辑 | `skills/checkpoint/SKILL.md` | T5.1 |
| T5.3 | 集成到 loop（初始化时检测恢复、每阶段转换时保存、完成时清理） | 修改 `skills/loop/detailed-flow.md` | T5.2 |

**检查点状态模型**：

```json
{
  "checkpoint_id": "ckpt-{task_hash}-{timestamp}",
  "version": 1,
  "task_description": "用户任务描述",
  "iteration": 3,
  "current_phase": "execution",
  "plan_file": ".claude/plans/xxx-3.md",
  "planner_result": { "tasks": [...], "dependencies": {...} },
  "completed_tasks": ["T1", "T2"],
  "failed_tasks": ["T3"],
  "pending_tasks": ["T4"],
  "metrics": { "total_tokens": 50000, "elapsed_ms": 120000 },
  "created_at": "2026-03-20T10:30:00Z"
}
```

**检查点生命周期**：
- **保存**：每个阶段转换时写入 `.claude/checkpoints/{task_hash}.json`
- **检测**：loop 初始化时扫描 `.claude/checkpoints/` 目录
- **恢复**：用户确认后跳过已完成任务，从断点继续
- **清理**：任务完成后删除对应检查点文件

**验收标准**：

| ID | 类型 | 描述 | 验证方法 |
|----|------|------|---------|
| AC5.1 | exact_match | 每个阶段转换自动保存检查点到 `.claude/checkpoints/` | 文件检查 |
| AC5.2 | exact_match | loop 启动时检测未完成检查点并提示用户选择恢复或重新开始 | 流程验证 |
| AC5.3 | exact_match | 恢复后跳过已完成任务（T1、T2），仅执行剩余任务（T3、T4） | 恢复测试 |
| AC5.4 | exact_match | 检查点文件为 JSON 格式，包含完整恢复信息 | 格式验证 |
| AC5.5 | exact_match | 任务完成后自动清理检查点文件 | 清理验证 |
| AC5.6 | exact_match | 通过质量检查命令验证 AI 可正确理解检查点技能 | 命令验证 |

**审批点设计**：
- 用户审批 T5.1 检查点状态模型设计
- 用户审批 T5.3 对 `detailed-flow.md` 的修改 diff

---

### 第4批：P1 自愈（串行）

---

#### T6: 自愈机制（Self-Healing）

**优先级**：P1-3 | **难度**：低 | **预估时间**：1-2 小时

**任务描述**：增强现有 adjuster 的 4 级升级策略（Retry -> Debug -> Replan -> Ask User），在 Level 1 和 Level 2 之间插入 Level 1.5 Self-Healing 层，自动检测和修复常见可预知错误。

**输入**：
- 现有 adjuster 策略：`skills/adjuster/adjuster-strategies.md`（4 级升级策略）
- 现有 adjuster agent：`agents/adjuster.md`
- 现有错误处理：`skills/loop/error-handling.md`
- 现有改进规划：`docs/IMPROVEMENTS-2026.md`（P2-1 自主恢复模式）

**输出**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/adjuster/self-healing.md` | 新建 | 自愈策略定义（可修复错误目录 + 修复脚本） |
| `skills/adjuster/adjuster-strategies.md` | 修改 | 新增 Level 1.5 Self-Healing 层 |
| `agents/adjuster.md` | 修改 | 增加自愈能力描述和触发条件 |

**子任务分解**：

| ID | 子任务 | 文件 | 依赖 |
|----|--------|------|------|
| T6.1 | 定义可自愈错误目录和对应修复方案 | `skills/adjuster/self-healing.md` | 无 |
| T6.2 | 集成到 adjuster 分级策略（Level 1 和 Level 2 之间插入 Level 1.5） | 修改 `adjuster-strategies.md`, `agents/adjuster.md` | T6.1 |

**可自愈错误目录**：

| 错误类型 | 错误签名匹配 | 自动修复方案 | 风险等级 |
|---------|------------|-------------|---------|
| 依赖缺失 | `ModuleNotFoundError`, `package not found` | 自动安装（npm/pip/go get） | review |
| 端口占用 | `EADDRINUSE`, `address already in use` | 自动切换到可用端口 | auto |
| 目录不存在 | `ENOENT`, `No such file or directory` | 自动创建缺失目录 | auto |
| 权限不足 | `EACCES`, `Permission denied` | 提示用户修复权限 | mandatory |
| 配置缺失 | `config not found`, `missing configuration` | 从模板生成默认配置 | review |
| 网络超时 | `ETIMEDOUT`, `connection timed out` | 指数退避重试（最多 3 次） | auto |

**升级策略（修订后）**：

```
Level 1: Retry（调整后重试）
     ↓ 连续 1 次相同错误且匹配可自愈目录
Level 1.5: Self-Healing（自动修复）  ← 新增
     ↓ 自动修复失败
Level 2: Debug（深度诊断）
     ↓ 连续 2 次 Debug 无效
Level 3: Replan（重新规划）
     ↓ 连续 2 次 Replan 无效
Level 4: Ask User（请求指导）
```

**验收标准**：

| ID | 类型 | 描述 | 验证方法 |
|----|------|------|---------|
| AC6.1 | exact_match | 依赖缺失错误自动触发安装修复（npm/pip/go） | 错误模拟 |
| AC6.2 | exact_match | 端口占用自动切换到可用端口 | 错误模拟 |
| AC6.3 | exact_match | 配置缺失自动从模板生成默认配置 | 错误模拟 |
| AC6.4 | exact_match | 自愈操作根据风险等级与 T1 HITL 联动（auto 自动执行、review 需确认） | 联动验证 |
| AC6.5 | exact_match | 通过质量检查命令验证 AI 可正确理解自愈策略 | 命令验证 |

**审批点设计**：
- 用户审批 T6.1 可自愈错误目录（决定哪些错误允许自动修复）
- 用户审批 T6.2 对 `adjuster-strategies.md` 的修改 diff

---

### 第5批：P2 上下文版本化（串行）

---

#### T7: 上下文版本化（Context Versioning）

**优先级**：P2-1 | **难度**：低 | **预估时间**：1-2 小时

**任务描述**：保存规划上下文的历史版本，支持回滚和对比。利用 Git 追踪 `.claude/context/` 目录中的上下文快照。

**输入**：
- planner 上下文学习：`skills/planner/planner-context-learning.md`（ACE 三层策略）
- 现有改进规划：`docs/IMPROVEMENTS-2026.md`（P1-2 上下文版本控制）
- Git 版本控制能力

**输出**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/context-versioning/SKILL.md` | 新建 | 上下文版本化主技能 |
| `skills/planner/planner-context-learning.md` | 修改 | 集成版本化（规划前保存快照） |

**子任务分解**：

| ID | 子任务 | 文件 | 依赖 |
|----|--------|------|------|
| T7.1 | 实现上下文版本快照（保存/列表/回滚/对比 API） | `skills/context-versioning/SKILL.md` | 无 |
| T7.2 | 集成到 planner（每次规划前自动保存快照，支持回滚到指定版本） | 修改 `planner-context-learning.md` | T7.1 |

**版本化机制设计**：

| 操作 | 存储位置 | 触发时机 |
|------|---------|---------|
| 保存快照 | `.claude/context/snapshots/{timestamp}.json` | 每次规划前 |
| 列表版本 | 读取 snapshots 目录 | 用户请求 |
| 回滚 | 恢复指定快照到当前上下文 | 用户请求 |
| 对比 | JSON diff 两个版本 | 用户请求 |

**快照内容**：

```json
{
  "snapshot_id": "ctx-{timestamp}",
  "created_at": "2026-03-20T10:30:00Z",
  "trigger": "pre-planning",
  "iteration": 2,
  "context": {
    "tier1_hot": { "language": "Go", "framework": "Gin", ... },
    "tier2_warm": { "test_strategy": "table-driven", ... },
    "tier3_cold": { "last_plan_hash": "abc123", ... }
  }
}
```

**验收标准**：

| ID | 类型 | 描述 | 验证方法 |
|----|------|------|---------|
| AC7.1 | exact_match | 每次规划前自动创建上下文快照到 `.claude/context/snapshots/` | 文件检查 |
| AC7.2 | exact_match | 支持查看历史版本列表（按时间排序） | 命令验证 |
| AC7.3 | exact_match | 支持回滚到指定版本（恢复上下文状态） | 回滚测试 |
| AC7.4 | exact_match | 版本对比可展示两个版本的 JSON diff | 对比验证 |
| AC7.5 | exact_match | 通过质量检查命令验证 AI 可正确理解上下文版本化技能 | 命令验证 |

**审批点设计**：
- 用户审批 T7.1 版本化 API 设计
- 用户审批 T7.2 对 `planner-context-learning.md` 的修改 diff

---

### 第6批：P2 多编排器（延后评估）

---

#### T8: 多编排器架构（Multi-Orchestrator）

**优先级**：P2-2 | **难度**：高 | **预估时间**：待评估

**任务描述**：支持不同编排策略（串行/并行/混合），根据任务类型自动选择最优编排模式。

**延后理由**：
1. 当前 loop 的 PDCA 模式已能覆盖大部分场景
2. 实施复杂度高，需要重构 loop 核心架构
3. ROI 低，需要更多实际使用数据支撑决策
4. 建议在 T1-T7 全部完成后，基于可观测性数据（T2）评估是否实施

**预期输出**（待确认）：
- `skills/orchestrator/SKILL.md` - 编排器选择技能
- `skills/orchestrator/strategies/serial.md` - 串行策略
- `skills/orchestrator/strategies/parallel.md` - 并行策略
- `skills/orchestrator/strategies/hybrid.md` - 混合策略

---

## 5. 完整文件改动清单

### 新建文件（15 个）

| # | 文件路径（相对于 `plugins/tools/task/`） | 任务 | 说明 |
|---|----------------------------------------|------|------|
| 1 | `skills/hitl/SKILL.md` | T1 | HITL 审批主技能 |
| 2 | `skills/hitl/risk-classifier.md` | T1 | 风险分级规则（auto/review/mandatory） |
| 3 | `skills/hitl/approval-policies.md` | T1 | 审批策略和行为定义 |
| 4 | `skills/observability/SKILL.md` | T2 | 可观测性主技能 |
| 5 | `skills/observability/metrics-collector.md` | T2 | 指标体系和收集规范 |
| 6 | `skills/observability/cost-report.md` | T2 | 成本报告模板和生成逻辑 |
| 7 | `skills/memory-bridge/SKILL.md` | T3 | 记忆桥接主技能 |
| 8 | `skills/memory-bridge/memory-schema.md` | T3 | 三层记忆数据模型 |
| 9 | `skills/memory-bridge/retrieval-strategy.md` | T3 | 记忆检索策略 |
| 10 | `skills/parallel-scheduler/SKILL.md` | T4 | 并行调度主技能 |
| 11 | `skills/parallel-scheduler/complexity-analyzer.md` | T4 | 任务复杂度分析器 |
| 12 | `skills/checkpoint/SKILL.md` | T5 | 检查点主技能 |
| 13 | `skills/checkpoint/state-serializer.md` | T5 | 状态序列化规范 |
| 14 | `skills/adjuster/self-healing.md` | T6 | 自愈策略和错误目录 |
| 15 | `skills/context-versioning/SKILL.md` | T7 | 上下文版本化主技能 |

### 修改文件（7 个）

| # | 文件路径（相对于 `plugins/tools/task/`） | 涉及任务 | 修改内容摘要 |
|---|----------------------------------------|---------|-------------|
| 1 | `skills/loop/detailed-flow.md` | T1,T2,T3,T4,T5 | 集成 HITL 审批检查点、可观测性指标采集、记忆加载/保存、智能调度、检查点保存/恢复 |
| 2 | `skills/loop/flows/plan.md` | T1,T3 | 增强计划确认（风险评估摘要）、集成记忆检索 |
| 3 | `skills/loop/monitoring.md` | T2 | 集成可观测性技能调用，替换基础 MonitoringCollector |
| 4 | `skills/planner/planner-context-learning.md` | T3,T7 | Tier 3 集成 memory-bridge、集成上下文版本化 |
| 5 | `skills/adjuster/adjuster-strategies.md` | T6 | 新增 Level 1.5 Self-Healing 层 |
| 6 | `agents/adjuster.md` | T6 | 增加自愈能力描述和触发条件 |
| 7 | `docs/IMPROVEMENTS-2026.md` | 全部 | 更新各优化项状态（规划中 -> 进行中/已完成） |

### 删除文件

无。

### 新建目录（6 个）

| 目录路径（相对于 `plugins/tools/task/`） | 任务 |
|----------------------------------------|------|
| `skills/hitl/` | T1 |
| `skills/observability/` | T2 |
| `skills/memory-bridge/` | T3 |
| `skills/parallel-scheduler/` | T4 |
| `skills/checkpoint/` | T5 |
| `skills/context-versioning/` | T7 |

---

## 6. 风险评估和缓解策略

### 风险矩阵

| # | 风险描述 | 概率 | 影响 | 风险等级 | 缓解策略 |
|---|---------|------|------|---------|---------|
| R1 | HITL 过度干预导致效率下降（用户被频繁打断） | 中 | 高 | **高** | 合理设定风险阈值，确保 auto 级别覆盖 80%+ 操作；提供"信任模式"快捷选项 |
| R2 | loop 核心流程修改引入回归（`detailed-flow.md` 被 5 个任务修改） | 中 | 高 | **高** | 每次修改后用质量检查命令验证 AI 理解；T1-T5 按批次依次修改，每批只改一个方面 |
| R3 | 记忆系统与 memory 插件版本不兼容 | 低 | 高 | **中** | memory-bridge 作为适配层隔离版本差异，仅通过 URI 接口交互 |
| R4 | 智能并行度超过用户约束（CLAUDE.md 要求最多 2 个） | 中 | 中 | **中** | 硬编码用户约束检查，动态并行度不超过用户配置上限；可观测性日志审计 |
| R5 | 检查点文件占用磁盘空间（长期积累） | 低 | 低 | **低** | 任务完成后自动清理；设置最大保留数（默认 10 个） |
| R6 | 自愈机制误判导致错误修复 | 低 | 中 | **低** | 自愈操作与 HITL 联动，review/mandatory 级别需用户确认；自愈后自动验证修复有效性 |
| R7 | EU AI Act 合规截止日前未完成 HITL | 低 | 高 | **中** | T1 作为最高优先级第1批实施，预留充足时间 |

### `detailed-flow.md` 修改策略

由于 `detailed-flow.md` 被 5 个任务涉及，采用分层修改策略避免冲突：

| 批次 | 修改任务 | 修改区域 | 修改内容 |
|------|---------|---------|---------|
| 第1批 | T1 | 执行阶段、调整阶段 | 插入 HITL 审批检查 |
| 第1批 | T2 | 初始化阶段、完成阶段 | 插入指标采集和报告 |
| 第2批 | T3 | 初始化阶段、完成阶段 | 插入记忆加载和保存 |
| 第3批 | T4 | 执行阶段 | 替换固定并行为智能调度 |
| 第3批 | T5 | 所有阶段转换处 | 插入检查点保存，初始化增加恢复检测 |

---

## 7. 实施时间估算

| 批次 | 任务 | 并行模式 | 预估时间 | 累计时间 |
|------|------|---------|---------|---------|
| 第1批 | T1 (HITL) + T2 (可观测性) | 并行 | 2-3 小时 | 3 小时 |
| 第2批 | T3 (记忆工程) | 串行 | 3-4 小时 | 7 小时 |
| 第3批 | T4 (并行调度) + T5 (检查点) | 并行 | 2-3 小时 | 10 小时 |
| 第4批 | T6 (自愈) | 串行 | 1-2 小时 | 12 小时 |
| 第5批 | T7 (版本化) | 串行 | 1-2 小时 | 14 小时 |
| 第6批 | T8 (多编排器) | 延后 | 待评估 | - |
| **总计** | **T1-T7** | | **12-16 小时** | |

---

## 8. 审批检查清单

用户可逐项审批以下内容：

### 总体方案审批

- [ ] 优先级排序是否合理（P0 > P1 > P2）
- [ ] 依赖关系是否正确
- [ ] 并行分组是否合理（均不超过 2 个）
- [ ] 文件改动清单是否完整

### 第1批审批项

- [ ] T1.1 风险分级规则（auto/review/mandatory 三级分类）
- [ ] T1.2 审批策略设计（超时、记录、行为）
- [ ] T1.3 `detailed-flow.md` 修改方案
- [ ] T1.3 `flows/plan.md` 修改方案
- [ ] T2.1 指标体系定义（8 个指标）
- [ ] T2.2 成本报告格式（JSON）
- [ ] T2.3 `monitoring.md` 修改方案

### 第2批审批项

- [ ] T3.1 三层记忆数据模型（短期/情节/语义）
- [ ] T3.2 记忆桥接 API 设计
- [ ] T3.3 检索策略定义
- [ ] T3.4 `planner-context-learning.md` 修改方案
- [ ] T3.4 `detailed-flow.md` 修改方案

### 第3批审批项

- [ ] T4.1 复杂度评估维度和权重
- [ ] T4.2 并行度上限配置
- [ ] T4.3 `detailed-flow.md` 修改方案
- [ ] T5.1 检查点状态模型设计
- [ ] T5.2 检查点生命周期管理
- [ ] T5.3 `detailed-flow.md` 修改方案

### 第4批审批项

- [ ] T6.1 可自愈错误目录（6 类错误）
- [ ] T6.2 `adjuster-strategies.md` 修改方案（Level 1.5 插入）
- [ ] T6.2 `agents/adjuster.md` 修改方案

### 第5批审批项

- [ ] T7.1 版本化 API 设计
- [ ] T7.2 `planner-context-learning.md` 修改方案

### 第6批审批项

- [ ] T8 是否实施（基于 T1-T7 完成后的数据评估）

---

## 9. 质量验证命令

每个新建/修改的 skill 文件完成后，使用以下命令验证 AI 可正确理解：

```bash
claude --settings ~/.claude/settings.glm-4.5-flash.json -p "<待测试的 skill 内容>" --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

验证标准：
- 返回结果非空且有意义
- AI 能正确识别 skill 的用途和 API
- AI 能正确理解验收标准和约束条件
