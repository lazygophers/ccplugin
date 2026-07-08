---
name: git-merge
description: 把指定源分支 merge 进当前分支。merge 前 fetch 确保用源分支的远端最新版,冲突半自动解决(当前分支有实质改动的以当前为准、否则以源分支为准),拿不准时停下用 AskUserQuestion 问用户、绝不自主决定。保留合并提交历史(不改写历史,故不需备份分支)。触发词:「merge 分支 X」「合并 X 进来」「把 X 并入当前分支」。
when_to_use: '要把某源分支合并进当前分支、保留分叉历史时。想要线性历史用 git-rebase。'
argument-hint: "<源分支> [--no-ff]"
arguments: [源分支 (必填, 要合并进当前分支的分支), --no-ff (可选, 强制保留合并提交)]
---

# git-merge — 半自动合并

merge 保留历史、可回退(`git merge --abort` / `git reset`),比 rebase 安全。铁律:**拉源分支最新 → 半自动解冲突 → 拿不准必停问**。

## 🔴 硬规

1. **必用源分支远端最新版**。merge 前 `git fetch`,合 `origin/<源分支>`,禁用本地陈旧副本。
2. **冲突拿不准必停问**。两边都实质改同一逻辑 → 🔴 STOP + AskUserQuestion,禁自主猜选一边。
3. **不自动 push**。merge 完成留在本地,推送归用户指令。

## 工作流

### 1. 取参数 + 前置检查

```bash
SRC=<源分支>                       # 缺省 → 报错要求指定,不猜
CUR=$(git branch --show-current)
git status --porcelain             # 必须干净;脏 → 先 git-commit 或 git stash(记下,merge 后 pop)
```

### 2. 拉源分支远端最新 + 执行

```bash
git fetch origin "$SRC"
git merge "origin/$SRC"
```

### 3. 冲突循环(半自动)

每个冲突文件按下表判定。⚠️ **merge 中 `--ours`=当前分支、`--theirs`=被合入的源分支**(与 rebase 相反):

| 情形 | 语义 | 命令(merge 语境) |
| --- | --- | --- |
| 该文件只有**当前分支**动过 | 以当前分支为准 | `git checkout --ours <file>` ← ours=当前分支 |
| 该文件只有**源分支**动过 | 以源分支为准 | `git checkout --theirs <file>` ← theirs=源分支 |
| **两边都实质改**同一逻辑 | 拿不准 | 🔴 STOP,AskUserQuestion 列冲突 hunk 让用户裁,禁自主 |

判定「有实质改动」:`git log origin/$SRC..HEAD -- <file>` 看当前分支侧是否有针对该文件的提交(空=只源分支动过)。方向记忆表 + `-s ours` 剧毒警告 + `-X` 用法见 [references/conflict-resolution.md](references/conflict-resolution.md)。

🔴 **用户说「都以当前为准」≠ 全盘 `--ours` / `-X ours`**:仍须逐文件判定。两边都实质改同一文件时,盲选当前会**静默丢弃源分支改动**;这类文件照样 STOP 问用户,别被一句「以当前为准」诱导跳过判定。更禁 `git merge -s ours`(丢弃源分支全部改动,只留假合并记录)。

解完一个文件:
```bash
git add <file>
git commit --no-edit       # 全部解完后,生成合并提交
```
⚠️ `git add` 前确认文件内无残留 `<<<<<<<` / `=======` / `>>>>>>>` 标记。

### 4. 完成

```bash
git log --oneline --graph -5   # 确认合并结果
```

回显:merge 完成 + 合并提交 hash。回退手段见 [references/recovery.md](references/recovery.md)。

## 失败处理(触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| merge 冲突拿不准 | 🔴 STOP + AskUserQuestion 列 hunk | 用户也不确定 → `git merge --abort` 回原状,报「需人工介入」 |
| 中途想放弃 | `git merge --abort`(回到 merge 前) | 已 commit → `git reset --hard HEAD~1`(确认后) |
| fast-forward 非预期 | 想留合并记录 → `git merge --no-ff` 重来 | 用户要 ff → 保持默认 |
| fetch 失败(网络/权限) | 重试 fetch;确认 remote 名正确 | 拉不到 → STOP,不拿本地陈旧分支 merge(违硬规 1) |
| 源分支不存在 | 列远端分支让用户确认名 | 名确实错 → STOP 待正确分支名 |
| `add` 后仍见冲突标记 | 重新编辑去掉 `<<<<`/`====`/`>>>>` 再 add | 拿不准该留哪边 → STOP 问用户 |

## 反例黑名单(禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 拿不准的冲突自主选一边 | 猜错静默丢代码 | STOP 问用户 |
| 2 | 把 merge 的 `--theirs` 当当前分支 | 方向反了(与 rebase 相反) | 查表:merge 中 ours=当前 |
| 3 | 用本地陈旧 `<源分支>` 而非 `origin/<源分支>` | 合入旧代码 | 先 fetch 用 origin/ |
| 4 | merge 后自动 push | 越权 | 只 merge,push 另说 |
| 5 | 冲突文件 `git add` 前没检查残留标记 | `<<<<<<<` 混入提交 | add 前确认无冲突标记 |
| 6 | `git merge -s ours <源>` 想「以我为准」 | 剧毒:丢弃源分支全部改动,只留合并记录假象 | 用 `-X ours`(仅冲突点);见 reference |

## 诚实边界

- **半自动非全自动**:只有「单边改动」能机器判定并 checkout;两边都改的语义冲突必须人工。
- merge 可回退(`--abort`/`reset`),故不像 git-rebase 强制建备份分支;但已 push 的合并 reset 仍影响协作者。
- 不处理 octopus merge(多分支一次并)、不处理 subtree/submodule merge。
- 「实质改动」判定基于提交历史,极端场景可能误判 → 落到「拿不准」分支停问。
- ⚠️ `--ours`/`--theirs` 方向与 git-rebase **正好相反**,跨 skill 操作勿混。
