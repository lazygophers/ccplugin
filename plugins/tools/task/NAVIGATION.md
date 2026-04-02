# Task插件导航索引


## 快速开始

- [README.md](./README.md) - 项目概览和快速入门
- [ROADMAP.md](docs/ROADMAP.md) - 功能路线图和完成状态

## 核心循环Agents (5)

| Agent | 用途 | 关键文件 | 使用场景 |
|-------|------|---------|---------|
| planner | 任务规划、分解、格式化 | [agents/planner.md](agents/planner.md)<br/>[skills/planner/](skills/planner/) | MECE分解复杂任务为原子子任务，自动格式化并写入计划文件 |
| verifier | 验收验证 | [agents/verifier.md](agents/verifier.md)<br/>[skills/verifier/](skills/verifier/) | 检查验收标准、质量评分 |
| adjuster | 失败调整 | [agents/adjuster.md](agents/adjuster.md)<br/>[skills/adjuster/](skills/adjuster/) | 5级渐进式升级（retry→debug→replan→ask_user） |
| finalizer | 资源清理 | [agents/finalizer.md](agents/finalizer.md)<br/>[skills/finalizer/](skills/finalizer/) | 任务完成后清理资源和生成报告 |
| prompt-optimizer | 提示词优化 | [agents/prompt-optimizer.md](agents/prompt-optimizer.md)<br/>[skills/prompt-optimizer/](skills/prompt-optimizer/) | 5W1H框架澄清模糊需求 |

## 支持功能Skills (15+)

### 核心技能

| Skill | 用途 | 触发条件 | 文档路径 |
|-------|------|---------|---------|
| loop | Loop持续执行 | `/loop`命令 | [skills/loop/SKILL.md](skills/loop/SKILL.md) |
| planner | 计划设计 | loop调用或独立使用 | [skills/planner/SKILL.md](skills/planner/SKILL.md) |
| verifier | 结果验证 | loop调用或独立使用 | [skills/verifier/SKILL.md](skills/verifier/SKILL.md) |
| adjuster | 失败调整 | loop调用或独立使用 | [skills/adjuster/SKILL.md](skills/adjuster/SKILL.md) |

### 高级功能

| Skill | 用途 | 触发条件 | 文档路径 |
|-------|------|---------|---------|
| hitl | HITL审批 | 高风险操作（删除、修改核心文件） | [skills/hitl/SKILL.md](skills/hitl/SKILL.md) |
| observability | 可观测性 | 每次迭代结束 | [skills/observability/SKILL.md](skills/observability/SKILL.md) |
| checkpoint | 检查点管理 | 关键节点（planning、execution） | [skills/checkpoint/SKILL.md](skills/checkpoint/SKILL.md) |
| memory-bridge | 记忆桥接 | 任务完成、失败分析 | [skills/memory-bridge/SKILL.md](skills/memory-bridge/SKILL.md) |
| deep-iteration | 深度迭代 | 质量不达标（<60分） | [skills/deep-iteration/SKILL.md](skills/deep-iteration/SKILL.md) |
| context-versioning | 上下文版本化 | 规划前自动保存、失败回滚 | [skills/context-versioning/SKILL.md](skills/context-versioning/SKILL.md) |
| prompt-optimizer | 提示词优化 | 评分<9 触发 | [skills/prompt-optimizer/SKILL.md](skills/prompt-optimizer/SKILL.md) |
| parallel-scheduler | 智能并行调度 | 多任务执行 | [skills/parallel-scheduler/SKILL.md](skills/parallel-scheduler/SKILL.md) |
| hooks | 生命周期钩子 | 事件触发（2个hooks） | [skills/hooks/SKILL.md](skills/hooks/SKILL.md) |

## 按场景查找

### 任务执行失败

| 问题 | 相关组件 | 文档链接 |
|------|---------|---------|
| 任务执行失败，如何恢复？ | adjuster → 四级升级策略 | [失败调整](skills/adjuster/adjuster-strategies.md) |
| 连续失败3次，系统如何处理？ | adjuster → 停滞检测 | [停滞检测](skills/adjuster/stall-detection.md) |
| 如何查看失败原因？ | loop → error-handling | [错误处理](skills/loop/error-handling.md) |
| 如何从历史失败学习？ | memory-bridge → pattern-extraction | [模式提取](skills/memory-bridge/pattern-extraction.md) |

