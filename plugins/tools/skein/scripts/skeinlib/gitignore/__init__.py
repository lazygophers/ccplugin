"""git 忽略文件管理 —— 衍生物登记 + worktree 目录忽略。

单一职责: 所有写 .gitignore 的逻辑集中于此。
- derivatives.py: .skein/.gitignore 衍生物条目登记处 + 幂等补缺
- worktree_ignore.py: 仓库根/子仓 .gitignore 的 worktree 目录忽略
"""
