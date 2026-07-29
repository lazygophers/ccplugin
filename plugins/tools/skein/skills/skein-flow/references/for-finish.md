# for-finish — finish 阶段作业手册

check 全绿后的**收尾门**。验收/完成度核对已在 check 阶段做完, **finish 只做收尾**, 不重做验收。`skein-finisher` 自主完成勘察改动+清悬挂+跑 `skein finish` 全套, main 只负责派发+读结果+失败兜底+异步 sediment。**未 finish 闭环 (标记完成) = 未闭环, 禁宣告 Done。** 归档 = 保留期 (默认 7 天) 到期后 `_autoclean` 自动目录迁移, 非 finish 步、非 Done 门。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=finish` (check 全绿后, 派 skein-finisher 收尾闭环 + 异步 sediment), 或 flow 全闭环内 check 放行后自动进入。
- **前置硬门 = check 全绿** — check 阶段完成判据未勾满禁进 finish, 详见 [for-check.md](for-check.md) 完成判据。

## 流程步骤 (main 保留项)

1. **派发 (经 `Agent` 工具派具名 subagent, 禁 teammate / team)** — 传 `task id + 工作目录` (task 的 `worktree` 字段; null=原地仓库根) → 派 `skein-finisher`。finisher 自主完成勘察改动 (git diff/status) + 清悬挂后台 task (`TaskList`/`TaskStop`) + 在仓库根跑 `skein finish <tid>` (commit→merge→销 worktree→标记完成), 全流程权威定义见 `skein-finisher.md` (agents/), 本文件不重复。
2. **读结果, 按 verdict 分流** — finisher 回传 `收尾干净 | 需处理`:
   - **收尾干净** → 已闭环 (finish 已由 finisher 自跑成功), 直接进第 3 步。
   - **需处理** → 按 `needs_main`/`dangling`/`tool_failures` 定位问题 (悬挂残留清不掉 / `skein finish` 报错 / 无改动异常), 处理后视情况重派 finisher 或人工介入, 见下方失败模式表。
3. **sediment (main 保留项, 异步 fire-and-forget)** — finish 闭环后异步派 `skein-specer`, main 不等回传即结束回合。细节见 [sediment-protocol.md](sediment-protocol.md)。
4. **auto-fix 双保险 (main 保留项, 异步 fire-and-forget)** — sediment 派出后, main 检测 `.skein/spec/.pending-fix` 标记 (Stop hook 回合结束若检出 spec 问题所写, 详见 skein-spec auto-fix 模式)。标记存在 → 异步 bg 派 `skein-specer` 跑 `skein-spec maintain --apply` 全自动修, 与 sediment 同批 fire-and-forget。标记不存在 → 跳过。

## 完成判据

- [ ] finisher 回传 verdict=收尾干净 (或「需处理」已按失败模式表处理完并重派确认干净)
- [ ] `skein finish` 已成功 (finisher 自跑, commit→merge→销 worktree→标记完成)
- [ ] sediment 已异步派出 (不等回传)
- [ ] `.pending-fix` 标记已检测 (有则 auto-fix bg 已派, 无则跳过)

## 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| finisher 报悬挂残留清不掉 (无 Write/Edit, 只能列不能删) | main 直接清理 (git clean/rm 该文件) 后重派 finisher | 清不掉 → 停手, 报用户裁 |
| finisher 报 `skein finish` merge 冲突 | `git status` 列冲突文件 → 读冲突双方 commit 理解各自 intent → 逐文件手动解 → 重派 finisher 重跑 | 解不开 → 停手, 保留 worktree, 报用户裁 |
| 原地模式 (use_worktree=false) + auto_commit=false, finish 后改动仍在工作区 | 这是设计行为 (交用户自管), 汇报时提示用户自行 `git commit` | — (worktree 模式必自动 commit, 不会走到这) |
| finisher 报悬挂 subagent `TaskStop` 关不掉 | 重派 finisher 重试 | 仍在 → 停手, 禁 finish (未闭环) |
| finisher 报「无改动, 疑误派 finish」 | main 核实 task 是否真无产出 | 确认误派 → 停手排查上游, 不强行 finish |

## 延伸引用

- `skein-finisher.md` (agents/) — 收尾 agent 自身工作流权威定义 (勘察/清悬挂/跑 finish), 本文件不重复
- [sediment-protocol.md](sediment-protocol.md) — sediment 异步派出细节
- [worktree-convention.md](worktree-convention.md) — 工作目录约定 (task worktree 字段真值)
