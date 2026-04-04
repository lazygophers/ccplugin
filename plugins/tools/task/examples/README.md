# metadata.json 样例文件

本目录包含 `.claude/tasks/{task_id}/metadata.json` 在不同完成状态下的样例文件。

## 样例说明

### 1. metadata-completed.json - 任务成功完成

**场景**：任务成功完成，所有验收标准通过，质量分数达标。

**关键字段**：
- `phase`: `"completed"`
- `quality_score`: `92`（高质量完成）
- `iteration`: `2`（经过 2 次迭代）
- `result.status`: `"completed"`
- `error`: `null`（无错误）

**时间跨度**：从创建到完成约 4 小时（14400 秒）

---

### 2. metadata-failed.json - 任务失败

**场景**：任务执行失败，达到最大重试次数后仍无法完成。

**关键字段**：
- `phase`: `"failed"`
- `quality_score`: `45`（质量分数较低）
- `iteration`: `3`（经过 3 次迭代尝试）
- `result.status`: `"failed"`
- `error`: 包含具体错误信息

**时间跨度**：从创建到失败约 2.8 小时（10000 秒）

---

### 3. metadata-partially-completed.json - 任务部分完成

**场景**：任务部分完成，核心功能实现但有次要功能未完成。

**关键字段**：
- `phase`: `"completed"`（最终 phase 仍为 completed）
- `quality_score`: `78`（中等质量）
- `iteration`: `1`（首次迭代）
- `result.status`: `"partially_completed"`（部分完成标记）
- `error`: `null`

**时间跨度**：从创建到完成约 3.8 小时（13600 秒）

---

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务唯一标识（2-6 个汉字） |
| `session_id` | string | Claude Code 会话标识（MD5 哈希） |
| `description` | string | 用户原始任务描述 |
| `phase` | string | 当前阶段（完成时为 `completed` 或 `failed`） |
| `created_at` | number | 任务创建时间（Unix 时间戳，秒） |
| `updated_at` | number | 最后更新时间（Unix 时间戳，秒） |
| `iteration` | number | 迭代轮次（0 开始） |
| `quality_score` | number | 验证质量分数（0-100） |
| `error` | string/null | 错误信息（失败时记录） |
| `result` | object | Cleanup 阶段结果（仅含 `status` 字段） |
| `skip_next_plan_confirm` | boolean | 是否跳过计划确认（完成时通常为 false） |

---

## result.status 枚举值

- `"completed"` - 任务完全成功完成
- `"partially_completed"` - 任务部分完成（核心功能完成，次要功能未完成）
- `"failed"` - 任务失败

---

## 时间戳转换

```python
import time
from datetime import datetime

# Unix 时间戳 → 人类可读格式
timestamp = 1733308800
dt = datetime.fromtimestamp(timestamp)
print(dt)  # 2024-12-04 16:00:00

# 人类可读格式 → Unix 时间戳
dt = datetime(2024, 12, 4, 16, 0, 0)
timestamp = int(dt.timestamp())
print(timestamp)  # 1733308800
```

---

## 完成状态判定

任务被认为是"完成"状态的条件：

1. `phase` 为 `"completed"` 或 `"failed"`
2. `result.status` 存在且为 `"completed"` / `"partially_completed"` / `"failed"` 之一
3. Cleanup 阶段已执行，资源已清理

---

## 与 index.json 的对应

完成状态的 metadata.json 会同步到 `.claude/tasks/index.json`：

```json
{
  "a1b2c3d4e5f6789012345678abcdef01": [
    {
      "task_id": "用户认证",
      "description": "添加用户登录和注册功能，包括表单验证和错误处理",
      "phase": "completed",
      "created_at": 1733308800,
      "updated_at": 1733323200,
      "iteration": 2,
      "quality_score": 92
    }
  ]
}
```

**注意**：索引中不包含 `session_id`（作为 key）、`error` 和 `result`（详细信息保留在 metadata.json）。
