---
name: skein-clean
description: 归档清理。task finish 中断、或残留孤儿 worktree / 悬挂 skein/* 分支 / 漏归档 task 时使用 — 安全清扫 (只清已完成/已合并的), 补归档 completed task, 存疑先报用户。
---

# skein-clean — 归档清理

正常 `skein.py finish` 已自动 commit→merge→archive→销 worktree。本 skill 处理**异常残留**: finish 中断、手动改动、并行任务留下的孤儿。

> 安全第一: 只清「已完成/已合并」的残留。**未 finish 的 active task、未合并的分支一律不删** (可能有未落地改动)。**STOP: 存疑一律先报用户裁定, 禁自行删。**

## 清扫项 (main 同步跑, 逐项查再动)

1. **孤儿 worktree** — `git worktree list` 列全部; 对每个 `.worktrees/skein-*`:
   - 对应 task 已 `completed`/已归档 → `git worktree remove <path> --force`。
   - 对应 task 仍 active → **保留** (在用)。
   - 无对应 task 记录 → 报用户裁定 (别猜)。
   - 收尾 `git worktree prune` 清元数据。

2. **悬挂 skein/* 分支** — `git branch --list 'skein/*'`:
   - 已合并 (`git branch --merged` 含之) 且 task 已归档 → `git branch -D`。
   - 未合并 → **保留 + 报用户** (有未落地 commit)。

3. **漏归档 task** — `skein.py list` 里 `completed` 却仍在 `.skein/task/` (未进 archive):
   - `python3 <plugin>/scripts/skein.py archive <id>` 补归档。

4. **刷看板** — `python3 <plugin>/scripts/skein.py board` 重渲染, 确认与实际一致。

## 输出

清扫报告: 删了哪些 worktree/分支、补归档哪些 task、**哪些存疑保留 (交用户裁)**。存疑项禁自行删。

## 反例

禁止操作与正确改法详见 references/anti-examples.md。
