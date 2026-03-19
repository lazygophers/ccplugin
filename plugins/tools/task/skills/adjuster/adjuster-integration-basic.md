# Adjuster 基础集成

本文档包含 Adjuster 的基础集成示例和常用场景。

## Loop 命令中的使用

### 基础集成

```python
def adjustment_phase(task_description, iteration):
    """Loop 命令失败调整（Adjustment / Act）阶段"""

    # 调用 adjuster agent
    adjustment_result = Agent(
        agent="task:adjuster",
        prompt=f"""执行失败调整：

任务目标：{task_description}
当前迭代：第 {iteration + 1} 轮

要求：
1. 获取所有失败任务的详细信息
2. 分析失败原因
3. 检测停滞模式
4. 应用分级升级策略
5. 生成调整报告（≤100字）
"""
    )

    # 输出报告
    print(f"[MindFlow·{task_description}·失败调整/{iteration + 1}·{adjustment_result['strategy']}]")
    print(f"调整报告：{adjustment_result['report']}")

    # 应用指数退避
    if "retry_config" in adjustment_result:
        backoff_seconds = adjustment_result["retry_config"]["backoff_seconds"]
        if backoff_seconds > 0:
            print(f"应用指数退避：等待 {backoff_seconds} 秒...")
            time.sleep(backoff_seconds)

    # 根据策略执行
    strategy = adjustment_result["strategy"]

    if strategy == "retry":
        # 应用调整建议
        for adj in adjustment_result["adjustments"]:
            apply_adjustment(adj)
        return "execution"  # 回到任务执行

    elif strategy == "debug":
        # 调用 debug agent
        debug_result = Agent(
            agent="debug",
            prompt=f"深度分析失败原因：{adjustment_result['debug_plan']}"
        )
        apply_debug_fixes(debug_result)
        return "execution"  # 回到任务执行

    elif strategy == "replan":
        # 调用 planner agent 重新规划
        new_plan = Agent(
            agent="planner",
            prompt=f"重新规划任务：{adjustment_result['replan_options']}"
        )
        return "planning"  # 回到计划设计

    elif strategy == "ask_user":
        # 请求用户指导
        user_response = AskUserQuestion(adjustment_result["question"])
        # 根据用户回答应用修复
        apply_user_guidance(user_response)
        return "execution"  # 回到任务执行

    return "execution"  # 默认回到任务执行
```

---

## 处理调整结果

### 完整处理流程

```python
def handle_adjustment_result(adjustment_result, task_description):
    """处理 Adjuster 返回结果

    Args:
        adjustment_result: Adjuster agent 的返回结果
        task_description: 任务描述

    Returns:
        str: 下一步行为（execution / planning）
    """

    # 1. 检查策略
    if adjustment_result["strategy"] not in ["retry", "debug", "replan", "ask_user"]:
        raise Exception(f"无效的调整策略：{adjustment_result['strategy']}")

    # 2. 输出调整报告
    print(f"\n调整报告：{adjustment_result['report']}")

    # 3. 输出调整详情
    if "adjustments" in adjustment_result:
        print("\n调整建议：")
        for i, adj in enumerate(adjustment_result["adjustments"], 1):
            print(f"  {i}. {adj['task_id']}: {adj['action']}")
            print(f"     详情：{adj['details']}")

    # 4. 应用指数退避
    if "retry_config" in adjustment_result:
        retry_config = adjustment_result["retry_config"]
        backoff_seconds = retry_config.get("backoff_seconds", 0)

        if backoff_seconds > 0:
            print(f"\n⏱️  指数退避：等待 {backoff_seconds} 秒...")
            time.sleep(backoff_seconds)

        # 输出重试信息
        current = retry_config.get("current_retry", 0)
        maximum = retry_config.get("max_retries", 3)
        print(f"重试次数：{current}/{maximum}")

    # 5. 根据策略执行
    strategy = adjustment_result["strategy"]

    if strategy == "retry":
        print("\n🔄 策略：调整后重试")
        apply_adjustments(adjustment_result["adjustments"])
        return "execution"

    elif strategy == "debug":
        print("\n🔍 策略：深度诊断")
        debug_plan = adjustment_result.get("debug_plan", {})
        debug_result = debug_with_plan(debug_plan)
        apply_debug_fixes(debug_result)
        return "execution"

    elif strategy == "replan":
        print("\n📋 策略：重新规划")
        replan_options = adjustment_result.get("replan_options", [])
        display_replan_options(replan_options)
        return "planning"

    elif strategy == "ask_user":
        print("\n❓ 策略：请求用户指导")

        # 显示停滞信息
        if "stalled_info" in adjustment_result:
            stalled = adjustment_result["stalled_info"]
            print(f"\n停滞信息：")
            print(f"  任务：{stalled['task_id']} - {stalled['task_name']}")
            print(f"  错误：{stalled['error']}")
            print(f"  重复次数：{stalled['occurrences']}")

        # 询问用户
        user_response = AskUserQuestion(adjustment_result["question"])
        apply_user_guidance(user_response)
        return "execution"

    return "execution"
```

