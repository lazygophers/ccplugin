# Verifier 基础集成

## Loop集成

1. **调用verifier**：`Skill(skill="task:verifier")` 传入任务目标、迭代轮次
2. **输出报告**：`[MindFlow·{task}·结果验证/{N}·{status}]`
3. **状态路由**：passed→exit | suggestions→询问用户(是→continue/否→exit) | failed→adjustment

## 结果处理

- 验证status有效性(passed/suggestions/failed)
- 输出summary统计(total/completed/failed/coverage/regression)
- passed：所有标准通过
- suggestions：显示建议(priority图标❗⚠️💡) → AskUserQuestion
- failed：列出每个failure的criterion/actual/reason

## 自定义场景

- **单任务验证**：传入task_id + acceptance_criteria
- **批量验证**：传入tasks JSON列表
- **增量验证**：传入new_tasks + previous_verification，确认之前通过的仍有效
