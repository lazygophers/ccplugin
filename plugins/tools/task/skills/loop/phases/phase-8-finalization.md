<!-- STATIC_CONTENT: Phase 8流程文档，可缓存 -->

# Phase 8: Finalization

完成阶段：清理资源、保存记忆、生成报告。

## 执行流程

1. **【强制】调用 finalizer skill**：即使任务失败，finalizer 也必须执行以清理资源
   ```
   Skill(skill="task:finalizer", args="清理任务资源：\n项目路径：{project_path}\n任务ID：{task_id}\n任务目标：{user_task}\n迭代：{iteration}\n计划文件：{plan_md_path}\n工作目录：{working_directory}\n要求：1.停止运行中任务 2.删除计划文件 3.清理临时文件 4.生成最终报告")
   ```
2. **模式提取**：`extract_failure_patterns(session_id)` → 提取失败模式(需failures>0且样本≥3)
3. **检查点清理**：`cleanup_checkpoint(user_task)`
4. **记忆保存**：`save_task_episode(result="success", duration, iterations, agents, skills)` → 返回episode_id
5. **短期记忆清理**：`cleanup_working_memory(session_id)`
6. **最终状态更新**：更新 `.claude/task/{task_id}.json`
   - `status` → `"completed"` 或 `"failed"`
   - `phase` → `"finalization"`
   - `updated_at` → 当前时间
   - `quality_score` → 验证阶段的最终评分
   - `tasks[]` → 所有子任务的最终状态
   - `error` → 失败时记录原因（成功为null）
7. **最终报告**：状态/迭代次数/停滞次数/指导次数/时长/变更文件/记忆URI

## 临时文件清理规则

| 文件类型 | 路径模式 | 清理时机 | 条件 |
|---------|----------|---------|------|
| 计划文件 | `.claude/plans/{name}-{N}.md` | 任务完成/失败时 | 始终删除 |
| 计划HTML | `.claude/plans/{name}-{N}.html` | 随计划文件删除 | 始终删除 |
| 检查点 | `.claude/checkpoints/{hash}.json` | 任务完成时 | 始终删除 |
| 短期记忆 | `task://sessions/{id}/*` | 归档后 | 始终删除 |
| 任务状态 | `.claude/task/{task_id}.json` | 30天未更新 | `updated_at` 超过30天 |
| Planner中间产物 | `.claude/plans/*-draft-*.md` | 计划确认后 | 非最终版本 |

**清理顺序**：检查点 → 短期记忆 → 计划文件 → 过期任务状态 → 中间产物

**保留规则**：
- `completed`/`failed` 状态的任务状态文件保留30天供查询
- 情节记忆（episodic memory）永久保留，不在清理范围
- 用户手动创建的文件不自动清理

**资源泄漏警告**：跳过 finalizer 可能导致：
- 计划文件残留（`.claude/plans/*.md`）
- 后台任务未终止（占用资源）
- 检查点未清理（状态污染）
- 短期记忆未归档（记忆泄漏）

## 清理操作

| 操作 | 目标 |
|------|------|
| 计划文件 | `.claude/plans/{name}-{N}.md` + `.html` |
| 检查点 | `.claude/checkpoints/{hash}.json` |
| 短期记忆 | `task://sessions/{id}` → 归档后删除 |
| 临时文件 | 执行过程中生成的临时文件 |
| 任务状态 | `.claude/task/{task_id}.json`（completed/failed状态保留，30天后自动清理） |

## 记忆保存

情节记忆：`workflow://task-episodes/{type}/{episode_id}` 含task_desc/type/result/plan/metrics/agents/skills

## 状态转换

完成 → 结束

<!-- /STATIC_CONTENT -->
