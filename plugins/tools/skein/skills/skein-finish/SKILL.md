---
name: skein-finish
description: task finish 阶段收尾编排。check 全绿后使用 — 派 skein-finisher 做收尾勘察 (diff 摘要 + subtask 完成核对 + 悬挂清单), 委托 skein-memory 走 sediment 判定门沉淀学习, 清理悬挂 subagent/后台任务, 再 skein.py finish (commit→merge→archive→销 worktree)。被 skein-flow finish 委托
user-invocable: false
argument-hint: "[task_id]"
arguments: "[task_id]"
model: haiku
effort: medium
---

# skein-finish — 收尾闭环门

check 全绿后、archive 前的**收尾门**。收尾勘察派 `skein-finisher`, sediment 沉淀委托 `skein-memory` (派 `skein-memorier`), 清理与生命周期脚本 main 同步跑。🛑 **未 archive = 未闭环, 禁宣告 Done。**

## 载体

- **收尾勘察** → 派 `skein-finisher` (只读, 读 git diff, 回传收尾摘要 + subtask 完成核对 + 悬挂清单)。
- **sediment 沉淀** → 委托 `skein-memory` skill (其派 `skein-memorier` 产草案), main 做 AskUserQuestion 审批 + `memory.py sediment` 写盘。
- **清理 + 生命周期脚本** → main 同步跑 (`TaskList`/`TaskStop` 关悬挂, `skein.py finish`), 不派 subagent、不算实质工作。

## 流程

1. **收尾勘察** — 派 `skein-finisher`: 传 Active task id + worktree 路径。回传 diff 摘要 + subtask 逐条完成核对 + 悬挂后台任务清单。未完成 subtask / 未满足验收 → 退回 exec 或 check, 不放行 finish。
2. **sediment 判定门** — 委托 `skein-memory` sediment (判定见 `skein-memory` skill): main 把 exec 各 subagent 的回传摘要 (含 `SPEC:` 标记) 连同 diff 传给 `skein-memorier`, 由它跑判定门 checklist 产候选规则 (core/recall/drop 分层草案) → main 逐项输出 trace → `AskUserQuestion` 审批 → `memory.py sediment` 写盘 + reindex。无增量则跳过 (禁硬凑)。
3. **清理悬挂 🔴 CHECKPOINT** — `TaskList` 查残留 subagent / 后台任务, `TaskStop` 关闭。未关 = 未闭环, 禁 finish。
4. **archive** — `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py finish <id>` (commit→merge→archive→销 worktree)。

## 反例

违反上文即流程错误: main 亲跑收尾勘察 (应派 skein-finisher) / finisher 自己改码或跑 sediment (勘察只读, sediment 归 skein-memorier) / sediment 判定不输出 trace (默默跳过) / 留悬挂 subagent 就 finish / 未 archive 宣告 Done。
