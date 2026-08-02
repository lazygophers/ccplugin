---
title: task-json-schema
category: arch
keywords: [task.json,中文key,映射表,时间戳,迁移]
status: active
inclusion: auto
---

## task-json 中文 key 映射表

# task-json-cn-schema — 详细设计

## 测试接缝
- 复用 tests/test_skein.py (create→confirm→check→finish 全链路断言 task.json 字段)
- 新增 tests/test_schema_migration.py (旧英文 key task.json → 读时自动迁移)

## 1. 完整中文 key 映射表

### task 级 (create 初始化 + 各阶段写入)

| 旧 key | 新 key | 类型 | 初始值 | 写入时机 |
|---|---|---|---|---|
| `id` | `id` | str | — | **保留** (全局标识, 非展示字段) |
| `name` | `名称` | str | — | create |
| `desc` | `描述` | str | — | create |
| `status` | `状态` | str | `"待处理"` | create + 各转换 |
| `deps` | `前置` | list[str] | `[]` | create |
| `contracts` | `契约` | list | `[]` | create |
| `subtasks` | `子任务` | list | `[]` | create |
| `priority` | `优先级` | int | 5 | create |
| `estimate` | `预计工时` | float\|None | None | estimate --set |
| `repos` | `仓库` | list | `[]` | create |
| `worktree` | `工作树` | str\|None | None | `_activate` |
| `worktrees` | `工作树列表` | list | `[]` | `_activate` |
| `branch` | `分支` | str | `f"skein/{tid}"` | create |
| `parent` | `父任务` | str\|None | None | create |
| `kind` | `类型` | str | `"task"` | create |
| `created` | `创建时间` | epoch | `now()` | create |
| `confirmed` | `确认时间` | epoch\|None | None | confirm |
| `confirmed_by` | `确认人` | str\|None | None | confirm |
| `started` | `执行开始` | epoch\|None | None | `_activate` (=confirm/start) |
| `checked` | `检查开始` | epoch\|None | None | check |
| **(新)** | `检查结束` | epoch\|None | None | finish |
| `finished` | `完成时间` | epoch\|None | None | finish |
| `updated` | `更新时间` | epoch | `now()` | 每次 save |

### subtask 级 (add 时初始化 + claim/done/fail 写入)

| 旧 key | 新 key | 类型 | 初始值 | 写入时机 |
|---|---|---|---|---|
| `sid` | `标识` | str | — | add |
| `name` | `名称` | str | — | add |
| `desc` | `描述` | str | — | add |
| `estimate` | `预计工时` | float | — | add |
| `depends_on` | `依赖` | list[str] | `[]` | add |
| `验收` | `验收` | list | — | add (**已中文, 不变**) |
| `验收done` | `验收完成` | list | `[]` | check |
| `status` | `状态` | str | `"待处理"` | add + claim/done/fail |
| `skills` | `技能` | list | `[]` | add |
| `created` | `创建时间` | epoch | `now()` | add |
| `started` | `执行开始` | epoch\|None | None | claim/start → 运行中 |
| `finished` | `执行结束` | epoch\|None | None | done/fail |
| `note` | `备注` | str | `""` | (可选) |

## 2. 阶段时间双戳模型

```
待处理 ──confirm--> 进行中 ──check--> 检查中 ──finish--> 已完成
│                  │           │          │            │
创建时间           确认时间     执行开始    检查开始      检查结束/完成时间
```

| 阶段 | 开始时间戳 | 结束时间戳 | 可算 |
|---|---|---|---|
| 规划 | 创建时间 | 确认时间 | 规划耗时 = 确认时间 - 创建时间 |
| 执行 | 执行开始 | 检查开始 | 执行耗时 = 检查开始 - 执行开始 |
| 检查 | 检查开始 | 检查结束 | 检查耗时 = 检查结束 - 检查开始 |
| 总计 | 创建时间 | 完成时间 | 总耗时 = 完成时间 - 创建时间 |

- `执行开始` = confirm/_activate 时刻 (首个 subtask 尚未开始, 但 task 已占槽)
- `检查开始` = check 命令时刻
- `检查结束` = finish 命令时刻 (= 完成时间, 精确到同一 `now()` 调用)

subtask 层:
- `执行开始` = 首次 claim/start 时
- `执行结束` = done/fail 时

## 3. 向后兼容

`store.py` 的 `load()` 加迁移:

```python
_TASK_KEY_MAP = {
    "name": "名称", "desc": "描述", "status": "状态", "deps": "前置",
    "contracts": "契约", "subtasks": "子任务", "priority": "优先级",
    "estimate": "预计工时", "repos": "仓库", "worktree": "工作树",
    "worktrees": "工作树列表", "branch": "分支", "parent": "父任务",
    "kind": "类型", "created": "创建时间", "confirmed": "确认时间",
    "confirmed_by": "确认人", "started": "执行开始", "checked": "检查开始",
    "finished": "完成时间", "updated": "更新时间",
}
_SUB_KEY_MAP = {
    "sid": "标识", "name": "名称", "desc": "描述", "estimate": "预计工时",
    "depends_on": "依赖", "验收done": "验收完成", "status": "状态",
    "skills": "技能", "created": "创建时间", "started": "执行开始",
    "finished": "执行结束", "note": "备注",
}
```

读到旧 key → 搬到新 key + 写回盘 (下次读到全是新 key)。
新增字段 (`检查结束`) 旧数据无 → 默认 None。

## 4. 不改名的 key

- `id` — 全局标识, 跨系统引用 (URL/git branch/skein 命令参数)
- `验收` — 已是中文

## 5. 影响面 (按改动类型)

### 初始化 + 写入 (lifecycle.py / scheduling.py)
- `create`: 初始所有中文 key
- `_activate`: `执行开始` + `确认时间` + `确认人`
- `check`: `检查开始`
- `finish`: `检查结束` + `完成时间`
- subtask `add`: 中文 key 初始化
- subtask `claim/start`: `执行开始` (subtask)
- subtask `done/fail`: `执行结束` (subtask)

### 读取 (全消费层)
- `store.py`: 镜像 + 迁移 + 排序 (`执行开始` 替换 `started`)
- `views.py`: 统计/看板/队列/ETA 全部读时间字段
- `query.py`: `ready()` 等只读查询
- `board.py`: 看板渲染
- `scheduling.py`: subtask 时间 (elapsed 等)
- `dag.py`: `_TASK_PCT_RANGE` key 不变 (用状态常量, 不读时间)
- `doctor.py`: 不变量体检
- `serve.py`: JSON API 响应
- `hooks/`: 上下文注入

### 前端
- `model.ts`: `STATUS_MAP` 等不改 (状态值已是中文), 但时间字段 `.started` → `.执行开始`
- `api.ts`: 类型定义
- `board/detail/help/queue/dashboard`: 展示时间的地方

### 测试
- 全量 `.get("started")` / `["started"]` → `.get("执行开始")` / `["执行开始"]`
- 新增迁移测试
