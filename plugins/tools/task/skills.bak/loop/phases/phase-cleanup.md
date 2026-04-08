
# Cleanup

完成阶段：loop 自身执行清理操作，保存记忆，生成报告，删除任务目录。

## 执行流程（loop 自身执行，无独立 agent）

1. **保存关键信息**：
   - 从 `.lazygophers/tasks/{task_id}/metadata.json` 读取所有信息（用于后续报告）
   - 保存到内存变量（因为后续会删除目录）

2. **标记任务完成**：
   - 更新 `.lazygophers/tasks/{task_id}/metadata.json` 的 `phase` 为 `"completed"` 或 `"failed"`
   - 更新 `.lazygophers/tasks/index.json`（**禁止使用 Write/Edit 工具，必须使用 Bash 工具执行以下 jq 命令**）：

   ```bash
   TASK_ID="当前任务的task_id"      # 从 context 获取
   FINAL_PHASE="completed"  # 或 failed
   QUALITY_SCORE=85  # 从内存变量读取（可能为 null）
   TIMESTAMP=$(date +%s)  # 整数时间戳

   jq --arg tid "$TASK_ID" \
      --arg phase "$FINAL_PHASE" \
      --argjson score "$QUALITY_SCORE" \
      --argjson ts "$TIMESTAMP" \
      '
      map(
        if .task_id == $tid then
          .phase = $phase |
          .quality_score = $score |
          .updated_at = $ts
        else . end
      ) | sort_by(.updated_at) | reverse
      ' .lazygophers/tasks/index.json > .lazygophers/tasks/index.json.tmp && \
      mv .lazygophers/tasks/index.json.tmp .lazygophers/tasks/index.json
   ```

3. **微回顾**（Micro-Retrospective，<=5 分钟）：
   ```
   [MindFlow·${task_id}·微回顾]
   - 有效实践：{内容}
   - 需改进：{内容}
   - 下次注意：{内容}
   ```

4. **记忆保存**（可选）：如果项目有记忆系统，保存任务经验和回顾

5. **删除任务目录**：
   ```bash
   TASK_ID="当前任务的task_id"  # 从 context 获取
   
   # 删除整个任务目录
   rm -rf ".lazygophers/tasks/${TASK_ID}"
   ```

6. **从索引中移除任务**：
   ```bash
   TASK_ID="当前任务的task_id"  # 从 context 获取
   
   # 从 index.json 中移除该任务
   jq --arg tid "$TASK_ID" \
      'map(select(.task_id != $tid))' \
      .lazygophers/tasks/index.json > .lazygophers/tasks/index.json.tmp && \
      mv .lazygophers/tasks/index.json.tmp .lazygophers/tasks/index.json
   ```

7. **最终报告**：状态/迭代次数/停滞次数/指导次数/时长/变更文件（使用步骤1保存的信息）

## 状态转换：进入 End

只有同时满足以下条件时，才允许进入 End：
1. 最终报告已输出
2. 状态变量已清理
3. metadata.json 和 index.json 已更新为终态

**End 是整个 Loop 流程中唯一允许结束回复的节点。在此之前的任何阶段都禁止结束回复。**
