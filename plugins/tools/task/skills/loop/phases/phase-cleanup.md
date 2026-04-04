
# Cleanup

完成阶段：loop 自身执行清理操作，保存记忆，生成报告。

**注意**：当前任务的中间产物不立即删除，由 SessionStart hook 在超过30天后自动清理。

## 执行流程（loop 自身执行，无独立 agent）

1. **标记任务完成**：
   - 更新 `.lazygophers/tasks/{task_id}/metadata.json` 的 `phase` 为 `"completed"` 或 `"failed"`
   - 更新 `.lazygophers/tasks/index.json`（**禁止使用 Write/Edit 工具，必须使用 Bash 工具执行以下 jq 命令**）：

   ```bash
   TASK_ID="当前任务的task_id"      # 从 context 获取
   SESSION_ID="当前会话的session_id"  # 从环境获取
   FINAL_PHASE="completed"  # 或 failed
   QUALITY_SCORE=85  # 从 metadata.json 读取（可能为 null）
   TIMESTAMP=$(date +%s)  # 整数时间戳

   jq --arg sid "$SESSION_ID" \
      --arg tid "$TASK_ID" \
      --arg phase "$FINAL_PHASE" \
      --argjson score "$QUALITY_SCORE" \
      --argjson ts "$TIMESTAMP" \
      '
      .[$sid] |= map(
        if .task_id == $tid then
          .phase = $phase |
          .quality_score = $score |
          .updated_at = $ts
        else . end
      )
      ' .lazygophers/tasks/index.json > .lazygophers/tasks/index.json.tmp && \
      mv .lazygophers/tasks/index.json.tmp .lazygophers/tasks/index.json
   ```

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
1. 最终报告已输出
2. 状态变量已清理
3. metadata.json 和 index.json 已更新为终态

**End 是整个 Loop 流程中唯一允许结束回复的节点。在此之前的任何阶段都禁止结束回复。**
