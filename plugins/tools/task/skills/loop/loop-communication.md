# Loop 通信和协作

本文档包含 MindFlow Loop 中 Agent 间通信规则、消息格式和协作模式。

## Agent 通信规则

### 严格禁止

**Agent 不得直接与用户交互**：
- ❌ Agent 不得调用 `AskUserQuestion`
- ❌ Agent 不得直接向用户输出信息
- ❌ Agent 不得绕过 Team Leader 与用户沟通

**原因**：
- 避免多个 Agent 同时提问造成混乱
- 确保 Team Leader 统一管理所有用户交互
- 保持清晰的责任边界和沟通路径

### 正确方式

**Agent → Team Leader → 用户**：
1. Agent 通过 `SendMessage` 向 `@main` 发送消息
2. `@main`（MindFlow）调用 `AskUserQuestion` 与用户交互
3. `@main` 将用户回答传递给相应的 Agent

**示例流程**：
```
[Verifier Agent] → SendMessage(@main, question)
    → [MindFlow] → AskUserQuestion(user)
    → [User] → response
    → [MindFlow] → SendMessage(Verifier, response)
```

## 消息格式

### Agent 发送问题给 Team Leader

```python
# Agent 代码
SendMessage(
    recipient="@main",
    message={
        "type": "question",
        "agent": "task:verifier",
        "content": "验收标准 '测试覆盖率 ≥ 90%' 当前为 85%，是否需要补充测试？",
        "options": ["是", "否", "调整标准为 85%"],
        "context": {
            "task_id": "T3",
            "current_coverage": 85,
            "target_coverage": 90
        }
    }
)
```

### Team Leader 处理并响应

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

### Agent 接收用户回答

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

## 消息类型

### 1. Question（提问）

**用途**：Agent 需要用户确认或决策

```python
{
    "type": "question",
    "agent": "task:planner",
    "content": "是否需要添加性能测试任务？",
    "options": ["是", "否"],
    "context": {"estimated_time": "2 hours"}
}
```

### 2. Response（响应）

**用途**：Team Leader 将用户回答传递给 Agent

```python
{
    "type": "response",
    "content": "是",
    "original_context": {"estimated_time": "2 hours"}
}
```

### 3. Report（报告）

**用途**：Agent 向 Team Leader 报告进度或结果

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

### 4. Alert（警报）

**用途**：Agent 检测到异常情况需要通知

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

### 5. Request（请求）

**用途**：Agent 请求 Team Leader 执行某个操作

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

## 协作模式

### 模式 1: 顺序协作

Agent 按顺序执行，后一个 Agent 依赖前一个的输出。

```
Planner → Executor → Verifier → [Pass/Fail] → Adjuster/Finalizer
```

**特点**：
- 严格的执行顺序
- 清晰的输入输出关系
- 适合线性流程

### 模式 2: 并行协作

多个 Agent 同时执行不相关的任务。

```
         ┌─ Agent A (Task T1)
         │
Leader ─┼─ Agent B (Task T2)
         │
         └─ Agent C (Task T3)
```

**特点**：
- 最多 2 个 Agent 并行
- 无依赖关系
- 提高执行效率

### 模式 3: 反馈循环

Agent 执行后根据结果决定下一步。

```
Executor → Verifier → [Failed] → Adjuster → Executor
                   → [Passed] → Finalizer
```

**特点**：
- 持续改进
- 自适应调整
- 适合迭代流程

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
