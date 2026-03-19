# Loop 通信和协作 - 基础

本文档包含 Agent 间通信规则、消息格式、消息类型和协作模式。

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
