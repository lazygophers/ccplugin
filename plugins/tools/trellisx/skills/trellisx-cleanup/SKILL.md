---
name: trellisx-cleanup
description: '🧹 批量收尾 —— 一次清理/归档/收尾**全部**已完成 task。三件事: ① 清理所有已合并的 worktree ② 归档所有已完成的任务 ③ 清理 task.md 看板的已完成行。完成判定 = completed ∪ merged (并集), 当前 active task 永不纳入。**强制 dry-run → 用户确认 → --apply 执行** 三段护栏, worktree 销毁沿用安全判据 (脏/未合并自动保留, 不丢提交)'

disable-model-invocation: true
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

- **核对失败项**: 某 task 收尾非 0 退出 (多为合并冲突) → 脚本报告并继续其余、最终非 0 退出。AI MUST 检失败清单, 逐个转手动解冲突后重跑, 禁当成功。
- **保留项跟进**: 脏/未合并 worktree 被保留 → 提示用户先提交/合并再重跑清理。

## 边界

- 只做 git (worktree/分支/merge/archive) + 看板 (task.md) 的**确定性**操作; 不改源码、不碰 task.json 真值 (经 task.py archive 间接归档)。
- **只处理已完成** (completed ∪ merged); **禁碰 in_progress / 悬挂后台 Task** —— 那些仍在执行, 归 trellisx-flow 收尾 (AI 层 `TaskList` → `TaskStop`), 不属本批量清理层。
- worktree 销毁**完全沿用** `trellisx-worktree.py` 既有安全判据, **不新增**强删路径 —— 脏树或分支未合并一律保留。
- 脚本缺失 (项目未跑 apply) → 提示先 `/trellisx-apply` 复制脚本到 `.trellis/scripts/`。
- 与 trellisx-workspace 关系: workspace 维护**单个**任务看板行 (读写投影); 本 skill 是**批量执行**层 (归档+销 worktree+清看板)。

## 失败模式 (触发 → 一线修复 → 仍失败兜底)

> 与下方「反例黑名单」区别: 黑名单是**不要做什么**, 本表是 **批量收尾跑起来卡壳时怎么办**。

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 某 task 收尾非 0 退出 (多为合并冲突) | 检脚本失败清单, 逐个转手动解冲突后 `--apply` 重跑 (幂等可重入) | 反复冲突解不开 → 🛑 STOP 该 task, 报给用户裁定 (改代码 / 弃分支), 禁当成功继续 |
| 脏 / 未合并 worktree 被自动保留 | 提示用户先提交或合并该分支, 再重跑清理 | 用户明确弃这些改动 → 仍不强删, 让用户手动 `git worktree remove --force`, 本 skill 不代执行破坏性删 |
| dry-run 与 --apply 间状态漂移 (期间新完成/新合并 task) | 重跑 dry-run 刷新清单再经 AskUserQuestion 确认 | 清单仍对不上 → 缩小范围逐 task `finish` 收尾, 禁按旧清单盲 apply |
| `--apply` 部分成功、部分失败 | 已归档的不回滚 (幂等), 仅对失败 tid 重跑 | 重跑仍失败 → 列残留 tid 给用户, 标「待手动收尾」 |
| 脚本不存在 (项目未跑 apply) | 提示用户先 `/trellisx-apply` 复制脚本到 `.trellis/scripts/` | 用户暂不跑 → 本批量层不可用, 降级逐个 `task.py finish` 手工收尾 |

## 反例黑名单 (禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 跳过 dry-run 直接 `--apply` | 破坏性操作未经确认 = 可能误销未合并 worktree | 先 dry-run → AskUserQuestion 确认 → 再 --apply |
| 2 | 用纯文本"我将清理…"代替 AskUserQuestion | 确认必须用专门工具 | 经 AskUserQuestion 列 tid + worktree 路径 |
| 3 | 把当前 active task 一起归档 | 销正在用的 worktree = 流程错误 | 脚本已排除 active; 禁手动绕过 |
| 4 | 收尾失败 (冲突) 当成功继续 | 漏合丢提交 | 检失败清单, 转手动解冲突后重跑 |
| 5 | 强删脏/未合并 worktree | 丢未提交/未合并改动 | 保留它们, 先提交/合并再清理 |
