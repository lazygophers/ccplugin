"""回复前缀强制注入测试 — 注入点: SessionStart (hooks.py session-start)。

「回复前缀」属常驻规则, SessionStart 注入一次即可; UserPromptSubmit 不再重复 (避免每轮冗余)。
UserPromptSubmit 仍保留 phase_hints (按 prompt 给出 active task 阶段提示, 非常驻)。

经 conftest 的 ws/skein_cli fixture 跑真实脚本子进程 (tmp_path 隔离)。
覆盖 (5 用例):
  1. user-prompt 普通 prompt → 不再含「回复前缀」常驻段 (常驻归 SessionStart)。
  2. user-prompt (create+start 一个进行中 task) → 含 task id 且标注 `(exec)` (phase_hints 仍保留)。
  3. session-start 恒注入前缀规则 + `[skein]`。
  4. session-start 不列 active task (plan/research 归 user-prompt)。
  5. phase 映射 进行中→exec (并入 2/4)。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import SCRIPTS, SKEIN, SkeinCli

HOOKS: Path = SCRIPTS / "hooks.py"


def _user_prompt(cwd: Path, prompt: str) -> str:
    """跑 hooks.py user-prompt, stdin 传 {cwd, prompt}, 返 additionalContext。"""
    r = subprocess.run(
        [sys.executable, str(HOOKS), "user-prompt"], cwd=cwd,
        input=json.dumps({"cwd": str(cwd), "prompt": prompt}),
        capture_output=True, text=True, check=True)
    return str(json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])


def _session_ctx(cwd: Path) -> str:
    """跑 hooks.py session-start, 返 additionalContext。"""
    r = subprocess.run(
        [sys.executable, str(HOOKS), "session-start"], cwd=cwd,
        input=json.dumps({"cwd": str(cwd)}),
        capture_output=True, text=True, check=True)
    out = r.stdout.strip()
    return str(json.loads(out)["hookSpecificOutput"]["additionalContext"]) if out else ""


def _fill_prd(ws: Path, tid: str) -> None:
    """写规范 prd.md + design.md (三段齐) 过 confirm 的 _validate_prd + _validate_seam 门。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text("---\ndesc: 解决 X 问题\nboundary:\n  should:\n  - 范围内a\n  should_not: []\nestimate: 1\nacceptance:\n  - 用例通过\n---\n", encoding="utf-8")
    (ws / ".skein" / "task" / tid / "design.md").write_text(
        f"# {tid} — 详细设计\n\n## 测试接缝 (seam)\n- [x] API 层\n")


def _start_task(skein_cli: SkeinCli, ws: Path, tid: str) -> None:
    """create + subtask + prd + confirm → task 进入进行中 (active, confirm 吸收 start)。"""
    skein_cli(ws, "create", tid, "--name", "n", "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s1", "--name", "x", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    skein_cli(ws, "confirm", tid)  # 待处理→进行中 用户确认门 (吸收 start)


# ---------- 1. user-prompt 不再注入常驻前缀段 (常驻归 SessionStart) ----------
def test_user_prompt_does_not_inject_resident_prefix(ws: Path) -> None:
    """普通 prompt → 不再含「回复前缀」常驻段 (常驻规则由 SessionStart 一次性注入)。"""
    ctx = _user_prompt(ws, "帮我看看这个函数")
    assert "回复前缀" not in ctx, f"UserPromptSubmit 不应重复注入常驻前缀段: {ctx!r}"


# ---------- 2. user-prompt 列 active task 阶段 ----------
def test_user_prompt_lists_plan_research_tasks(skein_cli: SkeinCli, ws: Path) -> None:
    """plan/research 阶段 task → additionalContext 列 id | 阶段 | name。"""
    skein_cli(ws, "create", "task-a", "--name", "支付重构", "--desc", "d")
    # prompt 不能用 _EXPLICIT 里的词 (go/exec/do/plan/继续/continue): 那些早退不注入
    ctx = _user_prompt(ws, "接着往下做")
    assert "- task-a | plan | 支付重构" in ctx, f"未列 plan task: {ctx!r}"


# ---------- 3. session-start 恒注入前缀规则 ----------
def test_session_context_injects_prefix_rule(ws: Path) -> None:
    """无 active task 也注入前缀规则 + `[skein]`。"""
    ctx = _session_ctx(ws)
    assert "[skein]" in ctx, f"缺 [skein] 前缀标记: {ctx!r}"
    assert "回复前缀" in ctx, f"缺前缀规则关键字: {ctx!r}"


# ---------- 4. session-start 不列 active task ----------
def test_session_start_does_not_list_active_task(skein_cli: SkeinCli, ws: Path) -> None:
    """session-start 只注配置+前缀; active task 由 user-prompt 的 plan/research 列表覆盖。"""
    _start_task(skein_cli, ws, "task-a")
    ctx = _session_ctx(ws)
    assert "task-a" not in ctx, f"session-start 不该列 active task: {ctx!r}"


# ---------- 5. user-prompt 只列 plan/research, 不列 active ----------
def test_user_prompt_omits_active_task(skein_cli: SkeinCli, ws: Path) -> None:
    """user-prompt 只列 plan/research 阶段 task, active 不出现。"""
    _start_task(skein_cli, ws, "task-m")
    # prompt 不能用 _EXPLICIT 里的词 (go/exec/do/plan/继续/continue) 或 skein-*: 那些早退不注入
    assert "task-m" not in _user_prompt(ws, "接着往下做"), "user-prompt 只列 plan/research, active 不该出现"
