"""回复前缀强制注入测试 — 注入点: SessionStart (skein.py session-context)。

「回复前缀」属常驻规则, SessionStart 注入一次即可; UserPromptSubmit 不再重复 (避免每轮冗余)。
UserPromptSubmit 仍保留 phase_hints (按 prompt 给出 active task 阶段提示, 非常驻)。

经 conftest 的 ws/skein_cli fixture 跑真实脚本子进程 (tmp_path 隔离)。
覆盖 (5 用例):
  1. user-prompt 普通 prompt → 不再含「回复前缀」常驻段 (常驻归 SessionStart)。
  2. user-prompt (create+start 一个进行中 task) → 含 task id 且标注 `(exec)` (phase_hints 仍保留)。
  3. session-context 无 active → 恒注入前缀规则 + `[skein]`。
  4. session-context (create+start) → 含 `当前 active task:` + `id(exec)`。
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
    """跑 skein.py session-context, 返 additionalContext。"""
    r = subprocess.run(
        [sys.executable, str(SKEIN), "session-context"], cwd=cwd,
        capture_output=True, text=True, check=True)
    return str(json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])


def _fill_prd(ws: Path, tid: str) -> None:
    """写规范 prd.md + design.md (三段齐) 过 confirm 的 _validate_prd + _validate_seam 门。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n"
        "## 边界\n- a\n\n"
        "## 验收标准\n- 通过\n\n")
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
def test_user_prompt_lists_active_task_phase(skein_cli: SkeinCli, ws: Path) -> None:
    """create+start task (进行中) → additionalContext 含 id 且标注 (exec)。"""
    _start_task(skein_cli, ws, "task-a")
    # prompt 不能用 _EXPLICIT 里的词 (go/exec/do/plan/继续/continue): 那些早退不注入
    ctx = _user_prompt(ws, "接着往下做")
    assert "task-a(exec)" in ctx, f"未列 active task 阶段 (进行中→exec): {ctx!r}"


# ---------- 3. session-context 恒注入前缀规则 ----------
def test_session_context_injects_prefix_rule(ws: Path) -> None:
    """无 active task 也注入前缀规则 + `[skein]`。"""
    ctx = _session_ctx(ws)
    assert "[skein]" in ctx, f"缺 [skein] 前缀标记: {ctx!r}"
    assert "回复前缀" in ctx, f"缺前缀规则关键字: {ctx!r}"


# ---------- 4. session-context 列 active 阶段 (含 phase 映射) ----------
def test_session_context_lists_active_phase(skein_cli: SkeinCli, ws: Path) -> None:
    """create+start task → 含 `当前 active task:` + id(exec) (进行中→exec)。"""
    _start_task(skein_cli, ws, "task-a")
    ctx = _session_ctx(ws)
    assert "当前 active task:" in ctx, f"缺 active task 行: {ctx!r}"
    assert "task-a(exec)" in ctx, f"phase 映射 进行中→exec 未生效: {ctx!r}"


# ---------- 5. phase 映射 进行中→exec 两注入点一致 ----------
def test_phase_mapping_active_to_exec(skein_cli: SkeinCli, ws: Path) -> None:
    """进行中 status 在 user-prompt (hooks._PHASE) 与 session (PHASE_OF) 均映射 exec。"""
    _start_task(skein_cli, ws, "task-m")
    # prompt 不能用 _EXPLICIT 里的词 (go/exec/do/plan/继续/continue) 或 skein-*: 那些早退不注入
    # (显式走 flow 无需路由提示)。「继续」曾用在这里, 2026-08-01 被划进 _EXPLICIT 后换掉。
    assert "task-m(exec)" in _user_prompt(ws, "接着往下做"), "hooks _PHASE 映射 进行中→exec 失效"
    assert "task-m(exec)" in _session_ctx(ws), "skein PHASE_OF 映射 进行中→exec 失效"
