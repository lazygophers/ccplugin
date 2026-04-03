# Verifier 输出格式

**所有结果通过文件传递**：verifier 完成后更新 `.claude/tasks/{task_id}/metadata.json` 的 `result` 字段，禁止输出 JSON 到对话。

## 状态决策

| 条件 | 状态 | Loop行为 |
|------|------|---------|
| 所有验收标准通过 | passed | → QualityGate（质量评估） |
| 至少一项未通过 | failed | → Adjustment（失败调整） |

**注意**：verifier 仅判断验收标准是否通过，不做质量分门控。quality_score 始终包含在 passed 结果中，由 Loop 的 QualityGate 阶段决定是否达标。

## passed（验收通过）

所有任务完成，验收标准全部满足。包含 quality_score 和可选的 suggestions。

**必需字段**：
- `status`: `"passed"`
- `report`: ≤100字，格式`所有任务已完成：T1(名)✓、T2(名)✓。覆盖率X%，CI通过，无回归。`
- `quality_score`: 7维度加权综合分（0-100）
- `verified_tasks`: 所有status=`"verified"`，含criteria_passed/total
- `summary`: `{total_tasks, completed_tasks, failed_tasks:0, test_coverage?, regression_tests_passed?}`

**可选字段**：
- `suggestions[]`: 优化建议，每个含`{task_id, category, suggestion, priority}`

### Suggestion类别

| 类别 | 说明 |
|------|------|
| code_quality | 降低复杂度、重构 |
| test_coverage | 添加边界/异常测试 |
| performance | 优化查询、缓存 |
| security | 输入验证、权限 |
| documentation | 注释、API文档 |

## failed（验收未通过）

验收标准未满足，存在功能缺陷。Loop进入失败调整阶段。

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
