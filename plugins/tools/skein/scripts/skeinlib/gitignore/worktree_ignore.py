"""仓库根/子仓 .gitignore 的 worktree 目录忽略。

把 worktree.root 写进该 git 仓 .gitignore (缺则补), 免 worktree 目录污染该仓 status。
子仓是独立 git/submodule, root .gitignore 管不到, 故各子仓自补。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def ignore_worktree_dir(repo_dir: Path, cfg: dict[str, Any]) -> None:
    wt = cfg["worktree"]["root"].rstrip("/") + "/"
    gi = repo_dir / ".gitignore"
    existing = gi.read_text() if gi.exists() else ""
    if wt in existing:
        return
    sep = "\n" if existing and not existing.endswith("\n") else ""
    with gi.open("a") as f:
        f.write(f"{sep}# skein worktree 隔离 (任务源码改动落此, 不入库)\n{wt}\n")
