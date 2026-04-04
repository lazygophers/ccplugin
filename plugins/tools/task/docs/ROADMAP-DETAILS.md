# Task Plugin Roadmap - 详细内容

本文档包含 ROADMAP.md 的详细实施内容，包括任务详情和风险分析。

---

## Phase 1: P0 合规 + 成本（立即实施）

### T1: HITL 审批机制（Human-in-the-Loop）

**优先级**: P0-1 / P1-4
**状态**: ✅ 已完成（100%）
**完成时间**: 2026-03-21
**合规要求**: EU AI Act 2026/8/2 截止
**预估工作量**: 2-3 小时

**核心目标**:
在 loop 关键决策点插入人工审批机制，满足 EU AI Act 高风险 AI 系统人工监督要求。

**风险分级策略**:
| 风险等级 | 操作类型 | 审批策略 | 示例 |
|---------|---------|---------|------|
| **auto** | 只读/生成类 | 自动通过 | 代码生成、测试运行、文件读取 |
| **review** | 写入/修改类 | 展示摘要后确认 | 文件修改、依赖安装、配置变更 |
| **mandatory** | 破坏性/不可逆 | 详细展示强制确认 | 文件删除、数据库变更、git force push、生产部署 |

**已完成内容**:
- [x] 创建 `skills/hitl/risk-classifier.md`（风险分级规则）
- [x] 创建 `skills/hitl/approval-policies.md`（审批策略）
- [x] 修改 `skills/loop/detailed-flow.md`（集成审批检查点）
- [x] 修改 `skills/loop/flows/plan.md`（增加风险评估摘要）

**验收标准**:
- ✅ 风险操作（文件删除、git force push）100% 触发 mandatory 审批
- ✅ 低风险操作（代码生成、测试运行）自动通过，无用户干扰
- ✅ 审批超时（默认 5 分钟）自动阻塞并提醒用户
- ✅ 审批记录追溯：每次审批决策记录在计划文件的审批日志中

**研究依据**: Oracle/AWS/Microsoft HITL implementations

---

### T2: 可观测性仪表板（Observability Dashboard）

**优先级**: P0-2 / P2-4
**状态**: ✅ 已完成（100%）
**完成时间**: 2026-03-21
**预估工作量**: 1.5-2 小时

**核心目标**:
构建结构化可观测系统，实时输出 token 消耗、agent 并行度、任务耗时、失败率等指标，并在任务完成时生成成本报告。

**指标体系**:
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

**成本报告格式**:
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

**已完成内容**:
- [x] 创建 `skills/observability/metrics-collector.md`（指标收集规范）
- [x] 创建 `skills/observability/cost-report.md`（成本报告生成逻辑）
- [x] 修改 `skills/loop/monitoring.md`（集成可观测性调用）

**验收标准**:
- ✅ 每次迭代结束输出结构化指标摘要（JSON 格式）
- ✅ 任务完成时输出总成本报告（包含 token、耗时、成功率）
- ✅ 并行度监控实时可查（当前/最大/平均三个维度）
- ✅ 指标格式为 JSON，字段定义清晰，可被外部工具解析

---

## Phase 2: P0 记忆工程（近期实施）

### T3: 记忆工程（Memory Engineering）

**优先级**: P0-3 / P2-5
**状态**: ✅ 已完成（100%）
**完成时间**: 2026-03-21
**依赖**: T2 可观测性（使用指标数据丰富记忆）
**预估工作量**: 3-4 小时

**核心目标**:
通过 memory-bridge 适配层集成现有 memory 插件（SQLite + URI 寻址），实现三层记忆系统（短期/情节/语义），支持跨会话知识复用。

**三层记忆模型**:
| 层级 | 名称 | 生命周期 | URI 路径 | 内容 |
|------|------|---------|---------|------|
| **短期** | Working Memory | 当前会话 | `task://session/{id}/context` | 当前任务上下文、中间状态 |
| **情节** | Episodic Memory | 跨会话持久 | `task://episodes/{hash}` | 成功方案、失败经验、耗时/成本指标 |
| **语义** | Semantic Memory | 长期持久 | `task://knowledge/{domain}` | 项目架构知识、技术栈约定、团队偏好 |

**记忆操作时机**:

