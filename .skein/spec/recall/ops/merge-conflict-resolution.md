---
title: merge-conflict-resolution
category: ops
keywords: [worktree,merge,conflict,三方合并,git merge-file,theirs,ours,归因审计,静默撤销,冲突解决]
status: active
inclusion: auto
---

## worktree 分支合并三方合并 + 独有改动归因审计（禁批量 --theirs）

### 触发场景
worktree 拆分执行、多分支需合回 master，出现批量冲突（如本次 s-系列 subtask 完成后合并遇 36 处冲突）。

### 陷阱-正解
**陷阱**：图省事用 `git checkout --theirs <file>` 或类似策略批量「一律取某一方版本」解冲突。若冲突文件里混有「在分支切出后才合入 master 的独立功能」（如 board-live-refresh 的 `applyTaskChanged`/`applyTaskChangedBatch`），批量取一方会把该功能整个静默撤销；测试往往只覆盖冲突文件里的一小部分（如仅 `.py` 有测试而 `.ts/.tsx` 无），功能删除测试完全抓不到。
**正解**：
1. 合并前先跑「排除已知坏 commit 后，base..master 真正独有改动的文件清单」做归因审计，识别哪些冲突文件在分支存在期间被 master 独立修改过。
2. 对每个冲突文件用 `git merge-file <当前版本> <共同祖先> <分支版本>` 做真正的三方合并，而非批量单向取值。
3. 合并后针对被审计标记的文件，逐个确认关键函数/组件仍然存在（grep 符号名），不能只靠测试通过就放行。
