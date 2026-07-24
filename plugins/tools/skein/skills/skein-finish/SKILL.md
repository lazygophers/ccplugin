---
name: skein-finish
description: task 收尾闭环门 (被 skein-flow finish 委托, 或用户显式 "收尾/归档/闭环")。check 全绿后 (验收已 check 做完) 派 skein-finisher 只勘察改动+悬挂残留 → skein finish 闭环 (commit→merge→archive→销 worktree) → 异步派 skein-specer 跑 sediment + 检测 .pending-fix 标记双保险派 auto-fix。finish 只收尾不做验收核对。未 archive = 未闭环, 禁宣告 Done。
user-invocable: true
argument-hint: "[任务ID]"
arguments: "[任务ID]"
model: haiku
effort: medium
---

# skein-finish — 收尾闭环门

check 全绿后、archive 前的**收尾门**。验收/完成度核对已在 check 阶段做完, **finish 只做收尾** (勘察改动+悬挂 → 合并 → 销 worktree → 标记完成 → 异步 spec), 不重做验收。**未 archive = 未闭环, 禁宣告 Done。**

## 载体分工

> **工作目录 (worktree 态自适应)** — 本仓 worktree 隔离启用态: !`skein config --json 2>/dev/null | jq -r '.use_worktree' || echo unknown`。`true`=task 有 worktree, finish 走 commit→merge→销 worktree; `false`/`unknown`=task `worktree=null` 原地, finish 仅 commit (无 merge/销 worktree 步)。真值以 task 的 `worktree` 字段为准 (null=原地)。`skein finish` 脚本按此自适应, 下文"worktree"按此二读。

| 动作            | 谁                                | 产出                                             |
| --------------- | --------------------------------- | ------------------------------------------------ |
| 收尾勘察        | 派 `skein-finisher` (只读, 合并前清障) | diff 摘要 + 悬挂清单 (不做验收核对)          |
| 清悬挂 + 生命周期 | main 同步跑 (不算实质工作)        | `TaskList`/`TaskStop` + `skein finish` (commit→merge→archive→销 worktree) |
| sediment 沉淀   | **异步 fire-and-forget** 派 `skein-specer` (finish 闭环后) | memorier 自主跑判定门 + `skein-spec sediment` 写盘 + reindex (main 不等回传, finish 已闭环) |

## 流程 (每步 输入 → 动作 → 出口)

1. **收尾勘察 (合并前清障)** — 输入 `task id + 工作目录 (task 的 worktree 字段; null=原地仓库根)` → 派 `skein-finisher` → 出口: diff 摘要 + 悬挂清单。**只勘察改动+悬挂残留供干净合并, 不做验收/subtask 完成度核对 (那是 check 的职责, 到此已全绿)**。悬挂残留 (调试码/临时文件) 由 main 清理后再合并。
2. **清悬挂** — `TaskList` 查残留 subagent / 后台任务 → `TaskStop` 关闭。未关 = 未闭环, 禁 finish。
3. **archive (闭环)** — `skein finish <id>` (commit→merge→archive→销 worktree)。**finish 到此即闭环, 禁为 sediment 阻塞**。
4. **sediment (异步 fire-and-forget)** — finish 闭环后异步派 `skein-specer`, main 不等回传即结束回合。细节见 [references/sediment-protocol.md](references/sediment-protocol.md)。
5. **auto-fix 双保险 (异步 fire-and-forget)** — sediment 派出后, main 检测 `.skein/spec/.pending-fix` 标记 (Stop hook 回合结束若检出 spec 问题所写, 详见 skein-spec auto-fix 模式)。标记存在 → 异步 bg 派 `skein-specer` 跑 `skein-spec maintain --apply` 全自动修 (超预算降级 / stale·keywords重复·废弃归档 / 断链只报告), 与 sediment 同批 fire-and-forget (main 不等回传, 同路径双保险防 Stop hook 漏检)。标记不存在 → 跳过。

**完成判据 (勾满才算闭环)**:
- [ ] finisher 勘察回传, 悬挂残留已清 (调试码/临时文件)
- [ ] 悬挂 subagent 全 `TaskStop` 关闭
- [ ] `skein finish` 成功 (commit→merge→archive→销 worktree)
- [ ] sediment 已异步派出 (不等回传)
- [ ] `.pending-fix` 标记已检测 (有则 auto-fix bg 已派, 无则跳过)

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                        | 一线修复                        | 仍失败兜底                                |
| --------------------------- | ------------------------------- | ----------------------------------------- |
| finisher 报悬挂残留 (调试码/临时文件) | main 清理后再合并               | 清不掉 → 停手, 报用户裁                    |
| `skein finish` merge 冲突 | 读冲突文件手动解 → 重跑 finish  | 解不开 → 停手, 保留 worktree, 报用户裁 (5 步纪律见 [references/merge-conflict-resolution.md](references/merge-conflict-resolution.md))    |
| 悬挂 subagent `TaskStop` 关不掉 | 重试 `TaskStop`                | 仍在 → 停手, 禁 archive (未闭环)          |

## ✅ 正向配方 (命中反面=流程错误)

> 🔒 铁律: 未 archive = 未闭环, 禁宣告 Done; sediment 异步 fire-and-forget 禁阻塞 finish。

| 场景             | 正确做法 (❌ 反面)                                |
| ---------------- | ------------------------------------------------ |
| 收尾勘察         | 派 `skein-finisher` 做勘察 (❌ main 亲跑收尾勘察) |
| finisher 职责    | finisher 只读勘察改动+悬挂, 不做验收核对 (验收归 check)、sediment 归 memorier (❌ finisher 核对 subtask 完成度 / 自己改码 / 跑 sediment) |
| sediment 时序    | finish 先闭环 (archive + 销 worktree), sediment 异步 fire-and-forget 在后 (❌ sediment 阻塞 finish / 为等 memorier 回传延后 `skein finish`) |
| sediment trace   | memorier 回传到达后 main 补 output trace 供审阅 (❌ sediment 判定不输出 trace) |
| 宣告 Done        | `skein finish` archive 成功后才宣告 Done (❌ 未 archive 宣告 Done) |
