"""回复前缀强制注入测试 — 两注入点: UserPromptSubmit (hooks.py) + SessionStart (skein.py)。

经 conftest 的 ws/skein_cli fixture 跑真实脚本子进程 (tmp_path 隔离)。
覆盖 (5 用例):
  1. user-prompt 普通 prompt → additionalContext 含 `[skein]` + 前缀规则关键字。
  2. user-prompt (create+start 一个进行中 task) → 含 task id 且标注 `(exec)`。
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
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def _session_ctx(cwd: Path) -> str:
    """跑 skein.py session-context, 返 additionalContext。"""
    r = subprocess.run(
        [sys.executable, str(SKEIN), "session-context"], cwd=cwd,
        capture_output=True, text=True, check=True)
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def _fill_prd(ws: Path, tid: str) -> None:
    """写规范 prd.md 过 start 的 _validate_prd 门 (章节齐 + 无 TODO 占位)。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n"
        "## 边界\n- a\n\n## 验收标准\n- 通过\n\n## 索引\n- design.md\n")


def _start_task(skein_cli: SkeinCli, ws: Path, tid: str) -> None:
    """create + subtask + prd + start → task 进入进行中 (active)。"""
    skein_cli(ws, "create", tid, "--name", "n", "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s1", "--name", "x", "--desc", "d",
              "--agent", "skein-executor")
    _fill_prd(ws, tid)
    skein_cli(ws, "start", tid)


# ---------- 1. user-prompt 注入前缀规则 ----------
def test_user_prompt_injects_prefix_rule(ws: Path) -> None:
    """普通 prompt → additionalContext 含 `[skein]` + 前缀规则关键字。"""
    ctx = _user_prompt(ws, "帮我看看这个函数")
    assert "[skein]" in ctx, f"缺 [skein] 前缀标记: {ctx!r}"
    assert "回复前缀" in ctx, f"缺前缀规则关键字: {ctx!r}"


# ---------- 2. user-prompt 列 active task 阶段 ----------
def test_user_prompt_lists_active_task_phase(skein_cli: SkeinCli, ws: Path) -> None:
    """create+start task (进行中) → additionalContext 含 id 且标注 (exec)。"""
    _start_task(skein_cli, ws, "task-a")
    ctx = _user_prompt(ws, "继续")
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
    assert "task-m(exec)" in _user_prompt(ws, "go"), "hooks _PHASE 映射 进行中→exec 失效"
    assert "task-m(exec)" in _session_ctx(ws), "skein PHASE_OF 映射 进行中→exec 失效"
