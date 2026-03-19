# Loop 通信和协作 - 最佳实践

本文档包含通信最佳实践。

## 通信最佳实践

### 清晰的消息边界

**明确消息意图**：
- 使用明确的 `type` 字段
- 提供足够的上下文信息
- 避免模糊的描述

**完整的上下文**：
- 包含所有必要的数据
- 提供可追踪的 ID
- 记录消息来源

### 超时处理

**设置合理的超时时间**：
- 短任务：30 秒
- 中等任务：2 分钟
- 长任务：5 分钟

**超时后的行为**：
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

### 错误传播

**错误信息完整性**：
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

**错误处理流程**：
1. Agent 捕获错误
2. 构造结构化错误消息
3. 发送给 Team Leader
4. Team Leader 决定处理策略

### 状态同步

**定期同步状态**：
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

**状态查询**：
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

### 消息优先级

**定义优先级**：
```python
{
    "type": "request",
    "priority": "high",  # low | medium | high | critical
    "agent": "task:execute",
    "content": "紧急任务需要立即执行"
}
```

**优先级处理**：
```python
def process_messages(message_queue):
    """按优先级处理消息"""
    # 排序消息（critical > high > medium > low）
    sorted_messages = sorted(
        message_queue,
        key=lambda m: priority_order[m.get("priority", "medium")],
        reverse=True
    )

    for message in sorted_messages:
        handle_message(message)
```

### 重试机制

**重试配置**：
```python
retry_config = {
    "max_attempts": 3,
    "backoff_multiplier": 2,
    "initial_delay": 1  # 秒
}
```

**重试实现**：
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

### 消息批处理

**批量发送**：
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

**批量处理**：
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
