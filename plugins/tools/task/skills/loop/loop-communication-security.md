# Loop 通信和协作 - 安全

本文档包含通信安全相关内容。

## 通信安全

### 消息验证

**验证消息来源**：
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

**验证消息格式**：
```python
def validate_message_format(message):
    """验证消息格式是否正确"""
    required_fields = ["type", "agent", "content"]
    return all(field in message for field in required_fields)
```

### 防止消息循环

**检测循环依赖**：
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

### 消息加密

**敏感信息加密**：
```python
def encrypt_sensitive_data(message):
    """加密敏感信息"""
    if "sensitive" in message:
        message["sensitive"] = encrypt(message["sensitive"])
    return message
```

**解密处理**：
```python
def decrypt_message(message):
    """解密消息中的敏感信息"""
    if "sensitive" in message:
        message["sensitive"] = decrypt(message["sensitive"])
    return message
```

### 访问控制

**权限检查**：
```python
def check_message_permission(message, recipient):
    """检查消息发送权限"""
    # 定义权限矩阵
    permissions = {
        "task:planner": ["@main"],
        "task:execute": ["@main", "task:verifier"],
        "task:verifier": ["@main", "task:adjuster"],
        "task:adjuster": ["@main", "task:execute"]
    }

    allowed_recipients = permissions.get(message["agent"], [])
    return recipient in allowed_recipients
```

### 审计日志

**记录所有消息**：
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

**审计查询**：
```python
def query_audit_log(agent=None, start_time=None, end_time=None):
    """查询审计日志"""
    logs = read_audit_log()

    # 过滤条件
    if agent:
        logs = [l for l in logs if l["agent"] == agent]
    if start_time:
        logs = [l for l in logs if l["timestamp"] >= start_time]
    if end_time:
        logs = [l for l in logs if l["timestamp"] <= end_time]

    return logs
```
