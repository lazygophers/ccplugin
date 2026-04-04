
# Cleanup

清理阶段：调用 finalizer 清理资源，保存记忆，生成报告。

## 关联资源

| 类型 | 名称 | 说明 |
|------|------|------|
| Agent | `task:finalizer` | 资源清理代理 |
| Skill | `task:finalizer` | 资源清理规范（逆序清理、错误容忍、防御性清理） |

## 调用 Agent

```
Agent(subagent_type="task:finalizer", prompt="清理任务资源：
  项目路径：{project_path}
  任务ID：{task_id}
  任务目标：{user_task}
  迭代：{iteration}
  计划文件：{plan_md_path}
  工作目录：{working_directory}")
```

**即使任务失败，finalizer 也必须执行**以清理所有资源。

Finalizer 内部完成：资源盘点 → 任务终止 → 文件清理（6 类产物 + rm -rf 任务目录）。详见 agent 定义。

Finalizer 返回 `result.status`：`completed` | `partially_completed` | `failed`。无需其他字段。

## 后续操作（loop 侧）

1. **模式提取**：`extract_failure_patterns(session_id)` → 提取失败模式（需 failures>0 且样本>=3）
2. **检查点清理**：`cleanup_checkpoint(user_task)`
3. **微回顾**（Micro-Retrospective，<=5 分钟）：
   ```
   [MindFlow·${task_id}·微回顾]
   - 有效实践：{内容}
   - 需改进：{内容}
   - 下次注意：{内容}
   ```
4. **记忆保存**：`save_task_episode(result, duration, iterations, agents, skills, retrospective)` → 返回 episode_id
5. **短期记忆清理**：`cleanup_working_memory(session_id)`
6. **最终报告**：状态/迭代次数/停滞次数/指导次数/时长/变更文件/记忆 URI

## 状态转换：进入 End

只有同时满足以下条件时，才允许进入 End：
1. finalizer skill 已执行完成
2. 最终报告已输出
3. 状态变量已清理
4. **标记 Loop 完成**：
   - 更新 `.claude/tasks/{task_id}/metadata.json` 的 `phase` 为 `"completed"` 或 `"failed"`
   - 更新 `.claude/tasks/index.json` 中对应任务的 `phase`、`updated_at`、`quality_score`

**End 是整个 Loop 流程中唯一允许结束回复的节点。在此之前的任何阶段都禁止结束回复。**
