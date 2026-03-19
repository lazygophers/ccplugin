# Planner 结构化验收标准

本文档详细说明了 Planner 的结构化验收标准功能。

## 向后兼容说明

`acceptance_criteria` 字段支持三种格式：

**1. 旧格式（字符串数组）** - 向后兼容
```json
"acceptance_criteria": ["单元测试覆盖率 ≥ 90%", "Lint 检查 0 错误"]
```

**2. 新格式（结构化对象）** - 推荐使用
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

**3. 混合格式** - 可在同一数组中混用
```json
"acceptance_criteria": [
  "所有 API 返回正确状态码",  // 旧格式
  {                           // 新格式
    "id": "AC1",
    "type": "exact_match",
    "description": "Lint 检查 0 错误",
    "verification_method": "run_linter",
    "priority": "required"
  }
]
```

---

## 支持的评估方法

### 1. 精确匹配（exact_match）

用于检验绝对要求（代码规范、测试通过、部署成功）

**字段定义**：

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | string | ✓ | 验收标准唯一标识 | `"AC1"` |
| `type` | string | ✓ | 固定为 `"exact_match"` | `"exact_match"` |
| `description` | string | ✓ | 验收标准描述 | `"Lint 检查 0 错误 0 警告"` |
| `verification_method` | string | ✓ | 验证方法 | `"run_linter"`, `"run_tests"`, `"check_build"` |
| `priority` | string | ✓ | `"required"` 或 `"recommended"` | `"required"` |
| `expected_value` | any | ✗ | 期望值（可选） | `0`, `"success"`, `true` |

**适用场景**：
- "所有单元测试通过"
- "Lint 检查 0 错误"
- "无类型错误（TypeScript）"
- "部署成功"

**完整示例**：
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

---

### 2. 量化阈值评估（quantitative_threshold）

用于处理可测量的数值指标，支持容差范围

**字段定义**：

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | string | ✓ | 验收标准唯一标识 | `"AC2"` |
| `type` | string | ✓ | 固定为 `"quantitative_threshold"` | `"quantitative_threshold"` |
| `description` | string | ✓ | 验收标准描述 | `"单元测试覆盖率 ≥ 90%"` |
| `metric` | string | ✓ | 度量指标名称 | `"test_coverage"`, `"response_time"` |
| `operator` | string | ✓ | 比较运算符 | `">="`, `"<="`, `">"`, `"<"`, `"=="` |
| `threshold` | number | ✓ | 阈值 | `0.9`, `200`, `100` |
| `unit` | string | ✗ | 单位（可选） | `"percentage"`, `"ms"`, `"MB"` |
| `tolerance` | number | ✗ | 容差（相对值，可选） | `0.02`（允许 ±2% 波动） |
| `priority` | string | ✓ | `"required"` 或 `"recommended"` | `"required"` |

**容差说明**：
- `tolerance = 0.02` 表示允许 ±2% 的波动
- 实际值在 `[threshold * (1 - tolerance), threshold * (1 + tolerance)]` 范围内视为通过
- 示例：阈值 90%，容差 2%，则 88%-92% 均视为通过

**适用场景**：
- "响应时间 < 200ms"
- "内存使用 < 100MB"
- "代码覆盖率 ≥ 90%"
- "圈复杂度 < 10"

**完整示例**：
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

---

## 使用示例

### 示例 1：旧格式（字符串）

```json
{
  "id": "T1",
  "description": "实现 JWT 工具函数",
  "agent": "coder（开发者）@task",
  "skills": ["golang:core（核心功能）@golang"],
  "files": ["internal/auth/jwt.go"],
  "acceptance_criteria": [
    "生成和验证 Token 功能完整",
    "单元测试覆盖率 ≥ 90%",
    "Lint 检查 0 错误"
  ]
}
```

### 示例 2：精确匹配（exact_match）

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

### 示例 3：量化阈值评估（quantitative_threshold）

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
    },
    {
      "id": "AC3",
      "type": "quantitative_threshold",
      "description": "内存使用 < 100MB",
      "metric": "memory_usage",
      "operator": "<",
      "threshold": 100,
      "unit": "MB",
      "tolerance": 0.05,
      "priority": "recommended"
    }
  ]
}
```

### 示例 4：混合格式

```json
{
  "id": "T4",
  "description": "完整的功能实现和验证",
  "agent": "full-stack（全栈开发）@task",
  "skills": ["development（开发）@task", "testing（测试）@task"],
  "acceptance_criteria": [
    "所有 API 端点返回正确状态码",  // 旧格式
    {
      "id": "AC1",
      "type": "exact_match",
      "description": "Lint 检查通过",
      "verification_method": "run_linter",
      "priority": "required"
    },
    {
      "id": "AC2",
      "type": "quantitative_threshold",
      "description": "测试覆盖率 ≥ 85%",
      "metric": "test_coverage",
      "operator": ">=",
      "threshold": 0.85,
      "tolerance": 0.03,
      "priority": "required"
    }
  ]
}
```

---

## 验证规则

Planner 在生成计划时，会自动验证结构化验收标准：

```python
def validate_acceptance_criteria(criteria_list):
    """验证验收标准的合理性"""
    for criterion in criteria_list:
        # 兼容旧版本字符串格式
        if isinstance(criterion, str):
            if not contains_quantifier(criterion):
                raise Exception(f"验收标准不够明确: {criterion}")

        # 新格式：对象
        elif isinstance(criterion, dict):
            # 验证必需字段
            assert 'id' in criterion, "缺少 id 字段"
            assert 'description' in criterion, "缺少 description 字段"
            assert 'type' in criterion, "缺少 type 字段"
            assert 'priority' in criterion, "缺少 priority 字段"
            assert criterion['priority'] in ['required', 'recommended']

            # 验证特定类型的字段
            if criterion['type'] == 'exact_match':
                assert 'verification_method' in criterion

            elif criterion['type'] == 'quantitative_threshold':
                assert 'metric' in criterion
                assert 'threshold' in criterion
                assert 'operator' in criterion
                assert criterion['operator'] in ['>=', '<=', '>', '<', '==']
```
