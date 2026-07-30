"""9 个阶段命令 (create/confirm/start/check/finish/archive/subtask.start/done/fail) 的
before/after 钩子接线测试 (config-hooks/c4) — 唯一接缝 = CLI 命令边界 (design.md 测试接缝段):
经真实 skein.py 子进程跑, 断言退出码 + 钩子副作用 (标记文件), 不断言内部实现。

覆盖 4 条验收 + c8 补的 recursion guard CLI 级用例:
1. 9 个阶段的 before/after 均能触发
2. check.before 失败使 check 不发生 (阻断语义 — 本特性核心价值)
3. 非法阶段名报错且列出全部合法值
4. 未配钩子的阶段行为零变化 (既有 test_statemachine.py 全绿即证明, 本文件只加 hooks 场景)
5. Recursion Guard: 钩子里调真实 skein 命令不触发嵌套钩子 (design.md §6) —
   test_run_hooks.py 只 monkeypatch 了 SKEIN_IN_HOOK, 本文件补真实子进程套子进程的场景
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

from conftest import HOOKS, HooksCli

SkeinCli = Callable[..., subprocess.CompletedProcess[str]]

SID = "sub-build"


def _mk(skein_cli: SkeinCli, ws: Path, tid: str = "feat-x", *,
        sub: bool = False, ready: bool = False) -> str:
    """造 task。sub=附 1 subtask + 填实 prd; ready=再 confirm 推到就绪。复用 test_statemachine.py 同名 helper。"""
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    if sub or ready:
        skein_cli(ws, "subtask", "add", tid, SID, "--name", "S", "--desc", "d", "--estimate", "1")
        _fill_prd(ws, tid)
    if ready:
        skein_cli(ws, "estimate", tid, "--set", "1")
        skein_cli(ws, "confirm", tid)
    return tid


def _fill_prd(ws: Path, tid: str) -> None:
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n"
        "## 目标\n- 解决 X 问题\n\n"
        "## 边界\n- 范围内: a\n\n"
        "## 验收标准\n- 用例通过\n\n"
        "## 索引\n- design.md\n")


def _append_hooks_yaml(ws: Path, body: str) -> None:
    with open(ws / ".skein" / "config.yaml", "a", encoding="utf-8") as f:
        f.write(body)


def _find(ws: Path, name: str) -> bool:
    """标记文件可能落 repo 根或 task worktree (cwd 缺省: worktree 已配则 worktree), 全仓搜。"""
    return any(ws.rglob(name))


# ---------- 验收1: 9 个阶段的 before/after 均能触发 ----------

def test_create_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    _append_hooks_yaml(ws, """
hooks:
  create:
    before:
      - command: "touch create-before.marker"
    after:
      - command: "touch create-after.marker"
""")
    r = skein_cli(ws, "create", "feat-a", "--name", "feat-a", "--desc", "d")
    assert r.returncode == 0
    assert _find(ws, "create-before.marker")
    assert _find(ws, "create-after.marker")


def test_confirm_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-b", sub=True)
    skein_cli(ws, "estimate", tid, "--set", "1")
    _append_hooks_yaml(ws, """
hooks:
  confirm:
    before:
      - command: "touch confirm-before.marker"
    after:
      - command: "touch confirm-after.marker"
""")
    r = skein_cli(ws, "confirm", tid)
    assert r.returncode == 0
    assert _find(ws, "confirm-before.marker")
    assert _find(ws, "confirm-after.marker")


def test_start_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-c", ready=True)
    _append_hooks_yaml(ws, """
hooks:
  start:
    before:
      - command: "touch start-before.marker"
    after:
      - command: "touch start-after.marker"
""")
    r = skein_cli(ws, "start", tid)
    assert r.returncode == 0, r.stderr
    assert _find(ws, "start-before.marker")
    assert _find(ws, "start-after.marker")


def test_check_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-d", ready=True)
    skein_cli(ws, "start", tid)
    _append_hooks_yaml(ws, """
hooks:
  check:
    before:
      - command: "touch check-before.marker"
    after:
      - command: "touch check-after.marker"
""")
    r = skein_cli(ws, "check", tid)
    assert r.returncode == 0
    assert _find(ws, "check-before.marker")
    assert _find(ws, "check-after.marker")


def test_finish_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-e", ready=True)
    skein_cli(ws, "start", tid)
    _append_hooks_yaml(ws, """
hooks:
  finish:
    before:
      - command: "touch finish-before.marker"
    after:
      - command: "touch finish-after.marker"
""")
    r = skein_cli(ws, "finish", tid)
    assert r.returncode == 0, r.stderr
    assert _find(ws, "finish-before.marker")
    assert _find(ws, "finish-after.marker")


def test_archive_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-f", ready=True)
    skein_cli(ws, "start", tid)
    skein_cli(ws, "finish", tid)
    _append_hooks_yaml(ws, """
