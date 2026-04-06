# 任务索引管理规范

## 概述

`.lazygophers/tasks/index.json` 是任务索引文件，存储所有任务的基本信息列表，便于快速查询和管理，无需遍历所有任务子目录。

## 文件位置

`.lazygophers/tasks/index.json`

## 数据结构

索引文件使用 **数组结构**，存储所有任务的基本信息，按 `updated_at` 降序排列（最新的在前）。

**⚠️ 重要**：
- 数组元素是任务对象，不使用任何包装键
- 时间戳必须是整数（秒），不可使用浮点数
- 必须包含 `updated_at` 字段
- 数组按 `updated_at` 降序排列

**正确示例**：
```json
[
  {
    "task_id": "数据导出",
    "description": "添加数据导出 CSV 功能",
    "phase": "planning",
    "created_at": 1733330000,
    "updated_at": 1733330000,
    "iteration": 0,
    "quality_score": null
  },
  {
    "task_id": "密码重置",
    "description": "实现密码重置功能",
    "phase": "completed",
    "created_at": 1733320000,
    "updated_at": 1733323600,
    "iteration": 1,
    "quality_score": 92
  },
  {
    "task_id": "用户认证",
    "description": "添加用户登录功能",
    "phase": "execution",
    "created_at": 1733308800,
    "updated_at": 1733312400,
    "iteration": 2,
    "quality_score": 85
  }
]
```

**❌ 错误示例**（不可使用）：
```json
{
  "tasks": [
    {
      "task_id": "修复日志",
      "phase": "initialization",
      "created_at": 1733308800.12345,
      "iteration": 0,
      "quality_score": null
    }
  ]
}
```
**错误原因**：
- ❌ 使用了 `"tasks"` 包装键
- ❌ 时间戳是浮点数而非整数
- ❌ 缺少 `updated_at` 和 `description` 字段

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `task_id` | string | 任务唯一标识（中文描述，2-6 个汉字） | `"用户认证"` |
| `description` | string | 用户原始任务描述 | `"添加用户登录功能"` |
| `phase` | string | 当前阶段（枚举值） | `"execution"` |
| `created_at` | number | 任务创建时间（Unix 时间戳，秒） | `1733308800` |
| `updated_at` | number | 最后更新时间（Unix 时间戳，秒） | `1733312400` |
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

**时机**：生成 task_id 后的第一步操作（在创建 metadata.json 之前）

**操作**：
1. 检查 `.lazygophers/tasks/index.json` 是否存在
   - 不存在：创建空数组 `[]`
   - 存在：读取现有内容
2. 在数组头部插入当前任务信息（保持最新任务在前）
3. 写回文件

**重要性**：PreToolUse hook 依赖 index.json 检查任务状态，必须在创建 metadata.json 之前完成索引更新

**示例代码**：
```python
import json
import time
from pathlib import Path

index_path = Path(".lazygophers/tasks/index.json")

# 读取或创建索引
if index_path.exists():
    with open(index_path) as f:
        index = json.load(f)
else:
    index = []

# 在数组头部插入当前任务（保持最新任务在前）
now = int(time.time())
index.insert(0, {
    "task_id": task_id,
    "description": user_task,
    "phase": "initialization",
    "created_at": now,
    "updated_at": now,
    "iteration": 0,
    "quality_score": None
})

# 写回索引
with open(index_path, "w") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)
```

### 2. Phase Transition：更新任务状态

**时机**：每次阶段转换时

**操作**：
1. 读取 `.lazygophers/tasks/index.json`
2. 在数组中找到对应 `task_id` 的记录
3. 更新 `phase`、`updated_at`、`iteration`（如果迭代增加）
4. 重新排序数组（按 `updated_at` 降序）
5. 写回文件

**示例代码**：
```python
# 读取索引
with open(".lazygophers/tasks/index.json") as f:
    index = json.load(f)

# 更新任务状态
for task in index:
    if task["task_id"] == task_id:
        task["phase"] = new_phase
        task["updated_at"] = int(time.time())
        if new_iteration is not None:
            task["iteration"] = new_iteration
        break

# 重新排序（按 updated_at 降序）
index.sort(key=lambda t: t["updated_at"], reverse=True)

# 写回索引
with open(".lazygophers/tasks/index.json", "w") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)
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

## 容错规则

1. **索引缺失**：如果 index.json 不存在，任务依然正常运行，只是缺少索引功能
2. **索引损坏**：如果 index.json 解析失败，备份旧文件为 `index.json.bak`，重新创建空索引
3. **记录缺失**：如果索引中找不到对应任务，添加新记录（使用当前状态）
4. **记录重复**：如果索引中有重复 task_id，保留最新的记录（按 updated_at 排序）

## 查询示例

### 查询所有进行中的任务

```bash
jq '[.[] | select(.phase != "completed" and .phase != "failed")]' .lazygophers/tasks/index.json
```

### 查询特定任务

```bash
jq --arg tid "用户认证" '.[] | select(.task_id == $tid)' .lazygophers/tasks/index.json
```

### 查询任务总数

```bash
jq 'length' .lazygophers/tasks/index.json
```

### 统计所有任务状态

```bash
jq '[.[] | {phase, task_id}] | group_by(.phase) | map({phase: .[0].phase, count: length})' .lazygophers/tasks/index.json
```

### 查询最近的 5 个任务

```bash
jq '.[0:5]' .lazygophers/tasks/index.json
```
**说明**：由于数组已按 `updated_at` 降序排列，直接切片即可。

### 查询所有已完成的任务

```bash
jq '[.[] | select(.phase == "completed")]' .lazygophers/tasks/index.json
```

## 与 metadata.json 的关系

| 特性 | index.json | metadata.json |
|------|-----------|---------------|
| 位置 | `.lazygophers/tasks/index.json` | `.lazygophers/tasks/{task_id}/metadata.json` |
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
