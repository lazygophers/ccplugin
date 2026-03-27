---
description: 失败调整规范 - 分析失败原因、检测停滞、应用升级策略的执行规范
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (7100+ tokens) -->

# Skills(task:adjuster) - 失败调整规范

## 概述

任务失败时介入，借鉴Circuit Breaker模式分析原因、检测停滞、分级升级。六级策略：L1 Retry(1次错误,0s) → L1.5 Self-Healing(匹配17类错误,0s) → L2 Debug(深度诊断,2s) → L2.5 Micro-Replan(仅失败任务+直接依赖) → L3 Full Replan(重建计划) → L4 Ask User(人工指导)。退避：`2^(failure_count-1)`秒。振荡检测(A→B→A→B立即ask_user)。紧急逃逸(总失败≥15立即ask_user)。

## Red Flags

| AI合理化 | 现实检查 |
|----------|---------|
| 失败一次直接replan | 必须按级升级，跳级浪费信息 |
| 删掉退避时间 | 退避是Circuit Breaker关键 |
| 用失败次数替代错误类型检测 | 相同错误3次≠不同错误各1-2次 |
| ask_user自动重试 | ask_user强制阻塞等用户 |
| 报告只写"失败了" | 必须含原因+策略+方案 |
| 复用旧debug结果 | 第2次可能不同原因，必须重新诊断 |
| 失败3次自动修复 | 停滞后必须人工确认 |

## 执行流程

1. **调用adjuster**：`Agent(agent="task:adjuster")` 要求：获取失败详情/分析原因(编译/测试/依赖/运行时/环境)/检测停滞/分级升级/报告≤100字
2. **指数退避**：按`retry_config.backoff_seconds`等待
3. **策略路由**：retry→应用adjustments重试 | debug→调用debug agent | replan→调用planner | ask_user→AskUserQuestion
4. **输出报告**：`[MindFlow·{task}·失败调整/{N}·{strategy}]` + adjustments详情

## 升级策略表

| 级别 | 策略 | 触发条件 | 等待 | Loop流向 |
|------|------|---------|------|---------|
| L1 | Retry | 1次相同错误 | 0s | 任务执行 |
| L1.5 | Self-Healing | 匹配17类错误 | 0s | 任务执行 |
| L2 | Debug | 持续性错误 | 2s | 任务执行 |
| L2.5 | Micro-Replan | 3次Debug无效 | 4s | 部分重设计 |
| L3 | Full Replan | Micro-Replan失败 | 8s | 完整重设计 |
| L4 | Ask User | 所有自动失败/振荡/总失败≥15 | - | 等待用户 |

### Micro-Replan(L2.5)

仅重规划失败任务+直接依赖，保留成功任务。输出`replan_scope{failed_tasks, direct_dependencies, keep_completed, new_approach}`。失败则升级L3。

## 注意事项

**必须**：`Agent(agent="task:adjuster")`调用 | 检查strategy字段 | 应用指数退避 | ask_user通过AskUserQuestion | 记录失败历史 | 最大重试3次

**禁止**：无限重试 | 忽略失败历史 | 跳过退避 | 停滞时自动重试 | 修改返回JSON

## 详细文档

- [升级策略](adjuster-strategies.md) | [升级流程图](escalation-flowchart.md) | [输出格式](adjuster-output-formats.md) | [集成示例](adjuster-integration.md)

<!-- /STATIC_CONTENT -->