### 成本和性能

| 问题 | 相关组件 | 文档链接 |
|------|---------|---------|
| 如何查看Token消耗？ | observability → cost-report | [成本报告](skills/observability/cost-report.md) |
| 如何优化成本？ | observability → optimization-suggestions | [优化建议](skills/observability/implementation-guide.md) |
| 如何启用Prompt Caching？ | loop → prompt-caching | [缓存优化](skills/loop/prompt-caching.md) |
| 如何控制预算？ | observability → budget-controller | [预算控制](skills/observability/cost-report.md) |

### 任务中断与恢复

| 问题 | 相关组件 | 文档链接 |
|------|---------|---------|
| 任务中断后如何恢复？ | checkpoint → 检查点恢复 | [检查点管理](skills/checkpoint/SKILL.md) |
| 检查点保存在哪里？ | checkpoint → 存储位置 | [检查点管理](skills/checkpoint/SKILL.md) |
| 如何手动触发检查点？ | checkpoint → 手动保存 | [检查点管理](skills/checkpoint/SKILL.md) |

### 质量和验收

| 问题 | 相关组件 | 文档链接 |
|------|---------|---------|
| 如何定义验收标准？ | planner → acceptance_criteria | [计划设计](skills/planner/SKILL.md) |
| 质量评分如何计算？ | verifier → quality-scoring | [结果验证](skills/verifier/SKILL.md) |
| 质量不达标如何自动优化？ | deep-iteration → 深度迭代 | [深度迭代](skills/deep-iteration/SKILL.md) |
| 如何触发深度研究？ | loop → deep-research-triggers | [深度研究触发](skills/loop/deep-research-triggers.md) |

### 计划和确认

| 问题 | 相关组件 | 文档链接 |
|------|---------|---------|
| 计划确认机制如何工作？ | loop → Plan Mode | [计划流程](skills/loop/flows/plan.md) |
| 什么时候需要用户确认？ | loop → 智能确认策略 | [详细流程](skills/loop/phases/phase-planning.md) |
| 如何重新设计计划？ | loop → 重新规划 | [计划流程](skills/loop/flows/plan.md) |
| 如何查看计划版本历史？ | context-versioning → 版本对比 | [上下文版本化](skills/context-versioning/SKILL.md) |

### 并行和调度

| 问题 | 相关组件 | 文档链接 |
|------|---------|---------|
| 如何控制并行任务数量？ | loop → parallel-scheduler | [并行调度](skills/parallel-scheduler/SKILL.md) |
| 为什么限制2个并行任务？ | loop → 复杂度评估 | [任务执行](skills/loop/phases/phase-execution.md) |
| Team何时创建和删除？ | execute → Team管理 | [详细流程](skills/loop/phases/phase-execution.md) |

### HITL审批

| 问题 | 相关组件 | 文档链接 |
|------|---------|---------|
| 什么操作需要人工审批？ | hitl → approval-policies | [审批策略](skills/hitl/approval-policies.md) |
| 三级审批策略是什么？ | hitl → auto/review/mandatory | [审批策略](skills/hitl/approval-policies.md) |
| 如何查看审批历史？ | hitl → 决策记录 | [审批策略](skills/hitl/approval-policies.md) |
| 如何自定义审批规则？ | hitl → 配置指南 | [实施指南](skills/hitl/implementation-guide.md) |

## 高级主题

### 深入理解

- [Loop详细执行流程](skills/loop/detailed-flow.md) - 8个执行阶段导航索引
- [深度迭代指南](skills/deep-iteration/implementation.md) - 质量递进机制（60→75→85→90分）
- [Memory Bridge详解](skills/memory-bridge/memory-schema.md) - 三层记忆架构
- [HITL审批策略](skills/hitl/approval-policies.md) - 风险分级审批
- [Observability实施指南](skills/observability/implementation-guide.md) - 指标收集和报告

### 最佳实践

