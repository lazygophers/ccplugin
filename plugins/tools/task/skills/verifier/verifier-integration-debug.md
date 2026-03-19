# Verifier 调试和错误处理

本文档包含 Verifier 的调试、测试、错误处理和重试机制。

## 高级用法

### 自定义验证规则

```python
def verify_with_custom_rules(tasks, custom_rules):
    """使用自定义验证规则

    Args:
        tasks: 任务列表
        custom_rules: 自定义验证规则

    Returns:
        dict: 验证结果
    """
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""验证任务（使用自定义规则）：

任务列表：
{json.dumps(tasks, indent=2, ensure_ascii=False)}

自定义验证规则：
{json.dumps(custom_rules, indent=2, ensure_ascii=False)}

要求：
1. 应用自定义验证规则
2. 验证标准验收标准
3. 生成验证报告
"""
    )

    return verification_result
```

### 条件验证

```python
def verify_conditional(tasks, conditions):
    """基于条件进行验证

    Args:
        tasks: 任务列表
        conditions: 验证条件（如环境、配置等）

    Returns:
        dict: 验证结果
    """
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""条件验证：

任务列表：
{json.dumps(tasks, indent=2, ensure_ascii=False)}

验证条件：
{json.dumps(conditions, indent=2, ensure_ascii=False)}

要求：
1. 根据条件调整验证标准
2. 执行验证
3. 生成验证报告
"""
    )

    return verification_result
```

### 分阶段验证

```python
def verify_phased(tasks, phase):
    """分阶段验证

    Args:
        tasks: 任务列表
        phase: 当前阶段（foundation / enhancement / refinement）

    Returns:
        dict: 验证结果
    """
    phase_criteria = {
        "foundation": "核心功能可运行，基本测试通过",
        "enhancement": "功能完整，测试覆盖率 ≥ 90%",
        "refinement": "代码质量优秀，文档完整，性能达标"
    }

    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""分阶段验证（{phase} 阶段）：

任务列表：
{json.dumps(tasks, indent=2, ensure_ascii=False)}

当前阶段标准：{phase_criteria[phase]}

要求：
1. 使用阶段性验证标准
2. 验证所有任务
3. 生成阶段验证报告
"""
    )

    return verification_result
```

---

## 调试和测试

### 调试模式

```python
def verify_with_debug(tasks, debug=True):
    """带调试信息的验证

    Args:
        tasks: 任务列表
        debug: 是否开启调试模式

    Returns:
        dict: 验证结果
    """
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""验证任务：
{json.dumps(tasks, indent=2, ensure_ascii=False)}
"""
    )

    if debug:
        print("\n=== Verifier Debug Info ===")
        print(f"Status: {verification_result['status']}")
        print(f"Verified Tasks: {len(verification_result['verified_tasks'])}")

        for task in verification_result['verified_tasks']:
            print(f"\n  Task {task['task_id']}:")
            print(f"    Status: {task['status']}")
            print(f"    Criteria: {task['criteria_passed']}/{task['criteria_total']}")

        if "suggestions" in verification_result:
            print(f"\nSuggestions: {len(verification_result['suggestions'])}")

        if "failures" in verification_result:
            print(f"\nFailures: {len(verification_result['failures'])}")

        print("==========================\n")

    return verification_result
```

### 模拟测试

```python
def test_verifier():
    """测试 Verifier 功能"""

    # 测试用例 1: 所有通过
    tasks1 = [
        {"id": "T1", "name": "任务1", "acceptance_criteria": ["标准1", "标准2"]}
    ]
    result1 = verify_single_task(tasks1[0]["id"], tasks1[0]["name"], tasks1[0]["acceptance_criteria"])
    assert result1["status"] in ["passed", "suggestions", "failed"]

    # 测试用例 2: 有建议
    # 模拟通过但有优化建议的场景

    # 测试用例 3: 失败
    # 模拟验收失败的场景

    print("✓ 所有测试通过")
```

---

## 错误处理

### 验证失败处理

```python
def handle_verification_failure(verification_result):
    """处理验证失败

    Args:
        verification_result: 验证结果

    Returns:
        dict: 失败分析和建议
    """
    if verification_result["status"] != "failed":
        return None

    # 分析失败原因
    failure_analysis = {
        "failed_tasks": [],
        "common_issues": [],
        "suggested_actions": []
    }

    for failure in verification_result["failures"]:
        failure_analysis["failed_tasks"].append(failure["task_id"])

        # 识别常见问题
        if "测试" in failure["criterion"]:
            failure_analysis["common_issues"].append("测试失败")
        if "覆盖率" in failure["criterion"]:
            failure_analysis["common_issues"].append("测试覆盖率不足")
        if "lint" in failure["criterion"].lower():
            failure_analysis["common_issues"].append("代码质量问题")

    # 生成建议
    if "测试失败" in failure_analysis["common_issues"]:
        failure_analysis["suggested_actions"].append("修复失败的测试用例")
    if "测试覆盖率不足" in failure_analysis["common_issues"]:
        failure_analysis["suggested_actions"].append("添加测试用例提高覆盖率")
    if "代码质量问题" in failure_analysis["common_issues"]:
        failure_analysis["suggested_actions"].append("运行 lint 并修复问题")

    return failure_analysis
```

### 重试机制

```python
def verify_with_retry(tasks, max_retries=3):
    """带重试机制的验证

    Args:
        tasks: 任务列表
        max_retries: 最大重试次数

    Returns:
        dict: 验证结果
    """
    for attempt in range(max_retries):
        try:
            verification_result = verify_multiple_tasks(tasks)

            if verification_result["status"] != "failed":
                return verification_result

            # 验证失败，分析原因
            print(f"验证失败（尝试 {attempt + 1}/{max_retries}）")

            if attempt < max_retries - 1:
                # 等待一段时间后重试
                time.sleep(2 ** attempt)  # 指数退避
            else:
                # 达到最大重试次数
                return verification_result

        except Exception as e:
            print(f"验证异常（尝试 {attempt + 1}/{max_retries}）：{str(e)}")

            if attempt == max_retries - 1:
                raise

    return verification_result
```
