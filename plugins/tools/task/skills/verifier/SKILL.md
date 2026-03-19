---
description: 结果验证规范 - 验收标准检查、质量评分、回归测试
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:verifier) - 结果验证规范

<overview>

Verifier 技能负责验证任务执行结果是否满足验收标准。它在 Loop 的 Check 阶段被调用，通过系统性检查每个子任务的完成情况、测试覆盖率和回归测试结果，输出三种状态之一：passed（全部通过）、suggestions（通过但有优化建议）、failed（验收失败）。详细实现按职责拆分为以下文件。

</overview>

<navigation>

## 核心功能

文件：[verifier-skill-core.md](verifier-skill-core.md)

包含 Verifier 的基础使用：适用场景、核心原则（验收测试最佳实践）、执行流程（步骤1-3）、输出格式和字段说明、快速参考、注意事项。

## 高级功能

文件：[verifier-skill-advanced.md](verifier-skill-advanced.md)

包含结构化验收标准的处理：结构化验收标准的验证流程、验证逻辑（通用验证函数、精确匹配、量化阈值）、容差验证示例、辅助函数、结构化验收标准最佳实践。

## 相关文档

- 验证检查清单 → [verifier-checklist.md](verifier-checklist.md)
- 集成示例 → [verifier-integration.md](verifier-integration.md)
- 输出格式 → [verifier-output-formats.md](verifier-output-formats.md)

</navigation>
