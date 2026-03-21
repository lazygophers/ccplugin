# 状态序列化规范

<overview>

本文档定义 MindFlow Loop 检查点的 JSON 数据模型，用于序列化和反序列化任务执行状态。检查点文件保存在 `.claude/checkpoints/{task_hash}.json`，包含迭代号、阶段、上下文、已完成任务等关键信息。

设计原则：
- **最小化存储**：只保存恢复执行所需的核心状态，避免冗余数据
- **向后兼容**：新增字段使用可选（Optional），确保旧检查点可正常加载
- **可读性**：使用 JSON 格式，indent=2，便于人工检查和调试
- **完整性验证**：加载时验证必需字段，确保数据完整性

</overview>

<schema>

## JSON Schema

### 完整数据模型

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["user_task", "task_hash", "iteration", "phase", "context", "timestamp"],
  "properties": {
    "user_task": {
      "type": "string",
      "description": "用户任务描述（原始输入）",
      "example": "实现用户登录功能"
    },
    "task_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{12}$",
      "description": "任务哈希（MD5前12位），用于唯一标识检查点文件",
      "example": "a1b2c3d4e5f6"
    },
    "iteration": {
      "type": "integer",
      "minimum": 0,
      "description": "当前迭代号（0表示初始化阶段）",
      "example": 2
    },
    "phase": {
      "type": "string",
      "enum": ["initialization", "planning", "confirmation", "execution", "verification", "adjustment", "completion"],
      "description": "当前执行阶段",
      "example": "execution"
    },
    "context": {
      "type": "object",
      "required": ["replan_trigger"],
      "properties": {
        "replan_trigger": {
          "type": ["string", "null"],
          "enum": [null, "user", "adjuster", "verifier"],
          "description": "重新规划触发来源（null=正常流程，user=用户主动，adjuster=失败调整，verifier=优化建议）",
          "example": "verifier"
        },
        "stalled_count": {
          "type": "integer",
          "minimum": 0,
          "description": "停滞次数（用于检测无限循环）",
          "example": 1
        },
        "guidance_count": {
          "type": "integer",
          "minimum": 0,
          "description": "用户指导次数",
          "example": 0
        },
        "max_stalled_attempts": {
          "type": "integer",
          "minimum": 1,
          "description": "最大停滞次数阈值",
          "default": 3
        }
      },
      "additionalProperties": true,
      "description": "上下文状态（包含所有控制流状态）"
    },
    "plan_md_path": {
      "type": ["string", "null"],
      "description": "计划文档路径（.claude/plans/xxx.md），null 表示尚未生成计划",
      "example": ".claude/plans/实现登录功能-2.md"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "检查点保存时间（ISO 8601 格式）",
      "example": "2026-03-21T14:30:00.123456"
    },
    "additional_state": {
      "type": "object",
      "description": "额外的状态信息（可选，用于扩展）",
      "properties": {
        "completed_tasks": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "已完成的任务ID列表",
          "example": ["T1", "T2", "T5"]
        },
        "failed_tasks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "task_id": {"type": "string"},
              "failure_reason": {"type": "string"},
              "retry_count": {"type": "integer"}
            }
          },
          "description": "失败任务记录"
        },
        "execution_metrics": {
          "type": "object",
          "properties": {
            "start_time": {"type": "string", "format": "date-time"},
            "total_duration_seconds": {"type": "number"},
            "task_count": {"type": "integer"}
          },
          "description": "执行指标（可选，用于分析）"
        }
      },
      "additionalProperties": true
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "检查点格式版本（用于未来升级兼容）",
      "default": "1.0.0",
      "example": "1.0.0"
    }
  },
  "additionalProperties": false
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `user_task` | string | ✓ | 用户任务描述（原始输入） |
| `task_hash` | string | ✓ | 任务哈希（MD5前12位） |
| `iteration` | integer | ✓ | 当前迭代号（≥0） |
| `phase` | enum | ✓ | 当前阶段（7个可选值） |
| `context` | object | ✓ | 上下文状态（包含 replan_trigger 等） |
| `context.replan_trigger` | string\|null | ✓ | 重新规划触发来源 |
| `context.stalled_count` | integer | - | 停滞次数 |
| `context.guidance_count` | integer | - | 用户指导次数 |
| `context.max_stalled_attempts` | integer | - | 最大停滞次数阈值 |
| `plan_md_path` | string\|null | ✓ | 计划文档路径 |
| `timestamp` | string | ✓ | 保存时间（ISO 8601） |
| `additional_state` | object | - | 额外状态（扩展用） |
| `additional_state.completed_tasks` | array | - | 已完成任务ID列表 |
| `additional_state.failed_tasks` | array | - | 失败任务记录 |
| `additional_state.execution_metrics` | object | - | 执行指标 |
| `version` | string | - | 检查点格式版本 |

</schema>

<examples>

## 示例数据

### 示例1：计划设计阶段检查点

```json
{
  "user_task": "实现用户登录功能",
  "task_hash": "a1b2c3d4e5f6",
  "iteration": 1,
  "phase": "planning",
  "context": {
    "replan_trigger": null,
    "stalled_count": 0,
    "guidance_count": 0,
    "max_stalled_attempts": 3
  },
  "plan_md_path": ".claude/plans/实现登录功能-1.md",
  "timestamp": "2026-03-21T10:30:00.123456",
  "additional_state": {},
  "version": "1.0.0"
}
```

### 示例2：任务执行阶段检查点

