# Finalizer 资源清理指南

## 核心原则

| 原则 | 说明 |
|------|------|
| 明确所有权 | 创建者负责释放，最小化共享所有权 |
| 错误容忍 | 单个清理失败不阻止整体流程，每个操作独立执行并捕获错误 |
| 逆序清理 | 按创建逆序：先停任务 → 后删文件 → 最后清目录 |
| 防御性 | 文件不存在时静默跳过，记录异常后继续 |

## 清理目标（6类中间产物 + 任务目录）

| 类型 | 路径模式 | 说明 | 清理条件 |
|------|---------|------|---------|
| 计划文件 | `.claude/tasks/{task_id}/plan.md` | 计划文档（含 draft 状态） | 始终删除 |
| 提示词文件 | `.claude/tasks/{task_id}/prompt.md` | 优化后的提示词（含任务边界/验收标准） | 始终删除 |
| 元数据 | `.claude/tasks/{task_id}/metadata.json` | 任务元信息（phase/iteration等） | 始终删除 |
| 任务清单 | `.claude/tasks/{task_id}/tasks.json` | 子任务列表及状态 | 始终删除 |
| 检查点 | `.claude/checkpoints/{task_id}.json` | 任务执行状态快照 | 始终删除 |
| 审批日志 | `.claude/tasks/{task_id}/approval-log.json` | HITL审批记录 | 始终删除 |
| 上下文快照 | `.claude/context/{task_id}/v*.json` | 规划阶段上下文版本 | 始终删除 |
| **任务目录** | `.claude/tasks/{task_id}/` | 任务工作目录 | 所有文件清理后删除整个目录 |

## 保留规则（不清理）

| 类型 | 路径模式 | 保留原因 |
|------|---------|---------|
| 情节记忆 | `workflow://task-episodes/` | 永久保留，长期学习数据 |
| 用户文件 | 用户手动创建的文件 | 非自动产物，不自动清理 |

## 执行流程

### ResourceInventory：资源盘点

- **任务**：`TaskList()` → 分类 running / pending / completed / failed
- **文件**：扫描以下目录
  - `.claude/tasks/{task_id}/` — 计划文件(plan.md)、提示词文件(prompt.md)、审批日志、元数据、任务清单
  - `.claude/checkpoints/` — 检查点JSON
  - `.claude/context/` — 上下文版本快照目录
- **其他**：lock文件、缓存

### TaskTermination：任务终止

- `TaskStop(task.id)` 停止 running 任务 → 记录 stopped / failed_to_stop
- `TaskStop(task.id)` 取消 pending 任务 → 标记 cancelled

### FileCleanup：文件清理

按以下顺序逐类清理（每步独立执行，失败记录后继续）：

1. **检查点**：删除 `.claude/checkpoints/{task_id}.json`
2. **上下文快照**：删除 `.claude/context/{task_id}/` 整个目录
3. **审批日志**：删除 `.claude/tasks/{task_id}/approval-log.json`
4. **计划文件**：删除 `.claude/tasks/{task_id}/plan.md`
5. **提示词文件**：删除 `.claude/tasks/{task_id}/prompt.md`
6. **元数据**：删除 `.claude/tasks/{task_id}/metadata.json`
7. **任务清单**：删除 `.claude/tasks/{task_id}/tasks.json`
8. **任务目录**：`rm -rf .claude/tasks/{task_id}/`（删除整个任务目录，包括可能遗漏的其他文件）

### FinalReport：最终报告

生成清理统计：任务数 / 文件数 / 错误数，报告 ≤ 100字。

## 检查清单

- [ ] 所有 running/pending 任务已处理
- [ ] 6类中间产物已扫描并清理
- [ ] `.claude/tasks/{task_id}/` 目录已删除
- [ ] 所有清理操作有错误处理且已记录
- [ ] 报告简洁准确
