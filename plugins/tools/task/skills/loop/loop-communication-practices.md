# Loop 通信和协作 - 最佳实践

本文档包含通信最佳实践，涵盖消息设计、错误处理和性能优化等方面。

<message_design>

## 消息设计

清晰的消息边界要求使用明确的 `type` 字段标识消息意图，提供足够的上下文信息，避免模糊的描述。每条消息应包含所有必要的数据、可追踪的 ID 和消息来源记录。消息设计的目标是让接收方无需额外查询就能理解消息内容并采取行动。

</message_design>

<timeout_handling>

## 超时处理

合理的超时时间因任务类型而异：短任务 30 秒，中等任务 2 分钟，长任务 5 分钟。设置超时的原因是防止 Agent 无限等待导致整个系统停滞。超时后应发送警报通知 Team Leader。

```python
try:
    response = wait_for_message(timeout=120)
except TimeoutError:
    log_warning("Agent response timeout")
    # 发送警报给 Team Leader
    SendMessage(
        recipient="@main",
        message={
            "type": "alert",
            "severity": "error",
            "content": "Agent 响应超时"
        }
    )
```

</timeout_handling>

<error_propagation>

## 错误传播

错误信息必须保持完整性，包含错误代码、描述、详细信息和相关日志。结构化的错误消息让 Team Leader 能够快速判断处理策略，而非花费时间解析模糊的错误描述。

```python
{
    "type": "error",
    "agent": "task:execute",
    "error": {
        "code": "TASK_EXECUTION_FAILED",
        "message": "任务执行失败：测试未通过",
        "details": {
            "task_id": "T2",
            "failed_tests": ["test_login", "test_auth"],
            "logs": "..."
        }
    }
}
```

错误处理流程为：Agent 捕获错误，构造结构化错误消息，发送给 Team Leader，由 Team Leader 决定处理策略。这种分层处理确保了错误决策权在正确的层级。

</error_propagation>

<state_sync>

## 状态同步

Agent 需要定期发送状态更新，让 Team Leader 掌握全局进度。状态同步的价值在于：Team Leader 需要实时了解所有 Agent 的工作状态才能做出正确的调度决策。

```python
# Agent 定期发送状态更新
def send_status_update(agent_name, status):
    SendMessage(
        recipient="@main",
        message={
            "type": "status_update",
            "agent": agent_name,
            "status": status,
            "timestamp": time.time()
        }
    )
```

```python
# Team Leader 查询 Agent 状态
def query_agent_status(agent_name):
    SendMessage(
        recipient=agent_name,
        message={"type": "query_status"}
    )

    response = wait_for_message(timeout=10)
    return response["status"]
```

</state_sync>

<message_priority>

## 消息优先级

消息优先级分为 low、medium、high、critical 四个级别。Team Leader 按优先级处理消息，确保紧急事项得到及时响应。

```python
{
    "type": "request",
    "priority": "high",  # low | medium | high | critical
    "agent": "task:execute",
    "content": "紧急任务需要立即执行"
}
```

```python
def process_messages(message_queue):
    """按优先级处理消息"""
    sorted_messages = sorted(
        message_queue,
        key=lambda m: priority_order[m.get("priority", "medium")],
        reverse=True
    )

    for message in sorted_messages:
        handle_message(message)
```

</message_priority>

<retry_mechanism>

## 重试机制

消息发送失败时使用指数退避重试。最大尝试次数默认 3 次，初始延迟 1 秒，每次翻倍。指数退避避免了在网络波动时大量重试请求同时涌入。

```python
retry_config = {
    "max_attempts": 3,
    "backoff_multiplier": 2,
    "initial_delay": 1  # 秒
}
```

```python
def send_message_with_retry(message, config):
    """带重试的消息发送"""
    attempt = 0
    delay = config["initial_delay"]

    while attempt < config["max_attempts"]:
        try:
            SendMessage(message)
            return True
        except Exception as e:
            attempt += 1
            if attempt >= config["max_attempts"]:
                raise

            # 指数退避
            time.sleep(delay)
            delay *= config["backoff_multiplier"]

    return False
```

</retry_mechanism>

<batch_processing>

## 消息批处理

当需要发送多条相关消息时，批量发送可以减少通信开销。每个批次分配唯一的 batch_id 用于追踪。

```python
def send_batch_messages(messages):
    """批量发送消息"""
    batch = {
        "type": "batch",
        "messages": messages,
        "batch_id": generate_batch_id()
    }
    SendMessage(batch)
```

```python
def handle_batch_message(batch):
    """处理批量消息"""
    results = []
    for message in batch["messages"]:
        result = handle_message(message)
        results.append(result)

    # 发送批处理结果
    SendMessage({
        "type": "batch_response",
        "batch_id": batch["batch_id"],
        "results": results
    })
```

</batch_processing>
