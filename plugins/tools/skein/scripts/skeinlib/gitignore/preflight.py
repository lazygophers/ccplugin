"""所有 CLI 入口的公共前置。

每个 CLI main() 开头调一次 run_preflight()，确保 .skein/.gitignore 与仓库根 .gitignore
增量补缺。失败不阻断主命令 — gitignore 只是卫生措施。
"""
from __future__ import annotations

import sys
from pathlib import Path


def run_preflight() -> None:
    """幂等增量补 .skein/.gitignore 条目 (仅已初始化的工作区)。

    所有 skein* CLI 入口必经此处。失败只 warn 不阻断。
    """
    # 定位 .skein/ — 与 Workspace._find_skein_root 同策略但更轻量
    from skeinlib.infra.worktree import git
    r = git("rev-parse", "--show-toplevel", check=False)
    if r.returncode != 0:
        return  # 非 git 仓库, cwd 找 .skein/
        # 注意: 非 git 场景仍可能有 .skein/, 但 hooks/spec CLI 在非 git 仓库里几乎不用跑,
        # 且 ensure_gitignore 自身会 mkdir, 不适合在不确定位置调。
    top = Path(r.stdout.strip())
    skein_dir = _find_skein_root(top)
    if skein_dir is None:
        return  # 未初始化, 不干预

    try:
        from skeinlib.gitignore.derivatives import ensure_gitignore
        ensure_gitignore(skein_dir)
    except Exception as e:
        print(f"⚠ .skein/.gitignore 增量补缺失败 (不阻断): {e}", file=sys.stderr)


def _find_skein_root(top: Path) -> Path | None:
    """从 git toplevel 找 .skein/ 目录; worktree 内回溯主仓。"""
    # worktree 内: .git 是文件 → 取主仓根
    git_link = top / ".git"
    if git_link.is_file():
        try:
            content = git_link.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                gitdir = Path(content.split(":", 1)[1].strip())
                main_git = gitdir.parent.parent
                main_root = main_git.parent
                if (main_root / ".skein").is_dir():
                    return main_root / ".skein"
        except (OSError, IndexError):
            pass
    p = top.resolve()
    if (p / ".skein").is_dir():
        return p / ".skein"
    for parent in p.parents:
        if (parent / ".skein").is_dir():
            return parent / ".skein"
    return None
