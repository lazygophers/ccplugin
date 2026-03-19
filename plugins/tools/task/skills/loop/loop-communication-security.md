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
