# Verifier 基础集成

本文档包含 Verifier 的基础集成示例和常用场景。

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
