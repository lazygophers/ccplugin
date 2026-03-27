<!-- STATIC_CONTENT: Phase 8流程文档，可缓存 -->

# Phase 8: Finalization

完成阶段：清理资源、保存记忆、生成报告。

## 执行流程

1. **调用finalizer**：`Agent(agent="task:finalizer")` 停止任务/删除计划文件(.md+.html)/清理临时文件/生成报告
2. **模式提取**：`extract_failure_patterns(session_id)` → 提取失败模式(需failures>0且样本≥3)
3. **检查点清理**：`cleanup_checkpoint(user_task)`
4. **记忆保存**：`save_task_episode(result="success", duration, iterations, agents, skills)` → 返回episode_id
5. **短期记忆清理**：`cleanup_working_memory(session_id)`
6. **最终报告**：状态/迭代次数/停滞次数/指导次数/时长/变更文件/记忆URI

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
