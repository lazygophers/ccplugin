# for-finish — finish 阶段作业手册

check 全绿后的**收尾门**。验收/完成度核对已在 check 阶段做完, **finish 只做收尾** (勘察改动+悬挂 → 合并 → 销 worktree → 标记完成 → 异步 spec), 不重做验收。**未 finish 闭环 (标记完成) = 未闭环, 禁宣告 Done。** 归档 = 保留期 (默认 7 天) 到期后 `_autoclean` 自动目录迁移, 非 finish 步、非 Done 门。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=finish` (check 全绿后, 派 skein-finisher 勘察 + skein finish 闭环 + 异步 sediment), 或 flow 全闭环内 check 放行后自动进入。
- **前置硬门 = check 全绿** — check 阶段完成判据未勾满禁进 finish, 详见 [for-check.md](for-check.md) 完成判据。

## 载体分工

| 动作 | 谁 | 产出 |
|---|---|---|
| 收尾勘察 | 派 `skein-finisher` (只读, 合并前清障) | diff 摘要 + 悬挂清单 (不做验收核对) |
| 清悬挂 + 生命周期 | main 同步跑 (不算实质工作) | `TaskList`/`TaskStop` + `skein finish` (commit→merge→销 worktree→标记完成) |
| sediment 沉淀 | **异步 fire-and-forget** 派 `skein-specer` (finish 闭环后) | specer 自主跑判定门 + `skein-spec sediment` 写盘 + reindex (main 不等回传) |

## 流程步骤

1. **收尾勘察 (合并前清障)** — 输入 `task id + 工作目录` → 派 `skein-finisher` → 出口: diff 摘要 + 悬挂清单。**只勘察改动+悬挂残留供干净合并, 不做验收/subtask 完成度核对 (那是 check 的职责, 到此已全绿)**。悬挂残留 (调试码/临时文件) 由 main 清理后再合并。
2. **清悬挂** — `TaskList` 查残留 subagent / 后台任务 → `TaskStop` 关闭。未关 = 未闭环, 禁 finish。
3. **标记完成 (闭环)** — `skein finish <id>` (commit→merge→销 worktree→标记完成, status=已完成)。**finish 到此即闭环, 禁为 sediment 阻塞**。归档不在此步 (保留期后自动)。
4. **sediment (异步 fire-and-forget)** — finish 闭环后异步派 `skein-specer`, main 不等回传即结束回合。细节见 [sediment-protocol.md](sediment-protocol.md)。
5. **auto-fix 双保险 (异步 fire-and-forget)** — sediment 派出后, main 检测 `.skein/spec/.pending-fix` 标记 (Stop hook 回合结束若检出 spec 问题所写, 详见 skein-spec auto-fix 模式)。标记存在 → 异步 bg 派 `skein-specer` 跑 `skein-spec maintain --apply` 全自动修, 与 sediment 同批 fire-and-forget。标记不存在 → 跳过。

## 完成判据

- [ ] finisher 勘察回传, 悬挂残留已清 (调试码/临时文件)
- [ ] 悬挂 subagent 全 `TaskStop` 关闭
- [ ] `skein finish` 成功 (commit→merge→销 worktree→标记完成)
- [ ] sediment 已异步派出 (不等回传)
- [ ] `.pending-fix` 标记已检测 (有则 auto-fix bg 已派, 无则跳过)

## 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| finisher 报悬挂残留 | main 清理后再合并 | 清不掉 → 停手, 报用户裁 |
| `skein finish` merge 冲突 | `git status` 列冲突文件 → 读冲突双方 commit 理解各自 intent → 逐文件手动解 → 重跑 finish | 解不开 → 停手, 保留 worktree, 报用户裁 |
| auto_commit=false 且有未提交改动 → finish 拒绝 | 提示用户手动 `git commit` 后重跑 finish | 用户不提交 → 停手, 禁 --force 强删 (会丢改动) |
| 悬挂 subagent `TaskStop` 关不掉 | 重试 `TaskStop` | 仍在 → 停手, 禁 finish (未闭环) |

## 延伸引用

- [sediment-protocol.md](sediment-protocol.md) — sediment 异步派出细节
- [worktree-convention.md](worktree-convention.md) — 工作目录约定 (task worktree 字段真值)
