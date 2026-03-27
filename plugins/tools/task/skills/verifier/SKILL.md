---
description: 结果验证规范 - 验收标准检查、质量评分、回归测试
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (6500+ tokens) -->

# Skills(task:verifier) - 结果验证规范

<overview>

Verifier 技能负责验证任务执行结果是否满足验收标准。采用**两阶段验证架构**：Stage 1（Spec Compliance）检查功能合规性，Stage 2（Code Quality）审查代码质量。Stage 1 是 MUST PASS 的门控阶段，失败直接触发 adjuster；Stage 2 仅在 Stage 1 通过后执行，生成 suggestions 但不触发 adjuster。最终输出三种状态之一：passed（全部通过）、suggestions（功能合规但质量有优化建议）、failed（功能合规未通过）。详细实现按职责拆分为以下文件。

</overview>

<red_flags>

| AI Rationalization | Reality Check |
|-------------------|---------------|
| "代码能运行就说明功能正确" | 能运行≠功能正确，必须验证所有验收标准（包括边界、异常、性能）通过 |
| "手动测试通过了就可以跳过单元测试验证" | 手动验证无法复现和回归，coverage 验证必须用工具（nyc、coverage.py等）检查 |
| "测试用例全是正常场景就够了" | 必须覆盖：正常case、边界值、异常情况、null/空值，否则无法通过完整性检查 |
| "把 failed 改成 suggestions 不会有后果" | suggestions 等于通过但有优化，实际失败却输出 suggestions = 隐瞒问题 |
| "验收标准检查很耗时，简化一些项目" | 验收标准不能简化，验收必须完整逐一检查，不能跳过任何标准 |
| "已有回归测试，不用重复验证新改动" | 新改动可能破坏回归测试，必须重新跑完整测试套件，不能省略 |
| "一个验收标准失败，其他通过也可以" | 验收规则是全量通过（passed）、优化建议（suggestions）或失败（failed），单个失败 = 整体失败 |
| "第三方库已验证过，测试时可以跳过它" | 第三方库与本代码交互处必须测试，跳过等于留下隐患 |

</red_flags>

<navigation>

## 核心功能

文件：[verifier-skill-core.md](verifier-skill-core.md)

包含 Verifier 的基础使用：适用场景、核心原则（验收测试最佳实践）、执行流程（步骤1-3）、输出格式和字段说明、快速参考、注意事项。

## 高级功能

文件：[verifier-skill-advanced.md](verifier-skill-advanced.md)

包含结构化验收标准的处理：结构化验收标准的验证流程、验证逻辑（通用验证函数、精确匹配、量化阈值）、容差验证示例、辅助函数、结构化验收标准最佳实践。

## 两阶段验证

- **Stage 1 - 功能合规检查** → [spec-compliance-checklist.md](spec-compliance-checklist.md)
  - MUST PASS 门控：验收标准匹配、功能完整性、回归检查
  - 任何 required 标准失败即触发 adjuster，不进入 Stage 2
- **Stage 2 - 代码质量审查** → [code-quality-checklist.md](code-quality-checklist.md)
  - CAN SUGGEST：测试质量、代码标准、性能考量、安全检查
  - quality_score >= 85 通过，否则生成 suggestions 创建优化迭代

## 相关文档

- 验证检查清单 → [verifier-checklist.md](verifier-checklist.md)
- 集成示例 → [verifier-integration.md](verifier-integration.md)
- 输出格式 → [verifier-output-formats.md](verifier-output-formats.md)

</navigation>

<!-- /STATIC_CONTENT -->
