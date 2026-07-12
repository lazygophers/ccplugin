---
name: skein-clean
description: 主动清理 (仅用户显式调用)。归档完成 task (保留期外) + 清残留孤儿 worktree / 悬挂 skein/* 分支 — 安全清扫 (只清已完成/已合并的), 存疑先报用户。入参 = 保留天数
disable-model-invocation: true
user-invocable: true
argument-hint: "[保留天数]"
arguments: "[保留天数]"
effort: low
---

# skein-clean — 主动清理

**仅用户显式调用** (`disable-model-invocation`)。两件事:

1. **归档完成 task** — `finish` 后完成 task **不立即归档**, 默认留看板 `retain_days` 天 (config.yaml, 默认 7); 超期由脚本在下次生命周期变更时**自动**归档。本 skill 让用户**主动提前归档**。
2. **清残留孤儿** — finish 中断 / 手动改动留下的孤儿 worktree / 悬挂分支。

> 安全第一: 只清「已完成/已合并」的。**未 finish 的 active task、未合并的分支一律不删** (可能有未落地改动)。**存疑一律先报用户裁定, 禁自行删。**

## 入参: 保留天数

调用形如 `/skein-clean [保留天数]`。

- **省略** → 用 config.yaml 的 `retain_days` (默认 7): 归档完成超 7 天的 task。
- **`0`** → 立即归档**全部**完成 task (不留看板)。
- **`N`** → 归档完成超 N 天的 task。**只能比 config `retain_days` 更激进 (更小)**; 更大值无效 (脚本每次 `_sync` 自动按 config ceiling 归档)。

## 清扫项 (main 同步跑, 逐项查再动)

1. **归档完成 task (保留期外)** — 直接跑脚本, 它按保留期算并归档:
   ```bash
   python3 <plugin>/scripts/skein.py clean [--days <保留天数>]
   ```
   完成 task 已走完整 `finish` (已 merge/销 worktree), 归档纯移目录, 安全。

2. **孤儿 worktree** — `git worktree list` 列全部; 对每个 `.worktrees/skein-*`:
   - 对应 task 已完成/已归档 → `git worktree remove <path> --force`。
   - 对应 task 仍 active → **保留** (在用)。
   - 无对应 task 记录 → 报用户裁定 (别猜)。
   - 收尾 `git worktree prune` 清元数据。

3. **悬挂 skein/\* 分支** — `git branch --list 'skein/*'`:
   - 已合并 (`git branch --merged` 含之) 且 task 已归档 → `git branch -D`。
   - 未合并 → **保留 + 报用户** (有未落地 commit)。

> 看板无需手动刷 — `clean` 已触发 `_sync` 自动重渲染 task.md/task.html; 孤儿 worktree/分支清理不涉 task.json, 不影响看板。

> **注意**: `skein.py list` 里完成 (已完成) 却仍在 `.skein/task/` 的 task **不是异常** — 是保留期内正常状态, 别当漏归档强行 `archive`。要提前清走, 用上面的 `clean` 命令 (走保留期语义)。

## 输出

清扫报告: 归档了哪些完成 task (保留 N 天)、删了哪些 worktree/分支、**哪些存疑保留 (交用户裁)**。存疑项禁自行删。

## 反例

禁止操作与正确改法详见 references/anti-examples.md。
