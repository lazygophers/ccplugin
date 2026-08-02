"""finish 的 commit 分流测试 (use_worktree 与 auto_commit 相互独立)。

- worktree 模式: 强制 commit (auto_commit=false 也照 commit + merge), 本键不参与判定。
- 原地模式 + auto_commit=true: finish 自动 commit, 工作区落干净。
- 原地模式 + auto_commit=false: 改动留工作区不提交, finish 仍成功 (非拒绝)。
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import SkeinCli
from test_worktree_cli import _advance_to_finishing, _mk


def _git_out(d: Path, *args: str) -> str:
    """取 git 输出 (conftest 的 git_cmd 返 None, 这里要读 stdout)。"""
    return subprocess.run(["git", *args], cwd=d, capture_output=True, text=True,
                          check=True).stdout.strip()


def _dirty(d: Path) -> str:
    """返回工作区未提交清单 (空串 = 干净)。"""
    return _git_out(d, "status", "--porcelain")


def test_worktree_forces_commit_ignoring_auto_commit(skein_cli: SkeinCli, ws: Path) -> None:
    """worktree 模式 + auto_commit=false: 仍强制 commit 并 merge 回主, finish 不拒。"""
    skein_cli(ws, "config", "set", "auto_commit", "false")
    tid = _mk(skein_cli, ws, "feat-wt-ac")
    wt = ws / ".worktrees" / f"skein-{tid}"
    (wt / "change.txt").write_text("c\n")  # 只改不提交, 验 finish 自己会 commit
    _advance_to_finishing(skein_cli, ws, tid)
    skein_cli(ws, "finish", tid)
    assert not wt.exists(), "worktree 未销"
    assert (ws / "change.txt").exists(), "未提交改动没被强制 commit + merge 回主"
    assert "change.txt" not in _dirty(ws), "改动没进 commit, 只是被 merge 带出来的脏文件"


def test_inplace_auto_commit_true(skein_cli: SkeinCli, ws: Path) -> None:
    """原地模式 + auto_commit=true: finish 自动 commit, 工作区干净。"""
    skein_cli(ws, "config", "set", "use_worktree", "false")
    tid = _mk(skein_cli, ws, "feat-inplace-on")
    (ws / "change.txt").write_text("c\n")
    _advance_to_finishing(skein_cli, ws, tid)
    skein_cli(ws, "finish", tid)
    assert _dirty(ws) == "", "原地模式 auto_commit=true 未自动 commit"
    log = _git_out(ws, "log", "-1", "--pretty=%s")
    assert tid in log, f"commit message 未含 task id: {log!r}"


def test_inplace_auto_commit_false_leaves_worktree_dirty(skein_cli: SkeinCli, ws: Path) -> None:
    """原地模式 + auto_commit=false: 改动留工作区, finish 仍成功 (旧行为是 raise)。"""
    skein_cli(ws, "config", "set", "use_worktree", "false")
    skein_cli(ws, "config", "set", "auto_commit", "false")
    tid = _mk(skein_cli, ws, "feat-inplace-off")
    (ws / "change.txt").write_text("c\n")
    _advance_to_finishing(skein_cli, ws, tid)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 0, f"原地模式 auto_commit=false 不该拒 finish: {r.stdout}{r.stderr}"
    assert "change.txt" in _dirty(ws), "改动应留工作区交用户自管"
