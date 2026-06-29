---
name: trellisx-cleanup
description: '批量收尾 —— 一次清理/归档/收尾**全部**已完成 task。三件事: ① 清理所有已合并的 worktree ② 归档所有已完成的任务 ③ 清理 task.md 看板的已完成行。完成判定 = completed ∪ merged (并集), 当前 active task 永不纳入。**强制 dry-run → 用户确认 → --apply 执行** 三段护栏, worktree 销毁沿用安全判据 (脏/未合并自动保留, 不丢提交)'
when_to_use: '用户要"批量清理 / 一次性归档 / 收尾所有已完成任务 / 清理所有 worktree / 清空看板已完成行"时; 多个 task 已完成堆积需统一收口时; 项目有遗留的已合并 worktree / 看板膨胀需清理时。单个 task 收尾用 finish (本 skill 是其批量层)'
user-invocable: true
argument-hint: '[--apply] [--days N]'
arguments: '[缺省 = dry-run 只报告; --apply = 执行; --days N = 看板已完成行清理阈值, 默认 0 全删]'
---

# trellisx-cleanup — 批量收尾全部已完成 task

trellis 逐个 `task.py finish/archive` 收尾单任务; 多个 task 完成后堆积 (残留已合并 worktree、看板已完成行膨胀、未归档 completed 任务) 时缺**批量收口**。本 skill 一次清理三类残留, **复用** `trellisx-finish.py` (单任务全链) + `trellisx-taskmd.py` (看板) + worktree 安全销毁判据, **不重写 git 逻辑**。

## 做三件事 (用户三需求)

| # | 需求 | 实现 |
| --- | --- | --- |
| ① | 清理所有已完成的 worktree | 已合并+干净的 worktree 销毁 (沿用 `trellisx-worktree.py` archive 安全判据: `merge-base --is-ancestor`); **脏/未合并自动保留, 禁丢提交** |
| ② | 归档所有已完成的任务 | 逐个 `trellisx-finish.py --task <tid>` (commit→merge --no-ff→archive→销 worktree, **逐个提交**, 幂等可重入) |
| ③ | 清理已完成任务的 task.md | `trellisx-taskmd.py cleanup --days N` 删看板"已完成"行 (默认 `--days 0` 全删) |

## 完成判定 = completed ∪ merged (并集)

- **completed**: `.trellis/tasks/<tid>/task.json` 的 `status == "completed"` 且未归档。
- **merged**: worktree 干净 **且** 分支已 merge 回主分支 (即使 task.json 未置 completed 的孤儿 worktree 也清)。
- **当前 active task 永不纳入** (`task.py current` 命中的 tid 排除, 防销正在用的)。

## 🛑 强制三段护栏 (破坏性操作, 不可跳)

> 销毁 worktree + 归档任务 + 删看板行 = **破坏性**。必须走: **dry-run 报告 → AskUserQuestion 确认 → --apply 执行**。禁跳过确认直接 `--apply`, 禁用"建议清理"软措辞替代确认工具。

1. **dry-run (默认, 只读)**: 不带 `--apply` 跑, 打印将归档的 task、将销的 worktree、将保留的 worktree (脏/未合并)、将删的看板行阈值。**不改任何状态**。
   ```bash
   python3 .trellis/scripts/trellisx-cleanup.py
   ```
2. **确认**: 把 dry-run 清单经 **AskUserQuestion 工具**呈给用户 (列出 tid + worktree 路径), 用户批准才进第 3 步。
3. **执行**: 用户确认后跑 `--apply`。
   ```bash
   python3 .trellis/scripts/trellisx-cleanup.py --apply [--days 0] [--message "<提交消息>"]
   ```

## 执行后 AI 必做 (脚本做不到)

- **关闭悬挂 Workflow / 后台 Task**: 脚本只做 git/看板 (确定性), 关闭悬挂的 Claude Code Workflow / 后台 agent 是 AI 层职责 —— 收尾前 `TaskList` 查 → `TaskStop` 逐个关。
- **核对失败项**: 某 task 收尾非 0 退出 (多为合并冲突) → 脚本报告并继续其余、最终非 0 退出。AI MUST 检失败清单, 逐个转手动解冲突后重跑, 禁当成功。
- **保留项跟进**: 脏/未合并 worktree 被保留 → 提示用户先提交/合并再重跑清理。

## 边界

- 只做 git (worktree/分支/merge/archive) + 看板 (task.md) 的**确定性**操作; 不改源码、不碰 task.json 真值 (经 task.py archive 间接归档)。
- worktree 销毁**完全沿用** `trellisx-worktree.py` 既有安全判据, **不新增**强删路径 —— 脏树或分支未合并一律保留。
- 脚本缺失 (项目未跑 apply) → 提示先 `/trellisx-apply` 复制脚本到 `.trellis/scripts/`。
- 与 trellisx-workspace 关系: workspace 维护**单个**任务看板行 (读写投影); 本 skill 是**批量执行**层 (归档+销 worktree+清看板)。

## 反例黑名单 (禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 跳过 dry-run 直接 `--apply` | 破坏性操作未经确认 = 可能误销未合并 worktree | 先 dry-run → AskUserQuestion 确认 → 再 --apply |
| 2 | 用纯文本"我将清理…"代替 AskUserQuestion | 确认必须用专门工具 | 经 AskUserQuestion 列 tid + worktree 路径 |
| 3 | 把当前 active task 一起归档 | 销正在用的 worktree = 流程错误 | 脚本已排除 active; 禁手动绕过 |
| 4 | 收尾失败 (冲突) 当成功继续 | 漏合丢提交 | 检失败清单, 转手动解冲突后重跑 |
| 5 | 强删脏/未合并 worktree | 丢未提交/未合并改动 | 保留它们, 先提交/合并再清理 |