*写入*:
- **短期记忆**: 每个阶段转换时自动更新
- **情节记忆**: 任务完成/失败时自动保存（含指标数据，来自 T2）
- **语义记忆**: 用户确认有价值的知识时保存

*检索*:
- **规划阶段**: 检索相似任务的历史方案
- **失败调整阶段**: 检索相同错误的历史解决方案
- **初始化阶段**: 加载项目语义记忆

**已完成内容**:
- [x] ~~创建 `skills/memory-bridge/`（已移除，记忆功能内置于 loop 初始化阶段）~~
- [x] 修改 `skills/planner/planner-context-learning.md`（Tier 3 集成记忆检索）
- [x] 修改 `skills/loop/detailed-flow.md`（初始化加载记忆、完成保存记忆）

**验收标准**:
- ✅ 任务完成后自动保存成功经验（任务描述 + 方案 + 结果 + 指标）
- ✅ 新任务规划时自动检索相似历史经验并展示给 planner
- ✅ 失败模式记录并在后续规划中预警（匹配错误签名）
- ✅ 跨会话记忆可持久化和恢复（通过 memory 插件 URI）
- ✅ memory-bridge 作为适配层隔离版本差异，不直接依赖 memory 内部实现

**研究依据**: Context Engineering - RAG → 3-tier evolution

---

## Phase 3: P1 效率 + 稳定（中期规划）

### T4: 智能并行调度（Intelligent Parallelism）

**优先级**: P1-1
**状态**: ✅ 已完成（100%）
**完成时间**: 2026-03-21
**预估工作量**: 2-3 小时

**核心目标**:
基于任务复杂度和资源占用动态调整并行度（2-5 个槽位），替代当前固定 2 并行的策略。自动分析任务的文件依赖、预估复杂度，智能决定并行/串行执行。

**复杂度评估维度**:
| 维度 | 权重 | 低复杂度 | 高复杂度 |
|------|------|---------|---------|
| 涉及文件数 | 30% | 1-2 个文件 | 5+ 个文件 |
| 依赖深度 | 25% | 无前置依赖 | 3+ 层依赖链 |
| 预估 token | 20% | < 10K tokens | > 50K tokens |
| 文件冲突 | 25% | 无共享文件 | 有共享文件（禁止并行） |

**并行度计算规则**:
| 场景 | 并行度 | 条件 |
|------|--------|------|
| 全部低复杂度 | 最大（可配置，默认 2，最大 5） | 无文件冲突 |
| 混合复杂度 | 2 | 高复杂度任务独占 1 槽位 |
| 存在文件冲突 | 1（串行） | 冲突任务必须串行 |
| 用户配置覆盖 | 用户指定值 | 尊重用户约束 |

**已完成内容**:
- [x] ~~创建 `skills/parallel-scheduler/`（已合并到 `skills/loop/phases/phase-execution.md`）~~
- [x] 修改 `skills/loop/detailed-flow.md`（执行阶段使用智能调度）

**验收标准**:
- ✅ 可并行任务自动识别并并行执行（基于文件冲突检测）
- ✅ 并行度动态调整（简单任务多并行、复杂任务少并行）
- ✅ 资源冲突检测：同文件写入的任务禁止并行
- ✅ 并行度上限可配置（默认 2，最大 5）

**研究依据**: Google Research (2026) - 可并行任务并行执行 +81% 提升，顺序任务错误并行 -70% 降低

---

### T5: 检查点恢复（Checkpoint Recovery）

**优先级**: P1-2 / P2-1
**状态**: ✅ 已完成（100%）
**完成时间**: 2026-03-21
**预估工作量**: 2-3 小时

**核心目标**:
在 loop 的每个阶段转换时自动保存检查点状态，支持任务中断后从断点恢复，避免重复已完成的工作。

**检查点状态模型**:
```json
{
  "checkpoint_id": "ckpt-{task_id}-{timestamp}",
  "version": 1,
  "task_description": "用户任务描述",
  "iteration": 3,
  "current_phase": "execution",
  "plan_file": ".claude/tasks/xxx-3.md",
  "planner_result": { "tasks": [...], "dependencies": {...} },
  "completed_tasks": ["T1", "T2"],
  "failed_tasks": ["T3"],
  "pending_tasks": ["T4"],
  "metrics": { "total_tokens": 50000, "elapsed_ms": 120000 },
  "created_at": "2026-03-20T10:30:00Z"
}
```

