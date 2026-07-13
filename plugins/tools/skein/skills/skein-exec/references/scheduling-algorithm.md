# 调度算法 (双层同构)

编排两层, 两层同构、都由 main 作调度器跑同一套 DAG: ① **subtask 级** (exec 阶段, 单 task 内把 planning 拆好的 subtask 为每个选一个合适的 agent (按任务性质挑现有 agent, 无合适的用 `skein-executor`) 执行); ② **task 级** (同 session 多 active task 并行, 见末节)。只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-plan`)。

## 调度 DAG = 显式 depends_on (唯一边源)

1. **显式依赖边** — subtask 的 `depends_on` (planning 用 `skein.py subtask add --deps` 直接登记进 per-task task.json, 无中间 md 图)。被依赖者未 done, 依赖者不 ready。**并行与否只看这张 DAG** — 无写文件冲突自算 (发挥 AI 自主性: 拆分时靠 planning 把真正有序的关系写进 depends_on, 不靠脚本猜写文件重叠)。
2. **就绪判定** = 所有前置 done + 有空闲并发槽。ready 的 subtask 并行派, 未就绪串行等。

## subtask 状态 = 脚本落盘, 非肉眼看 md 文件

subtask DAG 存 per-task `task.json` 的 `subtasks[]` (guard 硬阻 AI 直读写), 全程经 `skein.py subtask` 命令维护。**DAG 算法 + 就绪判定 + 改态由脚本一次性做** (`claim`), main 只负责派 agent (脚本不能 spawn):

| 命令 | 谁跑 | 作用 |
| --- | --- | --- |
| `subtask add <tid> <sid> --name --desc --agent [--deps --check --skills]` | planning/main | 登记 subtask 到 DAG。**`sid`/`--name`/`--desc`/`--agent` 四者必填** (缺一 argparse 报错; 无合适 agent 显式填 `general-purpose`); `--check` = 验收标准 checklist 分号分隔, `--skills` 逗号分隔 0-n |
| `subtask claim <tid>` | main (每轮) | **一次性算就绪批 + 整批标 running**, 返回给 main 逐个 dispatch |
| `pop` | main (查候选) | **只读提取一个可执行 (task, subtask) 对** (active task 内首个就绪 subtask); 仅选取不改态, 是否执行由 main/AI 判。决定执行后仍走 `claim`/`subtask start` 占槽 |
| `subtask check <tid> <sid> --passed "1,3"` | main (agent 回) | 勾选已过验收序号 (1-based; `all`/`none`), 更新 subtask 完成百分比 = 已过/总验收 (看板渲染进度条) |
| `subtask done/fail <tid> <sid>` | main (agent 回) | agent 完成/失败即改态 (`done` 自动把验收标满 → 100%) |
| `subtask ready <tid>` / `list <tid>` | main (查态) | 只读预览 / 列全 subtask 态 |
| `list --status open --json` | main (取未完成) | **一次取全部未完成 task 压缩 JSON** (省 token, 替代分别跑 `current`+`ready`+直读 task.json): 每项 `{id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}`; `ready=true` 的 pending 即就绪批 |

## 调度循环 (动态, 完成即派)

```
while skein.py subtask claim <tid> 返回非空:       # 脚本一步: 算就绪 + 标 running
    对认领到的每个 subtask: 为其选合适 agent (无则 skein-executor) 执行 (真实 Agent 调用)  # ≤ max_parallel
    等任一 subagent 返回
    → skein.py subtask done/fail <tid> <sid> → 回到 claim (脚本自动重算就绪, 完成即派)
