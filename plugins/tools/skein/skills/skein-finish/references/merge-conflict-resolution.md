# merge / rebase 冲突解构纪律

> skein-finish 的 `skein finish` (commit→merge→archive→销 worktree) 在多 task 并行 worktree 合并时常踩冲突。本文件是 ask-matt `/resolving-merge-conflicts` 的 5 步纪律 + skein-finish 失败模式兜底, 供 merge 阶段参考。

**触发场景**: `skein finish <id>` 跑到 merge 步骤遇冲突 (worktree 分支已与主分支发散), 或多 task 并行各占独立 worktree 合并回主干互撞。

## 5 步纪律

### 1. see current state (先看战场)
- `git status` 列出所有 conflicting files 清单。
- 不盲合 — 先确认是 merge (两分支合并) 还是 rebase (replay 一串 commit)。

### 2. find primary sources (读每方 intent)
- 读冲突双方的 commit messages / PRs / issues, 理解每方**为什么这么改**。
- **禁盲合** (两段都留) — 盲合 = 没读懂意图的拼凑, 后续回归必崩。

### 3. resolve each hunk (保双方意图)
逐 hunk 解:
- **preserve both intents** — 双方意图都保留 (典型: 一方加字段, 一方加校验 → 两段都要)。
- **互斥则按 merge 目标选 + note trade-off** — 真互斥 (同一行两种写法) 时, 按本 task 的 merge 目标 (回归 design.md / prd.md 的 intent) 选其一, **在 commit message 里 note trade-off** 记下为什么否了另一边。
- **🛑 禁 invent new behavior** — 冲突解决禁顺手加新逻辑 / 新字段 / 新分支。merge 只解冲突, 不借机改功能。
- **🛑 always resolve, never `--abort`** — 禁 `git merge --abort` / `git rebase --abort` 逃回干净态。abort = 把双方工作量全丢, 等于该 task 白做。

### 4. discover + run automated checks (解完即验)
解完冲突**在 commit 之前**按顺序跑:
1. **typecheck** (类型错 = 解错了签名 / 接口)
2. **tests** (回归 = 解掉了别人刚加的覆盖)
3. **format** (格式化收尾)

任一步红 → 回 step 3 重解对应 hunk, 不带红过 step 5。

### 5. finish merge / rebase
- **merge**: `git add <冲突文件>` → `git commit` (完成 merge commit, message 记互斥 hunk 的 trade-off note)。
- **rebase**: `git rebase --continue` 逐 commit 解, 直到所有 commit rebased (每解一个 conflict 都要 continue, 不是解一次就完)。

## skein-finish 失败模式兜底

解不开 (反复 step 4 红 / 双方 intent 读不出 / 冲突面过大超认知负荷):
- **停手, 保留 worktree** — 禁 `--abort`, 禁强制覆盖。
- **报用户裁** — 把冲突文件清单 + 双方 commit message + 读出的 intent (或读不出的卡点) 给用户, 让用户拍板互斥 hunk 取舍。
- 回传 skein-finish 失败模式表 (SKILL.md L43): 「解不开 → 停手, 保留 worktree, 报用户裁」。

## 外部引用 (可选)

ask-matt `/resolving-merge-conflicts` 是上述 5 步纪律同源 skill。**未安装则跳过, skein 用本文件原生覆盖** — 不因缺外部 skill 而失效。