- [任务分解原则](skills/planner/task-decomposition.md) - MECE原则应用
- [失败升级策略](skills/adjuster/adjuster-strategies.md) - 四级渐进式升级
- [并行调度策略](skills/execute/parallel-scheduler.md) - 复杂度评估和动态调整
- [Prompt缓存优化](skills/loop/prompt-caching.md) - 90%成本节省
- [深度研究触发](skills/loop/deep-research-triggers.md) - 4维度评估

### 架构文档

- [Agent/Skill边界](docs/AGENT_SKILL_BOUNDARY.md) - 设计决策和职责划分

## 开发和贡献

### 开发指南

- [质量检查规范](../../.claude/skills/plugin-skills/quality-check/SKILL.md) - AI可理解性验证
- [插件开发指南](../../docs/plugin-development.md) - 插件开发最佳实践

### 测试和验证

- [集成测试](tests/integration/) - 端到端测试用例
- [AI质量检查](../../.claude/skills/plugin-skills/quality-check/) - 文档AI可理解性

## 常见问题

### Q1: Loop和普通Agent有什么区别？

Loop是Team Leader角色，统一管理所有调度和用户交互。普通Agent只负责具体执行，通过SendMessage上报给Loop，不能直接向用户提问。

相关文档：[Loop概览](skills/loop/SKILL.md)

### Q2: 为什么限制2个并行任务？

基于复杂度评估和资源控制，避免：
- Token消耗爆炸
- 上下文混乱
- 文件冲突
- 调试困难

相关文档：[并行调度](skills/execute/parallel-scheduler.md)

### Q3: 什么时候触发深度研究？

三种触发条件：
1. 复杂度>8分（自动）
2. 失败2次后询问用户
3. 用户可拒绝

相关文档：[深度研究触发](skills/loop/deep-research-triggers.md)

### Q4: 计划确认何时需要用户批准？

智能确认策略：
- **需要确认**：首次规划（iteration=1）、用户重新设计
- **跳过确认**：adjuster/verifier自动触发的重新规划

相关文档：[计划流程](skills/loop/flows/plan.md)

### Q5: 如何从任务中断恢复？

检查点自动保存在关键节点：
- 计划确认后
- 任务执行前
- 验证完成后

恢复时自动检测并加载最近的检查点。

相关文档：[检查点管理](skills/checkpoint/SKILL.md)

### Q6: 成本报告包含哪些优化建议？

三类优化建议：
1. **缓存优化**：标记静态内容（40-60%节省）
2. **模型选择**：简单任务用Haiku（70%节省）
3. **Prompt精简**：减少冗余描述（15-25%节省）

相关文档：[成本报告](skills/observability/cost-report.md)

### Q7: 失败后如何自动修复？

5级渐进式升级策略：
1. **retry**：简单重试（0秒退避）
2. **debug**：深度诊断（2秒退避）
3. **replan**：重新规划（4秒退避）
4. **ask_user**：请求用户指导
5. **escalate**：升级到更高级agent

相关文档：[失败调整](skills/adjuster/adjuster-strategies.md)

### Q8: Memory Bridge如何工作？

三层记忆架构：
- **Working Memory**：当前会话状态（临时）
- **Episodic Memory**：任务执行记录（中期）
- **Semantic Memory**：知识和模式（长期）

检索策略：相似任务匹配、失败模式匹配、上下文预加载

相关文档：[Memory Bridge](skills/memory-bridge/SKILL.md)

## 关键术语

- **PDCA循环**：Plan-Do-Check-Act，持续改进循环
- **MECE原则**：Mutually Exclusive, Collectively Exhaustive，任务分解原则
- **Team Leader**：Loop作为统一调度者和用户交互接口
- **Plan Mode**：只读探索阶段，使用EnterPlanMode/ExitPlanMode
- **深度迭代**：质量递进60→75→85→90分
- **5级升级**：retry→debug→replan→ask_user→escalate
- **三级审批**：auto→review→mandatory
- **三层记忆**：Working→Episodic→Semantic

## 版本信息

- **许可证**：AGPL-3.0-or-later
- **仓库**：https://github.com/lazygophers/ccplugin/tree/master/plugins/tools/task

---

**导航提示**：使用Ctrl+F或Cmd+F搜索关键字，快速定位相关文档。