```

- **并发上限 2** — `claim` 内按 `max_parallel - running` 截断, 满槽返回空。
- **完成即派** — 任一返回即 `done` 后再 `claim`, 脚本立刻放行新就绪, 不等一批跑完。
- **脚本一步到位** — 就绪判定 + 占槽由 `claim` 原子完成, main 不逐个 `subtask start` (`start` 仅单个 retry 补派)。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 依赖它的 subtask 保持未 ready; main 转达用户/补信息后重派该 subtask, 禁标完成、禁放行下游。
- **subtask 报错 → 不推进** — 按 dispatch 的失败处理缩范围重试; 反复失败 → 停并回传, 禁跳过该 subtask 继续。
- **禁在 subtask 间问用户顺序** — 顺序归 planning。task.json 缺子任务 DAG (depends_on) → 退回 planning 补。

## worktree

- fan-out 的所有 subagent **共享 task worktree** (subtask 不绑定 worktree, 不为 subtask 单开)。
- 默认 1 task 1 worktree。多 worktree 允许但 opt-in (非自动, 不靠 subtask 触发)。

## 多 task 并行 (同 session)

- active 集 ≤ 2 (`skein.py` max_active), start 第三个报错。
- 各 active task 各占各 worktree, 可并行派, 合计每层并发仍 ≤ 2。
- task 级 DAG = task.json `deps` (`skein.py create --deps`) — 同 subtask 级, 只看显式依赖, 无写文件冲突自算。

## dispatch prompt (6 字段自包含, 缺字段不派)

**执行者 = main 为该 subtask 选的合适 agent** (按任务性质挑现有 agent, 无合适的用默认 `skein-executor`)。默认 `skein-executor` 工具面已剔除 Agent/Task, 递归护栏在工具层强制; 但若选中的具名 agent **有** Agent/Task 工具, 靠工具面兜住的执行纪律 (递归护栏 + 读后写硬门) 就得靠 dispatch prompt 补上 — 故无论选中哪个 agent, 6 字段 prompt 都显式带上下面这套纪律:

```
目标: <这个 subtask 要产出什么>
已知: Active task <id>, worktree=<路径>, 相关文件/上文, 召回的 recall 规则
工作目录与范围: <worktree 路径>; 只在此 worktree 内改, 禁碰主工作区。具体改哪些文件你按目标自主定 (给了自主权, 别越出本 subtask 目标)。
执行纪律 (硬性, 逐条照做):
  - Recursion Guard: 你只做派给你的这一个 subtask, 禁再派 subagent (禁调 Agent/Task), 自己动手做完。
  - 改前查上游: 改函数/类/契约前先 grep 调用站点 (或 gitnexus_impact), 避免半改。
  - 缺信息不硬猜: 缺关键输入时在返回里标 `需要: <问题>` 交 main 转达用户 (你不能 AskUserQuestion)。
  - spec 优先, 别凭记忆重推: 动手前相关约定先 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py recall <关键词>` 拉 recall 层; SubagentStart 已注入的 core 全文即硬约束。踩到「后续同类任务会再犯」的坑 / 定下可复用约定, 在回传给 main 的摘要里标一行 `SPEC:` 供 finish sediment 落盘。
  - 写前硬门 — 读后写: 改任何文件前先 Read 全文 (禁凭摘要/记忆动手) → 复述适用契约 (来源 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <id>`) 无矛盾才 Edit/Write。文件现状与契约矛盾 (契约已满足 / 该文件按契约不该改) → 停手, 标 `需要: <文件 path + 矛盾点>` 回传 main, 禁硬改。
验收标准 (完成前逐条自检, 全过才回 done):
  - <planning 登记的 --check 验收条 1>
  - <验收条 2>
输出格式 (回传 main, 压缩摘要非流水账):
  subtask <id>: <done | 需要: 问题 | 失败: 原因>
  改动文件: <path 列表>
  关键决策: <一两句, 为何这么改>
  自测: <跑过的验证 + 结果; 无则写 未测>
  验收: <逐条对照验收标准的自检结果>
  遗留: <后续 subtask 需知的信息 / 无>
失败处理: 缺信息在返回标 `需要: <问题>`; 报错读原因缩范围重试
```

- **验收标准来自 planning 的 `--check`** — 每个 subtask 登记时带一份可验断言 checklist (存 per-task task.json 的 `验收[]`), dispatch 时原样带给执行 agent, agent 完成前逐条自检、回传时对照。取代旧的 per-file reason: 不再逐文件声明"为何改", 而是给一份"做完要满足什么"的验收清单, 文件由 agent 自主定。
- **完成百分比 = 验收勾选比例** — subtask 完成度不靠估, 由验收 checklist 勾选自动算: agent 回传时 main 用 `subtask check <sid> --passed "1,3"` 勾已过条目, 百分比 = 已过/总验收 (存 `验收done[]`); `done` 自动标满 100%。看板 (task.md/task.html) 逐 subtask 渲染进度条, task 综合完成率 = 各 subtask 百分比均值 (取代旧的 done 计数二值)。
- **Recursion Guard 靠 dispatch prompt 硬性禁止** — 通用 agent 有 Agent/Task 工具, 故不靠工具面而靠上面 prompt 的硬性指令挡住递归: 执行 agent 只做这一个 subtask, 禁再派 subagent, 自己动手做完; 也不能 `AskUserQuestion` — 缺信息标 `需要:` 由 main 转达用户。
