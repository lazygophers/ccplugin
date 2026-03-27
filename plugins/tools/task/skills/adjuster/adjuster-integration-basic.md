# Adjuster 基础集成

## Loop集成流程

1. **调用adjuster**：`Skill(skill="task:adjuster", args="执行失败调整：{task}，迭代{N}，要求：获取失败详情/分析原因/检测停滞/分级升级/生成报告≤100字")`
2. **输出报告**：`[MindFlow·{task}·失败调整/{N}·{strategy}]`
3. **指数退避**：按`retry_config.backoff_seconds`等待
4. **策略路由**：

| 策略 | 操作 | 返回 |
|------|------|------|
| retry | 应用adjustments列表修复 | → 任务执行 |
| debug | 调用debug agent深度分析 | → 任务执行 |
| replan | 显示replan_options | → 计划设计 |
| ask_user | AskUserQuestion请求指导 | → 任务执行 |

## 调整应用

遍历`adjustments`数组，按`action`类型执行：
- 含"修复" → `apply_fix(task_id, details)`
- 含"调整" → `apply_configuration_change(task_id, details)`
- 含"安装" → `install_dependency(details)`

## 深度诊断

从`debug_plan`获取`agent`和`focus_areas` → 调用debug agent → `apply_debug_fixes(result)`

## 用户指导

显示`stalled_info`(task_id/error/occurrences) → `AskUserQuestion(question)` → 解析回答应用修复
