# Adjuster 集成示例

本文档包含在不同场景下集成和使用 Adjuster 的示例代码。

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

---

## 自定义场景集成

### 场景 1: 单次失败调整

```python
def adjust_single_failure(task_id, task_name, error):
    """调整单次失败

    Args:
        task_id: 任务 ID
        task_name: 任务名称
        error: 错误信息

    Returns:
        dict: 调整结果
    """
    adjustment_result = Agent(
        agent="task:adjuster",
        prompt=f"""调整单次失败：

任务：{task_id} - {task_name}
错误：{error}

要求：
1. 分析错误原因
2. 提供修复建议
3. 应用 Retry 策略
"""
    )

    return adjustment_result
```

### 场景 2: 批量失败调整

```python
def adjust_multiple_failures(failed_tasks):
    """调整多个失败任务

    Args:
        failed_tasks: 失败任务列表

    Returns:
        dict: 调整结果
    """
    adjustment_result = Agent(
        agent="task:adjuster",
        prompt=f"""批量调整失败任务：

失败任务：
{json.dumps(failed_tasks, indent=2, ensure_ascii=False)}

要求：
1. 分析每个任务的失败原因
2. 识别共同模式
3. 提供统一或独立的修复方案
4. 应用分级升级策略
"""
    )

    return adjustment_result
```

### 场景 3: 条件调整

```python
def adjust_conditional(task, conditions):
    """基于条件进行调整

    Args:
        task: 失败任务
        conditions: 调整条件

    Returns:
        dict: 调整结果
    """
    adjustment_result = Agent(
        agent="task:adjuster",
        prompt=f"""条件调整：

任务：{json.dumps(task, indent=2, ensure_ascii=False)}

调整条件：
{json.dumps(conditions, indent=2, ensure_ascii=False)}

要求：
1. 根据条件选择合适的策略
2. 应用调整
3. 生成调整报告
"""
    )

    return adjustment_result
```

---

## 停滞检测

### 检测停滞模式

```python
def detect_stall(error_history):
    """检测停滞模式

    Args:
        error_history: 错误历史列表

    Returns:
        bool: True 表示检测到停滞
    """
    if len(error_history) < 3:
        return False

    # 获取最近 3 次错误
    recent_errors = error_history[-3:]

    # 提取错误签名
    error_signatures = [get_error_signature(e) for e in recent_errors]

    # 检查相似度
    similarities = []
    for i in range(len(error_signatures) - 1):
        similarity = calculate_similarity(error_signatures[i], error_signatures[i + 1])
        similarities.append(similarity)

    # 如果所有相似度都 >= 0.9，认为是停滞
    return all(s >= 0.9 for s in similarities)

def get_error_signature(error):
    """获取错误签名"""
    # 提取错误类型和关键信息
    return {
        "type": error.get("error_type"),
        "message": error.get("message"),
        "task_id": error.get("task_id")
    }

def calculate_similarity(sig1, sig2):
    """计算两个错误签名的相似度"""
    # 简单的相似度计算
    if sig1["type"] != sig2["type"]:
        return 0.0

    if sig1["task_id"] != sig2["task_id"]:
        return 0.5

    # 比较错误消息
    if sig1["message"] == sig2["message"]:
        return 1.0

    # 部分匹配
    return 0.7
```

---

## 指数退避实现

### 计算退避时间

```python
def calculate_backoff(failure_count):
    """计算指数退避时间

    Args:
        failure_count: 失败次数

    Returns:
        int: 退避时间（秒）
    """
    if failure_count <= 0:
        return 0

    # 指数退避公式：2^(failure_count - 1)
    backoff_seconds = 2 ** (failure_count - 1)

    # 限制最大退避时间（例如 60 秒）
    max_backoff = 60
    return min(backoff_seconds, max_backoff)
```

### 应用退避

```python
def apply_backoff(retry_config):
    """应用指数退避

    Args:
        retry_config: 重试配置
    """
    backoff_seconds = retry_config.get("backoff_seconds", 0)

    if backoff_seconds > 0:
        print(f"⏱️  等待 {backoff_seconds} 秒（指数退避）...")

        # 显示倒计时
        for remaining in range(backoff_seconds, 0, -1):
            print(f"  剩余 {remaining} 秒...", end="\r")
            time.sleep(1)

        print("\n✓ 退避完成")
```

---

## 错误处理

### 处理无效策略

```python
def handle_invalid_strategy(adjustment_result):
    """处理无效的调整策略

    Args:
        adjustment_result: 调整结果

    Raises:
        Exception: 策略无效时抛出异常
    """
    valid_strategies = ["retry", "debug", "replan", "ask_user"]
    strategy = adjustment_result.get("strategy")

    if strategy not in valid_strategies:
        raise Exception(
            f"无效的调整策略：{strategy}。"
            f"有效策略：{', '.join(valid_strategies)}"
        )
```

### 超过最大重试次数

```python
def handle_max_retries_exceeded(retry_config):
    """处理超过最大重试次数

    Args:
        retry_config: 重试配置

    Returns:
        bool: True 表示已超过最大重试次数
    """
    current = retry_config.get("current_retry", 0)
    maximum = retry_config.get("max_retries", 3)

    if current >= maximum:
        print(f"\n⚠️  已达到最大重试次数（{current}/{maximum}）")
        return True

    return False
```
