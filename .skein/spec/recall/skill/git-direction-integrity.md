---
title: git-direction-integrity
layer: recall
category: skill
keywords: [git,merge,rebase,--ours,--theirs,反转,冲突处理,单一真值源]
status: active
---

## git merge↔rebase 反转表禁合并

### 触发场景
git merge 与 git rebase skill 都有冲突处理指导，两份文件内容结构相似但语义相反（`--ours`/`--theirs` 指代的分支不同）。

### 陷阱-正解
**陷阱**：为降低冗余，把两份 `conflict-resolution.md` 合并成一份，用条件分支区分 merge vs rebase。
**正解**：merge 与 rebase 的方向判定是 **最易出错的地方**，禁合并成一份带分支的文件——这等于把 footgun 藏进 progressive disclosure 后面。正确做法是**各自保留自己那半 + 显式反转表 + 两侧互指**。

### 处置方案

**两份文件各保留自己那半**：
- `git-merge/references/conflict-resolution.md` §core 段：前置检查、实质改动判据、冲突循环骨架（方向无关，可共享）→ 但放在 merge 侧，rebase 引用
- `git-merge/references/conflict-resolution.md` §direction：merge 侧 `--ours`=当前分支的反转表 + 指向 rebase 侧
- `git-rebase/references/conflict-resolution.md` §core 段：引用 merge 侧的 §core（方向无关部分）
- `git-rebase/references/conflict-resolution.md` §direction：rebase 侧 `--ours`=目标分支的反转表 + 指向 merge 侧

**不合并 recovery.md**：
- merge 侧：abort / reset / revert / ff — 这些是真实差异，不是 duplication
- rebase 侧：backup / reflog / force-with-lease — 不可逆操作的恢复手段
- 两份完全独立，无共享内容

### 规则
- MUST：merge ↔ rebase 的反转表必须显式化（一张表两侧互指），禁隐含在条件分支里
- MUST：recovery.md 一对保持不合并（真实差异，方向特定）
- MUST：方向无关的共有内容（前置检查/实质改动判据/冲突循环骨架）单一真值源 + 交叉引用

### 背景
git 的 merge vs rebase 是新手最常混淆的地方，结合「两份文件结构相似」这个特点，合并一份文件看似减少冗余但实际增加认知负担。这条规则是对「信息分层」(progressive disclosure) 的补充约束。

### 关联
与 skill-quality-checklist.md 的「取舍 2」同源；git-merge/references 与 git-rebase/references 相关文件设计的核心约束
