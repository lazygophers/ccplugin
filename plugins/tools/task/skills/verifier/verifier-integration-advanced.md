# Verifier 高级集成

## 结构化验收标准验证

### validate_structured_criterion

字符串格式直接通过(向后兼容)。结构化格式验证：

| 检查 | 规则 |
|------|------|
| 必需字段 | id + type + description + priority |
| priority | required/recommended |
| exact_match | 需verification_method(run_linter/run_tests/check_build) |
| quantitative_threshold | 需metric + operator(>=,<=,>,<,==) + threshold；tolerance可选(0-1) |

### validate_all_criteria

遍历所有tasks的acceptance_criteria，收集验证错误。返回 `{valid: bool, errors: [{task_id, criterion_index, error}]}`

## 混合格式验证

支持同一任务中字符串和结构化标准共存。对结构化标准使用专用验证逻辑，字符串标准使用原有逻辑。

## 容差处理

对于 quantitative_threshold + tolerance：
- actual ≥ threshold → `passed`
- actual ≥ threshold×(1-tolerance) → `passed_with_tolerance`
- actual < threshold×(1-tolerance) → `failed`

返回margin信息：gap(绝对差距) + relative_gap(相对差距)
