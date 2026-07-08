# 冲突解决 · ours/theirs 方向 —— git-merge 详表

主流程见 [../SKILL.md](../SKILL.md)。**merge 的方向与 rebase 相反,跨 skill 操作勿混。**

## §direction ours/theirs 方向(merge 语境)

merge 的机制:当前分支不动,把源分支「合进来」。所以 **HEAD = 当前分支 = ours**,合入方 = 源分支 = theirs。这是符合直觉的方向。

| 标记 | 指向 | 冲突块标签 |
| --- | --- | --- |
| `--ours` / `<<<<<<< HEAD` | **当前分支**(你所在的分支) | `HEAD` |
| `--theirs` / `>>>>>>>` | **源分支**(被合入的 `origin/$SRC`) | `origin/<src>` |

对照:rebase 里 ours=目标/源分支(反直觉);**merge 里 ours=当前分支(顺直觉)**。同样一句「以当前分支为准」,rebase 用 `--theirs`、merge 用 `--ours`——务必查表,别凭记忆。

### 单边判定 → 自动 checkout
```bash
# 该文件当前分支侧有没有改过?
git log origin/$SRC..HEAD -- <file>
```
- 有输出(当前分支改过) → 以当前为准 → `git checkout --ours <file>`
- 无输出(只源分支改过) → 以源分支为准 → `git checkout --theirs <file>`
- 两边都有实质改 → 🔴 STOP,AskUserQuestion,禁自主

checkout 后必查无残留冲突标记再 `git add <file>`;全部解完 `git commit --no-edit`。

## §poison `-s ours` vs `-X ours`

| 写法 | 行为 | 用于本 skill? |
| --- | --- | --- |
| `-X ours` / `-X theirs` | **仅冲突 hunk** 自动选一边,非冲突改动正常合入 | ✅ 可用(等价批量 checkout) |
| `-s ours` | 用 `ours` 整个策略:**完全丢弃源分支所有改动**,只产生一个「假装合并了」的提交 | 🔴 禁用 |

⚠️ `git merge -s ours <源>` 常被误用为「以我为准解冲突」,实际是**记录一次合并但一行源分支改动都不要**——源分支后续再 merge 会以为已合过而跳过,造成永久丢失。要「冲突处以某边为准」永远用 `-X`,不用 `-s`。

## §markers 冲突标记

解冲突后、`git add` 前,确认文件里没有残留:
```
<<<<<<< HEAD
=======
>>>>>>> origin/<src>
```
可批量自检:`git diff --check`(报告残留冲突标记与空白错误)。有残留就编辑清掉再 add,别把 `<<<<<<<` 提交进去。
