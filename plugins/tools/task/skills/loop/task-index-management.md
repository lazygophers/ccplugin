# 任务索引管理规范

## 概述

`.claude/tasks/index.json` 是任务索引文件，存储所有任务的基本信息列表，便于快速查询和管理，无需遍历所有任务子目录。

## 文件位置

`.claude/tasks/index.json`

## 数据结构

```json
[
  {
    "task_id": "任务标识",
    "session_id": "会话标识",
    "description": "用户任务描述",
    "phase": "当前阶段",
    "created_at": "2026-04-04T10:30:00Z",
    "updated_at": "2026-04-04T11:45:00Z",
    "iteration": 2,
    "quality_score": 85
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `task_id` | string | 任务唯一标识（中文描述，2-6 个汉字） | `"用户认证"` |
| `session_id` | string | Claude Code 会话标识（MD5 哈希） | `"a1b2c3d4e5f6..."` |
| `description` | string | 用户原始任务描述 | `"添加用户登录功能"` |
| `phase` | string | 当前阶段（枚举值） | `"execution"` |
| `created_at` | string | 任务创建时间（ISO8601） | `"2026-04-04T10:30:00Z"` |
| `updated_at` | string | 最后更新时间（ISO8601） | `"2026-04-04T11:45:00Z"` |
| `iteration` | number | 当前迭代轮次 | `2` |
| `quality_score` | number/null | 验证质量分数（0-100），未验证时为 null | `85` |

### phase 枚举值

- `initialization` - 初始化
- `planning` - 计划设计
- `execution` - 任务执行
- `verification` - 结果验证
- `quality_gate` - 质量门检查
- `adjustment` - 失败调整
- `cleanup` - 资源清理
- `completed` - 已完成
- `failed` - 已失败

## 索引操作规范

### 1. Initialization：创建任务索引

**时机**：任务初始化时

**操作**：
1. 检查 `.claude/tasks/index.json` 是否存在
   - 不存在：创建空数组 `[]`
   - 存在：读取现有内容
2. 追加当前任务信息到数组
3. 写回文件

**示例代码**：
```python
import json
from pathlib import Path
from datetime import datetime

index_path = Path(".claude/tasks/index.json")

# 读取或创建索引
if index_path.exists():
    with open(index_path) as f:
        tasks = json.load(f)
else:
    tasks = []

# 追加当前任务
tasks.append({
    "task_id": task_id,
    "session_id": session_id,
    "description": user_task,
    "phase": "initialization",
    "created_at": datetime.utcnow().isoformat() + "Z",
    "updated_at": datetime.utcnow().isoformat() + "Z",
    "iteration": 0,
    "quality_score": None
})

# 写回索引
with open(index_path, "w") as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)
```

### 2. Phase Transition：更新任务状态

**时机**：每次阶段转换时

**操作**：
1. 读取 `.claude/tasks/index.json`
2. 找到对应 `task_id` 的记录
3. 更新 `phase`、`updated_at`、`iteration`（如果迭代增加）
4. 写回文件

**示例代码**：
```python
# 读取索引
with open(".claude/tasks/index.json") as f:
    tasks = json.load(f)

# 更新任务状态
for task in tasks:
    if task["task_id"] == task_id:
        task["phase"] = new_phase
        task["updated_at"] = datetime.utcnow().isoformat() + "Z"
        if new_iteration is not None:
            task["iteration"] = new_iteration
        break

# 写回索引
with open(".claude/tasks/index.json", "w") as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)
```

### 3. Verification：更新质量分数

**时机**：Verification 阶段完成后

**操作**：
1. 读取索引
2. 更新对应任务的 `quality_score`
3. 写回文件

### 4. Cleanup：标记任务完成

**时机**：Cleanup 阶段完成后

**操作**：
1. 读取索引
2. 更新任务的 `phase` 为 `completed` 或 `failed`
3. 更新 `updated_at`
4. 写回文件

### 5. Maintenance：过期清理

**时机**：定期维护（可选）

**操作**：
1. 读取索引
2. 过滤掉 30 天前的 `completed` 或 `failed` 任务
3. 写回文件

**示例代码**：
```python
from datetime import datetime, timedelta

# 读取索引
with open(".claude/tasks/index.json") as f:
    tasks = json.load(f)

# 过滤过期任务
cutoff = datetime.utcnow() - timedelta(days=30)
tasks = [
    task for task in tasks
    if task["phase"] not in ["completed", "failed"]
    or datetime.fromisoformat(task["updated_at"].rstrip("Z")) > cutoff
]

# 写回索引
with open(".claude/tasks/index.json", "w") as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)
```

## 容错规则

1. **索引缺失**：如果 index.json 不存在，任务依然正常运行，只是缺少索引功能
2. **索引损坏**：如果 index.json 解析失败，备份旧文件为 `index.json.bak`，重新创建空索引
3. **记录缺失**：如果索引中找不到对应任务，添加新记录（使用当前状态）
4. **记录重复**：如果索引中有重复 task_id，保留最新的记录（按 updated_at 排序）

## 查询示例

### 查询所有进行中的任务

```bash
jq '[.[] | select(.phase != "completed" and .phase != "failed")]' .claude/tasks/index.json
```

### 查询特定会话的任务

```bash
jq --arg sid "$SESSION_ID" '[.[] | select(.session_id == $sid)]' .claude/tasks/index.json
```

### 统计任务状态

```bash
jq 'group_by(.phase) | map({phase: .[0].phase, count: length})' .claude/tasks/index.json
```

### 查询最近的任务

```bash
jq 'sort_by(.updated_at) | reverse | .[0:5]' .claude/tasks/index.json
```

## 与 metadata.json 的关系

| 特性 | index.json | metadata.json |
|------|-----------|---------------|
| 位置 | `.claude/tasks/index.json` | `.claude/tasks/{task_id}/metadata.json` |
| 作用 | 所有任务的索引列表 | 单个任务的完整元数据 |
| 字段 | 基本信息（8个字段） | 完整信息（12个字段 + result 对象） |
| 更新时机 | 阶段转换时 | 每次状态变化时 |
| 查询速度 | 快（单文件） | 慢（需遍历目录） |
| 数据完整性 | 摘要信息 | 详细信息 |

**规则**：index.json 是 metadata.json 的缓存/索引，metadata.json 是权威数据源。发生冲突时，以 metadata.json 为准。

## 最佳实践

1. **原子写入**：使用临时文件 + 原子重命名，避免写入过程中的损坏
2. **格式化**：使用 `indent=2` 和 `ensure_ascii=False`，便于人类阅读
3. **备份**：更新前备份旧索引为 `index.json.bak`
4. **验证**：写入后验证 JSON 格式正确性
5. **并发**：使用文件锁避免并发写入冲突（如需要）
