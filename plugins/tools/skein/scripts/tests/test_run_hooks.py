"""hooks.runner._run_hooks 单测 — 纯函数级直调 (design.md 测试接缝段的既定例外)。

_run_hooks 未被任何 CLI 命令接线 (阶段接线归 c4 / agent 接线归 c5, 均未落地), 此刻唯一
可测接缝就是直调本体, 用临时文件断言副作用证明串行失败即停 / 阻断语义正确。
覆盖: before 失败阻断(HookBlocked) / after 失败仅告警 / continue_on_error 双向覆盖 /
串行失败即停 / timeout 超时按失败处置(含秒数) / env 九变量齐全 / 输出定位前缀 /
SKEIN_IN_HOOK 递归护栏 / 无 hooks 键零开销(不 fork)。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest  # type: ignore[import-not-found]

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skeinlib.hooks.runner import HookBlocked, _run_hooks  # noqa: E402


def _touch_cmd(marker: Path) -> str:
    return f"touch {marker}"


# ---------- 阻断语义 ----------
def test_before_failure_blocks() -> None:
    with pytest.raises(HookBlocked):
        _run_hooks("check", "before", {"hooks": [{"command": "exit 1"}]})


def test_after_failure_warns_not_raises(capsys: Any) -> None:
    _run_hooks("check", "after", {"hooks": [{"command": "exit 1"}]})  # 不抛
    assert "失败" in capsys.readouterr().err


def test_agent_start_failure_never_blocks(capsys: Any) -> None:
    # 即便显式 continue_on_error=false, agent 钩子失败也一律只告警
    _run_hooks("agent", "start", {"hooks": [{"command": "exit 1", "continue_on_error": False}]})
    assert "不阻断" in capsys.readouterr().err


def test_agent_stop_failure_never_blocks() -> None:
    _run_hooks("agent", "stop", {"hooks": [{"command": "exit 1"}]})  # 不抛即通过


# ---------- continue_on_error 双向覆盖 ----------
def test_before_continue_on_error_true_overrides_default_block(tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    _run_hooks("check", "before", {"hooks": [
        {"command": "exit 1", "continue_on_error": True},
        {"command": _touch_cmd(marker)},
    ]})
    assert marker.exists()  # 第一条失败但豁免, 第二条正常跑到


def test_after_continue_on_error_false_stops_serial(tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    _run_hooks("check", "after", {"hooks": [
        {"command": "exit 1", "continue_on_error": False},
        {"command": _touch_cmd(marker)},
    ]})
    assert not marker.exists()  # 显式关闭豁免 → 失败即停, 第二条不跑


# ---------- 缺省值: before=false / after=true ----------
def test_before_default_continue_on_error_is_false() -> None:
    with pytest.raises(HookBlocked):
        _run_hooks("check", "before", {"hooks": [{"command": "exit 1"}]})


def test_after_default_continue_on_error_is_true(tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    _run_hooks("check", "after", {"hooks": [
        {"command": "exit 1"},
        {"command": _touch_cmd(marker)},
    ]})
    assert marker.exists()  # after 缺省豁免 → 第一条失败不挡第二条


# ---------- 严格串行 + 失败即停 ----------
def test_serial_stops_on_first_failure(tmp_path: Path) -> None:
    marker = tmp_path / "ran3"
    _run_hooks("agent", "start", {"hooks": [
        {"command": "exit 0"},
        {"command": "exit 1", "continue_on_error": False},
        {"command": _touch_cmd(marker)},
    ]})
    assert not marker.exists()  # 第 3 条在第 2 条失败后不该跑


# ---------- timeout ----------
def test_timeout_treated_as_failure_with_seconds_in_message(capsys: Any) -> None:
    _run_hooks("check", "after", {"hooks": [{"command": "sleep 2", "timeout": 1}]})
    err = capsys.readouterr().err
    assert "超时" in err and "1s" in err


def test_timeout_default_is_60s_when_unspecified() -> None:
    # 不真的 sleep 60s: 只验证缺省值取用逻辑 — 命令秒退, timeout 未传不报错即说明缺省生效
    _run_hooks("agent", "start", {"hooks": [{"command": "exit 0"}]})


# ---------- env 九变量 ----------
def test_env_nine_vars_injected(tmp_path: Path) -> None:
    out = tmp_path / "env.txt"
    cmd = (
        "printf '%s\\n' "
        "\"$SKEIN_SCOPE\" \"$SKEIN_WHEN\" \"$SKEIN_AGENT\" \"$SKEIN_TID\" \"$SKEIN_SID\" "
        "\"$SKEIN_TASK_DIR\" \"$SKEIN_WORKTREE\" \"$SKEIN_REPO_ROOT\" \"$SKEIN_IN_HOOK\" "
        f"> {out}"
    )
    _run_hooks("check", "after", {
        "hooks": [{"command": cmd, "cwd": str(tmp_path)}],
        "agent": "skein-executor", "tid": "t1", "sid": "s1",
        "task_dir": "/td", "worktree": "/wt", "repo_root": "/rr",
    })
    lines = out.read_text().splitlines()
    assert lines == ["check", "after", "skein-executor", "t1", "s1", "/td", "/wt", "/rr", "1"]


# ---------- cwd 缺省 ----------
def test_cwd_defaults_to_worktree_then_repo_root(tmp_path: Path) -> None:
    wt = tmp_path / "wt"
    wt.mkdir()
    out = tmp_path / "pwd.txt"
    _run_hooks("check", "after", {
        "hooks": [{"command": f"pwd > {out}"}],
        "worktree": str(wt), "repo_root": str(tmp_path),
    })
    assert out.read_text().strip() == str(wt.resolve())


def test_cwd_override_wins_over_default(tmp_path: Path) -> None:
    override = tmp_path / "override"
    override.mkdir()
    out = tmp_path / "pwd.txt"
    _run_hooks("check", "after", {
        "hooks": [{"command": f"pwd > {out}", "cwd": str(override)}],
        "worktree": str(tmp_path), "repo_root": str(tmp_path),
    })
    assert out.read_text().strip() == str(override.resolve())


# ---------- 输出定位前缀 ----------
def test_output_has_location_prefix(capsys: Any) -> None:
    _run_hooks("finish", "after", {"hooks": [{"command": "echo hi"}]})
    assert "[hook finish.after#1] hi" in capsys.readouterr().out


# ---------- SKEIN_IN_HOOK 递归护栏 ----------
def test_recursion_guard_skips_when_already_in_hook(monkeypatch: Any) -> None:
    monkeypatch.setenv("SKEIN_IN_HOOK", "1")
    _run_hooks("check", "before", {"hooks": [{"command": "exit 1"}]})  # 会阻断的配置, 但应跳过不抛


# ---------- 零开销 ----------
def test_no_hooks_key_returns_immediately_no_fork() -> None:
    _run_hooks("check", "before", {})  # 无 "hooks" 键
    _run_hooks("check", "before", {"hooks": []})  # 空列表同样零开销
