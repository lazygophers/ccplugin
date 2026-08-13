# 冲突解决 · ours/theirs 方向 · rerere —— git-rebase 详表

主流程见 [../SKILL.md](../SKILL.md)。**反转 (inversion)**:merge 与 rebase 下 `--ours`/`--theirs` 指向相反的分支,是两个 skill 间最易错的判定,查表别凭记忆,merge 侧方向见 [git-merge 详表](../../git-merge/references/conflict-resolution.md)。方向无关的共有判据骨架(前置检查/实质改动判据/冲突循环步骤)与 `-s ours`/`-X ours` 剧毒对照,单一真值源见该文件 §core / §poison,本文件不重复定义,只保留 rebase 侧的反转表本侧半 + rerere(rebase 独有,merge 无此步)。

## §direction ours/theirs 方向(rebase 语境)

rebase 的机制:切到目标(`origin/$SRC`)后,把当前分支的提交逐个 replay 上去。所以冲突时 **HEAD = 已经就位的目标分支(newbase)**,replay 中的补丁 = 你的提交。

| 标记 | 指向 | 冲突块标签 |
| --- | --- | --- |
| `--ours` / `<<<<<<< HEAD` | **源分支/目标 base**(newbase) | `HEAD` |
| `--theirs` / `>>>>>>>` | **当前分支**你正被 replay 的提交 | commit hash |

对照:merge 里 ours=当前分支(顺直觉);**rebase 里 ours=目标/源分支(反直觉)**——同样一句「以当前分支为准」,rebase 用 `--theirs`、merge 用 `--ours`,务必查表,别凭记忆。

### 单边判定 → 自动 checkout
```bash
# 该文件当前分支侧有没有改过?
git log origin/$SRC..<backup 分支> -- <file>
```
- 有输出(当前分支改过,源分支没实质改) → 以当前为准 → `git checkout --theirs <file>`
- 无输出(只源分支改过) → 以源分支为准 → `git checkout --ours <file>`
- 两边都有实质改 → 🔴 STOP,AskUserQuestion,不自主

checkout 后:`git add <file>`;全部解完 `git rebase --continue`。

## §rerere 记住冲突解法(可选,推荐长 rebase)

```bash
git config rerere.enabled true      # 开启:记录你怎么解冲突,下次同样冲突自动套用
# 不开 autoupdate:让你 review 后再 add,别自动 stage
git config --get rerere.autoupdate  # 确认为 false / 空
```
- rebase 中断重来、或多分支反复遇同一冲突时省大量重复劳动。
- 保持 autoupdate **关闭**:rerere 自动应用记忆解法后仍要你人工确认再 `git add`,避免错误解法被静默重放。
