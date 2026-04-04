
# Adjustment

失败调整阶段：调用 adjuster 分析失败原因并决定恢复策略。

## 关联资源

| 类型 | 名称 | 说明 |
|------|------|------|
| Agent | `task:adjuster` | 失败调整代理 |
| Skill | `task:adjuster` | 失败调整规范（四级渐进升级、自愈机制、停滞检测） |

## 调用 Agent

1. **记忆检索**（loop 侧）：提取失败原因关键词 → `search_failure_patterns()` 检索相似失败情节
2. **调用 Agent**：
   ```
   Agent(subagent_type="task:adjuster", prompt="失败调整分析：
     项目路径：{project_path}
     任务ID：{task_id}
     任务目标：{user_task}
     迭代：{iteration}
     计划文件：{plan_md_path}
     工作目录：{working_directory}
     失败任务：{failed_tasks}
     失败原因：{failure_reason}
     失败标准：{failed_criteria}
     历史失败模式：{failure_patterns}")
   ```
   每次调用独立传递所有上下文，不依赖会话记忆。

Adjuster 内部完成：自愈尝试 → 原因分析 → 停滞检测 → 策略选择 → 写入 metadata.json result。详见 agent 定义。

## 结果处理

读取 metadata.json 的 `result` 字段，按 `result.strategy` 路由：

| result.strategy | 退避 | 下一步 | 强制要求 |
|-----------------|------|--------|---------|
| `retry` | 0s | PromptOptimization | **必须立即**回到提示词评估 |
| `debug` | 2s | PromptOptimization | **必须立即**回到提示词评估 |
| `replan` | 4s | PromptOptimization | **必须立即**回到提示词评估 |
| `ask_user` | - | 用户决定 → PromptOptimization | 获得响应后**必须立即**回到提示词评估 |

## 后续操作

1. 检查点保存：`save_checkpoint(phase="adjustment", strategy)`
2. HITL 审批：若 adjuster 建议危险操作 → `hitl_approve_operation()` 风险评估
3. 指数退避：按 `result.retry_config.backoff_seconds` 等待

**禁止**：调整完成后结束回复。Loop 流程不可中断。
