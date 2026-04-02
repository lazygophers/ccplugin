
# Adjustment

失败调整阶段：分析失败原因，决定恢复策略，支持四级渐进升级和HITL审批。

## 执行流程

1. **记忆检索**：提取失败原因关键词 → `search_failure_patterns()` 检索相似失败情节
2. **调用 adjuster**：
   ```
   Skill(skill="task:adjuster", args="失败调整分析：\n项目路径：{project_path}\n任务ID：{task_id}\n任务目标：{user_task}\n迭代：{iteration}\n计划文件：{plan_md_path}\n工作目录：{working_directory}\n失败任务：{failed_tasks}\n失败原因：{failure_reason}\n历史失败模式：{failure_patterns}")
   ```
   每次调用独立传递所有上下文，不依赖会话记忆。
3. **检查点保存**：`save_checkpoint(phase="adjustment", strategy, report)`
4. **HITL审批**：若 adjuster 建议危险操作 → `hitl_approve_operation()` 风险评估
5. **指数退避**：按 `retry_config.backoff_seconds` 等待
6. **状态转换**：按 strategy 路由到下一阶段

## 四级渐进升级

| Level | 策略 | 触发条件 | 退避 | 下一步 | 强制要求 |
|-------|------|---------|------|--------|---------|
| 1 | retry | 首次失败/临时错误（含自愈） | 0s | Execution | **必须立即**继续执行 |
| 2 | debug | 重试失败/逻辑错误 | 2s | Execution | **必须立即**继续执行 |
| 3 | replan | 调试失败/计划缺陷 | 4s | Planning(自动批准) | **必须立即**重新规划 |
| 4 | ask_user | 重规划失败/停滞 | - | 用户决定 | 获得响应后**必须立即**继续 |

**禁止**：调整完成后就结束回复。Loop 流程不可中断，必须继续到 Finalizer。

## HITL审批

| 风险 | 示例 | 处理 |
|------|------|------|
| 低 | 调整参数/重试 | 自动批准 |
| 中 | 修改代码/回滚 | 首次询问 |
| 高 | 删除数据/强制推送 | 每次询问 |

用户拒绝后选项：手动修复 / 跳过任务 / 重新规划 / 终止循环

## 停滞检测

- 连续3次相同错误签名 → 停滞
- 连续3次重规划，相似度>80% → 停滞
- 达到阈值 → 保存失败情节 → 请求用户决定

