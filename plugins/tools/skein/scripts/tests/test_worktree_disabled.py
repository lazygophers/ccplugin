"""use_worktree=false 禁用态全链路 gate 测试 (R1 禁填 / R2 不展示 / R3 注入)。

经 conftest 的 skein_cli/ws/git_cmd fixture 跑真实子进程 (tmp_path 隔离)。启用态生命周期
+ Req6 (git-only 自动建: plain_subdir_rejected / deep_nested_git) 归 test_worktree_cli.py;
本文件只测禁用态: worktree 概念在填写/展示/注入三层的消失与配置块注入。

- R1 禁填: use_worktree=false 时 create --repos / repos --set 直接拒 (SystemExit)。
- R2 不展示: 禁用态下 session-context / current / status --json 不含 worktree 段。
- R3 注入: session-context + hooks user-prompt 都注入「# SKEIN 运行配置」块 (worktree 态 +
  max_active); 值经 skein.CONFIG_DEFAULTS 兜底, hook 不硬编码。
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
    skein_cli(ws, "config", "set", "use_worktree", "false")


def _session_ctx(skein_cli: SkeinCli, ws: Path) -> str:
    """跑 session-context, 取 additionalContext 文本 (hook JSON 出口)。"""
    r = skein_cli(ws, "session-context")
    return json.loads(r.stdout.strip())["hookSpecificOutput"]["additionalContext"]


def _user_prompt(ws: Path, prompt: str) -> str:
    """跑 hooks.py user-prompt, 取 additionalContext (禁用态注入验证)。"""
    payload = json.dumps({"cwd": str(ws), "prompt": prompt})
    r = subprocess.run([sys.executable, str(HOOKS), "user-prompt"],
                       cwd=ws, input=payload, capture_output=True, text=True, check=True)
    return json.loads(r.stdout.strip())["hookSpecificOutput"]["additionalContext"]


# ---------- R1 禁填 (use_worktree=false → create/repos 拒) ----------

def test_create_repos_rejected_when_disabled(skein_cli: SkeinCli, git_cmd: GitCmd,
                                             ws: Path) -> None:
    """use_worktree=false 时 create --repos → 直接拒 (rc!=0, 不落 task)。"""
    _disable(skein_cli, ws)
    r = skein_cli(ws, "create", "feat-x", "--name", "x", "--desc", "d",
                  "--repos", "sub-a", check=False)
    assert r.returncode != 0, f"禁用态 create --repos 未拒: rc={r.returncode}"
    assert "use_worktree=false" in r.stdout + r.stderr, f"文案不符: {r.stdout + r.stderr!r}"
    # 拒后不落 task
    assert not (ws / ".skein" / "task" / "feat-x").exists(), "拒后不应残留 task"


def test_repos_set_rejected_when_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """use_worktree=false 时 repos <tid> --set → 直接拒。"""
    skein_cli(ws, "create", "feat-y", "--name", "y", "--desc", "d")
    _disable(skein_cli, ws)
    r = skein_cli(ws, "repos", "feat-y", "--set", "sub-a", check=False)
    assert r.returncode != 0, f"禁用态 repos --set 未拒: rc={r.returncode}"
    assert "use_worktree=false" in r.stdout + r.stderr, f"文案不符: {r.stdout + r.stderr!r}"


def test_create_repos_allowed_when_enabled(skein_cli: SkeinCli, git_cmd: GitCmd,
                                           ws: Path) -> None:
    """启用态 (默认) create --repos 行为不变 (对照组, 证拒仅由禁用态触发)。"""
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
    """禁用态 start 后 status --json → worktree=null, worktrees=[] (原地执行无隔离)。"""
    _disable(skein_cli, ws)
    tid = "feat-st"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d")
    _fill_prd(ws, tid)
    skein_cli(ws, "start", tid)
    data = json.loads(skein_cli(ws, "status", tid, "--json").stdout.strip())
    assert data.get("worktree") is None, f"禁用态 worktree 非 null: {data.get('worktree')!r}"
    assert data.get("worktrees", []) == [], f"禁用态 worktrees 非空: {data.get('worktrees')!r}"


def test_current_no_worktree_col_when_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 current 输出不含 worktree 目录段 (.worktrees 路径不出现)。"""
    _disable(skein_cli, ws)
    tid = "feat-cur"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d")
    _fill_prd(ws, tid)
    skein_cli(ws, "start", tid)
    out = skein_cli(ws, "current").stdout
    assert ".worktrees" not in out, f"禁用态 current 泄露 worktree 路径: {out!r}"


def test_session_context_hides_worktree_when_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 session-context: active task 行无 ' — worktree:' 段。"""
    _disable(skein_cli, ws)
    tid = "feat-sc"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d")
    _fill_prd(ws, tid)
    skein_cli(ws, "start", tid)
    ctx = _session_ctx(skein_cli, ws)
    assert "— worktree:" not in ctx, f"禁用态 active 行泄露 worktree: {ctx!r}"


# ---------- R3 注入 (两 hook 都注入运行配置块) ----------

def test_session_context_config_block_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 session-context 注入运行配置块: worktree 禁用 + max_active。"""
    _disable(skein_cli, ws)
    ctx = _session_ctx(skein_cli, ws)
    assert "# SKEIN 运行配置" in ctx, "缺运行配置块"
    assert "禁用" in ctx, f"worktree 未标禁用: {ctx!r}"
    assert "最大并行 subtask" in ctx, "缺 max_active 行"


def test_session_context_config_block_enabled(skein_cli: SkeinCli, ws: Path) -> None:
    """启用态 (默认) session-context 注入: worktree 启用 + max_active=2 (默认真值)。"""
    ctx = _session_ctx(skein_cli, ws)
    assert "# SKEIN 运行配置" in ctx, "缺运行配置块"
    assert "启用" in ctx, f"worktree 未标启用: {ctx!r}"
    assert "最大并行 subtask: 2" in ctx, f"max_active 非默认 2: {ctx!r}"


def test_user_prompt_config_block_disabled(skein_cli: SkeinCli, ws: Path) -> None:
    """禁用态 hooks user-prompt 注入运行配置块: worktree 禁用 + max_active。"""
    _disable(skein_cli, ws)
    ctx = _user_prompt(ws, "改一下 a.py 的逻辑")
    assert "# SKEIN 运行配置" in ctx, "缺运行配置块"
    assert "禁用" in ctx, f"worktree 未标禁用: {ctx!r}"
    assert "最大并行 subtask" in ctx, "缺 max_active 行"


def test_user_prompt_config_block_default_from_config_defaults(skein_cli: SkeinCli,
                                                               ws: Path) -> None:
    """user-prompt 默认值经 CONFIG_DEFAULTS 兜底 (不硬编码): 启用 + max_active=2。"""
    ctx = _user_prompt(ws, "改一下 a.py 的逻辑")
    assert "启用" in ctx, f"默认 worktree 未标启用: {ctx!r}"
    assert "最大并行 subtask: 2" in ctx, f"默认 max_active 非 2: {ctx!r}"
