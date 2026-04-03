# Deep Iteration 实现指南

## 配置初始化

评估任务复杂度(文件数×25 + 技术新颖度×25 + 任务类型×25 + 质量要求×25 = 0-100)：≤30=simple(min 1轮) | 31-60=moderate(min 2轮) | >60=complex(min 3轮)

质量阈值动态递进（按任务类型区分）：

| 任务类型 | 第1轮 | 第2轮 | 第3轮 | 第4+轮 | 说明 |
|---------|-------|-------|-------|--------|------|
| exploration（探索） | 50 | 60 | 70 | 70 | 探索重理解，质量要求较低 |
| feature（开发） | 60 | 75 | 85 | 90 | 默认递进，适用大多数场景 |
| bugfix（修复） | 60 | 75 | 85 | 90 | 与开发一致 |
| refactor（重构） | 70 | 80 | 85 | 90 | 重构起点高，需保证不破坏现有功能 |

任务类型由 Planner 在计划文件 frontmatter 的 `task_type` 字段指定，默认 `feature`。

## DeepResearch：深度研究（可选）

触发条件：第1轮 | 失败2次+ | 质量<阈值-10 | 高复杂度 | 用户要求

调用 `deepresearch:deep-research`：查找最新方案→对比3-5种→确定最佳实践→可量化标准。输出：技术对比表/推荐方案/质量标准/参考链接。

## 计划设计（融合研究）

Planner prompt注入：任务目标 + 质量目标(当前阈值) + 迭代等级(Foundation/Enhancement/Refinement/Excellence)。有研究结果时追加：研究发现/推荐方案/质量标准。

## 结果验证（质量门控+持续改进）

三重职责：验收标准检查 + 质量门控评分(功能/测试覆盖率/代码质量/性能/可维护性/安全/最佳实践) + 持续改进识别

质量门控：score < threshold → QualityGate 不达标→PromptOptimization（非失败）。passed 且达标 → Cleanup。failed → Adjustment。

## 深度失败分析（失败2次+触发）

调用 `deepresearch:deep-research` 执行5 Why根因分析→查找类似案例→对比3种修复方案(快速/根本/重构)→推荐方案注入adjuster prompt。

## 输出格式

JSON: `{status, iteration, quality_progression[{iteration,score,level}], research_conducted, final_quality_score, quality_threshold_met, next_action}`

完成报告：总迭代/质量进展(分数序列)/研究次数/用户指导次数/变更文件数/是否达标

## 辅助决策

- **迭代等级**：第1轮=Foundation / 第2轮=Enhancement / 第3轮=Refinement / 第4+轮=Excellence
- **质量阈值**：根据 task_type 查表，默认 feature（60/75/85/90）
- **技术债记录**：将识别的优化点记录到 `.claude/memory/tech-debt.md`
