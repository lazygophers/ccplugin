"""use_worktree=false 禁用态全链路 gate 测试 (R1 禁填 / R2 不展示 / R3 注入)。

经 conftest 的 skein_cli/ws/git_cmd fixture 跑真实子进程 (tmp_path 隔离)。启用态生命周期
+ Req6 (git-only 自动建: plain_subdir_rejected / deep_nested_git) 归 test_worktree_cli.py;
本文件只测禁用态: worktree 概念在填写/展示/注入三层的消失与配置块注入。

- R1 禁填: use_worktree=false 时 create --repos / repos --set 直接拒 (SystemExit)。
- R2 不展示: 禁用态下 session-start / list --status open / status --json 不含 worktree 段。
- R3 注入: session-start 恒注入「# SKEIN 运行配置」块 (仅 worktree + auto_commit); hooks
  user-prompt 一轮都不重发这块。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import SkeinCli, GitCmd
from test_worktree_cli import _fill_prd

HOOKS: Path = Path(__file__).resolve().parent.parent / "hooks.py"


def _disable(skein_cli: SkeinCli, ws: Path) -> None:
    """置 config use_worktree=false (禁用态前置)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "false")


def _session_ctx(ws: Path) -> str:
    """跑 hooks.py session-start, 取 additionalContext 文本 (hook JSON 出口)。"""
    payload = json.dumps({"cwd": str(ws)})
    r = subprocess.run([sys.executable, str(HOOKS), "session-start"],
                       cwd=ws, input=payload, capture_output=True, text=True, check=True)
    return str(json.loads(r.stdout.strip())["hookSpecificOutput"]["additionalContext"])


def _user_prompt(ws: Path, prompt: str) -> str:
    """跑 hooks.py user-prompt, 取 additionalContext (禁用态注入验证)。"""
    payload = json.dumps({"cwd": str(ws), "prompt": prompt})
    r = subprocess.run([sys.executable, str(HOOKS), "user-prompt"],
                       cwd=ws, input=payload, capture_output=True, text=True, check=True)
    return str(json.loads(r.stdout.strip())["hookSpecificOutput"]["additionalContext"])


# ---------- R1 禁填 (use_worktree=false → create/repos 拒) ----------

def test_create_repos_rejected_when_disabled(skein_cli: SkeinCli, git_cmd: GitCmd,
                                             ws: Path) -> None:
    """use_worktree=false 时 create --repos → 直接拒 (rc!=0, 不落 task)。"""
    _disable(skein_cli, ws)
    r = skein_cli(ws, "create", "feat-x", "--name", "x", "--desc", "d",
                  "--repos", "sub-a", check=False)
    assert r.returncode != 0, f"禁用态 create --repos 未拒: rc={r.returncode}"
    assert "worktree.enabled=false" in r.stdout + r.stderr, f"文案不符: {r.stdout + r.stderr!r}"
    # 拒后不落 task
    assert not (ws / ".skein" / "task" / "feat-x").exists(), "拒后不应残留 task"


def test_repos_set_rejected_when_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """use_worktree=false 时 repos <tid> --set → 直接拒。"""
    skein_cli(ws, "create", "feat-y", "--name", "y", "--desc", "d")
    _disable(skein_cli, ws)
    r = skein_cli(ws, "repos", "feat-y", "--set", "sub-a", check=False)
    assert r.returncode != 0, f"禁用态 repos --set 未拒: rc={r.returncode}"
    assert "worktree.enabled=false" in r.stdout + r.stderr, f"文案不符: {r.stdout + r.stderr!r}"


