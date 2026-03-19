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
