---
name: git-rebase
description: 把当前分支 rebase 到指定源分支。强制先建备份分支保护(不可逆兜底),rebase 前 fetch 确保用源分支的远端最新版为基,冲突半自动解决(当前分支有实质改动的以当前为准、否则以源分支为准),拿不准时停下用 AskUserQuestion 问用户、绝不自主决定。触发词:「rebase 到 X」「变基到 X」「把分支基于 X 重放」。
when_to_use: '要把当前分支线性变基到某源分支最新时。需保留合并历史用 git-merge。'
argument-hint: "<源分支> [--onto <base>]"
arguments: [源分支 (必填, rebase 的目标基), base (可选, --onto 指定新基点)]
---

# git-rebase — 带备份的安全变基

rebase 改写历史、不可逆。铁律:**先备份 → 拉源分支最新 → 半自动解冲突 → 拿不准必停问**。

## 🔴 硬规(违反即失效,不可跳)

1. **必建备份分支**。rebase 开始前 `git branch backup/<当前分支>-<时间戳>`。用户强制要求,任何情况不跳过。
2. **必用源分支远端最新版**。rebase 前 `git fetch`,以 `origin/<源分支>` 为 base,禁用本地陈旧副本。
3. **冲突拿不准必停问**。两边都实质改同一逻辑 → 🔴 STOP + AskUserQuestion,禁自主猜选一边(不可逆,猜错丢代码)。

## 工作流

### 1. 取参数 + 前置检查

```bash
SRC=<源分支>                       # 缺省 → 报错要求指定,不猜(禁默认 main/master)
CUR=$(git branch --show-current)
git status --porcelain             # 必须干净;脏 → 先 git-commit 或 git stash(记下,rebase 后 pop)
```

### 2. 🔴 建备份分支(硬规 1)

```bash
git branch "backup/${CUR}-$(date +%Y%m%d-%H%M%S)"
```

回显备份分支名。**这一步失败则整个流程 STOP**(无备份不 rebase)。可选开 rerere 记住冲突解法(见 [references/conflict-resolution.md](references/conflict-resolution.md) §rerere)。

### 3. 拉源分支远端最新 + 执行

```bash
git fetch origin "$SRC"
git rebase "origin/$SRC"
```

### 4. 冲突循环(半自动)

每个冲突文件按下表判定。⚠️ **rebase 中 `--ours`/`--theirs` 与直觉相反**(HEAD 是被 replay 到的 base=源分支):

| 情形 | 语义 | 命令(rebase 语境) |
| --- | --- | --- |
| 该文件只有**当前分支**动过 | 以当前分支为准 | `git checkout --theirs <file>` ← theirs=当前分支的提交 |
| 该文件只有**源分支**动过 | 以源分支为准 | `git checkout --ours <file>` ← ours=源分支/base |
| **两边都实质改**同一逻辑 | 拿不准 | 🔴 STOP,AskUserQuestion 列冲突 hunk 让用户裁,禁自主 |

判定「有实质改动」:`git log origin/$SRC..<backup 分支> -- <file>` 看当前分支侧是否有针对该文件的提交(空=只源分支动过)。方向记忆表 + `-s ours` 剧毒警告见 [references/conflict-resolution.md](references/conflict-resolution.md)。

解完一个文件:
```bash
git add <file>
git rebase --continue      # 全部解完后
```

### 5. 完成

```bash
git log --oneline -5       # 确认重放结果
```

回显:rebase 完成 + **备份分支名(验证无误后可 `git branch -D` 删,未验证前保留)**。已推远端的分支需 `git push --force-with-lease`(**禁裸 `--force`**,见 [references/recovery.md](references/recovery.md) §push)。

## 失败处理(触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 建备份分支失败(重名) | 时间戳加秒/加 `-2` 重试 | 建不成 → STOP,绝不无备份 rebase |
| rebase 冲突拿不准 | 🔴 STOP + AskUserQuestion 列 hunk | 用户也不确定 → `git rebase --abort` 回原状,保留备份,报「需人工介入」 |
| `--continue` 报「no changes」 | 该文件应为空提交 → `git rebase --skip` | skip 后仍乱 → abort 恢复 |
| 重放中途想放弃 | `git rebase --abort`(回到 rebase 前) | abort 也异常 → `git reset --hard backup/<...>` 用备份恢复 |
| 已 rebase 完才发现选错 | `git reset --hard backup/<...>` 回退 | 备份也删了 → `git reflog` 找 rebase 前 HEAD(见 recovery) |
| 当前分支已推远端且被他人共享 | 告知 rebase 改历史会致他人 `--force` 后冲突,确认后再继续 | 用户不接受 → 改用 git-merge |
| fetch 失败(网络/权限) | 重试 fetch;确认 remote 名正确 | 拉不到 → STOP,不拿本地陈旧分支 rebase(违硬规 2) |

## 反例黑名单(禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 跳过备份分支 | 违硬规 1,rebase 不可逆无兜底 | 必先 `git branch backup/...` |
| 2 | 拿不准的冲突自主选一边 | 猜错静默丢代码 | STOP 问用户 |
| 3 | 用本地陈旧 `<源分支>` 而非 `origin/<源分支>` | 基于旧代码变基,白干 | 先 fetch 用 origin/ |
| 4 | 把 rebase 的 `--ours` 当当前分支 | 方向反了,选错来源 | 查表:rebase 中 theirs=当前 |
| 5 | `git rebase -s ours` 想「以我为准」 | 剧毒:整分支丢弃源分支所有改动 | 用 `-X ours`(仅冲突点);见 reference |
| 6 | 已推共享分支裸 `--force` 推 | 覆盖他人提交 | `--force-with-lease` |
| 7 | 完成即删备份 | 未验证就毁兜底 | 用户确认无误后才删 |

## 诚实边界

- **半自动非全自动**:只有「单边改动」能机器判定并 checkout;两边都改的语义冲突必须人工。
- 强制备份只护本地历史;已推远端且他人已拉的分支,rebase 后仍需 `--force-with-lease` 推,可能影响协作者(会告知)。
- 不处理 rebase `-i` 交互式(改提交顺序/squash),那是另一场景。
- 「实质改动」判定基于提交历史,极端场景(同 commit 改多文件)可能误判 → 落到「拿不准」分支停问。
