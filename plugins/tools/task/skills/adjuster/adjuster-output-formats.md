# Adjuster 输出格式

<overview>

Adjuster 的输出格式定义了四种失败调整策略的数据结构。每种策略对应不同的失败严重程度和处理方式，Loop 根据 strategy 字段决定下一步流向。格式设计的关键在于提供足够的上下文信息（失败原因、调整建议、退避配置），使 Loop 能够程序化地执行恢复操作。详细格式已按策略分组拆分。

</overview>

<navigation>

## Retry 和 Debug 策略

文件：[adjuster-output-retry-debug.md](adjuster-output-retry-debug.md)

包含前两级策略的输出格式。retry 格式用于首次失败，包含调整建议和立即重试配置（0秒退避），Loop 回到任务执行。debug 格式用于第2次失败，额外包含 debug_plan 字段（调试 agent 和关注领域），退避2秒后深度诊断。文档还包含 replan 和 ask_user 的完整格式、错误分类参考。

## Replan 和 Ask User 策略

文件：[adjuster-output-replan-askuser.md](adjuster-output-replan-askuser.md)

包含后两级策略的输出格式。replan 格式用于第3次失败，包含 replan_options 字段（重新规划的方案选项），退避4秒后回到计划设计。ask_user 格式用于停滞3次，包含 stalled_info（停滞详情）和 question（向用户提问的内容）。文档还包含字段参考、失败升级策略表和报告编写指南。

</navigation>
