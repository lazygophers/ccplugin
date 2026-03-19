# Verifier 高级集成

本文档包含结构化验收标准验证的详细说明和高级用法。

## 结构化验收标准验证

### 验证函数：处理结构化标准

```python
def validate_structured_criterion(criterion, task_id):
    """验证结构化验收标准的字段完整性

    Args:
        criterion: 验收标准（可以是字符串或对象）
        task_id: 任务 ID

    Raises:
        Exception: 当必需字段缺失或字段值无效时

    Returns:
        bool: 验证通过返回 True
    """
    # 如果是字符串格式，直接通过（向后兼容）
    if isinstance(criterion, str):
        return True

    # 验证结构化格式
    if not isinstance(criterion, dict):
        raise Exception(f"任务 {task_id} 的验收标准格式无效：必须是字符串或对象")

    # 1. 验证必需字段
    required_fields = ['id', 'type', 'description', 'priority']
    for field in required_fields:
        if field not in criterion:
            raise Exception(f"任务 {task_id} 的验收标准缺少必需字段: {field}")

    # 2. 验证 priority 值
    if criterion['priority'] not in ['required', 'recommended']:
        raise Exception(
            f"任务 {task_id} 的验收标准 {criterion['id']} priority 值无效: "
            f"{criterion['priority']}（应为 'required' 或 'recommended'）"
        )

    # 3. 根据类型验证特定字段
    criterion_type = criterion.get('type')

    if criterion_type == 'exact_match':
        # 精确匹配需要 verification_method 字段
        if 'verification_method' not in criterion:
            raise Exception(
                f"任务 {task_id} 的验收标准 {criterion['id']} 缺少字段: "
                f"verification_method（exact_match 类型必需）"
            )

        # 验证 verification_method 值
        valid_methods = ['run_linter', 'run_tests', 'check_build']
        if criterion['verification_method'] not in valid_methods:
            raise Exception(
                f"任务 {task_id} 的验收标准 {criterion['id']} verification_method 值无效: "
                f"{criterion['verification_method']}（支持: {', '.join(valid_methods)}）"
            )

    elif criterion_type == 'quantitative_threshold':
        # 量化阈值需要 metric, operator, threshold 字段
        required_quantitative = ['metric', 'operator', 'threshold']
        for field in required_quantitative:
            if field not in criterion:
                raise Exception(
                    f"任务 {task_id} 的验收标准 {criterion['id']} 缺少字段: "
                    f"{field}（quantitative_threshold 类型必需）"
                )

        # 验证 operator 值
        valid_operators = ['>=', '<=', '>', '<', '==']
        if criterion['operator'] not in valid_operators:
            raise Exception(
                f"任务 {task_id} 的验收标准 {criterion['id']} operator 值无效: "
                f"{criterion['operator']}（支持: {', '.join(valid_operators)}）"
            )

        # 验证 tolerance（如果存在）
        if 'tolerance' in criterion:
            tolerance = criterion['tolerance']
            if not isinstance(tolerance, (int, float)) or tolerance < 0 or tolerance > 1:
                raise Exception(
                    f"任务 {task_id} 的验收标准 {criterion['id']} tolerance 值无效: "
                    f"{tolerance}（应为 0-1 之间的相对值，如 0.05 表示 5%）"
                )

    else:
        raise Exception(
            f"任务 {task_id} 的验收标准 {criterion['id']} type 值不支持: "
            f"{criterion_type}（支持: exact_match, quantitative_threshold）"
        )

    return True


def validate_all_criteria(tasks):
    """验证所有任务的验收标准

    Args:
        tasks: 任务列表，每个任务包含 id 和 acceptance_criteria

    Returns:
        dict: 验证结果 {valid: bool, errors: list}
    """
    errors = []

    for task in tasks:
        task_id = task.get('id', 'unknown')
        acceptance_criteria = task.get('acceptance_criteria', [])

        for i, criterion in enumerate(acceptance_criteria):
            try:
                validate_structured_criterion(criterion, task_id)
            except Exception as e:
                errors.append({
                    'task_id': task_id,
                    'criterion_index': i,
                    'error': str(e)
                })

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
```

### 示例：验证混合格式的验收标准

```python
def verify_mixed_format_criteria():
    """验证混合使用字符串和结构化格式的验收标准"""

    tasks = [
        {
            "id": "T1",
            "name": "实现 API 性能优化",
            "acceptance_criteria": [
                # 字符串格式（向后兼容）
                "代码编译通过",
                # 结构化格式：精确匹配
                {
                    "id": "AC1",
                    "type": "exact_match",
                    "description": "Lint 检查无错误",
                    "verification_method": "run_linter",
                    "expected_value": 0,
                    "priority": "required"
                },
                # 结构化格式：量化阈值
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
    ]

    # 1. 验证格式
    validation_result = validate_all_criteria(tasks)
    if not validation_result['valid']:
        print("验证标准格式错误：")
        for error in validation_result['errors']:
            print(f"  任务 {error['task_id']}: {error['error']}")
        return

    print("✓ 验收标准格式验证通过")

    # 2. 执行验证
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""验证任务：

任务列表：
{json.dumps(tasks, indent=2, ensure_ascii=False)}

要求：
1. 处理混合格式的验收标准（字符串 + 结构化对象）
2. 对结构化标准使用专门的验证逻辑
3. 生成详细的验证报告
"""
    )

    # 3. 输出结果
    print(f"\n验证状态：{verification_result['status']}")
    print(f"验证报告：{verification_result['report']}")

    return verification_result
```

### 示例：处理容差范围验证

```python
def verify_with_tolerance():
    """展示如何处理带容差的量化阈值验证"""

    tasks = [
        {
            "id": "T1",
            "name": "性能优化",
            "acceptance_criteria": [
                {
                    "id": "AC1",
                    "type": "quantitative_threshold",
                    "description": "测试覆盖率 ≥ 90%",
                    "metric": "test_coverage",
                    "operator": ">=",
                    "threshold": 0.9,
                    "unit": "percentage",
                    "tolerance": 0.02,  # 2% 容差，即 88%-92% 都视为通过
                    "priority": "required"
                }
            ]
        }
    ]

    # 验证任务
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""验证任务（支持容差）：

任务：{json.dumps(tasks[0], indent=2, ensure_ascii=False)}

验证说明：
- 对于 threshold=0.9（90%），tolerance=0.02（2%）
- 容差范围：88% - 92%
- 如果实际值在此范围内，状态为 "passed_with_tolerance"
- 如果实际值 ≥ 90%，状态为 "passed"
- 如果实际值 < 88%，状态为 "failed"
"""
    )

    # 检查验证结果
    for task_result in verification_result.get('verified_tasks', []):
        for criterion_result in task_result.get('criteria_results', []):
            status = criterion_result.get('status')

            if status == 'passed_with_tolerance':
                print(f"\n⚠️  标准 {criterion_result['criterion_id']} 在容差范围内通过")
                print(f"    期望：{criterion_result['expected']}")
                print(f"    实际：{criterion_result['actual']}")
                print(f"    容差：{criterion_result.get('tolerance', 0) * 100}%")

                margin = criterion_result.get('margin', {})
                print(f"    差距：{margin.get('gap', 0)} (相对差距: {margin.get('relative_gap', 0) * 100:.1f}%)")

    return verification_result
```
