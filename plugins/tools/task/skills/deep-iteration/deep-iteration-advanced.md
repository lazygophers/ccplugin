# Skills(task:deep-iteration) - 集成和实践

## Loop 集成

深度迭代增强 Loop 各阶段行为，非独立模块。

| 阶段 | 增强行为 | 详见 |
|------|---------|------|
| 初始化 | 评估复杂度 → 配置 min_iterations + quality_threshold(60→75→85→90) | - |
| 深度研究(1.5) | 触发条件满足时在计划前执行 | [loop-deep-iteration.md](../loop/loop-deep-iteration.md) |
| 计划设计 | 研究发现注入上下文 + 推荐方案优先 + 质量标准→验收标准 | 同上 |
| 结果验证 | 质量门控(分数≥阈值) + 最小迭代检查 + 持续改进(高价值优化点) | 同上 |
| 失败调整 | 失败2次→5 Why深度根因分析→应用推荐修复 | 同上 |

## 输出格式

JSON: `{status, iteration, quality_progression[{iteration,score,level}], research_conducted, final_quality_score, quality_threshold_met, next_action}`

最终报告：总迭代、质量进展(分数序列)、深度研究次数、用户指导次数、变更文件数

## 最佳实践

**必须**：第1轮启用深度研究、每轮提高质量阈值、失败时分析根因、通过后仍检查优化空间、研究发现存入 `.claude/memory/`

**禁止**：浅尝辄止(功能完成≠质量达标)、重复低质量迭代、跳过深度研究、过早终止(需完成最小迭代)

## 快速参考

质量阈值：1→60 | 2→75 | 3→85 | 4+→90。研究触发：第1轮/失败2次/质量不达标/复杂任务/用户要求。终止条件：验收通过+质量达标+最佳实践+用户满意+最小迭代——全部满足。

详细文档：[deep-iteration-details.md](deep-iteration-details.md) | [loop-deep-iteration.md](../loop/loop-deep-iteration.md)
