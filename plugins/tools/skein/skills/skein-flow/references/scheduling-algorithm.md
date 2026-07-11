# 调度算法 (双层同构)

编排两层, 两层同构、都由 main 作调度器跑同一套 DAG: ① **subtask 级** (exec 阶段, 单 task 内把 planning 拆好的 subtask 为每个选一个合适的 agent (按任务性质挑现有 agent, 无合适的用 `general-purpose`) 执行); ② **task 级** (同 session 多 active task 并行, 见末节)。只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-planning`)。

## 调度 DAG = 冲突自算边 ∪ 显式 depends_on

1. **静态冲突边 (自算)** — 两 subtask 的 write-files glob 相交 或 exec-scope 相交 → 串行 (不能并发)。不相交 → 可并行。
2. **显式依赖边** — subtask 的 `depends_on` (planning 在 implement.md 调度图定, `skein.py subtask add --deps` 登记进 per-task task.json)。被依赖者未 done, 依赖者不 ready。
3. **最终 DAG** = 两者并集。ready (所有前置 done + 无冲突占用) 的 subtask 并行派, 未就绪串行等。

## subtask 状态 = 脚本落盘, 非肉眼看 implement.md

subtask DAG 存 per-task `task.json` 的 `subtasks[]` (guard 硬阻 AI 直读写), 全程经 `skein.py subtask` 命令维护。**DAG 算法 + 就绪判定 + 改态由脚本一次性做** (`claim`), main 只负责派 agent (脚本不能 spawn):

| 命令 | 谁跑 | 作用 |
| --- | --- | --- |
| `subtask add <tid> <sid> --deps --write --reason` | planning/main | 登记 subtask 到 DAG |
| `subtask claim <tid>` | main (每轮) | **一次性算就绪批 + 整批标 running**, 返回给 main 逐个 dispatch |
| `subtask done/fail <tid> <sid>` | main (agent 回) | agent 完成/失败即改态 |
| `subtask ready <tid>` / `list <tid>` | main (查态) | 只读预览 / 列全 subtask 态 |

## 调度循环 (动态, 完成即派)

```
while skein.py subtask claim <tid> 返回非空:       # 脚本一步: 算就绪 + 标 running
    对认领到的每个 subtask: 为其选合适 agent (无则 general-purpose) 执行 (真实 Agent 调用)  # ≤ max_parallel
    等任一 subagent 返回
    → subtask done/fail <sid> → 回到 claim (脚本自动重算就绪, 完成即派)
```

- **并发上限 2** — `claim` 内按 `max_parallel - running` 截断, 满槽返回空。
- **完成即派** — 任一返回即 `done` 后再 `claim`, 脚本立刻放行新就绪, 不等一批跑完。
- **脚本一步到位** — 就绪判定 + 占槽由 `claim` 原子完成, main 不逐个 `subtask start` (`start` 仅单个 retry 补派)。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 依赖它的 subtask 保持未 ready; main 转达用户/补信息后重派该 subtask, 禁标完成、禁放行下游。
- **subtask 报错 → 不推进** — 按 dispatch 的失败处理缩范围重试; 反复失败 → 停并回传, 禁跳过该 subtask 继续。
- **禁在 subtask 间问用户顺序** — 顺序归 planning。PRD 缺调度图 → 退回 planning 补。

## worktree

- fan-out 的所有 subagent **共享 task worktree** (subtask 不绑定 worktree, 不为 subtask 单开)。
- 默认 1 task 1 worktree。多 worktree 允许但 opt-in (非自动, 不靠 subtask 触发)。

## 多 task 并行 (同 session)

- active 集 ≤ 2 (`skein.py` max_active), start 第三个报错。
- 两 task 的 write-files / exec-scope 相交 → 串行; 不相交 → 各 worktree 各派, 合计每层并发仍 ≤ 2。
- task 级 DAG = 冲突边 ∪ task.json `deps` (`skein.py create --deps`)。

## dispatch prompt (6 字段自包含, 缺字段不派)

**执行者 = main 为该 subtask 选的合适 agent** (按任务性质挑现有 agent, 无合适的用 `general-purpose`)。通用 agent **有** Agent/Task 工具, 故原本靠工具面兜住的执行纪律 (递归护栏 + 读后写硬门) **改由 dispatch prompt 硬性携带** — 无论选中哪个 agent, 6 字段 prompt 都显式带上下面这套纪律:

```
目标: <这个 subtask 要产出什么>
已知: Active task <id>, worktree=<路径>, 相关文件/上文, 召回的 recall 规则
工作目录与范围: <worktree 路径>; 只改下列文件 (每文件带 reason), 禁碰其他:
  - <文件路径A> — reason: <改它是为了满足哪条契约/需求>
  - <文件路径B> — reason: <...>
执行纪律 (硬性, 逐条照做):
  - Recursion Guard: 你只做派给你的这一个 subtask, 禁再派 subagent (禁调 Agent/Task), 自己动手做完。
  - 只在指定 worktree 内改: 禁碰主工作区 / 其他 subtask 的 write-files。
  - 改前查上游: 改函数/类/契约前先 grep 调用站点 (或 gitnexus_impact), 避免半改。
  - 缺信息不硬猜: 缺关键输入时在返回里标 `需要: <问题>` 交 main 转达用户 (你不能 AskUserQuestion)。
  - spec 优先, 别凭记忆重推: 动手前相关约定先 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py recall <关键词>` 拉 recall 层; SubagentStart 已注入的 core 全文即硬约束。踩到「后续同类任务会再犯」的坑 / 定下可复用约定, 在 journal 记一行标 `SPEC:` 供 finish sediment 落盘。
  - 写前 CHECKPOINT — 读后写硬门 (每个待改文件必过): 改任何文件前逐文件按序 —
      ① STOP → Read 全文 (禁凭摘要/记忆动手);
      ② 复述适用契约 + 本次 per-file reason (契约来源 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <id>`);
      ③ 复述无矛盾才允许 Edit/Write, 改动落在 reason 声明意图内。
    若复述发现 reason 与文件现状矛盾 (契约已满足 / 该文件按契约不该改 / reason 指向需求已不存在) → 停手, 标 `需要: <文件 path + 矛盾点>` 回传 main, 禁硬改。
输出格式 (回传 main, 压缩摘要非流水账):
  subtask <id>: <done | 需要: 问题 | 失败: 原因>
  改动文件: <path 列表>
  关键决策: <一两句, 为何这么改>
  自测: <跑过的验证 + 结果; 无则写 未测>
  遗留: <后续 subtask 需知的信息 / 无>
验收标准: <可验证断言: 测试过 / lint 净 / 功能点>
失败处理: 缺信息在返回标 `需要: <问题>`; 报错读原因缩范围重试
```

- **per-file reason 必填** — 范围段每个目标文件后附一句 reason (为什么改它), 让执行 agent 拿到就知道每个文件的改动意图, 并据此在写前复述契约 (见本节 dispatch prompt 读后写硬门)。reason 与该文件适用契约矛盾时执行 agent 会标 `需要:` 回传, 不擅改。
- **Recursion Guard 靠 dispatch prompt 硬性禁止** — 通用 agent 有 Agent/Task 工具, 故不靠工具面而靠上面 prompt 的硬性指令挡住递归: 执行 agent 只做这一个 subtask, 禁再派 subagent, 自己动手做完; 也不能 `AskUserQuestion` — 缺信息标 `需要:` 由 main 转达用户。
