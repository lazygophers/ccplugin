<!-- STATIC_CONTENT: Phase 8流程文档，可缓存 -->

# Phase 8: Finalization

完成阶段：清理资源、保存记忆、生成报告。

## 执行流程

1. **【强制】调用 finalizer skill**：即使任务失败，finalizer 也必须执行以清理资源
   ```
   Skill(skill="task:finalizer", args="清理任务资源：\n任务目标：{user_task}\n迭代：{iteration}\n要求：1.停止运行中任务 2.删除计划文件 3.清理临时文件 4.生成最终报告")
   ```
2. **模式提取**：`extract_failure_patterns(session_id)` → 提取失败模式(需failures>0且样本≥3)
3. **检查点清理**：`cleanup_checkpoint(user_task)`
4. **记忆保存**：`save_task_episode(result="success", duration, iterations, agents, skills)` → 返回episode_id
5. **短期记忆清理**：`cleanup_working_memory(session_id)`
6. **最终报告**：状态/迭代次数/停滞次数/指导次数/时长/变更文件/记忆URI

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

## 记忆保存

情节记忆：`workflow://task-episodes/{type}/{episode_id}` 含task_desc/type/result/plan/metrics/agents/skills

## 状态转换

完成 → 结束

<!-- /STATIC_CONTENT -->
