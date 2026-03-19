# Planner 结构化验收标准

本文档详细说明了 Planner 的结构化验收标准功能。

<compatibility>

## 向后兼容

`acceptance_criteria` 字段支持三种格式。旧格式使用字符串数组，简单直接；新格式使用结构化对象，提供更精确的验证定义；混合格式允许在同一数组中同时使用两种格式，便于逐步迁移。

旧格式（字符串数组）：
```json
"acceptance_criteria": ["单元测试覆盖率 ≥ 90%", "Lint 检查 0 错误"]
```

新格式（结构化对象，推荐）：
```json
"acceptance_criteria": [
  {
    "id": "AC1",
    "type": "quantitative_threshold",
    "description": "单元测试覆盖率 ≥ 90%",
    "metric": "test_coverage",
    "operator": ">=",
    "threshold": 0.9,
    "tolerance": 0.02,
    "priority": "required"
  }
]
```

混合格式：
```json
"acceptance_criteria": [
  "所有 API 返回正确状态码",
  {
    "id": "AC1",
    "type": "exact_match",
    "description": "Lint 检查 0 错误",
    "verification_method": "run_linter",
    "priority": "required"
  }
]
```

</compatibility>

<evaluation_methods>

## 评估方法

精确匹配（exact_match）用于检验绝对要求，如代码规范、测试通过、部署成功等二元判定场景。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | string | 是 | 验收标准唯一标识 | `"AC1"` |
| `type` | string | 是 | 固定为 `"exact_match"` | `"exact_match"` |
| `description` | string | 是 | 验收标准描述 | `"Lint 检查 0 错误 0 警告"` |
| `verification_method` | string | 是 | 验证方法 | `"run_linter"`, `"run_tests"`, `"check_build"` |
| `priority` | string | 是 | `"required"` 或 `"recommended"` | `"required"` |
| `expected_value` | any | 否 | 期望值 | `0`, `"success"`, `true` |

适用场景包括"所有单元测试通过"、"Lint 检查 0 错误"、"无类型错误（TypeScript）"、"部署成功"。

```json
{
  "id": "AC1",
  "type": "exact_match",
  "description": "Lint 检查 0 错误 0 警告",
  "verification_method": "run_linter",
  "expected_value": 0,
  "priority": "required"
}
```

量化阈值评估（quantitative_threshold）用于处理可测量的数值指标，支持容差范围。容差（tolerance）为相对值，例如 `tolerance = 0.02` 表示允许正负 2% 的波动，实际值在 `[threshold * (1 - tolerance), threshold * (1 + tolerance)]` 范围内视为通过。

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | string | 是 | 验收标准唯一标识 | `"AC2"` |
| `type` | string | 是 | 固定为 `"quantitative_threshold"` | `"quantitative_threshold"` |
| `description` | string | 是 | 验收标准描述 | `"单元测试覆盖率 ≥ 90%"` |
| `metric` | string | 是 | 度量指标名称 | `"test_coverage"`, `"response_time"` |
| `operator` | string | 是 | 比较运算符 | `">="`, `"<="`, `">"`, `"<"`, `"=="` |
| `threshold` | number | 是 | 阈值 | `0.9`, `200`, `100` |
| `unit` | string | 否 | 单位 | `"percentage"`, `"ms"`, `"MB"` |
| `tolerance` | number | 否 | 容差（相对值） | `0.02`（允许正负 2% 波动） |
| `priority` | string | 是 | `"required"` 或 `"recommended"` | `"required"` |

适用场景包括"响应时间 < 200ms"、"内存使用 < 100MB"、"代码覆盖率 >= 90%"、"圈复杂度 < 10"。

```json
{
  "id": "AC2",
  "type": "quantitative_threshold",
  "description": "单元测试覆盖率 ≥ 90%",
  "metric": "test_coverage",
  "operator": ">=",
  "threshold": 0.9,
  "unit": "percentage",
  "tolerance": 0.02,
  "priority": "required"
}
```

</evaluation_methods>

<examples>

## 使用示例

精确匹配示例：

```json
{
  "id": "T2",
  "description": "代码规范检查",
  "agent": "linter（代码检查）@task",
  "skills": ["code-quality（代码质量）@task"],
  "acceptance_criteria": [
    {
      "id": "AC1",
      "type": "exact_match",
      "description": "Lint 检查 0 错误 0 警告",
      "verification_method": "run_linter",
      "expected_value": 0,
      "priority": "required"
    },
    {
      "id": "AC2",
      "type": "exact_match",
      "description": "所有单元测试通过",
      "verification_method": "run_tests",
      "expected_value": true,
      "priority": "required"
    }
  ]
}
```

量化阈值示例：

```json
{
  "id": "T3",
  "description": "性能优化和测试覆盖",
  "agent": "optimizer（性能优化）@task",
  "skills": ["performance（性能优化）@task", "testing（测试）@task"],
  "acceptance_criteria": [
    {
      "id": "AC1",
      "type": "quantitative_threshold",
      "description": "单元测试覆盖率 ≥ 90%",
      "metric": "test_coverage",
      "operator": ">=",
      "threshold": 0.9,
      "unit": "percentage",
      "tolerance": 0.02,
      "priority": "required"
    },
    {
      "id": "AC2",
      "type": "quantitative_threshold",
      "description": "API 响应时间 < 200ms",
      "metric": "response_time",
      "operator": "<",
      "threshold": 200,
      "unit": "ms",
      "tolerance": 0.1,
      "priority": "required"
    }
  ]
}
```

</examples>

<validation_rules>

## 验证规则

Planner 在生成计划时自动验证结构化验收标准。验证逻辑兼容旧版字符串格式，同时对结构化对象执行严格的字段和类型检查。

```python
def validate_acceptance_criteria(criteria_list):
    """验证验收标准的合理性"""
    for criterion in criteria_list:
        if isinstance(criterion, str):
            if not contains_quantifier(criterion):
                raise Exception(f"验收标准不够明确: {criterion}")
        elif isinstance(criterion, dict):
            assert 'id' in criterion, "缺少 id 字段"
            assert 'description' in criterion, "缺少 description 字段"
            assert 'type' in criterion, "缺少 type 字段"
            assert 'priority' in criterion, "缺少 priority 字段"
            assert criterion['priority'] in ['required', 'recommended']

            if criterion['type'] == 'exact_match':
                assert 'verification_method' in criterion
            elif criterion['type'] == 'quantitative_threshold':
                assert 'metric' in criterion
                assert 'threshold' in criterion
                assert 'operator' in criterion
                assert criterion['operator'] in ['>=', '<=', '>', '<', '==']
```

</validation_rules>
