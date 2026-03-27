# Verifier 输出格式 - Passed 和 Suggestions

## passed（完全通过）

所有任务完成，验收标准全部满足。Loop正常退出。

**必需字段**：
- `status`: `"passed"`
- `report`: ≤100字，格式`所有任务已完成：T1(名)✓、T2(名)✓。覆盖率X%，CI通过，无回归。`
- `verified_tasks`: 所有status=`"verified"`，含criteria_passed/total，可选criteria_results(含evidence)
- `summary`: `{total_tasks, completed_tasks, failed_tasks:0, test_coverage?, regression_tests_passed?}`

## suggestions（通过但有建议）

验收标准满足但发现可优化之处。Loop自动继续新一轮迭代。

**额外字段**：
- `suggestions[]`: 每个含`{task_id, category, suggestion, priority}`
- `report`格式：`任务已完成，标准满足。建议优化：[建议1]；[建议2]。`
- `verified_tasks`可含`notes`字段

### Suggestion类别

| 类别 | 说明 |
|------|------|
| code_quality | 降低复杂度、重构 |
| test_coverage | 添加边界/异常测试 |
| performance | 优化查询、缓存 |
| security | 输入验证、权限 |
| documentation | 注释、API文档 |
