# Verifier 技能 - 高级功能

本文档包含结构化验收标准的验证流程和高级用法。

## 结构化验收标准的验证流程

**支持格式**：Verifier 自动检测并处理两种验收标准格式

1. **旧格式（字符串）**：按原有逻辑验证
   ```python
   "acceptance_criteria": ["单元测试覆盖率 ≥ 90%"]
   ```

2. **新格式（结构化对象）**：使用专门的验证逻辑
   ```python
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

## 验证逻辑

### 通用验证函数

```python
def verify_criterion(criterion, task_output, task_id):
    """通用的验收标准验证函数

    Args:
        criterion: 验收标准（字符串或对象）
        task_output: 任务输出结果
        task_id: 任务 ID

    Returns:
        dict: 验证结果 {status, expected, actual, ...}
    """

    # 检测格式
    if isinstance(criterion, str):
        # 旧格式：字符串验证
        return verify_string_criterion(criterion, task_output, task_id)

    elif isinstance(criterion, dict):
        # 新格式：结构化验证
        criterion_type = criterion.get('type')

        if criterion_type == 'exact_match':
            return verify_exact_match(criterion, task_output, task_id)

        elif criterion_type == 'quantitative_threshold':
            return verify_quantitative_threshold(criterion, task_output, task_id)

        else:
            raise Exception(f"不支持的验收标准类型: {criterion_type}")

    else:
        raise Exception(f"无效的验收标准格式: {type(criterion)}")
```

### 精确匹配验证

```python
def verify_exact_match(criterion, task_output, task_id):
    """精确匹配验证

    验证结果是否完全匹配期望值（0 错误、True、"success" 等）
    """
    verification_method = criterion.get('verification_method')
    expected_value = criterion.get('expected_value', 0)

    # 根据验证方法提取实际值
    if verification_method == 'run_linter':
        actual_value = extract_lint_errors(task_output)
    elif verification_method == 'run_tests':
        actual_value = all_tests_passed(task_output)
    elif verification_method == 'check_build':
        actual_value = build_succeeded(task_output)
    else:
        raise Exception(f"不支持的验证方法: {verification_method}")

    # 精确匹配
    passed = (actual_value == expected_value)

    return {
        "criterion_id": criterion['id'],
        "status": "passed" if passed else "failed",
        "evaluation_method": "exact_match",
        "expected": str(expected_value),
        "actual": str(actual_value),
        "priority": criterion['priority']
    }
```

### 量化阈值验证

```python
def verify_quantitative_threshold(criterion, task_output, task_id):
    """量化阈值验证（支持容差）

    验证度量值是否满足阈值要求，支持容差范围
    """
    metric = criterion.get('metric')
    operator = criterion.get('operator')
    threshold = criterion.get('threshold')
    tolerance = criterion.get('tolerance', 0)

    # 从任务输出中提取度量值
    actual_value = extract_metric_value(metric, task_output)

    # 计算容差范围
    if operator == '>=':
        lower_bound = threshold * (1 - tolerance)
        passed = actual_value >= threshold
        in_tolerance = actual_value >= lower_bound
    elif operator == '<=':
        upper_bound = threshold * (1 + tolerance)
        passed = actual_value <= threshold
        in_tolerance = actual_value <= upper_bound
    elif operator == '>':
        passed = actual_value > threshold
        in_tolerance = passed  # > 操作符不支持容差
    elif operator == '<':
        passed = actual_value < threshold
        in_tolerance = passed  # < 操作符不支持容差
    elif operator == '==':
        passed = actual_value == threshold
        in_tolerance = abs(actual_value - threshold) <= (threshold * tolerance)
    else:
        raise Exception(f"不支持的运算符: {operator}")

    # 确定状态
    if passed:
        status = "passed"
    elif in_tolerance:
        status = "passed_with_tolerance"  # 在容差范围内视为通过
    else:
        status = "failed"

    return {
        "criterion_id": criterion['id'],
        "status": status,
        "evaluation_method": "quantitative_threshold",
        "expected": f"{operator} {threshold}{criterion.get('unit', '')}",
        "actual": f"{actual_value}{criterion.get('unit', '')}",
        "tolerance": tolerance,
        "margin": {
            "gap": abs(actual_value - threshold),
            "relative_gap": abs(actual_value - threshold) / threshold if threshold != 0 else 0
        },
        "priority": criterion['priority']
    }
```

## 容差验证示例

```python
# 示例：覆盖率 88%，要求 ≥ 90%，容差 2%
criterion = {
    "id": "AC1",
    "type": "quantitative_threshold",
    "metric": "test_coverage",
    "operator": ">=",
    "threshold": 0.9,
    "tolerance": 0.02  # 2% 容差
}

# 验证结果
result = verify_quantitative_threshold(criterion, task_output, "T1")
# result = {
#     "status": "passed_with_tolerance",  # 88% 在 [88%, 92%] 范围内
#     "actual": "88%",
#     "expected": ">= 90%",
#     "tolerance": 0.02,
#     "margin": {"gap": 0.02, "relative_gap": 0.022}
# }
```

## 辅助函数

### 度量值提取

```python
def extract_metric_value(metric, task_output):
    """从任务输出中提取度量值

    Args:
        metric: 度量名称（test_coverage, response_time, etc.）
        task_output: 任务输出结果

    Returns:
        float: 度量值
    """
    if metric == 'test_coverage':
        return parse_coverage_report(task_output)
    elif metric == 'response_time':
        return parse_response_time(task_output)
    elif metric == 'error_count':
        return count_errors(task_output)
    else:
        raise Exception(f"不支持的度量: {metric}")
```

### Lint 错误提取

```python
def extract_lint_errors(task_output):
    """从任务输出中提取 lint 错误数"""
    # 解析 lint 输出
    lint_result = parse_lint_output(task_output)
    return lint_result.get('error_count', 0)
```

### 测试通过检查

```python
def all_tests_passed(task_output):
    """检查所有测试是否通过"""
    test_result = parse_test_output(task_output)
    return test_result.get('all_passed', False)
```

### 构建成功检查

```python
def build_succeeded(task_output):
    """检查构建是否成功"""
    build_result = parse_build_output(task_output)
    return build_result.get('success', False)
```

## 结构化验收标准最佳实践

### 必需字段完整性

所有结构化验收标准必须包含：
- `id`: 唯一标识符
- `type`: 验证类型（exact_match / quantitative_threshold）
- `description`: 人类可读描述
- `priority`: 优先级（required / recommended）

### 类型特定字段

**exact_match 类型**：
- `verification_method`: 验证方法
- `expected_value`: 期望值（可选，默认0）

**quantitative_threshold 类型**：
- `metric`: 度量名称
- `operator`: 比较运算符（>=, <=, >, <, ==）
- `threshold`: 阈值
- `tolerance`: 容差（可选，相对值）
- `unit`: 单位（可选）

### 容差使用指南

容差值为相对值，例如：
- `tolerance: 0.05` 表示 5% 的相对容差
- 对于阈值 90%，容差 5% 意味着 85.5%-94.5% 都视为通过

容差适用场景：
- 测试覆盖率（允许小幅波动）
- 性能指标（允许合理偏差）
- 资源使用（允许一定范围）

不适用场景：
- Lint 错误数（必须精确为 0）
- 构建状态（必须成功）
- 布尔判断（必须精确匹配）