hooks:
  archive:
    before:
      - command: "touch archive-before.marker"
    after:
      - command: "touch archive-after.marker"
""")
    r = skein_cli(ws, "archive", tid)
    assert r.returncode == 0
    assert _find(ws, "archive-before.marker")
    assert _find(ws, "archive-after.marker")


def test_subtask_start_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-g", ready=True)
    skein_cli(ws, "start", tid)
    _append_hooks_yaml(ws, """
hooks:
  subtask.start:
    before:
      - command: "touch sub-start-before.marker"
    after:
      - command: "touch sub-start-after.marker"
""")
    r = skein_cli(ws, "subtask", "start", tid, SID)
    assert r.returncode == 0, r.stderr
    assert _find(ws, "sub-start-before.marker")
    assert _find(ws, "sub-start-after.marker")


def test_subtask_done_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-h", ready=True)
    skein_cli(ws, "start", tid)
    skein_cli(ws, "subtask", "start", tid, SID)
    _append_hooks_yaml(ws, """
hooks:
  subtask.done:
    before:
      - command: "touch sub-done-before.marker"
    after:
      - command: "touch sub-done-after.marker"
""")
    r = skein_cli(ws, "subtask", "done", tid, SID)
    assert r.returncode == 0, r.stderr
    assert _find(ws, "sub-done-before.marker")
    assert _find(ws, "sub-done-after.marker")


def test_subtask_fail_before_and_after_fire(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-i", ready=True)
    skein_cli(ws, "start", tid)
    skein_cli(ws, "subtask", "start", tid, SID)
    _append_hooks_yaml(ws, """
hooks:
  subtask.fail:
    before:
      - command: "touch sub-fail-before.marker"
    after:
      - command: "touch sub-fail-after.marker"
""")
    r = skein_cli(ws, "subtask", "fail", tid, SID)
    assert r.returncode == 0, r.stderr
    assert _find(ws, "sub-fail-before.marker")
    assert _find(ws, "sub-fail-after.marker")


# ---------- 验收2: before 失败阻断阶段 (核心价值) ----------

def test_check_before_failure_blocks_stage(skein_cli: SkeinCli, ws: Path) -> None:
    """check.before 跑 lint 失败(exit 1) → check 不发生: 命令非零退出 + 状态仍是 active。"""
    tid = _mk(skein_cli, ws, "feat-j", ready=True)
    skein_cli(ws, "start", tid)
    _append_hooks_yaml(ws, """
hooks:
  check:
    before:
      - command: "exit 1"
""")
    r = skein_cli(ws, "check", tid, check=False)
    assert r.returncode != 0
    out = skein_cli(ws, "list").stdout
    assert "检查中" not in out.split(tid, 1)[-1].split("\n")[0], "check.before 失败仍进了检查中 — 阻断未生效"
    assert "进行中" in out


def test_before_continue_on_error_overrides_default_block(skein_cli: SkeinCli, ws: Path) -> None:
    """continue_on_error=true 显式覆盖 before 缺省阻断 — 阶段照常发生。"""
    tid = _mk(skein_cli, ws, "feat-k", ready=True)
    skein_cli(ws, "start", tid)
    _append_hooks_yaml(ws, """
hooks:
  check:
    before:
      - command: "exit 1"
        continue_on_error: true
""")
    r = skein_cli(ws, "check", tid)
    assert r.returncode == 0, r.stderr


def test_after_failure_only_warns_stage_result_unchanged(skein_cli: SkeinCli, ws: Path) -> None:
    """after 失败只 warning, 阶段结果不变 — check 仍成功切换态, 命令仍 exit 0。"""
    tid = _mk(skein_cli, ws, "feat-l", ready=True)
    skein_cli(ws, "start", tid)
    _append_hooks_yaml(ws, """
hooks:
  check:
    after:
      - command: "exit 1"
""")
    r = skein_cli(ws, "check", tid)
    assert r.returncode == 0, r.stderr
    out = skein_cli(ws, "list").stdout
    assert "检查中" in out


# ---------- 验收3: 非法阶段名报错 + 列全部合法值 ----------

_BAD_STAGE = """
hooks:
  chekc:
    before:
      - command: "touch never.marker"