**检查点生命周期**:
- **保存**: 每个阶段转换时写入 `.claude/checkpoints/{task_id}.json`
- **检测**: loop 初始化时扫描 `.claude/checkpoints/` 目录
- **恢复**: 用户确认后跳过已完成任务，从断点继续
- **清理**: 任务完成后删除对应检查点文件

**已完成内容**:
- [x] 创建 `skills/checkpoint/SKILL.md`（检查点主技能）
- [x] 创建 `skills/checkpoint/state-serializer.md`（状态序列化规范）
- [x] 修改 `skills/loop/detailed-flow.md`（每阶段转换保存检查点，初始化时检测恢复）

**验收标准**:
- ✅ 每个阶段转换自动保存检查点到 `.claude/checkpoints/`
- ✅ loop 启动时检测未完成检查点并提示用户选择恢复或重新开始
- ✅ 恢复后跳过已完成任务（T1、T2），仅执行剩余任务（T3、T4）
- ✅ 检查点文件为 JSON 格式，包含完整恢复信息
- ✅ 任务完成后自动清理检查点文件

**研究依据**: 长时间运行的 agent 在 35 分钟后成功率显著下降

---

### T6: 自愈机制（Self-Healing）

**优先级**: P1-3
**状态**: ✅ 已完成（100%）
**完成时间**: 2026-03-21
**依赖**: T1 HITL（自愈操作需审批）、T5 检查点（恢复需检查点）
**预估工作量**: 1-2 小时

**核心目标**:
增强现有 adjuster 的 4 级升级策略（Retry → Debug → Replan → Ask User），在 Level 1 和 Level 2 之间插入 Level 1.5 Self-Healing 层，自动检测和修复常见可预知错误。

**可自愈错误目录**:
| 错误类型 | 错误签名匹配 | 自动修复方案 | 风险等级 |
|---------|------------|-------------|---------|
| 依赖缺失 | `ModuleNotFoundError`, `package not found` | 自动安装（npm/pip/go get） | review |
| 端口占用 | `EADDRINUSE`, `address already in use` | 自动切换到可用端口 | auto |
| 目录不存在 | `ENOENT`, `No such file or directory` | 自动创建缺失目录 | auto |
| 权限不足 | `EACCES`, `Permission denied` | 提示用户修复权限 | mandatory |
| 配置缺失 | `config not found`, `missing configuration` | 从模板生成默认配置 | review |
| 网络超时 | `ETIMEDOUT`, `connection timed out` | 指数退避重试（最多 3 次） | auto |

**升级策略（修订后）**:
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

**已完成内容**:
- [x] 创建 `skills/adjuster/self-healing.md`（自愈策略和错误目录）
- [x] 修改 `skills/adjuster/adjuster-strategies.md`（新增 Level 1.5）
- [x] 修改 `agents/adjuster.md`（增加自愈能力描述）

**验收标准**:
- ✅ 依赖缺失错误自动触发安装修复（npm/pip/go）
- ✅ 端口占用自动切换到可用端口
- ✅ 配置缺失自动从模板生成默认配置
- ✅ 自愈操作根据风险等级与 T1 HITL 联动（auto 自动执行、review 需确认）

**研究依据**: Failure Recovery 研究 - 自主恢复减少人工干预 60%

---

## Phase 4: P2 上下文版本化（长期规划）

### T7: 上下文版本化（Context Versioning）

**优先级**: P2-1 / P2-3
**状态**: ✅ 已完成（100%）
**完成时间**: 2026-03-21
**预估工作量**: 1-2 小时

**核心目标**:
保存规划上下文的历史版本，支持回滚和对比。利用 Git 追踪 `.claude/context/` 目录中的上下文快照。

**版本化机制**:
| 操作 | 存储位置 | 触发时机 |
|------|---------|---------|
| 保存快照 | `.claude/context/{task_id}/v{iteration}.json` | 每次规划前 |
| 列表版本 | 读取 `context/{task_id}/` 目录 | 用户请求 |
| 回滚 | 恢复指定快照到当前上下文 | 用户请求 |
| 对比 | JSON diff 两个版本 | 用户请求 |

**快照内容**:
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

