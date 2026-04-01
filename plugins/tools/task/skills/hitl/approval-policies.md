# Approval Policies - 审批策略

## 概述

定义不同风险等级操作的审批行为、超时处理、记录追溯和用户交互模式。

## 三级审批策略

| 级别 | 触发条件 | 行为 | 超时 | 用户选项 |
|------|---------|------|------|---------|
| **auto** | 风险0-3 或 信任模式+review | 自动执行，静默记录 | N/A | 无 |
| **review** | 风险4-6 | 暂停，展示摘要 | 5min→阻塞+提醒 | 批准/拒绝/修改参数/暂停 |
| **mandatory** | 风险7-10（不受信任模式影响） | 立即暂停，详细警告+不可逆提醒 | 10min→自动拒绝 | 明确批准(输入确认文本)/拒绝(默认)/中止任务 |

**review展示**：操作类型/目标文件/变更摘要(+N行-N行)/影响范围/风险评分

**mandatory展示**：高风险警告+详细影响说明+不可逆性提醒+风险评分+分级原因+确认文本(基于操作动态生成，防误触)

## 审批流程

操作请求→风险分级→auto:直接执行 | review:展示摘要→等待确认 | mandatory:展示详细警告→等待明确确认→记录审批日志→返回结果

**状态机**：待分级→auto:自动执行→已执行 | review:等待确认→批准/拒绝/修改(重分级)/超时(阻塞) | mandatory:等待强制确认→明确批准/拒绝/中止/超时(自动拒绝)

## 配置

`.claude/task.local.md` YAML配置：enabled/trust_mode/timeout(review_seconds:300, mandatory_seconds:600)/timeout_behavior(review:block, mandatory:auto_reject)/notifications/overrides[pattern→risk_level]/batch_approval(enabled/max_batch_size:10)

## 批量审批

触发：连续3个相同类型review操作。选项：批量批准/全部拒绝/逐个审批。限制：仅review级别，mandatory必须逐个，上限10个。

## 审批日志

存储：`.claude/plans/{task_id}/approval-log.json`。每条含：timestamp/operation/risk_classification/approval(requested_at/user_decision/decided_at/response_time)/execution。统计：total/auto/reviewed/approved/rejected/mandatory/avg_response_time。

## 合规

符合EU AI Act Article 14：决策可追溯、时间戳记录、用户身份、支持CSV导出审计。
