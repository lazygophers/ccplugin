
# Finalization

完成阶段：清理资源、保存记忆、生成报告。

## 执行流程

1. **【强制】调用 finalizer skill**：即使任务失败，finalizer 也必须执行以清理所有资源（计划文件、检查点、任务状态文件）
   ```
   Skill(skill="task:finalizer", args="清理任务资源：\n项目路径：{project_path}\n任务ID：{task_id}\n任务目标：{user_task}\n迭代：{iteration}\n计划文件：{plan_md_path}\n工作目录：{working_directory}\n要求：1.停止运行中任务 2.删除计划文件 3.清理临时文件 4.生成最终报告")
   ```
3. **模式提取**：`extract_failure_patterns(session_id)` → 提取失败模式(需failures>0且样本≥3)
4. **检查点清理**：`cleanup_checkpoint(user_task)`
5. **记忆保存**：`save_task_episode(result="success", duration, iterations, agents, skills)` → 返回episode_id
6. **短期记忆清理**：`cleanup_working_memory(session_id)`
7. **最终报告**：状态/迭代次数/停滞次数/指导次数/时长/变更文件/记忆URI

## 临时文件清理规则

| 文件类型 | 路径模式 | 清理时机 | 条件 |
|---------|----------|---------|------|
| 计划文件 | `.claude/plans/{task_id}.md` | 任务完成/失败时 | 始终删除（包括 draft 状态） |
| 检查点 | `.claude/checkpoints/{task_id}.json` | 任务完成时 | 始终删除 |
| 短期记忆 | `task://sessions/{id}/*` | 归档后 | 始终删除 |
| 任务状态 | `.claude/tasks/{task_id}/status.json` | 任务完成/失败时 | 始终删除 |

**清理顺序**：检查点 → 短期记忆 → 计划文件 → 过期任务状态 → 中间产物

**保留规则**：
- `completed`/`failed` 状态的任务状态文件在 Finalization 阶段立即清理
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
| 计划文件 | `.claude/plans/{task_id}.md` |
| 检查点 | `.claude/checkpoints/{task_id}.json` |
| 短期记忆 | `task://sessions/{id}` → 归档后删除 |
| 临时文件 | 执行过程中生成的临时文件 |
| 任务状态 | `.claude/tasks/{task_id}/status.json`（Finalization 阶段立即清理） |

## 微回顾（Micro-Retrospective）

**在 finalizer 完成后、记忆保存前执行**（≤5分钟），生成本次迭代的经验总结：

| 维度 | 内容 | 示例 |
|------|------|------|
| 做得好的 | 1-2 条有效实践 | "MECE 分解准确，无遗漏任务" |
| 需改进的 | 1-2 条问题发现 | "执行阶段直接用 Edit 违反铁律" |
| 下次注意 | 1-2 条行动项 | "所有执行必须通过 Skill() 调用" |

**输出格式**：
```
[MindFlow·${task_id}·微回顾]
- 有效实践：{内容}
- 需改进：{内容}
- 下次注意：{内容}
```

**回顾结果保存**：作为情节记忆的 `retrospective` 字段一并保存，供后续迭代参考。

## 记忆保存

情节记忆：`workflow://task-episodes/{type}/{episode_id}` 含task_desc/type/result/plan/metrics/agents/skills/retrospective

## 状态转换（唯一允许结束 Loop 的阶段）

**本阶段是整个 Loop 流程中唯一允许结束回复的阶段。**

只有同时满足以下条件时，才允许结束回复：
1. finalizer skill 已执行完成
2. 最终报告已输出
3. 状态变量已清理

4. **标记 Loop 完成**：写入 completed 状态，此后 Stop hook 才允许停止
   ```bash
   echo "completed" > .claude/tasks/{task_id}/loop-phase
   ```

完成以上所有步骤 → 结束回复

**在此之前的任何阶段都禁止结束回复。**