```json
{
  "user_task": "实现用户登录功能",
  "task_hash": "a1b2c3d4e5f6",
  "iteration": 2,
  "phase": "execution",
  "context": {
    "replan_trigger": "verifier",
    "stalled_count": 0,
    "guidance_count": 0,
    "max_stalled_attempts": 3
  },
  "plan_md_path": ".claude/plans/实现登录功能-2.md",
  "timestamp": "2026-03-21T14:30:00.123456",
  "additional_state": {
    "completed_tasks": ["T1", "T2"],
    "execution_metrics": {
      "start_time": "2026-03-21T14:00:00.000000",
      "total_duration_seconds": 1800,
      "task_count": 5
    }
  },
  "version": "1.0.0"
}
```

### 示例3：失败调整阶段检查点

```json
{
  "user_task": "实现用户登录功能",
  "task_hash": "a1b2c3d4e5f6",
  "iteration": 3,
  "phase": "adjustment",
  "context": {
    "replan_trigger": null,
    "stalled_count": 1,
    "guidance_count": 0,
    "max_stalled_attempts": 3
  },
  "plan_md_path": ".claude/plans/实现登录功能-3.md",
  "timestamp": "2026-03-21T16:00:00.123456",
  "additional_state": {
    "completed_tasks": ["T1", "T2", "T5"],
    "failed_tasks": [
      {
        "task_id": "T3",
        "failure_reason": "数据库连接超时",
        "retry_count": 2
      }
    ],
    "execution_metrics": {
      "start_time": "2026-03-21T14:00:00.000000",
      "total_duration_seconds": 7200,
      "task_count": 5
    }
  },
  "version": "1.0.0"
}
```

</examples>

<serialization>

## 序列化/反序列化实现

### Python 实现

```python
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def serialize_checkpoint(
    user_task: str,
    task_hash: str,
    iteration: int,
    phase: str,
    context: Dict[str, Any],
    plan_md_path: Optional[str] = None,
    additional_state: Optional[Dict[str, Any]] = None
) -> str:
    """
    将检查点状态序列化为 JSON 字符串

    返回：JSON 字符串（格式化后）
    """
    checkpoint_data = {
        "user_task": user_task,
        "task_hash": task_hash,
        "iteration": iteration,
        "phase": phase,
        "context": context,
        "plan_md_path": plan_md_path,
        "timestamp": datetime.now().isoformat(),
        "additional_state": additional_state or {},
        "version": "1.0.0"
    }

    return json.dumps(checkpoint_data, ensure_ascii=False, indent=2)


def deserialize_checkpoint(json_str: str) -> Dict[str, Any]:
    """
    从 JSON 字符串反序列化检查点状态

    返回：检查点数据字典
    抛出：ValueError（数据不完整或格式错误）
    """
    try:
        checkpoint_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"无效的 JSON 格式: {e}")

    # 验证必需字段
    required_fields = ["user_task", "task_hash", "iteration", "phase", "context", "timestamp"]
    missing_fields = [f for f in required_fields if f not in checkpoint_data]

    if missing_fields:
        raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")

    # 验证 phase 枚举值
    valid_phases = ["initialization", "planning", "confirmation", "execution", "verification", "adjustment", "completion"]
    if checkpoint_data["phase"] not in valid_phases:
        raise ValueError(f"无效的 phase 值: {checkpoint_data['phase']}")

    # 验证 context.replan_trigger 枚举值
    if "replan_trigger" in checkpoint_data["context"]:
        valid_triggers = [None, "user", "adjuster", "verifier"]
        if checkpoint_data["context"]["replan_trigger"] not in valid_triggers:
            raise ValueError(f"无效的 replan_trigger 值: {checkpoint_data['context']['replan_trigger']}")

    return checkpoint_data


def validate_checkpoint_expiry(checkpoint_data: Dict[str, Any], max_hours: int = 24) -> bool:
    """
    验证检查点是否过期

    返回：
    - True: 未过期
    - False: 已过期
    """
    from datetime import datetime, timedelta

    checkpoint_time = datetime.fromisoformat(checkpoint_data["timestamp"])
    return datetime.now() - checkpoint_time <= timedelta(hours=max_hours)
```

</serialization>

<migration>

## 版本迁移

当检查点格式升级时，需要支持旧版本数据的迁移：

```python
def migrate_checkpoint(checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将旧版本检查点迁移到最新版本

    版本历史：
    - 1.0.0: 初始版本
    """
    current_version = checkpoint_data.get("version", "1.0.0")

    if current_version == "1.0.0":
        # 已是最新版本，无需迁移
        return checkpoint_data

    # 未来版本迁移逻辑在此添加
    # if current_version == "0.9.0":
    #     checkpoint_data = migrate_0_9_to_1_0(checkpoint_data)

    return checkpoint_data
```

</migration>

<notes>

## 注意事项

1. **字符编码**：JSON 文件必须使用 UTF-8 编码，确保中文任务描述正确保存
2. **时间格式**：timestamp 使用 ISO 8601 格式（`datetime.now().isoformat()`）
3. **任务哈希**：使用 MD5(user_task)[:12] 生成唯一标识
4. **过期时间**：默认24小时，可根据需要调整
5. **数据完整性**：加载时必须验证必需字段，确保数据完整
6. **向后兼容**：新增字段必须设为可选，避免破坏旧检查点
7. **敏感数据**：检查点文件不应包含敏感信息（密码、token 等）
8. **文件权限**：检查点目录 `.claude/checkpoints/` 应设置合理权限，避免泄露

</notes>
