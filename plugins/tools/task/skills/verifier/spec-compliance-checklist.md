# Spec Compliance Checklist (Stage 1)

## 概述
Stage 1 验证关注"是否做了要求的事"，即功能是否满足验收标准。

## MUST PASS - 功能合规检查

所有以下检查必须通过，否则直接触发 adjuster（不进入 Stage 2）。

### 1. 验收标准匹配
- [ ] 每个 acceptance_criteria 都有对应的实现
- [ ] exact_match 类型标准完全满足
- [ ] quantitative_threshold 类型标准在容差范围内
- [ ] 无遗漏的 required 优先级标准

### 2. 交付物完整性
- [ ] 每个任务的 `task.files` 中列出的文件实际存在（使用 Glob/Read 验证）
- [ ] 文件内容有实质性变更（非空文件、非仅空行/注释变更）
- [ ] 所有计划中的文件已创建/修改，无遗漏

### 3. 功能完整性
- [ ] 核心功能可正常运行（通过测试或手动验证）
- [ ] 输入输出格式符合规范
- [ ] 依赖的接口/API 已正确集成

### 4. 回归检查
- [ ] 现有测试仍然通过（无新增失败）
- [ ] 已有功能未被破坏
- [ ] 依赖关系未被打破

### 5. 深度校验（详见 deep-validation-checklist.md）
- [ ] 用户预期验证：交付物解决用户原始需求、符合使用场景
- [ ] 业务逻辑验证：规则正确实现、边界按业务规则处理
- [ ] 交付物完整性：所有承诺文件已交付、跨文件变更一致

## 输出格式

```json
{
  "stage": "spec_compliance",
  "status": "passed|failed",
  "criteria_results": [
    {
      "criterion_id": "AC1",
      "status": "passed|failed",
      "evidence": {
        "command": "npm test",
        "output": "...",
        "timestamp": "..."
      }
    }
  ],
  "gate_decision": "proceed_to_quality|trigger_adjuster"
}
```

## GATE 规则
- 任何 required 标准失败 -> gate_decision = "trigger_adjuster"
- 所有 required 标准通过 -> gate_decision = "proceed_to_quality"
