# Loop 错误处理和重试

<overview>

本文档定义了 MindFlow Loop 的错误处理机制。错误处理的核心设计是分级升级：从简单重试逐步升级到深度诊断、重新规划、最终请求用户指导。这种渐进式策略避免了在简单问题上浪费时间（直接重试），同时确保复杂问题能得到充分诊断（升级到 debug 或 replan）。补偿模式（Saga Pattern）处理任务失败后的回滚，确保系统一致性。

</overview>

<retry_strategy>

## 重试配置

错误处理按失败次数分级。首次失败（failure_count=1）立即重试，退避 0 秒，应用简单调整后重新执行。重复失败（failure_count=2）等待 2 秒后深度诊断，调用 debug agent 分析根因。持续失败（failure_count=3）等待 4 秒后返回计划设计阶段重新规划。

停滞检测在连续 3 次相同错误时触发，请求用户指导但不退出循环。超过最大停滞次数时强制结束，输出停滞报告并建议人工介入。

```python
def calculate_backoff(failure_count):
    """计算退避时间"""
    if failure_count == 1:
        return 0  # 立即重试
    elif failure_count == 2:
        return 2  # 2 秒
    elif failure_count >= 3:
        return 4  # 4 秒
    return 0
```

</retry_strategy>

<saga_pattern>

## Saga Pattern（补偿模式）

当任务执行失败且无法恢复时，需要执行补偿操作以确保系统一致性。补偿流程分三步：首先识别已完成的任务并确定需要回滚的操作，然后为每个已完成任务按依赖关系生成逆操作，最后从最后一个任务开始逐个撤销。

```python
def compensate_on_failure(completed_tasks):
    """在失败时执行补偿操作

    Args:
        completed_tasks: 已完成的任务列表
    """
    for task in reversed(completed_tasks):
        if task.has_compensation:
            try:
                print(f"执行补偿操作：{task.id} - {task.description}")
                execute_compensation(task)
            except Exception as e:
                print(f"补偿失败：{task.id} - {str(e)}")
```

补偿操作在任务定义时声明，支持多种类型：

```python
task = {
    "id": "T1",
    "description": "创建数据库表",
    "compensation": {
        "type": "sql",
        "operation": "DROP TABLE users;"
    }
}

def execute_compensation(task):
    """执行具体的补偿操作"""
    comp = task.compensation

    if comp["type"] == "sql":
        execute_sql(comp["operation"])
    elif comp["type"] == "file":
        delete_file(comp["path"])
    elif comp["type"] == "api":
        call_api(comp["endpoint"], comp["params"])
```

</saga_pattern>

<error_classification>

## 错误分类

错误分为可恢复和不可恢复两类，处理策略不同。可恢复错误（网络超时、资源临时不可用、测试失败）通过自动重试或退避后重试解决。不可恢复错误（配置错误、权限不足、依赖缺失）需要请求用户介入修正。

停滞模式检测通过比较最近 3 次错误的签名来判断是否陷入重复失败：

```python
def detect_stall(error_history):
    """检测停滞模式"""
    if len(error_history) < 3:
        return False

    recent_errors = error_history[-3:]
    error_signatures = [get_error_signature(e) for e in recent_errors]

    return len(set(error_signatures)) == 1  # 所有错误签名相同
```

</error_classification>

<escalation_levels>

## 分级升级策略

Level 1 Retry（首次失败）：应用简单调整后重试，如增加超时时间、清理缓存。Level 2 Debug（重复失败）：深度诊断和修复，分析日志、检查环境。Level 3 Replan（持续失败）：返回计划设计阶段，调整任务分解或修改依赖。Level 4 Ask User（停滞检测）：请求用户提供指导，询问是否调整目标或需要人工介入。

</escalation_levels>
