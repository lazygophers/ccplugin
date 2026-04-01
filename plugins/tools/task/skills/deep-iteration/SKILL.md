---
description: 深度迭代规范 - 质量递进、深度研究、质量门控
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:deep-iteration) - 深度迭代规范

<overview>

深度迭代是 MindFlow 的核心质量保障机制。与普通迭代（完成功能即止）不同，深度迭代通过多轮递进式研究和优化，确保最终结果完全符合预期。每轮迭代设定递增的质量阈值（60→75→85→90），结合深度研究（调研最新方案和最佳实践）、质量门控（多维度评分）和持续改进（识别高价值优化点），持续提升直到用户满意。

详细实现按职责拆分为两个文件。

</overview>

<navigation>

## 核心机制

文件：[deep-iteration-core.md](deep-iteration-core.md)

包含深度迭代的原理和参数定义：与普通迭代的区别对比、四个核心机制（深度理解、质量递进、深度分析、持续改进）、深度研究触发条件（第1轮、复杂任务、失败2次、质量不达标、用户要求）、终止条件（验收通过 + 质量达标 + 最佳实践 + 用户满意 + 最小迭代）。

## 集成和实践

文件：[deep-iteration-advanced.md](deep-iteration-advanced.md)

包含实际应用：集成到 Loop 各阶段（初始化配置、深度研究、计划设计融合、结果验证增强、失败调整增强）、输出格式（深度迭代报告和最终报告的 JSON 结构）、最佳实践（应做和避免的事项）、预期收益对比。

## 相关文档

- 详细代码实现 → [Loop 深度迭代实现](../loop/loop-deep-iteration.md)
- Loop 主文档 → [Loop Skill](../loop/SKILL.md)

</navigation>

<!-- /STATIC_CONTENT -->
