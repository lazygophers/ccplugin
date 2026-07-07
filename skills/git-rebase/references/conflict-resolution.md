# 冲突解决 · ours/theirs 方向 · rerere —— git-rebase 详表

主流程见 [../SKILL.md](../SKILL.md)。**rebase 的方向与 merge 相反,这是头号 footgun。**

## §direction ours/theirs 方向(rebase 语境)

rebase 的机制:切到目标(`origin/$SRC`)后,把当前分支的提交逐个 replay 上去。所以冲突时 **HEAD = 已经就位的目标分支(newbase)**,replay 中的补丁 = 你的提交。

| 标记 | 指向 | 冲突块标签 |
| --- | --- | --- |
| `--ours` / `<<<<<<< HEAD` | **源分支/目标 base**(newbase) | `HEAD` |
| `--theirs` / `>>>>>>>` | **当前分支**你正被 replay 的提交 | commit hash |

记忆:rebase 里「你」变成 theirs(客人),目标反而是 ours(主人)——因为你在往目标上「重放」。**与 merge 正好相反**(merge 里 ours=当前分支)。

### 单边判定 → 自动 checkout
```bash
# 该文件当前分支侧有没有改过?
git log origin/$SRC..<backup 分支> -- <file>
```
- 有输出(当前分支改过,源分支没实质改) → 以当前为准 → `git checkout --theirs <file>`
- 无输出(只源分支改过) → 以源分支为准 → `git checkout --ours <file>`
- 两边都有实质改 → 🔴 STOP,AskUserQuestion,禁自主

checkout 后:`git add <file>`;全部解完 `git rebase --continue`。

## §poison `-s ours` vs `-X ours` 剧毒区分

| 写法 | 行为 | 用于本 skill? |
| --- | --- | --- |
| `-X ours` / `-X theirs` | **仅在冲突 hunk** 自动选一边,非冲突改动正常合 | ✅ 可用(等价于批量 checkout) |
| `-s ours` | 用 `ours` **整个策略**:丢弃另一边所有改动,结果 = 单边树 | 🔴 禁用 |

⚠️ **rebase 场景 `-s ours` 尤其致命**:rebase 是逐 commit replay,`-s ours` 会让每个 replay 的补丁「以已有为准」→ **等于清空当前分支的全部改动**,静默数据丢失。要「冲突处以某边为准」永远用 `-X`,不用 `-s`。

## §rerere 记住冲突解法(可选,推荐长 rebase)

```bash
git config rerere.enabled true      # 开启:记录你怎么解冲突,下次同样冲突自动套用
# 不开 autoupdate:让你 review 后再 add,别自动 stage
git config --get rerere.autoupdate  # 确认为 false / 空
```
- rebase 中断重来、或多分支反复遇同一冲突时省大量重复劳动。
- 保持 autoupdate **关闭**:rerere 自动应用记忆解法后仍要你人工确认再 `git add`,避免错误解法被静默重放。
