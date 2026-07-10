# 调度算法 (双层同构)

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