---

## 辅助函数实现

### 应用调整建议

```python
def apply_adjustments(adjustments):
    """应用调整建议

    Args:
        adjustments: 调整建议列表
    """
    for adj in adjustments:
        task_id = adj["task_id"]
        action = adj["action"]
        details = adj["details"]

        print(f"\n应用调整：{task_id} - {action}")

        # 根据 action 类型执行相应操作
        if "修复" in action:
            apply_fix(task_id, details)
        elif "调整" in action:
            apply_configuration_change(task_id, details)
        elif "安装" in action:
            install_dependency(details)
        else:
            print(f"  未知操作类型：{action}")

def apply_fix(task_id, details):
    """应用代码修复"""
    print(f"  修复代码：{details}")
    # 实际的代码修复逻辑

def apply_configuration_change(task_id, details):
    """应用配置更改"""
    print(f"  更改配置：{details}")
    # 实际的配置更改逻辑

def install_dependency(details):
    """安装依赖"""
    print(f"  安装依赖：{details}")
    # 实际的依赖安装逻辑
```

### 深度诊断

```python
def debug_with_plan(debug_plan):
    """使用调试计划进行深度诊断

    Args:
        debug_plan: 调试计划

    Returns:
        dict: 调试结果
    """
    agent = debug_plan.get("agent", "debug")
    focus_areas = debug_plan.get("focus_areas", [])

    print(f"\n调用 {agent} 进行深度诊断")
    print(f"关注领域：{', '.join(focus_areas)}")

    # 调用 debug agent
    debug_result = Agent(
        agent=agent,
        prompt=f"""深度诊断失败原因：

关注领域：
{chr(10).join(f"- {area}" for area in focus_areas)}

要求：
1. 分析每个关注领域
2. 找出根本原因
3. 提供修复建议
"""
    )

    return debug_result

def apply_debug_fixes(debug_result):
    """应用调试修复"""
    print(f"\n应用调试修复：")
    # 处理 debug_result 并应用修复
```

### 显示重新规划选项

```python
def display_replan_options(replan_options):
    """显示重新规划选项

    Args:
        replan_options: 重新规划选项列表
    """
    if not replan_options:
        print("  无可用的重新规划选项")
        return

    print("\n可用的重新规划选项：")
    for i, option in enumerate(replan_options, 1):
        print(f"\n选项 {i}: {option['option']}")
        print(f"  描述：{option['description']}")
        print(f"  预估工作量：{option['estimated_effort']}")
```

### 应用用户指导

```python
def apply_user_guidance(user_response):
    """应用用户指导

    Args:
        user_response: 用户的回答
    """
    print(f"\n用户指导：{user_response}")

    # 解析用户回答并应用
    if "A" in user_response or "调整验收标准" in user_response:
        print("  执行：调整验收标准")
        # 调整验收标准的逻辑

    elif "B" in user_response or "修复代码" in user_response:
        print("  执行：修复被测代码逻辑")
        # 修复代码的逻辑

    elif "C" in user_response or "测试数据" in user_response:
        print("  执行：检查并修正测试数据")
        # 修正测试数据的逻辑

    else:
        print("  执行：应用用户自定义方案")
        # 应用用户提供的自定义解决方案
```
