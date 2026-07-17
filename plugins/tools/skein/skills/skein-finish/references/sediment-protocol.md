# sediment 异步判定门

skein-finish 流程第 4 步的 sediment 沉淀细节。**finish 闭环 (archive + 销 worktree) 后**的异步 fire-and-forget, **不阻塞 finish**。本节是 finisher/main 之外的第三载体 `skein-memorier` 的活, 完全复用 `skein-memory` skill, **禁新造沉淀机制**。

## 触发与机制 (fire-and-forget)

finish 闭环后, main **异步**派 `skein-memorier` 跑 sediment 判定门:

- **触发时机** — 第 3 步 `skein finish` 闭环 (archive + 销 worktree) **之后**, 非阻塞。main 派 memorier 后**不等回传即结束回合**, finish 已闭环。
- **fire-and-forget** — memorier 的回传到达后, main **只补 output trace** (finish 已闭环, sediment 判定不输出 trace 即流程错误)。sediment 结果不影响 finish 的闭环性。
- **禁阻塞 finish** — 禁为等 memorier 回传延后 `skein finish`; finish 先闭环, sediment 异步在后。

## memorier 自主判定门

memorier 读 diff + 各 subagent 回传摘要 (含 `SPEC:` 标记), **自主**判定是否沉淀:

- 跑 `skein-memory sediment` 判定门 (判定 → 分层 → 自动写盘), 命中即写, **不逐次询问用户**。
- **自主写盘** — 判定通过后 memorier 自主 `skein-memory sediment` 写盘 + reindex, 无需 main 介入。
- **无增量 → 自判跳过 (禁硬凑)** — 若本次 task 无可沉淀增量 (一次性 bug / 私有细节 / 已有规则覆盖), memorier 自判 drop 跳过, 禁硬凑成沉淀契约。
- 详见 `skein-memory` skill。
