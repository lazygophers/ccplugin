---
description: "Adjuster 失败调整 - Loop Adjustment 阶段调用：任务失败时分析原因、检测停滞，四级升级策略（Retry → Debug → Replan → Ask User）。由 Loop 内部调度，不直接面向用户"
model: sonnet
user-invocable: false
agent: task:adjuster
---


# Skills(task:adjuster) - 失败调整规范

## 概述

任务失败时介入，借鉴Circuit Breaker模式分析原因、检测停滞、分级升级。四级策略：L1 Retry(含Self-Healing,匹配17类错误自动修复) → L2 Debug(深度诊断) → L3 Replan(含Micro-Replan优先局部重规划) → L4 Ask User(人工指导)。退避：`2^(failure_count-1)`秒。

**停滞检测**：当连续 2 次失败的 `error_type` + 失败任务 ID 完全相同时，判定为停滞（相同错误在相同任务上重复出现）。停滞后跳过中间级别，直接升级到 L4 Ask User。

**振荡检测**：策略模式出现 A→B→A→B 交替时，立即 ask_user。**紧急逃逸**：总失败≥15 立即 ask_user。

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

1. **调用adjuster**：`Skill(skill="task:adjuster")` 要求：获取失败详情/分析原因(编译/测试/依赖/运行时/环境)/检测停滞/分级升级/报告≤100字
2. **指数退避**：按`retry_config.backoff_seconds`等待
3. **策略路由**：retry→应用adjustments重试 | debug→调用debug agent | replan→调用planner | ask_user→AskUserQuestion
4. **输出报告**：`[MindFlow·{task}·失败调整/{N}·{strategy}]` + adjustments详情

## 升级策略表

| 级别 | 策略(status) | 触发条件 | 退避 | Loop流向 |
|------|-------------|---------|------|---------|
| L1 | retry | 首次失败/临时错误。含Self-Healing：匹配17类可预测错误时自动修复 | 0s | PromptOptimization |
| L2 | debug | Retry×3失败/持续性错误 | 2s | PromptOptimization |
| L3 | replan | Debug×3无效。优先Micro-Replan(仅失败任务+直接依赖)，失败则Full Replan | 4s | PromptOptimization |
| L4 | ask_user | Replan×2失败/振荡(A→B→A→B)/总失败≥15 | - | 用户决定→PromptOptimization |

## 注意事项

**必须**：`Skill(skill="task:adjuster")`调用 | 检查strategy字段 | 应用指数退避 | ask_user通过AskUserQuestion | 记录失败历史 | 最大重试3次

**禁止**：无限重试 | 忽略失败历史 | 跳过退避 | 停滞时自动重试 | 修改返回JSON

## 详细文档

- [升级策略与自愈机制](adjuster-strategies.md) | [输出格式](adjuster-output.md) | [集成指南](adjuster-integration.md)

