---
name: git-rebase
description: 把当前分支 rebase 到指定源分支。强制先建备份分支保护(不可逆兜底),rebase 前 fetch 确保用源分支的远端最新版为基,冲突半自动解决(当前分支有实质改动的以当前为准、否则以源分支为准),拿不准时停下用 AskUserQuestion 问用户、绝不自主决定。触发词:「rebase 到 X」「变基到 X」「把分支基于 X 重放」。

argument-hint: "<源分支> [--onto <base>]"
---

# git-rebase — 不可逆兜底的安全变基

**不可逆 (irreversible)**:rebase 改写历史,一旦推远端或备份被删就收不回,是本 skill 的头号性质。三条硬规都是为它兜底:必建备份分支(唯一能撤销的退路)、必用源分支远端最新版(避免把陈旧 base 不可逆地烧进历史)、冲突拿不准必停问(猜错即不可逆丢代码)。

## 🔴 硬规(不可逆兜底,违反即失效不可跳)

1. **必建备份分支**。rebase 开始前 `git branch backup/<当前分支>-<时间戳>`,任何情况不跳过——这是 rebase 唯一的撤销退路。
2. **必用源分支远端最新版**。rebase 前 `git fetch`,以 `origin/<源分支>` 为 base,不用本地陈旧副本(陈旧 base 重放后同样不可逆)。
3. **冲突拿不准必停问**。两边都实质改同一逻辑 → 🔴 STOP + AskUserQuestion,不自主猜选一边(猜错即不可逆丢代码)。

## 工作流

### 1. 取参数 + 前置检查

```bash
SRC=<源分支>                       # 缺省 → 报错要求用户显式指定,不代入 main/master 默认值
CUR=$(git branch --show-current)
git status --porcelain             # 必须干净;脏则先 git-commit 或 git stash(记下,rebase 后 pop)
```
✅ 完成判据:`SRC` 非空且 `git status --porcelain` 无输出(或脏改动已 commit/stash 掉)。

### 2. 🔴 建备份分支(硬规 1)

```bash
git branch "backup/${CUR}-$(date +%Y%m%d-%H%M%S)"
```

回显备份分支名。可选开 rerere 记住冲突解法(见 [references/conflict-resolution.md](references/conflict-resolution.md) §rerere)。

✅ 完成判据:`git branch` 退出码 0 且备份分支名已回显;失败(如重名)→ 按失败处理表重试,仍败则 STOP,不进入第 3 步。

### 3. 拉源分支远端最新 + 执行

```bash
git fetch origin "$SRC"
git rebase "origin/$SRC"
```
✅ 完成判据:`git fetch` 退出码 0;`git rebase` 已跑完 —— 无冲突则直接进第 5 步,有冲突转第 4 步。

### 4. 冲突循环(半自动)

每个冲突文件按下表判定。**反转 (inversion)**:rebase 下 `--ours`/`--theirs` 与 merge 指向相反的分支,是两个 skill 间最易错的判定,查表别凭记忆。rebase 里 `--ours`=源分支/base(newbase)、`--theirs`=当前分支被重放的提交;merge 方向相反,见 [git-merge 详表](../git-merge/references/conflict-resolution.md)。

| 情形 | 语义 | 命令(rebase 语境) |
| --- | --- | --- |
| 该文件只有**当前分支**动过 | 以当前分支为准 | `git checkout --theirs <file>` ← theirs=当前分支被重放的提交 |
| 该文件只有**源分支**动过 | 以源分支为准 | `git checkout --ours <file>` ← ours=源分支/base(newbase) |
| **两边都实质改**同一逻辑 | 拿不准 | 🔴 STOP,AskUserQuestion 列冲突 hunk 让用户裁,不自主 |

判定「有实质改动」:`git log origin/$SRC..<backup 分支> -- <file>` 看当前分支侧是否有针对该文件的提交(空=只源分支动过)。方向无关的判据骨架(前置检查/实质改动判据/冲突循环步骤)+ `-s ours` 剧毒警告单一真值源见 [git-merge 的 references/conflict-resolution.md](../git-merge/references/conflict-resolution.md) §core / §poison;rebase 侧的反转表本侧半见 [references/conflict-resolution.md](references/conflict-resolution.md)。

解完一个文件:
```bash
git add <file>
git rebase --continue      # 全部解完后
```
`git add` 前用 `git diff --check` 确认文件内无残留 `<<<<<<<`/`=======`/`>>>>>>>` 标记。

✅ 完成判据:全部冲突文件均已判定并 `add`,无残留冲突标记,`git rebase --continue` 已跑完(rebase 状态结束,回到分支正常态)。

### 5. 完成

```bash
git log --oneline -5       # 确认重放结果
```

回显:rebase 完成 + **备份分支名(验证无误后可 `git branch -D` 删,未验证前保留)**。已推远端的分支需 `git push --force-with-lease`(仅当远端仍是你上次见到的状态才覆盖;🔴 禁裸 `--force`,配套做法见 [references/recovery.md](references/recovery.md) §push)。

✅ 完成判据:`git log --oneline -5` 显示预期的重放结果,`git status --porcelain` 干净,备份分支仍存在(未删)。

## 失败处理(触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 建备份分支失败(重名) | 时间戳加秒/加 `-2` 重试 | 建不成 → STOP,没有备份就不 rebase |
| rebase 冲突拿不准 | 🔴 STOP + AskUserQuestion 列 hunk | 用户也不确定 → `git rebase --abort` 回原状,保留备份,报「需人工介入」 |
| `--continue` 报「no changes」 | 该文件应为空提交 → `git rebase --skip` | skip 后仍乱 → abort 恢复 |
| 重放中途想放弃 | `git rebase --abort`(回到 rebase 前) | abort 也异常 → `git reset --hard backup/<...>` 用备份恢复 |
| 已 rebase 完才发现选错 | `git reset --hard backup/<...>` 回退 | 备份也删了 → `git reflog` 找 rebase 前 HEAD(见 recovery) |
| 当前分支已推远端且被他人共享 | 告知 rebase 改历史会致他人 `--force` 后冲突,确认后再继续 | 用户不接受 → 改用 git-merge |
| fetch 失败(网络/权限) | 重试 fetch;确认 remote 名正确 | 拉不到 → STOP,用源分支远端最新版而非本地陈旧副本(硬规 2) |

## 诚实边界

- **半自动非全自动**:只有「单边改动」能机器判定并 checkout;两边都改的语义冲突必须人工。
- 强制备份只护本地历史;已推远端且他人已拉的分支,rebase 后仍需 `--force-with-lease` 推,可能影响协作者(会告知)。
- 不处理 rebase `-i` 交互式(改提交顺序/squash),那是另一场景。
- 「实质改动」判定基于提交历史,极端场景(同 commit 改多文件)可能误判 → 落到「拿不准」分支停问。
