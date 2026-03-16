# Verifier 集成示例

本文档包含在不同场景下集成和使用 Verifier 的示例代码。

## Loop 命令中的使用

### 基础集成

```python
def verification_phase(task_description, iteration):
    """Loop 命令结果验证（Verification / Check）阶段"""

    # 调用 verifier agent
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""执行结果验证：

任务目标：{task_description}
当前迭代：第 {iteration + 1} 轮

要求：
1. 获取所有任务的状态和验收标准
2. 系统性验证每个任务的验收标准
3. 检查回归测试
4. 生成验收报告（≤100字）
5. 决定验收状态
"""
    )

    # 输出报告
    print(f"[MindFlow·{task_description}·结果验证/{iteration + 1}·{verification_result['status']}]")
    print(f"验收报告：{verification_result['report']}")

    # 根据状态决定行为
    if verification_result["status"] == "passed":
        # 完全通过，Loop 退出
        return "exit"

    elif verification_result["status"] == "suggestions":
        # 有建议，询问用户
        user_response = AskUserQuestion(
            f"{verification_result['report']}\n\n" +
            "建议：\n" +
            "\n".join(f"- {s['suggestion']}" for s in verification_result['suggestions']) +
            "\n\n这些优化是否属于当前任务范围？(是/否)"
        )

        if user_response.strip().lower() in ["是", "yes", "y"]:
            return "continue"  # 继续迭代
        else:
            return "exit"  # 完成

    elif verification_result["status"] == "failed":
        # 失败，进入调整阶段
        return "adjustment"  # 进入失败调整

    return "adjustment"  # 默认进入调整
```

---

## 处理验证结果

### 完整处理流程

```python
def handle_verification_result(verification_result, task_description):
    """处理 Verifier 返回结果

    Args:
        verification_result: Verifier agent 的返回结果
        task_description: 任务描述

    Returns:
        str: 下一步行为（exit / continue / adjustment）
    """

    # 1. 检查状态
    if verification_result["status"] not in ["passed", "suggestions", "failed"]:
        raise Exception(f"无效的验收状态：{verification_result['status']}")

    # 2. 输出验收报告
    print(f"\n验收报告：{verification_result['report']}")

    # 3. 输出统计信息
    summary = verification_result["summary"]
    print(f"\n任务统计：")
    print(f"  总任务数：{summary['total_tasks']}")
    print(f"  完成任务：{summary['completed_tasks']}")
    print(f"  失败任务：{summary['failed_tasks']}")

    if "test_coverage" in summary:
        print(f"  测试覆盖率：{summary['test_coverage']}%")

    if "regression_tests_passed" in summary:
        status_text = "通过" if summary["regression_tests_passed"] else "失败"
        print(f"  回归测试：{status_text}")

    # 4. 根据状态决定下一步
    if verification_result["status"] == "passed":
        print("\n✓ 所有验收标准通过，任务完成！")
        return "exit"

    elif verification_result["status"] == "suggestions":
        print("\n✓ 验收标准通过，但有以下优化建议：")
        for i, suggestion in enumerate(verification_result['suggestions'], 1):
            priority_icon = {"high": "❗", "medium": "⚠️", "low": "💡"}
            icon = priority_icon.get(suggestion['priority'], "•")
            print(f"  {icon} {i}. {suggestion['suggestion']}")

        # 询问用户
        user_decision = AskUserQuestion(
            "这些优化是否属于当前任务范围？",
            options=["是（继续优化）", "否（完成任务）"]
        )

        if "是" in user_decision or "yes" in user_decision.lower():
            return "continue"
        else:
            return "exit"

    else:  # failed
        print("\n✗ 验收失败，以下标准未满足：")
        for i, failure in enumerate(verification_result['failures'], 1):
            print(f"  {i}. 任务 {failure['task_id']}: {failure['criterion']}")
            print(f"     期望：{failure['criterion']}")
            print(f"     实际：{failure['actual']}")
            print(f"     原因：{failure['reason']}\n")

        return "adjustment"
```

---

## 自定义场景集成

### 场景 1: 单次任务验证

```python
def verify_single_task(task_id, task_name, acceptance_criteria):
    """验证单个任务

    Args:
        task_id: 任务 ID
        task_name: 任务名称
        acceptance_criteria: 验收标准列表

    Returns:
        dict: 验证结果
    """
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""验证单个任务：

任务 ID：{task_id}
任务名称：{task_name}

验收标准：
{chr(10).join(f"- {criterion}" for criterion in acceptance_criteria)}

要求：
1. 验证所有验收标准
2. 检查质量指标
3. 生成验证报告
"""
    )

    return verification_result
```

### 场景 2: 批量任务验证

```python
def verify_multiple_tasks(tasks):
    """批量验证多个任务

    Args:
        tasks: 任务列表，每个任务包含 id、name、acceptance_criteria

    Returns:
        dict: 批量验证结果
    """
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""批量验证多个任务：

任务列表：
{json.dumps(tasks, indent=2, ensure_ascii=False)}

要求：
1. 依次验证每个任务
2. 记录每个任务的验证结果
3. 生成汇总报告
4. 判断整体验收状态
"""
    )

    return verification_result
```

### 场景 3: 增量验证

```python
def verify_incremental(new_tasks, previous_verification):
    """增量验证新任务

    Args:
        new_tasks: 新增任务列表
        previous_verification: 之前的验证结果

    Returns:
        dict: 增量验证结果
    """
    verification_result = Agent(
        agent="task:verifier",
        prompt=f"""增量验证：

新增任务：
{json.dumps(new_tasks, indent=2, ensure_ascii=False)}

之前的验证结果：
{json.dumps(previous_verification, indent=2, ensure_ascii=False)}

要求：
1. 验证新增任务
2. 确认之前通过的任务仍然有效
3. 生成增量验证报告
"""
    )

    return verification_result
```

---

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
