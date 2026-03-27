# Verifier 技能 - 核心功能

## 适用场景

Loop Check阶段：系统验证任务完成情况和质量标准，检查验收标准/交付物完整性/回归测试/迭代目标。

## 核心原则

- **可测试**：客观可验证，无主观判断
- **可度量**：数值指标(≥90%, <200ms)
- **独立**：每个标准可独立验证
- **结果导向**：验证用户体验而非技术步骤
- **避免绝对**：不用all/always/never

## 执行流程

1. **调用verifier**：`Skill(skill="task:verifier")` 要求：获取任务状态/系统验证/回归测试/报告≤100字/决定状态
2. **处理结果**：passed→退出Loop | suggestions→询问用户 | failed→失败调整
3. **输出报告**：`[MindFlow·{task}·结果验证/{N}·{status}]` + summary统计

## 输出字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 必填 | passed/suggestions/failed |
| report | string | 必填 | ≤100字 |
| verified_tasks | array | 必填 | `{task_id, task_name, status, criteria_passed, criteria_total, notes?}` |
| summary | object | 必填 | 统计摘要 |
| suggestions | array | 可选 | 优化建议(suggestions状态) |
| failures | array | 可选 | 失败详情(failed状态) |

## 详细文档

[结构化标准](verifier-skill-advanced.md) | [输出格式](verifier-output-formats.md) | [集成示例](verifier-integration.md) | [检查清单](verifier-checklist.md)

## 注意事项

**必须**：`Skill(skill="task:verifier")`调用 | 处理三种状态 | suggestions询问用户 | 验证所有任务

**禁止**：模糊标准 | 忽略suggestions | 跳过回归测试 | 修改返回JSON
