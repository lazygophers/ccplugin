# Verifier 输出格式

## 状态决策

| 条件 | 状态 | Loop行为 |
|------|------|---------|
| 所有通过+无建议 | passed | 正常退出 |
| 所有通过+有建议 | suggestions | 自动继续优化 |
| 部分未通过 | failed | 失败调整 |

## passed（完全通过）

所有任务完成，验收标准全部满足。Loop正常退出。

**必需字段**：
- `status`: `"passed"`
- `report`: ≤100字，格式`所有任务已完成：T1(名)✓、T2(名)✓。覆盖率X%，CI通过，无回归。`
- `verified_tasks`: 所有status=`"verified"`，含criteria_passed/total
- `summary`: `{total_tasks, completed_tasks, failed_tasks:0, test_coverage?, regression_tests_passed?}`

## suggestions（通过但有建议）

验收标准满足但发现可优化之处。Loop自动继续新一轮迭代。

**额外字段**：
- `suggestions[]`: 每个含`{task_id, category, suggestion, priority}`
- `report`格式：`任务已完成，标准满足。建议优化：[建议1]；[建议2]。`

### Suggestion类别

| 类别 | 说明 |
|------|------|
| code_quality | 降低复杂度、重构 |
| test_coverage | 添加边界/异常测试 |
| performance | 优化查询、缓存 |
| security | 输入验证、权限 |
| documentation | 注释、API文档 |

## failed（验收未通过）

验收标准未满足，存在功能缺陷或质量问题。Loop进入失败调整阶段。

**必需字段**：

| 字段 | 说明 |
|------|------|
| status | `"failed"` |
| report | 失败情况（≤100字） |
| verified_tasks | 含通过和失败任务，失败任务status=`"failed"` |
| failures | 详细失败列表 |
| summary | `{total_tasks, completed_tasks, failed_tasks, test_coverage?, regression_tests_passed?}` |

### failures数组元素

| 字段 | 说明 |
|------|------|
| task_id | 失败任务ID |
| criterion | 未满足的验收标准 |
| actual | 实际结果 |
| reason | 失败原因详情 |
| evidence(必须) | `{command, output, timestamp(ISO8601)}` |

### 报告格式

`验收失败：T1 [问题]，T2 [问题]。[关键指标不达标]。` 列出失败任务和问题，提及未达标指标，详细信息在failures字段。
