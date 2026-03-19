# Adjuster 高级集成

本文档包含 Adjuster 的自定义场景、停滞检测和错误处理。

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
