# Adjuster 输出格式 - Retry 和 Debug

## Retry（第1次失败）

轻量恢复，直接调整后立即重试。

输出：`{strategy:"retry", report(≤100字), adjustments[{task_id,task_name,action,details,error_type,root_cause}], retry_config:{max_retries:3,current_retry:1,backoff_seconds:0}}`

Loop 行为：应用调整 → 回到任务执行阶段，退避 0s。

## Debug（第2次失败）

简单调整不够，调用 debug agent 深度诊断。

输出：在 retry 基础上增加 `debug_plan:{agent,focus_areas[]}`，adjustments 含 `failure_count`，`backoff_seconds:2`

Loop 行为：等待 2s → 调用 debug agent → 修复 → 回到任务执行阶段。

## 错误分类

| 类型 | 说明 | 策略 |
|------|------|------|
| compilation_error | 编译/语法 | retry |
| test_failure | 断言失败 | retry/debug |
| dependency_error | 依赖缺失/冲突 | replan |
| runtime_error | 运行时异常 | debug |
| environment_error | 环境配置 | ask_user |
| timeout | 执行超时 | retry(增加超时) |
