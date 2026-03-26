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

<structured_error_format>

## 结构化错误消息格式

### 核心数据结构

所有错误必须使用以下JSON格式：

```json
{
  "error_id": "err_${hash8}",
  "timestamp": "ISO 8601格式时间戳",
  "category": "recoverable|unrecoverable",
  "severity": "critical|high|medium|low",
  "message": "人类可读的错误描述",
  "context": {
    "task_id": "当前任务ID",
    "iteration": "当前迭代次数",
    "phase": "planning|execution|verification|adjustment|etc.",
    "agent": "触发错误的agent名称",
    "file_path": "相关文件路径（如适用）",
    "line_number": "行号（如适用）"
  },
  "stack_trace": "完整的堆栈跟踪（如适用）",
  "suggested_fix": {
    "strategy": "retry|debug|replan|ask_user",
    "details": "具体的修复建议",
    "estimated_success_rate": "0.0-1.0"
  },
  "related_patterns": [
    {
      "pattern_id": "匹配的历史模式ID",
      "confidence": "0.0-1.0"
    }
  ]
}
```

### 字段说明

#### error_id
- 格式：`err_` + 8位哈希
- 生成方式：`hashlib.md5(f"{timestamp}_{message}_{context}".encode()).hexdigest()[:8]`
- 用途：唯一标识错误，便于追踪和去重

#### category
- `recoverable`：可恢复的错误（网络超时、依赖缺失、语法错误等）
- `unrecoverable`：不可恢复的错误（磁盘满、权限不足、配置错误等）
- 用途：指导adjuster选择恢复策略

#### severity
- `critical`：阻塞任务继续，需要立即处理
- `high`：影响核心功能，应尽快处理
- `medium`：影响部分功能，可延后处理
- `low`：轻微影响，可忽略
- 用途：优先级排序和升级决策

#### context
提供足够的上下文信息用于诊断：
- `task_id`：跟踪错误属于哪个任务
- `iteration`：识别是否为重复失败
- `phase`：定位错误发生的执行阶段
- `agent`：识别哪个组件出错
- `file_path`、`line_number`：精确定位代码位置

#### suggested_fix
基于错误分析提供初步修复建议：
- `strategy`：推荐的恢复策略
- `details`：具体的操作步骤
- `estimated_success_rate`：修复成功率估计

#### related_patterns
关联历史失败模式（如果模式提取功能已启用）：
- `pattern_id`：匹配的模式ID
- `confidence`：匹配置信度

### 错误生成函数

```python
import hashlib
from datetime import datetime

def create_structured_error(
    message: str,
    category: str,
    severity: str,
    context: dict,
    stack_trace: str = None,
    suggested_fix: dict = None,
    related_patterns: list = None
) -> dict:
    """
    生成结构化错误消息

    Args:
        message: 错误描述
        category: recoverable|unrecoverable
        severity: critical|high|medium|low
        context: 上下文字典
        stack_trace: 堆栈跟踪（可选）
        suggested_fix: 修复建议（可选）
        related_patterns: 关联模式（可选）

    Returns:
        结构化错误字典
    """
    timestamp = datetime.now().isoformat()
    error_id = f"err_{hashlib.md5(f'{timestamp}_{message}_{context}'.encode()).hexdigest()[:8]}"

    return {
        "error_id": error_id,
        "timestamp": timestamp,
        "category": category,
        "severity": severity,
        "message": message,
        "context": context,
        "stack_trace": stack_trace or "",
        "suggested_fix": suggested_fix or {},
        "related_patterns": related_patterns or []
    }
```

### 使用示例

#### 示例1：可恢复错误（网络超时）

```python
error = create_structured_error(
    message="HTTP request to API endpoint timed out after 30 seconds",
    category="recoverable",
    severity="medium",
    context={
        "task_id": "t_abc123",
        "iteration": 2,
        "phase": "execution",
        "agent": "api-client",
        "file_path": "src/services/api.py",
        "line_number": 45
    },
    suggested_fix={
        "strategy": "retry",
        "details": "Retry with exponential backoff: 2s → 4s → 8s",
        "estimated_success_rate": 0.85
    }
)
```

#### 示例2：不可恢复错误（配置缺失）

```python
error = create_structured_error(
    message="Required configuration 'DATABASE_URL' not found in environment",
    category="unrecoverable",
    severity="critical",
    context={
        "task_id": "t_def456",
        "iteration": 1,
        "phase": "initialization",
        "agent": "config-loader"
    },
    suggested_fix={
        "strategy": "ask_user",
        "details": "Request user to set DATABASE_URL environment variable",
        "estimated_success_rate": 1.0
    }
)
```

### 错误日志存储

所有结构化错误应保存到：
- 文件路径：`.claude/logs/task-{session_id}.log`
- 格式：每行一个JSON对象（JSONL格式）
- 旋转策略：每个会话一个文件
- 保留期限：30天

```python
import json
from pathlib import Path

def log_structured_error(error: dict, session_id: str):
    """
    将结构化错误写入日志文件

    Args:
        error: 结构化错误字典
        session_id: 会话ID
    """
    log_dir = Path.home() / ".claude/logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"task-{session_id}.log"

    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(error, ensure_ascii=False) + "\n")
```

### 集成到Loop流程

在每个执行阶段捕获异常时，生成结构化错误：

```python
try:
    # 执行任务...
    result = execute_task(task)
except Exception as e:
    error = create_structured_error(
        message=str(e),
        category=classify_error(e),
        severity=assess_severity(e),
        context={
            "task_id": task.id,
            "iteration": current_iteration,
            "phase": current_phase,
            "agent": current_agent
        },
        stack_trace=traceback.format_exc(),
        suggested_fix=generate_suggestion(e)
    )

    # 保存到日志
    log_structured_error(error, session_id)

    # 传递给adjuster
    adjustment = Agent(
        agent="task:adjuster",
        prompt=f"Analyze and handle this structured error:\n{json.dumps(error, indent=2)}"
    )
```

</structured_error_format>