"""


def test_illegal_stage_name_warns_but_does_not_block(skein_cli: SkeinCli, ws: Path) -> None:
    """拼错的阶段名: stderr 告警 + 列全部合法值, 但**不阻断**普通命令。

    告警不阻断是刻意的 —— _hooks_cfg 在钩子热路径上, 一个配置笔误不该让每条 skein 命令都退非零
    (与 _yaml_bad 同策略)。硬判定归 doctor, 见下一条测试。
    """
    _append_hooks_yaml(ws, _BAD_STAGE)
    r = skein_cli(ws, "create", "feat-m", "--name", "feat-m", "--desc", "d", check=False)
    assert r.returncode == 0, f"配置笔误不该阻断 create: {r.stderr}"
    assert "chekc" in r.stderr, f"未告警拼错的阶段名: {r.stderr}"
    for legal in ("create", "confirm", "start", "exec", "check", "finish", "archive",
                  "subtask.start", "subtask.done", "subtask.fail"):
        assert legal in r.stderr, f"合法阶段名清单缺 {legal}"
    assert not _find(ws, "never.marker"), "非法阶段名不该被静默执行"


def test_illegal_stage_name_is_doctor_error(skein_cli: SkeinCli, ws: Path) -> None:
    """doctor 把同一笔误判为 ✗ error (非 ⚠ warning) — 用户主动跑、看得见的地方才硬报。"""
    _append_hooks_yaml(ws, _BAD_STAGE)
    r = skein_cli(ws, "doctor", check=False)
    out = r.stdout + r.stderr
    assert "chekc" in out, f"doctor 未报拼错的阶段名: {out}"
    assert any(ln.startswith("✗") and "chekc" in ln for ln in out.splitlines()), \
        f"doctor 该判 error(✗) 而非 warning: {out}"


def test_unknown_entry_field_is_reported(skein_cli: SkeinCli, ws: Path) -> None:
    """条目里的未知字段不静默忽略 (静默降级 = 配置无声失效, design.md §3)。"""
    _append_hooks_yaml(ws, """
hooks:
  create:
    before:
      - command: "touch fieldtest.marker"
        tiemout: 5
""")
    r = skein_cli(ws, "doctor", check=False)
    out = r.stdout + r.stderr
    assert "tiemout" in out, f"未知字段未报出: {out}"


# ---------- 验收4: 未配钩子零行为变化 ----------

def test_no_hooks_key_stage_behavior_unchanged(skein_cli: SkeinCli, ws: Path) -> None:
    """无 hooks 键: create 行为与既有 test_statemachine.py 断言一致 (exit 0, 落 pending)。"""
    r = skein_cli(ws, "create", "feat-n", "--name", "feat-n", "--desc", "d")
    assert r.returncode == 0
    out = skein_cli(ws, "list").stdout
    assert "feat-n" in out and "待处理" in out


def test_hooks_key_present_but_other_stage_unconfigured_zero_overhead(skein_cli: SkeinCli, ws: Path) -> None:
    """hooks 键存在但当前跑的阶段 (create) 未配 — 零开销: 不触发任何标记, create 正常成功。
    只断言副作用 (标记文件不存在), 不做性能计时 (c8 铁律: 计时不稳定)。"""
    _append_hooks_yaml(ws, """
hooks:
  confirm:
    before:
      - command: "touch confirm-only.marker"
""")
    r = skein_cli(ws, "create", "feat-o", "--name", "feat-o", "--desc", "d")
    assert r.returncode == 0
    assert not _find(ws, "confirm-only.marker")


# ---------- 验收5: Recursion Guard (真实子进程套子进程, design.md §6) ----------
#
# 用 hooks.py agent-start (无 .skein flock) 而非 skein.py 阶段命令 (create 等持写锁) 做嵌套调用 —
# 若嵌套调 create 之类写命令, 外层 after 钩子仍在锁内运行, 嵌套子进程等锁会超时, 混进另一条
# (锁内嵌套) 结论, 污染本用例只想测的递归护栏。agent-start 无锁, 干净隔离出护栏本身。

def test_recursion_guard_nested_hook_call_skips_own_hooks(ws: Path, hooks_cli: HooksCli) -> None:
    """agent-start 钩子里真的再调一次 `hooks.py agent-start`(同一 agent, 同样配了 start)。
    _run_hooks 给子进程注入 SKEIN_IN_HOOK=1, 该 env 会被 shell 派生的嵌套 hooks.py 进程继承 —
    嵌套调用完成时自己的 start 钩子应被递归护栏跳过, 不再往下钻一层。
    断言: 计数文件只被写入 1 次 (外层那次), 而非 2 次 (若护栏失效)。
    """
    nested_cmd = f'{sys.executable} {HOOKS} agent-start --agent skein-executor --cwd {ws}'
    with open(ws / ".skein" / "config.yaml", "a", encoding="utf-8") as f:
        f.write(f"""
hooks:
  agent:
    skein-executor:
      start:
        - command: "echo fired >> after-fired.log"
        - command: "{nested_cmd}"
""")
    r = hooks_cli(ws, "agent-start", "--agent", "skein-executor", "--cwd", str(ws))
    assert r.returncode == 0
    log = (ws / "after-fired.log").read_text()
    assert log.count("fired") == 1, "递归护栏未生效 — 嵌套调用的 start 钩子不该再跑"