def test_create_repos_allowed_when_enabled(skein_cli: SkeinCli, git_cmd: GitCmd,
                                           ws: Path) -> None:
    """启用态 (显式启用) create --repos 行为不变 (对照组, 证拒仅由禁用态触发)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    sub = ws / "sub-a"
    sub.mkdir()
    git_cmd(sub, "init", "-q")
    git_cmd(sub, "config", "user.email", "t@t.dev")
    git_cmd(sub, "config", "user.name", "t")
    (sub / "s.txt").write_text("s\n")
    git_cmd(sub, "add", "-A")
    git_cmd(sub, "commit", "-qm", "seed")
    r = skein_cli(ws, "create", "feat-z", "--name", "z", "--desc", "d",
                  "--repos", "sub-a", check=False)
    assert r.returncode == 0, f"启用态 create --repos 被误拒: {r.stderr}"


# ---------- R2 不展示 (禁用态各出口无 worktree) ----------

def test_status_json_worktree_null_when_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 confirm 后 status --json → worktree=null, worktrees=[] (原地执行无隔离)。"""
    _disable(skein_cli, ws)
    tid = "feat-st"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    skein_cli(ws, "confirm", tid)
    data = json.loads(skein_cli(ws, "status", tid).stdout)
    task = data.get("task", data)
    assert task.get("worktree") is None, f"禁用态 worktree 非 null: {task.get('worktree')!r}"
    assert task.get("worktrees", []) == [], f"禁用态 worktrees 非空: {task.get('worktrees')!r}"


def test_open_list_no_worktree_col_when_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 open list 输出不含 worktree 目录段 (.worktrees 路径不出现)。"""
    _disable(skein_cli, ws)
    tid = "feat-cur"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    skein_cli(ws, "confirm", tid)
    out = skein_cli(ws, "list", "--status", "open").stdout
    assert ".worktrees" not in out, f"禁用态 open list 泄露 worktree 路径: {out!r}"


def test_session_start_hides_worktree_when_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 session-start: 配置行标禁用, 不出现 worktree 路径段。"""
    _disable(skein_cli, ws)
    tid = "feat-sc"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    skein_cli(ws, "confirm", tid)
    ctx = _session_ctx(ws)
    assert "— worktree:" not in ctx, f"禁用态泄露 worktree: {ctx!r}"
    assert "- worktree: 禁用 (原地执行, 无 worktree)" in ctx


# ---------- R3 注入 (SessionStart 注入运行配置块) ----------

def test_session_start_config_block_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 session-start 注入运行配置块: worktree 禁用 + auto_commit。"""
    _disable(skein_cli, ws)
    ctx = _session_ctx(ws)
    assert "# SKEIN 运行配置" in ctx, "缺运行配置块"
    assert "- worktree: 禁用" in ctx, f"worktree 未标禁用: {ctx!r}"
    assert "- auto_commit: " in ctx, "缺 auto_commit 行"


def test_session_start_config_block_enabled(skein_cli: SkeinCli, ws: Path) -> None:
    """启用态 session-start 注入: worktree 启用 (auto_commit 随之标强制)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")
    ctx = _session_ctx(ws)
    assert "# SKEIN 运行配置" in ctx, "缺运行配置块"
    assert "- worktree: 启用 (task 各开 worktree 隔离, 目录: " in ctx, f"worktree 未标启用: {ctx!r}"
    assert "- auto_commit: 启用 (finish 时自动 commit)" in ctx, "worktree 模式 auto_commit 生效值恒启用"


def test_user_prompt_never_repeats_config_block(skein_cli: SkeinCli, ws: Path) -> None:
    """运行配置已由 SessionStart 注入, user-prompt 每轮都不重发 (有无在途 task 都不发)。"""
    ctx = _user_prompt(ws, "改一下 a.py 的逻辑")
    assert "# SKEIN 运行配置" not in ctx, f"user-prompt 重发了运行配置块: {ctx!r}"

    skein_cli(ws, "create", "feat-up", "--name", "up", "--desc", "d")
    ctx = _user_prompt(ws, "继续 feat-up")
    assert "# SKEIN 运行配置" not in ctx, f"user-prompt 重发了运行配置块: {ctx!r}"
