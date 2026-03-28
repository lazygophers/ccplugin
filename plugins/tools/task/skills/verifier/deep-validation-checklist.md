# Deep Validation Checklist (Stage 3)

## 概述
Stage 3 深度校验关注"是否真正满足了用户预期"，即交付物不仅技术上正确，更在业务语义和用户意图层面完全对齐。
仅在 Stage 1（功能合规）和 Stage 2（代码质量）通过后执行。

## 维度 1 - MUST PASS - 用户预期验证

交付物必须从用户视角验证，确保解决的是用户的真实问题。

### 1. 需求溯源
- [ ] 交付物直接解决了用户原始问题/需求（而非偏离后的衍生问题）
- [ ] 功能行为符合用户描述的使用场景
- [ ] 输出结果（文件/代码/文档）与用户期望的形式和内容一致
- [ ] 隐含需求已被识别和处理（用户未明确说但合理预期的部分）

### 2. 交互体验
- [ ] 用户能按预期方式使用交付物（无额外学习成本）
- [ ] 错误提示对用户友好、可操作
- [ ] 默认行为符合用户直觉

## 维度 2 - MUST PASS - 业务逻辑验证

确保代码不仅能跑，逻辑也符合业务规则。

### 1. 规则正确性
- [ ] 业务规则正确实现（计算公式、流程分支、状态转换）
- [ ] 数据流符合业务语义（字段含义、单位、精度未被错误转换）
- [ ] 业务约束条件完整（权限、时效、额度等限制已实现）

### 2. 边界与异常
- [ ] 边界条件按业务规则处理（而非仅技术兜底）
- [ ] 异常场景有合理的业务层面响应（降级、重试、补偿）
- [ ] 并发/竞态条件在业务层面有明确策略

## 维度 3 - MUST PASS - 交付物完整性验证

确保交付物作为整体是完整且一致的。

### 1. 产出完整性
- [ ] 所有承诺的文件/模块已交付（无遗漏）
- [ ] 文档/注释/配置与代码实现同步
- [ ] 依赖关系完整（无遗漏引用、无悬空导入）

### 2. 跨文件一致性
- [ ] 变更在所有相关位置保持一致（类型定义、接口签名、配置项）
- [ ] 重命名/重构已传播到全部引用点
- [ ] 版本号/常量在多处引用时值一致

## 输出格式

```json
{
  "stage": "deep_validation",
  "status": "passed|failed|suggestions",
  "dimension_results": [
    {
      "name": "user_expectation",
      "status": "passed|failed",
      "checks": [
        {
          "item": "交付物直接解决用户原始需求",
          "status": "passed|failed",
          "evidence": "...",
          "note": "可选补充说明"
        }
      ]
    },
    {
      "name": "business_logic",
      "status": "passed|failed",
      "checks": []
    },
    {
      "name": "delivery_completeness",
      "status": "passed|failed",
      "checks": []
    }
  ],
  "gate_decision": "accepted|trigger_adjuster",
  "relation_to_prior_stages": "Stage 1 确认做了什么，Stage 2 确认做得好不好，Stage 3 确认做对了没有"
}
```

## GATE 规则
- 任何 required 维度（三个维度均为 required）失败 -> gate_decision = "trigger_adjuster"
- 所有维度通过 -> gate_decision = "accepted"
- 维度内单项 failed 即该维度 failed
