# Adjuster 集成指南

## 基础集成（Loop内）

1. **调用adjuster**：`Skill(skill="task:adjuster", args="执行失败调整：{task}，迭代{N}，要求：获取失败详情/分析原因/检测停滞/分级升级/生成报告≤100字")`
2. **输出报告**：`[MindFlow·{task}·失败调整/{N}·{strategy}]`
3. **指数退避**：按`retry_config.backoff_seconds`等待
4. **策略路由**：

| 策略 | 操作 | 返回 |
|------|------|------|
| retry | 应用adjustments列表修复 | → PromptCheck |
| debug | 调用debug agent深度分析 | → PromptCheck |
| replan | 显示replan_options | → PromptCheck |
| ask_user | AskUserQuestion请求指导 | → 用户决定→PromptCheck |

### 调整应用

遍历`adjustments`数组，按`action`类型执行：
- 含"修复" → `apply_fix(task_id, details)`
- 含"调整" → `apply_configuration_change(task_id, details)`
- 含"安装" → `install_dependency(details)`

### 深度诊断

从`debug_plan`获取`agent`和`focus_areas` → 调用debug agent → 应用修复

### 用户指导

显示`stalled_info`(task_id/error/occurrences) → `AskUserQuestion(question)` → 解析回答应用修复

## 高级集成

### 自定义场景

- **单次失败**：传入task_id+error → Retry策略
- **批量失败**：传入failed_tasks JSON → 识别共同模式 → 统一或独立修复
- **条件调整**：传入task+conditions → 根据条件选择策略

### 停滞检测

检测最近3次错误签名(`{type, message, task_id}`)的相似度：
- 不同type → 0.0 | 不同task_id → 0.5 | 相同message → 1.0 | 部分匹配 → 0.7
- 所有相似度≥0.9 → 停滞

### 指数退避

公式：`2^(failure_count-1)`秒，上限60秒。`backoff_seconds>0`时等待。

### 错误处理

- **无效策略**：检查strategy∈{retry,debug,replan,ask_user}，否则抛异常
- **超过重试**：`current_retry>=max_retries(默认3)` → 返回True
