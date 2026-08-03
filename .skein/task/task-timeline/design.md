# task 生命周期时间线 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 数据模型

`TaskData` 加一个字段 `timeline: list[TimelineEvent]`，落在 per-task 的 `.skein/task/<id>/task.json`（**不是** 顶层 `.skein/task.json` —— 那份是索引镜像，只存卡片摘要，不承载事件流）。

```python
class TimelineEvent(BaseModel):
    kind: Literal["task", "subtask"]
    status: str          # task 事件存 TaskStatus, subtask 事件存 SubtaskStatus
    at: int              # Unix epoch 秒, 与其余落盘时间字段同制
    sid: str | None      # 仅 subtask 事件
    note: str            # 失败原因 / 回滚说明, 默认空
    rollback: bool       # 状态序号回退时 True
```

字段少是刻意的：timeline 随 task.json 每次 `save` 全量重写，长 task 会累积上百条，每多一个字段就乘以条数。

## 2. 写入路径 (单一入口)

`skeinlib/task/timeline.py` 出一个纯函数：

```python
def append(t: dict, kind, status, *, sid=None, note="") -> None
```

内部自己判 `rollback`：拿同 `kind`（且 subtask 事件同 `sid`）的**上一条**事件比状态序号，新序号 ≤ 旧序号即回滚。序号表复用既有的 `STATUS_ORDER` / subtask 的隐含顺序，不新定义一套。

**取舍**：不做成 `store.save()` 里的自动埋点。save 看不见"为什么变"，note 传不进来，且同一次 save 可能夹带多个变更，会记出假事件。改成在 6 处 task 迁移 + 3 处 subtask 迁移显式调用——多写 9 行，换来事件语义准确。

写入点：
- task: `create`(pending) / `research` / `plan`(回 pending) / `confirm`(active) / `check` / `finishing` / `finish`(done)
- subtask: `claim`+`subtask start`(running) / `done` / `fail`(带 note)

## 3. 回滚的两条真实路径

1. `research` → `pending`（`plan` 收敛调研结果回规划）
2. `check` → `active`（check FAIL 后补修复 subtask；flow 语义上叫"前进式修补"，但状态序号确实退了，时间线要如实画）

subtask 侧的 `failed` → `running`（定点重派）同理。

## 4. 输出与渲染

后端：task 详情响应原样带出 `timeline` 数组，不做聚合——聚合规则属展示层，后端多一层加工只会和前端打架。

前端 `task/detail/page.tsx` 的 `buildStages` 从"读 4 个扁平时间戳"改为"读 timeline"：

1. 骨架恒定：`规划中 → 调研中 → 进行中 → 检查中 → 收尾中 → 已完成`。
2. 对每个骨架节点，从 timeline 过滤出同 status 的全部事件：有则实心 + 取**首次**进入时间 + `↺ N 轮`（N = 命中条数，N≥2 才显示）；无则空心占位。
3. subtask 事件不进主骨架，走详情页已有的子任务时间线组件（避免两个组件画同一批数据）。
4. `timeline` 缺失/空（老 task）→ 回落到现有的扁平时间戳渲染路径，不报错、不空白。

## 5. 可能性分支

- **触发条件**：单个 task 的 timeline 超过 ~500 条导致 task.json 明显变大。
  **做法**：事件分文件到 `.skein/task/<id>/timeline.jsonl` 追加写。现在不做——正常 task 几十条，为没发生的规模先拆文件是自找复杂度。
- **触发条件**：用户要看跨 task 的返工率统计。
  **做法**：`rollback: true` 已经是机读标记，届时加一条聚合命令即可，无需改数据模型。

## 6. 难逆决策

**事件只追加、不可改、不可删**。一旦允许改写，时间线就不再是可信的审计记录，后续任何"修正历史"的需求都会侵蚀这个性质。宁可留着一条记错的事件，也不提供改写入口。

## 测试接缝 (seam)

check 阶段验证的是`行为对不对`而非`跑没跑起来`, 全靠这里选对接缝。三条规则:
1. 优先复用现有接缝, 不新建
2. 取最高接缝 (越靠外部行为越好)
3. 越少越好, 理想 = 1 个

- **唯一接缝：`skein_cli` fixture（`tests/conftest.py`）跑真实 CLI 命令 → 读回 `.skein/task/<id>/task.json` 断言 `timeline`。**
  这是最高接缝：走的是用户真实路径（命令行），断言的是落盘事实（JSON），中间实现怎么重构都不影响。禁 import `timeline.append` 之类私有函数直接单测——上一轮 `test_agent_routing_by_phase` 就是这么写的，`_agent_for` 一删测试即红。
  前端渲染无接缝可复用（无组件测试基建），靠 `tsc --noEmit` + 人工核对兜底，已在 PRD「验证方式」写明。
