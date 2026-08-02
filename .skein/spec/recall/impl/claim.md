---
title: claim
layer: recall
category: impl
keywords: [claim,dry-run,subtask,start,占槽,running,executor,生命周期,调度,batch,concurrent,idempotent,started,timestamp]
status: active
---

## claim 三态分工 + executor 不重复占槽

### 触发场景
派发 subtask / 重派失败 subtask / 调度循环起手时, 需选 claim 还是 start, 还是只看不改态。

### 三态分工 (铁律, 文档要显眼)

| 命令 | 行为 | 占槽 | 用途 |
| --- | --- | --- | --- |
| `skein claim` / `skein subtask claim <tid>` | **默认即整批标 running** | 占 `pools.work` | **执行主路径**, 无需任何额外参数 |
| `skein claim --dry-run` | 只读预览就绪批, **不改态** | 不占 | 想先看再决定是否执行 |
| `skein subtask start <tid> <sid>` | 单 sid 标 running | 占 1 槽 | 失败重派 / 定点补派单 subtask |

### 陷阱-正解

**陷阱**: 文档把「claim 默认改态」埋深, AI 误以为 claim 需额外参数 (如 `--start`) 才改态占槽 → 错走 `subtask start` 逐个派, 多一轮往返 + 竞态窗口。
**正解**: claim 裸调用即改态占槽 (主路径), 反向 `--dry-run` 才是只读预览; 单 sid 补派用 start, **不接受 sid 是 claim 的契约边界** (整批就绪由 DAG 算, 非挑单)。

**陷阱**: executor 被派时再跑 `claim`/`start` "重新占槽" → 重复改态 + started 覆盖 + 计时错乱。
**正解**: main 用 claim **前置占槽**, executor 被派时 subtask 已是 running 态, **直接执行产出, 不跑生命周期命令 (claim/start/done/fail 归 main)** — 与「禁跑生命周期脚本」checkpoint 同源。

### 反例表

| 禁 | 改为 |
| --- | --- |
| 逐个 `subtask start` 派整批 | `claim` 一次性整批标 running |
| claim 加 `--start` 参数才改态 (AI 臆造) | claim 裸调用即改态 (无 --start 参数, 旧 prd 已撤) |
| executor 被派时重跑 claim/start "确保占槽" | 已 running 不重复占槽, 直接执行 |
| 想预览就绪批忘了 `--dry-run` 直接 claim | 预览必带 `--dry-run`, 裸 claim 已改态 |

### 规则

- 代码: `skein.py:1705-1755` (claim 默认改态 + dry_run 分支), `skein.py:1799-1814` (subtask claim 同构), `skein.py:1818-1830` (start 单 sid 路径)
- 文档锚: `skein-exec/SKILL.md:34`, `skein-exec/references/scheduling-algorithm.md:11-15`, `agents/skein-executor.md:22`

### 关联

- [[claim#批认领 subtask（一次性 claim 整批）]] (批认领整批, 互补: 本规则补三态分工 + executor 不重复占槽)
- [[claim#started 首次置定后禁覆盖（幂等）]] (started 幂等不覆盖, 同源计时问题)

## 批认领 subtask（一次性 claim 整批）

### 触发场景
批量派发 subtask 时，确保整批一次性认领而非逐个 start。

### 陷阱-正解
**陷阱**：逐个 start 各 subtask，每个一回合，窗口内多次发起间隔。
**正解**：`subtask claim` 一次性认领整批，标 running，减少往返 + 消除竞态。

### 规则
see skein.py:1415-1421 (subtask claim 与 claim 对比)。

### 关联
arch/concurrent-write-state-machine (C2), arch/workspace-lock (C1)

## started 首次置定后禁覆盖（幂等）

### 触发场景
重试或重启幂等场景，subtask 已经 started，需要重认领。

### 陷阱-正解
**陷阱**：重认领时覆盖 started 时刻，导致计时错误。
**正解**：started 首次置定后永不覆盖，幂等检查 `if not s.get("started")` 再设。

### 规则
见 skein.py:1419-1420, 1445-1446。

### 关联
impl/idempotent-start-marker
