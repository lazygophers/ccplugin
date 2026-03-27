# Verifier 输出格式 - Failed

验收标准未满足，存在功能缺陷或质量问题。Loop不退出，进入失败调整阶段。

## 必需字段

| 字段 | 说明 |
|------|------|
| status | `"failed"` |
| report | 失败情况（≤100字） |
| verified_tasks | 含通过和失败任务，失败任务status=`"failed"` |
| failures | 详细失败列表 |
| summary | `{total_tasks, completed_tasks, failed_tasks, test_coverage?, regression_tests_passed?}` |

## failures数组元素

| 字段 | 说明 |
|------|------|
| task_id | 失败任务ID |
| criterion | 未满足的验收标准 |
| actual | 实际结果 |
| reason | 失败原因详情 |
| evidence(必须) | `{command, output, timestamp(ISO8601)}` |

## verified_tasks元素

`{task_id, task_name, status("verified"/"failed"), criteria_passed, criteria_total, notes?}`

## 报告格式

`验收失败：T1 [问题]，T2 [问题]。[关键指标不达标]。` 列出失败任务和问题，提及未达标指标，详细信息在failures字段。

## 状态决策

| 条件 | 状态 | Loop行为 |
|------|------|---------|
| 所有通过+无建议 | passed | 正常退出 |
| 所有通过+有建议 | suggestions | 询问用户 |
| 部分未通过 | failed | 失败调整 |
