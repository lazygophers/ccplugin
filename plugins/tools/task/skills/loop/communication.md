# Loop 通信和协作规范

# Loop 通信和协作

本文档是 Loop 通信和协作的索引，详细内容已拆分为以下文件：

<navigation>

基础通信内容在 [communication-basics.md](communication-basics.md) 中，包括 Agent 通信规则（严格禁止直接与用户交互、正确的通信路径）、消息格式（Agent 发送、Team Leader 处理、Agent 接收）、消息类型（Question、Response、Report、Alert、Request）和协作模式（顺序协作、并行协作、反馈循环）。

最佳实践内容在 [communication-practices.md](communication-practices.md) 中，包括清晰的消息边界、超时处理、错误传播、状态同步、消息优先级、重试机制和消息批处理。

通信安全内容在 [communication-security.md](communication-security.md) 中，包括消息验证、防止消息循环、消息加密、访问控制和审计日志。

</navigation>

---

# Loop 通信和协作 - 基础

本文档包含 Agent 间通信规则、消息格式、消息类型和协作模式。

<communication_rules>

## Agent 通信规则

Agent 不得直接与用户交互——不得调用 `AskUserQuestion`，不得直接向用户输出信息，不得绕过 Team Leader 与用户沟通。这条规则存在的原因是：当多个 Agent 同时向用户提问时会造成混乱，由 Team Leader 统一管理所有用户交互可以保持清晰的责任边界和沟通路径。

正确的通信路径是 Agent 通过 `SendMessage` 向 `@main` 发送消息，`@main`（MindFlow）调用 `AskUserQuestion` 与用户交互，然后将用户回答传递给相应的 Agent。

```
[Verifier Agent] → SendMessage(@main, question)
    → [MindFlow] → AskUserQuestion(user)
    → [User] → response
    → [MindFlow] → SendMessage(Verifier, response)
```

</communication_rules>

<message_formats>

## 消息格式

Agent 发送问题给 Team Leader：

```python
# Agent 代码
SendMessage(
    recipient="@main",
    message={
        "type": "question",
        "agent": "task:verifier",
        "content": "验收标准 '测试覆盖率 >= 90%' 当前为 85%，是否需要补充测试？",
        "options": ["是", "否", "调整标准为 85%"],
        "context": {
            "task_id": "T3",
            "current_coverage": 85,
            "target_coverage": 90
        }
    }
)
```

Team Leader 处理并响应：

```python
# MindFlow 代码
def handle_agent_message(message):
    """处理 Agent 消息"""

    if message["type"] == "question":
        # 向用户提问
        user_answer = AskUserQuestion(
            question=message["content"],
            options=message.get("options")
        )

        # 将答案返回给 Agent
        SendMessage(
            recipient=message["agent"],
            message={
                "type": "response",
                "content": user_answer,
                "original_context": message.get("context")
            }
        )
```

Agent 接收用户回答：

```python
# Agent 代码
response = receive_message()  # 接收来自 @main 的消息

if response["type"] == "response":
    user_answer = response["content"]
    context = response["original_context"]

    # 根据用户回答继续执行
    if user_answer == "是":
        add_more_tests(context["task_id"])
    elif user_answer == "否":
        proceed_with_current_coverage()
    else:
        adjust_acceptance_criteria(85)
```

</message_formats>

<message_types>

## 消息类型

Question（提问）用于 Agent 需要用户确认或决策的场景：

```python
{
    "type": "question",
    "agent": "task:planner",
    "content": "是否需要添加性能测试任务？",
    "options": ["是", "否"],
    "context": {"estimated_time": "2 hours"}
}
```

Response（响应）用于 Team Leader 将用户回答传递给 Agent：

```python
{
    "type": "response",
    "content": "是",
    "original_context": {"estimated_time": "2 hours"}
}
```

Report（报告）用于 Agent 向 Team Leader 报告进度或结果：

```python
{
    "type": "report",
    "agent": "task:execute",
    "content": "任务 T1 已完成",
    "data": {
        "task_id": "T1",
        "status": "completed",
        "duration": 120  # 秒
    }
}
```

Alert（警报）用于 Agent 检测到异常情况需要通知：

```python
{
    "type": "alert",
    "agent": "task:verifier",
    "severity": "warning",
    "content": "测试覆盖率低于预期",
    "data": {
        "current": 75,
        "expected": 90
    }
}
```

Request（请求）用于 Agent 请求 Team Leader 执行某个操作：