**已完成内容**:
- [x] ~~创建 `skills/context-versioning/SKILL.md`（已移除，快照功能内置于 loop）~~
- [x] 修改 `skills/planner/planner-context-learning.md`（集成版本化）

**验收标准**:
- ✅ 每次规划前自动创建上下文快照到 `.claude/context/{task_id}/`
- ✅ 支持查看历史版本列表（按时间排序）
- ✅ 支持回滚到指定版本（恢复上下文状态）
- ✅ 版本对比可展示两个版本的 JSON diff

**研究依据**: Context Engineering - 上下文文件应可版本控制、支持增量演化和回滚

---

### T8: 多编排器架构（延后评估）

**优先级**: P2-2
**状态**: 延后评估
**预估工作量**: 待评估

**核心目标**:
支持不同编排策略（串行/并行/混合），根据任务类型自动选择最优编排模式。

**延后理由**:
1. 当前 loop 的 PDCA 模式已能覆盖大部分场景
2. 实施复杂度高，需要重构 loop 核心架构
3. ROI 低，需要更多实际使用数据支撑决策
4. 建议在 T1-T7 全部完成后，基于可观测性数据（T2）评估是否实施

**预期输出**（待确认）:
- `skills/orchestrator/SKILL.md` - 编排器选择技能
- `skills/orchestrator/strategies/serial.md` - 串行策略
- `skills/orchestrator/strategies/parallel.md` - 并行策略
- `skills/orchestrator/strategies/hybrid.md` - 混合策略

---

## 风险与缓解策略

### 风险矩阵

| # | 风险描述 | 概率 | 影响 | 风险等级 | 缓解策略 |
|---|---------|------|------|---------|---------|
| R1 | HITL 过度干预导致效率下降 | 中 | 高 | **高** | 合理设定风险阈值，确保 auto 级别覆盖 80%+ 操作；提供"信任模式"快捷选项 |
| R2 | loop 核心流程修改引入回归 | 中 | 高 | **高** | 每次修改后用质量检查命令验证 AI 理解；按批次依次修改，每批只改一个方面 |
| R3 | 记忆系统与 memory 插件版本不兼容 | 低 | 高 | **中** | memory-bridge 作为适配层隔离版本差异，仅通过 URI 接口交互 |
| R4 | 智能并行度超过用户约束 | 中 | 中 | **中** | 硬编码用户约束检查，动态并行度不超过用户配置上限；可观测性日志审计 |
| R5 | 检查点文件占用磁盘空间 | 低 | 低 | **低** | 任务完成后自动清理；设置最大保留数（默认 10 个） |
| R6 | 自愈机制误判导致错误修复 | 低 | 中 | **低** | 自愈操作与 HITL 联动，review/mandatory 级别需用户确认；自愈后自动验证修复有效性 |
| R7 | EU AI Act 合规截止日前未完成 HITL | 低 | 高 | **中** | T1 作为最高优先级第1批实施，预留充足时间 |

### detailed-flow.md 修改策略

由于 `detailed-flow.md` 被 5 个任务涉及，采用分层修改策略避免冲突：

| 批次 | 修改任务 | 修改区域 | 修改内容 |
|------|---------|---------|---------|
| 第1批 | T1 | 执行阶段、调整阶段 | 插入 HITL 审批检查 |
| 第1批 | T2 | 初始化阶段、完成阶段 | 插入指标采集和报告 |
| 第2批 | T3 | 初始化阶段、完成阶段 | 插入记忆加载和保存 |
| 第3批 | T4 | 执行阶段 | 替换固定并行为智能调度 |
| 第3批 | T5 | 所有阶段转换处 | 插入检查点保存，初始化增加恢复检测 |

---

## 实施时间估算

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

## 研究引用

本路线图基于以下研究成果：

- **Google Research (2026)**: Multi-agent coordination (+81% for parallel tasks, -70% for sequential tasks executed in parallel)
- **Oracle/AWS/Microsoft**: Human-in-the-Loop implementations
- **Context Engineering**: RAG → 3-tier evolution
- **Long-running agents**: 35-minute success rate decline
- **EU AI Act**: Compliance deadline August 2, 2026
- **Failure Recovery**: Self-healing reduces human intervention by 60%

---

**文档版本**: v1.0
**维护者**: CCPlugin Task Team
**最后审核**: 2026-03-21
