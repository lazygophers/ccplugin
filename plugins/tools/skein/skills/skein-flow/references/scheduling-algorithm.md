# 调度算法 (双层同构)

编排两层, 两层同构、都由 main 作调度器跑同一套 DAG: ① **subtask 级** (exec 阶段, 单 task 内把 planning 拆好的 subtask 派 `skein-implementer` 执行); ② **task 级** (同 session 多 active task 并行, 见末节)。只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-planning`)。

## 调度 DAG = 冲突自算边 ∪ 显式 depends_on

1. **静态冲突边 (自算)** — 两 subtask 的 write-files glob 相交 或 exec-scope 相交 → 串行 (不能并发)。不相交 → 可并行。
2. **显式依赖边** — subtask 的 `depends_on` (planning 定, 写进 implement.md 调度图)。被依赖者未 done, 依赖者不 ready。
3. **最终 DAG** = 两者并集。ready (所有前置 done + 无冲突占用) 的 subtask 并行派, 未就绪串行等。

## 调度循环 (动态, 完成即派)

```
就绪集 = DAG 中所有前置已 done 且无冲突占用的 subtask
while 还有未完成 subtask:
    while 并发数 < 2 且 就绪集非空:
        派 1 个就绪 subtask 给 skein-implementer (真实 Agent 调用)
    等任一 subagent 返回
    更新完成态 → 重算就绪集 → 立即派新就绪 (不空等全部)
```

- **并发上限 2** — 同时在跑 subagent ≤ 2。
- **完成即派** — 任一返回立即查新 ready 并派, 不等一批跑完。
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

派给 `skein-implementer`, 6 字段:

```
目标: <这个 subtask 要产出什么>
已知: Active task <id>, worktree=<路径>, 相关文件/上文, 召回的 recall 规则
工作目录与范围: <worktree 路径>; 只改下列文件 (每文件带 reason), 禁碰其他:
  - <文件路径A> — reason: <改它是为了满足哪条契约/需求>
  - <文件路径B> — reason: <...>
输出格式: <改了哪些文件 + 关键决策 + 遗留>
验收标准: <可验证断言: 测试过 / lint 净 / 功能点>
失败处理: 缺信息在返回标 `需要: <问题>`; 报错读原因缩范围重试
```

- **per-file reason 必填** — 范围段每个目标文件后附一句 reason (为什么改它), 让 implementer 拿到就知道每个文件的改动意图, 并据此在写前复述契约 (见 `skein-implementer` 写前硬门)。reason 与该文件适用契约矛盾时 implementer 会标 `需要:` 回传, 不擅改。
- `skein-implementer` **本身即无 Agent/Task 工具** (Recursion Guard), 只执行 1 subtask, 不自派; 也不能 `AskUserQuestion` — 缺信息标 `需要:` 由 main 转达用户。
