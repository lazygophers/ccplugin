# Finalizer 资源清理指南

## 核心原则

| 原则 | 说明 |
|------|------|
| 明确所有权 | 创建者负责释放，最小化共享所有权 |
| 错误容忍 | 单个清理失败不阻止整体流程，try-except 包裹每个操作 |
| 逆序清理 | 按创建逆序：先停任务 → 后删文件 → 最后清目录 |
| 防御性 | 文件不存在时静默跳过，记录异常后继续 |

## 清理目标（6类中间产物）

| 类型 | 路径模式 | 说明 | 清理条件 |
|------|---------|------|---------|
| 计划文件 | `.claude/plans/{name}-{N}.md` + `.html` | 计划文档及HTML预览 | 始终删除 |
| 检查点 | `.claude/checkpoints/{hash}.json` | 任务执行状态快照 | 始终删除 |
| 审批日志 | `.claude/plans/{task_hash}/approval-log.json` | HITL审批记录 | 始终删除 |
| 指标数据 | `.claude/plans/{task_hash}/metrics.json` | 可观测性指标 | 始终删除 |
| 上下文快照 | `.claude/context-versions/{task_hash}/v*.json` | 规划阶段上下文版本 | 始终删除 |
| 草稿产物 | `.claude/plans/*-draft-*.md` | 未确认的计划草稿 | 始终删除 |

## 保留规则（不清理）

| 类型 | 路径模式 | 保留原因 |
|------|---------|---------|
| 任务状态 | `.claude/task/{task_id}.json` | 保留30天供查询，超期由初始化阶段自动清理 |
| 情节记忆 | `workflow://task-episodes/` | 永久保留，长期学习数据 |
| 用户文件 | 用户手动创建的文件 | 非自动产物，不自动清理 |

## 执行流程

### 阶段1：资源盘点

- **任务**：`TaskList()` → 分类 running / pending / completed / failed
- **文件**：扫描以下目录
  - `.claude/plans/` — 计划文件(.md/.html)、审批日志、指标数据、草稿、子目录
  - `.claude/checkpoints/` — 检查点JSON
  - `.claude/context-versions/` — 上下文版本快照目录
- **其他**：lock文件、缓存

### 阶段2：任务终止

- `TaskStop(task.id)` 停止 running 任务 → 记录 stopped / failed_to_stop
- `TaskStop(task.id)` 取消 pending 任务 → 标记 cancelled

### 阶段3：文件清理

按以下顺序逐类清理（每步 try-except，失败记录后继续）：

1. **检查点**：删除 `.claude/checkpoints/{hash}.json`
2. **上下文快照**：删除 `.claude/context-versions/{task_hash}/` 整个目录
3. **审批日志**：删除 `.claude/plans/{task_hash}/approval-log.json`
4. **指标数据**：删除 `.claude/plans/{task_hash}/metrics.json`
5. **草稿产物**：删除 `.claude/plans/*-draft-*.md`
6. **计划文件**：删除 `.claude/plans/{name}-{N}.md` + `.html`
7. **空目录**：清理 `.claude/plans/{task_hash}/` 等空子目录

### 阶段4：最终报告

生成清理统计：任务数 / 文件数 / 错误数，报告 ≤ 100字。

## 检查清单

- [ ] 所有 running/pending 任务已处理
- [ ] 6类中间产物已扫描并清理
- [ ] 空目录已移除
- [ ] 所有清理操作有错误处理且已记录
- [ ] 报告简洁准确
