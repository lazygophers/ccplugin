# 回退 —— git-merge 详表

主流程见 [../SKILL.md](../SKILL.md)。merge 可回退,故不强制建备份分支(与 git-rebase 不同)。

## §abort 回退手段(按阶段)

| 阶段 | 恢复命令 |
| --- | --- |
| merge 有冲突、尚未 commit,想放弃 | `git merge --abort`(回到 merge 前工作区,最干净) |
| merge 已生成合并提交,想撤销 | `git reset --hard HEAD~1`(回退到合并前;**确认后再执行**) |
| 已 push 的合并想撤 | `git revert -m 1 <merge-commit>`(生成反向提交,不改历史,协作友好) |
| reset 后又想找回 | `git reflog` 找合并提交 sha,`git reset --hard <sha>` |

## §choice reset vs revert(已 push 场景)

| 手段 | 改历史? | 适用 |
| --- | --- | --- |
| `git reset --hard HEAD~1` | 是 | 合并**未 push**、仅本地 → 干净删除 |
| `git revert -m 1 <merge>` | 否(加新提交) | 合并**已 push**、他人可能已拉 → 用 revert,别 reset 后强推 |

`-m 1` 指定保留第一父(通常是当前分支),撤掉从源分支合入的改动。已 push 的合并用 `reset --hard` + 强推会破坏他人历史,优先 `revert`。

## §ff fast-forward 说明

- 当前分支落后源分支且无分叉时,`git merge` 默认 fast-forward(不产生合并提交,只移动指针)。
- 想强制留合并记录:`git merge --no-ff origin/$SRC`。
- 用户明确要线性历史 → 保持默认 ff,或改用 git-rebase。
