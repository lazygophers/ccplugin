# Verifier 输出格式

<overview>

Verifier 的输出格式定义了验证结果的数据结构。输出分为三种状态，每种状态对应不同的数据字段和后续行为。格式设计的目标是让 Loop 能够程序化地处理验证结果，同时通过 report 字段提供人类可读的摘要。详细格式和字段说明已按状态类型拆分。

</overview>

<navigation>

## Passed 和 Suggestions 格式

文件：[verifier-output-passed-suggestions.md](verifier-output-passed-suggestions.md)

包含两种成功状态的输出格式。passed 格式用于所有验收标准完全通过的场景，Loop 收到后正常退出。suggestions 格式用于验收通过但存在优化空间的场景，Loop 会询问用户是否将建议纳入当前任务。文档包含完整的 JSON 示例、字段说明、suggestion 类别定义和报告编写指南。

## Failed 格式和字段参考

文件：[verifier-output-failed.md](verifier-output-failed.md)

包含失败状态的输出格式和通用字段参考。failed 格式用于验收标准未满足的场景，Loop 收到后进入失败调整阶段。文档包含失败详情的数据结构、字段参考（通用字段、Verified Task、Summary）、状态决策矩阵（帮助判断应输出哪种状态）和报告编写指南。

</navigation>