```python
{
    "type": "request",
    "agent": "task:adjuster",
    "action": "rerun_task",
    "data": {
        "task_id": "T2",
        "reason": "flaky test detected"
    }
}
```

</message_types>

<collaboration_patterns>

## 协作模式

顺序协作中 Agent 按顺序执行，后一个 Agent 依赖前一个的输出。这种模式有严格的执行顺序和清晰的输入输出关系，适合线性流程。

```
Planner → Executor → Verifier → [Pass/Fail] → Adjuster/Finalizer
```

并行协作中多个 Agent 同时执行不相关的任务，最多 2 个 Agent 并行，无依赖关系，提高执行效率。

```
         ┌─ Agent A (Task T1)
         │
Leader ─┼─ Agent B (Task T2)
         │
         └─ Agent C (Task T3)
```

反馈循环中 Agent 执行后根据结果决定下一步，支持持续改进和自适应调整，适合迭代流程。

```
Executor → Verifier → [Failed] → Adjuster → Executor
                   → [Passed] → Finalizer
```

</collaboration_patterns>

---

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

---

# Loop 通信和协作 - 安全

本文档包含通信安全相关内容，确保 Agent 间通信的可靠性和安全性。

<message_validation>

## 消息验证

消息来源验证确保只有合法的 Agent 才能发送消息。消息格式验证确保每条消息都包含必要的字段。验证的目的是防止格式错误或来源不明的消息干扰系统正常运行。

```python
def validate_message_source(message):
    """验证消息来源是否合法"""
    allowed_agents = [
        "task:planner",
        "task:execute",
        "task:verifier",
        "task:adjuster",
        "task:finalizer"
    ]
    return message.get("agent") in allowed_agents
```

```python
def validate_message_format(message):
    """验证消息格式是否正确"""
    required_fields = ["type", "agent", "content"]
    return all(field in message for field in required_fields)
```

</message_validation>

<loop_prevention>

## 防止消息循环

消息循环会导致系统资源耗尽和无限递归。通过跟踪最近的消息链并检测重复模式来识别循环。当重复消息过多时，中断循环并报告异常。

```python
message_chain = []

def detect_message_loop(message):
    """检测消息循环"""
    message_chain.append(message["id"])

    # 检查最近 10 条消息
    recent = message_chain[-10:]
    if len(set(recent)) < len(recent) / 2:
        # 重复消息过多，可能存在循环
        return True
    return False
```

</loop_prevention>

<encryption>

## 消息加密

当消息包含敏感信息（如密钥、凭证、个人数据）时，需要在发送前加密，接收后解密。加密确保即使消息被截获也不会泄露敏感数据。

```python
def encrypt_sensitive_data(message):
    """加密敏感信息"""
    if "sensitive" in message:
        message["sensitive"] = encrypt(message["sensitive"])
    return message
```

```python
def decrypt_message(message):
    """解密消息中的敏感信息"""
    if "sensitive" in message:
        message["sensitive"] = decrypt(message["sensitive"])
    return message
```

</encryption>

<access_control>

## 访问控制

权限矩阵定义了每个 Agent 可以向哪些接收方发送消息。访问控制防止 Agent 越权通信，确保消息只在授权的路径上流转。

```python
def check_message_permission(message, recipient):
    """检查消息发送权限"""
    permissions = {
        "task:planner": ["@main"],
        "task:execute": ["@main", "task:verifier"],
        "task:verifier": ["@main", "task:adjuster"],
        "task:adjuster": ["@main", "task:execute"]
    }

    allowed_recipients = permissions.get(message["agent"], [])
    return recipient in allowed_recipients
```

</access_control>

<audit>

## 审计日志

记录所有消息用于事后审计和问题排查。日志记录消息的时间戳、方向（发送/接收）、来源 Agent、类型和内容哈希。内容哈希而非原文的设计是为了在支持审计追溯的同时保护消息内容的隐私。

```python
def log_message(message, direction):
    """记录消息用于审计"""
    log_entry = {
        "timestamp": time.time(),
        "direction": direction,  # "sent" | "received"
        "agent": message["agent"],
        "type": message["type"],
        "content_hash": hash(message["content"])
    }

    append_to_audit_log(log_entry)
```

```python
def query_audit_log(agent=None, start_time=None, end_time=None):
    """查询审计日志"""
    logs = read_audit_log()

    if agent:
        logs = [l for l in logs if l["agent"] == agent]
    if start_time:
        logs = [l for l in logs if l["timestamp"] >= start_time]
    if end_time:
        logs = [l for l in logs if l["timestamp"] <= end_time]

    return logs
```

</audit>
