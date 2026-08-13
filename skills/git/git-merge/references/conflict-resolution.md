# 冲突解决 · ours/theirs 方向 —— git-merge 详表

主流程见 [../SKILL.md](../SKILL.md)。**反转 (inversion)**:merge 与 rebase 下 `--ours`/`--theirs` 指向相反的分支,是两个 skill 间最易错的判定,查表别凭记忆,rebase 侧方向见 [git-rebase 详表](../../git-rebase/references/conflict-resolution.md)。

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

## §core 方向无关共有骨架(merge/rebase 单一真值源)

以下判定逻辑 merge/rebase 完全一致,只是「哪个标记指哪个分支」按各自 direction 表反转,git-rebase 侧同名判定引用本节,不重复定义:

- **前置检查**:工作区必须干净(`git status --porcelain` 空);脏则先 `git-commit` 或 `git stash`,操作完成后再继续(needed 时 pop)。
- **实质改动判据**:`git log <base>..<head> -- <file>` 有输出 = 该侧对文件有实质提交,空 = 未动;`<base>`/`<head>` 取值因方向而异,merge 用 `origin/$SRC..HEAD`,rebase 用 `origin/$SRC..<backup 分支>`。
- **冲突循环骨架**:① 逐个冲突文件按 direction 表判单边/双边 → ② 单边改动用对应 `checkout --ours`/`--theirs` 自动解(方向查表,别凭记忆) → ③ 双边实质改同一逻辑 🔴 STOP + AskUserQuestion,禁自主猜 → ④ `add`/`--continue` 前用 `git diff --check` 确认无残留冲突标记(`<<<<<<<`/`=======`/`>>>>>>>`) → ⑤ 全部解完跑收尾命令(merge: `git commit --no-edit`;rebase: `git rebase --continue`)。

## §poison `-s ours` vs `-X ours`(merge/rebase 通用,危害因方向而异)

| 写法 | 行为 | 用于本 skill? |
| --- | --- | --- |
| `-X ours` / `-X theirs` | **仅冲突 hunk** 自动选一边,非冲突改动正常合入 | ✅ 可用(等价批量 checkout) |
| `-s ours` | 用 `ours` 整个策略:**完全丢弃另一边所有改动**,只产生一个「假装合并了」的提交 | 🔴 禁用 |

merge 语境 `git merge -s ours <源>` 常被误用为「以我为准解冲突」,实际是**记录一次合并但一行源分支改动都不要**——源分支后续再 merge 会以为已合过而跳过,造成永久丢失。rebase 语境更致命——逐 commit replay 下 `-s ours` 等于清空当前分支的全部改动,静默数据丢失。两种语境要「冲突处以某边为准」永远用 `-X`,不用 `-s`。

## §markers 冲突标记

解冲突后、`git add` 前,确认文件里没有残留:
```
<<<<<<< HEAD
=======
>>>>>>> origin/<src>
```
可批量自检:`git diff --check`(报告残留冲突标记与空白错误)。有残留就编辑清掉再 add,别把 `<<<<<<<` 提交进去。
