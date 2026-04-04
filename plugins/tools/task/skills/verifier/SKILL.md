---
description: "Verifier 结果验证 - Loop Verification 阶段调用：三阶段验证（功能合规性门控 + 代码质量审查 + 深度校验），输出 passed/failed 状态。质量分由 QualityGate 判定。由 Loop 内部调度，不直接面向用户"
model: sonnet
user-invocable: false
agent: task:verifier
hooks:
  SessionStop:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
---


# Skills(task:verifier) - 结果验证规范

<overview>

Verifier 技能负责验证任务执行结果是否满足验收标准。采用**三阶段验证架构**：Stage 1（Spec Compliance）检查功能合规性，Stage 2（Code Quality）审查代码质量，Stage 3（Deep Validation）深度校验。Stage 1 是 MUST PASS 的门控阶段，失败直接返回 failed。最终输出两种状态：passed（验收通过，含 quality_score 和可选 suggestions）、failed（验收未通过）。质量分判定由 Loop 的 QualityGate 阶段负责，verifier 不做质量分门控。

</overview>

<red_flags>

| AI Rationalization | Reality Check |
|-------------------|---------------|
| "代码能运行就说明功能正确" | 能运行≠功能正确，必须验证所有验收标准（包括边界、异常、性能）通过 |
| "手动测试通过了就可以跳过单元测试验证" | 手动验证无法复现和回归，coverage 验证必须用工具（nyc、coverage.py等）检查 |
| "测试用例全是正常场景就够了" | 必须覆盖：正常case、边界值、异常情况、null/空值，否则无法通过完整性检查 |
| "把 failed 改成 passed 不会有后果" | passed 等于验收通过，实际失败却输出 passed = 隐瞒问题 |
| "验收标准检查很耗时，简化一些项目" | 验收标准不能简化，验收必须完整逐一检查，不能跳过任何标准 |
| "已有回归测试，不用重复验证新改动" | 新改动可能破坏回归测试，必须重新跑完整测试套件，不能省略 |
| "一个验收标准失败，其他通过也可以" | 验收规则是全量通过（passed）或失败（failed），单个失败 = 整体失败 |
| "第三方库已验证过，测试时可以跳过它" | 第三方库与本代码交互处必须测试，跳过等于留下隐患 |
| "大部分问题都修了，剩下的标注为已知问题就行" | 存在未解决问题 = 自动 failed，禁止带已知问题标记 passed |
| "这个问题超出范围，先完成再说" | 执行过程中发现的问题必须处理或明确排除在验收标准外，不可忽略 |

</red_flags>

<navigation>

## 核心功能与检查清单

文件：[verifier-core.md](verifier-core.md)

适用场景、核心原则、执行流程、输出字段、结构化验收标准验证（精确匹配/量化阈值/容差）、验证前/中/后检查清单、最佳实践。

## 三阶段验证

- **Stage 1 - 功能合规检查** → [spec-compliance-checklist.md](spec-compliance-checklist.md)
  - MUST PASS 门控：验收标准匹配、功能完整性、回归检查
- **Stage 2 - 代码质量审查** → [code-quality-checklist.md](code-quality-checklist.md)
  - CAN SUGGEST：测试质量、代码标准、性能考量、安全检查
- **Stage 3 - 深度校验** → [deep-validation-checklist.md](deep-validation-checklist.md)
  - MUST PASS：用户预期验证、业务逻辑验证、交付物完整性验证

## 相关文档

- 输出格式（passed/failed） → [verifier-output.md](verifier-output.md)
- 集成指南（基础/高级/调试） → [verifier-integration.md](verifier-integration.md)

</navigation>

