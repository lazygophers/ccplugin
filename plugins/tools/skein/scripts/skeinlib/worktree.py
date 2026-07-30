"""git 调用封装 + worktree 生命周期。

`root` (仓库根) 与 `cfg` (配置) 显式当参数传, 不建类 —— 这层没有别的状态。
有 task 必有 worktree 是 skein 的隔离前提; 多子 git 场景下一个 task 可能开多个 worktree
(`worktrees_of` 返回列表, 非单值)。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, cast

from skeinlib.hooks.runner import DBG
from skeinlib.errors import SkeinError


def git(*args: str, cwd: Optional[Path] = None, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    DBG.log(f"$ git {' '.join(args)}" + (f"   (cwd={cwd})" if cwd else ""), style="dim")
    r = subprocess.run(
        ["git", *args], cwd=cwd, check=False,
        capture_output=capture, text=True,
    )
    if r.returncode != 0:
        DBG.log(f"  ↳ git exit={r.returncode}", style="yellow")
    if check and r.returncode != 0:
        sys.stderr.write((r.stderr or "") + "\n")
        raise SkeinError(f"git {' '.join(args)} 失败 (exit {r.returncode})")
    return r


def parse_repos(raw: Any) -> list[str]:
    # "a, b/c" → ["a","b/c"]; 归一去空/去首尾斜杠 ('.' 保留=根仓)
    return [p.strip().strip("/") or "." for p in (raw or "").split(",") if p.strip()]


def worktrees_of(t: dict[str, Any]) -> list[dict[str, Any]]:
    # task 的 worktree 生命周期真值; 兼容旧结构 (仅 scalar worktree/branch)
    ws = t.get("worktrees")
    if ws:
        return cast(list[dict[str, Any]], ws)
    rel = t.get("worktree")
    if rel:
        return [{"repo": ".", "wt": rel, "branch": t.get("branch"), "merged": False}]
    return []


def commit_all(cwd: Path, msg: str) -> None:
    # git add -A + commit; 无改动时静默 (nothing to commit 不算错)
    git("add", "-A", cwd=cwd)
    r = git("commit", "-m", msg, cwd=cwd, check=False)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        sys.stderr.write(r.stdout + r.stderr)


def ignore_worktree_dir(repo_dir: Path, cfg: dict[str, Any]) -> None:
    # 把 worktree.root 写进该 git 仓 .gitignore (缺则补), 免 worktree 目录污染该仓 status。
    # 子仓是独立 git/submodule, root .gitignore 管不到, 故各子仓自补。
    wt = cfg["worktree"]["root"].rstrip("/") + "/"
    gi = repo_dir / ".gitignore"
    existing = gi.read_text() if gi.exists() else ""
    if wt in existing:
        return
    sep = "\n" if existing and not existing.endswith("\n") else ""
    with gi.open("a") as f:
        f.write(f"{sep}# skein worktree 隔离 (任务源码改动落此, 不入库)\n{wt}\n")


def make_worktree(t: dict[str, Any], repo: str, cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    # 在指定子 git (repo='.'=根仓) 建 worktree+branch; 校验 sub 确是 git 顶层 (根/submodule/嵌套独立 git)
    sub = root if repo == "." else root / repo
    if not sub.exists():
        raise SkeinError(f"repos 声明的路径不存在: {repo}")
    # 必须是 sub 自己那个 git 仓的顶层才可开 worktree: show-toplevel == sub。
    # 不用 --is-inside-work-tree — 它对根仓的普通子目录也返回 true, 会让 `git worktree add cwd=sub`
    # 错落到外层根仓 (隔离错位)。等值判定恰好: 根仓/submodule/任意深度嵌套独立 git → toplevel==sub ✓;
    # 普通子目录 → toplevel==外层仓 ≠ sub ✗ (拒)。
    rc = git("rev-parse", "--show-toplevel", cwd=sub, check=False)
    top = rc.stdout.strip()
    if rc.returncode != 0 or not top or Path(top).resolve() != sub.resolve():
        raise SkeinError(
            f"{repo} 不是 git 顶层 — repos 只能声明 git 仓顶层 (根/submodule/嵌套独立 git); "
            f"普通子目录不可声明 (worktree 会错落到外层仓)")
    wt_root = cfg["worktree"]["root"].strip("/")
    # worktree 落在**该子 git 内部** (<repo>/<worktree.root>/skein-<id>), 相对 root 存盘免绝对路径入库。
    # 每子仓各自 .worktrees 目录, 天然无碰撞 (旧版全塞 root, 现落各仓内)。
    base = wt_root if repo == "." else f"{repo}/{wt_root}"
    wt_rel = f"{base}/skein-{t['id']}"
    git("worktree", "add", "-b", t["branch"], str(root / wt_rel), "HEAD", cwd=sub)
    if repo != ".":
        ignore_worktree_dir(sub, cfg)  # 子仓自忽略; 根仓已由 init 补
    return {"repo": repo, "wt": wt_rel, "branch": t["branch"], "merged": False}


def destroy_worktrees(t: dict[str, Any], root: Path) -> None:
    # 销 task 全部 worktree + 分支 (active task 删/归档前清理悬挂); 复用 archive 的强删策略
    for w in worktrees_of(t):
        sub = root if w["repo"] == "." else root / w["repo"]
        wt = root / w["wt"]
        if wt.exists():
            # --force: 即使有未提交改动/未跟踪文件也强删 (del 是用户明确销毁意图)
            git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
        git("branch", "-D", w["branch"], cwd=sub, check=False)
