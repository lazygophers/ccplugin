---
name: skein-finish
description: task 收尾闭环门。check 全绿后使用 (被 skein-flow finish 委托, 或用户显式 "收尾/归档/闭环") — 派 skein-finisher 收尾勘察 (diff/subtask 核对/悬挂清单) → 委托 skein-memory sediment 沉淀 → 清悬挂 → skein finish (commit→merge→archive→销 worktree)
user-invocable: false
argument-hint: "[task_id]"
arguments: "[task_id]"
model: haiku
effort: medium
---

# skein-finish — 收尾闭环门

check 全绿后、archive 前的**收尾门**。**未 archive = 未闭环, 禁宣告 Done。**

## 载体分工

| 动作            | 谁                                | 产出                                             |
| --------------- | --------------------------------- | ------------------------------------------------ |
| 收尾勘察        | 派 `skein-finisher` (只读)        | diff 摘要 + subtask 逐条核对 + 悬挂清单          |
| sediment 沉淀   | 委托 `skein-memory` (派 memorier) | 草案 → main 审批 + `skein-memory sediment` 写盘     |
| 清悬挂 + 生命周期 | main 同步跑 (不算实质工作)        | `TaskList`/`TaskStop` + `skein finish`        |

## 流程 (每步 输入 → 动作 → 出口)

1. **收尾勘察** — 输入 `task id + worktree 路径` → 派 `skein-finisher` → 出口: diff 摘要 + subtask 完成核对 + 悬挂清单。**未完成 subtask / 未满足验收 → 退回 exec 或 check, 禁放行**。
2. **sediment 判定门** — 输入 `diff + exec 各 subagent 回传摘要 (含 SPEC: 标记)` → 委托 `skein-memory` sediment (memorier 跑判定门产 core/recall/drop 草案) → main 逐项输出 trace → `AskUserQuestion` 审批 (写盘前硬停, main 亲做) → `skein-memory sediment` 写盘 + reindex。**无增量 → 跳过 (禁硬凑)**。
3. **清悬挂** — `TaskList` 查残留 subagent / 后台任务 → `TaskStop` 关闭。未关 = 未闭环, 禁 finish。
4. **archive** — `skein finish <id>` (commit→merge→archive→销 worktree)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                        | 一线修复                        | 仍失败兜底                                |
| --------------------------- | ------------------------------- | ----------------------------------------- |
| finisher 报未完成 subtask   | 退回 exec 补该 subtask          | 反复不完成 → 回 skein-plan 深化拆分       |
| `skein finish` merge 冲突 | 读冲突文件手动解 → 重跑 finish  | 解不开 → 停手, 保留 worktree, 报用户裁    |
| 悬挂 subagent `TaskStop` 关不掉 | 重试 `TaskStop`                | 仍在 → 停手, 禁 archive (未闭环)          |

## 反例 (命中 = 流程错误)

- main 亲跑收尾勘察 (应派 `skein-finisher`)。
- finisher 自己改码 / 跑 sediment (勘察只读, sediment 归 memorier)。
- sediment 判定不输出 trace (默默跳过)。
- 留悬挂 subagent 就 finish。
- 未 archive 宣告 Done。
