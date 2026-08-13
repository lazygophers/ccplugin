"""utils / hooks / cli / task 的进程内单元测试 — 直调函数, 不走 subprocess。

分区对应被测模块: utils(fs/timefmt/exec_policy/debug/token_conversion) →
hooks(__init__/cli/agent/stop/pre_tool_use/post_tool_use/user_prompt_submit) →
cli(main) → task(prd/readystate/store/migrate/priority/timeline)。

状态串一律走 TaskStatus / SubtaskStatus 枚举 (英文落盘), 中文只在展示层出现。
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterator

import pytest

from skeinlib.task.model import SubtaskStatus, TaskStatus

# ── skeinlib.utils.fs ─────────────────────────────────────────────────────────


def test_fs_git_root_walks_up_to_dot_git(tmp_path: Path) -> None:
    """git_root 从深层子目录逐级上溯, 命中含 .git/ 的那层即停。"""
    from skeinlib.utils.fs import git_root

    (tmp_path / ".git").mkdir()
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert git_root(str(deep)) == str(tmp_path.resolve())


def test_fs_git_root_falls_back_to_start_when_no_git(tmp_path: Path) -> None:
    """上溯到文件系统根仍无 .git → 退回起点绝对路径 (而非 '/' )。"""
    from skeinlib.utils.fs import git_root

    d = tmp_path / "nogit"
    d.mkdir()
    assert git_root(str(d)) == str(d.resolve())


def test_fs_git_root_empty_start_means_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """空串 start 按 '.' 解, 即当前工作目录。"""
    from skeinlib.utils.fs import git_root

    monkeypatch.chdir(tmp_path)
    assert git_root("") == str(tmp_path.resolve())


def test_fs_load_stdin_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """stdin 是合法 JSON 对象 → 返回 dict。"""
    from skeinlib.utils.fs import load_stdin

    monkeypatch.setattr("sys.stdin", io.StringIO('{"a": 1}'))
    assert load_stdin() == {"a": 1}


def test_fs_load_stdin_returns_none_on_garbage(monkeypatch: pytest.MonkeyPatch) -> None:
    """stdin 非 JSON → None (hook 调用方据此静默退出, 不炸)。"""
    from skeinlib.utils.fs import load_stdin

    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert load_stdin() is None


def test_fs_prefix_lines_tags_each_line() -> None:
    """逐行加前缀且每行补换行; 空串 → 空串 (不产生孤立换行)。"""
    from skeinlib.utils.fs import prefix_lines

    assert prefix_lines("[t]", "a\nb") == "[t] a\n[t] b\n"
    assert prefix_lines("[t]", "") == ""


# ── skeinlib.utils.timefmt ────────────────────────────────────────────────────


def test_timefmt_fmt_ts_formats_and_handles_zero() -> None:
    """epoch → 本地 '%Y-%m-%d %H:%M'; None/0 一律 '-'。"""
    from skeinlib.utils.timefmt import fmt_ts

    ts = 1700000000
    assert fmt_ts(ts) == time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
    assert fmt_ts(None) == "-"
    assert fmt_ts(0) == "-"


# ── skeinlib.utils.exec_policy ────────────────────────────────────────────────


def _tail(argv: list[str] | None) -> list[str]:
    """剥掉 [python, skein.py] 前缀, 只留业务 argv。"""
    assert argv is not None
    return argv[2:]


def test_exec_policy_readonly_commands() -> None:
    """只读类 cmd: list/ready/doctor 无必填参数, list 的 status 可选。"""
    from skeinlib.utils.exec_policy import exec_argv

    assert _tail(exec_argv({"cmd": "list"})) == ["list", "--json"]
    assert _tail(exec_argv({"cmd": "list", "status": "open"})) == ["list", "--json", "--status", "open"]
    # 空白 status 视同未给 (s() 会 strip 后判空)
    assert _tail(exec_argv({"cmd": "list", "status": "   "})) == ["list", "--json"]
    assert _tail(exec_argv({"cmd": "ready"})) == ["ready"]
    assert _tail(exec_argv({"cmd": "doctor"})) == ["doctor"]


def test_exec_policy_status_requires_id_and_takes_optional_sid() -> None:
    """status 无 id 直接拒; sid 可选, 给了就追加在 id 后。"""
    from skeinlib.utils.exec_policy import exec_argv

    assert exec_argv({"cmd": "status"}) is None
    assert _tail(exec_argv({"cmd": "status", "id": "t1"})) == ["status", "t1", "--json"]
    assert _tail(exec_argv({"cmd": "status", "id": "t1", "sid": "s1"})) == ["status", "t1", "s1", "--json"]


def test_exec_policy_single_id_commands() -> None:
    """subtask-list/confirm/finish/del: 只认 id, 缺 id 一律拒。"""
    from skeinlib.utils.exec_policy import exec_argv

    assert _tail(exec_argv({"cmd": "subtask-list", "id": "t1"})) == ["subtask", "list", "t1"]
    assert exec_argv({"cmd": "subtask-list"}) is None
    assert _tail(exec_argv({"cmd": "confirm", "id": "t1"})) == ["task", "confirm", "t1", "--approved"]
    assert exec_argv({"cmd": "confirm"}) is None
    assert _tail(exec_argv({"cmd": "finish", "id": "t1"})) == ["task", "finish", "t1"]
    assert exec_argv({"cmd": "finish"}) is None
    assert _tail(exec_argv({"cmd": "del", "id": "t1"})) == ["del", "t1"]
    assert exec_argv({"cmd": "del"}) is None


def test_exec_policy_create_requires_id_name_desc() -> None:
    """create 三项必填, 缺一即拒; deps 可选。"""
    from skeinlib.utils.exec_policy import exec_argv

    assert exec_argv({"cmd": "create", "id": "t1", "name": "n"}) is None
    body = {"cmd": "create", "id": "t1", "name": "n", "desc": "d"}
    assert _tail(exec_argv(body)) == ["task", "create", "t1", "--name", "n", "--desc", "d"]
    assert _tail(exec_argv({**body, "deps": "t0"}))[-2:] == ["--deps", "t0"]


def test_exec_policy_subtask_add_requires_five_fields() -> None:
    """subtask-add 五项必填 (id/sid/name/desc/estimate), deps 可选。"""
    from skeinlib.utils.exec_policy import exec_argv

    body = {"cmd": "subtask-add", "id": "t1", "sid": "s1", "name": "n", "desc": "d", "estimate": "2"}
    assert _tail(exec_argv(body)) == ["subtask", "add", "t1", "s1", "--name", "n",
                                      "--desc", "d", "--estimate", "2"]
    assert _tail(exec_argv({**body, "deps": "s0"}))[-2:] == ["--deps", "s0"]
    assert exec_argv({**body, "estimate": ""}) is None


def test_exec_policy_clean_days_type_gate() -> None:
    """clean 的 days: bool 与非 int/str 类型拒, 非数字串拒, 负数拒, 数字串接受。"""
    from skeinlib.utils.exec_policy import exec_argv

    assert _tail(exec_argv({"cmd": "clean"})) == ["clean", "--days", "0"]
    assert _tail(exec_argv({"cmd": "clean", "days": "7"})) == ["clean", "--days", "7"]
    assert exec_argv({"cmd": "clean", "days": True}) is None  # bool 是 int 子类, 必须先挡
    assert exec_argv({"cmd": "clean", "days": [1]}) is None
    assert exec_argv({"cmd": "clean", "days": "x"}) is None
    assert exec_argv({"cmd": "clean", "days": -1}) is None


def test_exec_policy_priority_requires_id_and_set() -> None:
    """priority 需 id + set 两者齐备。"""
    from skeinlib.utils.exec_policy import exec_argv

    assert _tail(exec_argv({"cmd": "priority", "id": "t1", "set": "high"})) == [
        "task", "priority", "t1", "--set", "high"]
    assert exec_argv({"cmd": "priority", "id": "t1"}) is None


def test_exec_policy_prd_action_whitelist() -> None:
    """prd: action 限五值; 非 read 时 --list 必给 (缺则拒); read 不带 --list。"""
    from skeinlib.utils.exec_policy import exec_argv

    base = {"cmd": "prd", "id": "t1", "type": "goal"}
    assert _tail(exec_argv({**base, "action": "read"})) == ["prd", "read", "t1", "--type", "goal"]
    assert exec_argv({**base, "action": "drop"}) is None
    assert exec_argv({**base, "action": "write"}) is None  # 缺 --list
    assert _tail(exec_argv({**base, "action": "write", "list": "x"})) == [
        "prd", "write", "t1", "--type", "goal", "--list", "x"]
    assert exec_argv({"cmd": "prd", "id": "t1", "action": "read"}) is None  # 缺 type


def test_exec_policy_rejects_unknown_cmd() -> None:
    """白名单外的 cmd 一律 None — 这是「绝不 shell 拼串」的兜底。"""
    from skeinlib.utils.exec_policy import exec_argv

    assert exec_argv({"cmd": "rm -rf /"}) is None
    assert exec_argv({}) is None


# ── skeinlib.utils.debug ──────────────────────────────────────────────────────


def test_debug_enabled_reads_args_then_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """args.debug 优先; 否则看 SKEIN_DEBUG, 空/0/false/no 都算关。"""
    from skeinlib.utils.debug import debug_enabled

    monkeypatch.delenv("SKEIN_DEBUG", raising=False)
    assert debug_enabled(None) is False
    assert debug_enabled(type("A", (), {"debug": True})()) is True
    for off in ("", "0", "false", "NO"):
        monkeypatch.setenv("SKEIN_DEBUG", off)
        assert debug_enabled(None) is False
    monkeypatch.setenv("SKEIN_DEBUG", "1")
    assert debug_enabled(None) is True


@pytest.fixture
def no_rich(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """把 rich.console 打成不可导入 — 逼 Debug 走 sys.stderr 纯文本降级分支。"""
    monkeypatch.setitem(sys.modules, "rich.console", None)
    monkeypatch.setitem(sys.modules, "rich.table", None)
    yield


def test_debug_disabled_swallows_log_but_not_warn(capsys: pytest.CaptureFixture[str],
                                                  no_rich: None) -> None:
    """enabled=False: log/rule/kv 静默, 但 warn/error 照出 (它们不看开关)。"""
    from skeinlib.utils.debug import Debug

    d = Debug(False)
    d.log("hidden")
    d.rule("hidden-rule")
    d.kv({"k": "v"}, title="hidden-kv")
    d.warn("W")
    d.error("E")
    err = capsys.readouterr().err
    assert "hidden" not in err
    assert "W\n" in err and "E\n" in err


def test_debug_enabled_plain_text_fallback(capsys: pytest.CaptureFixture[str],
                                           no_rich: None) -> None:
    """rich 不可用时 log/rule/kv 全走 stderr 纯文本, 且 kv 空 mapping 直接跳过。"""
    from skeinlib.utils.debug import Debug

    d = Debug(True)
    assert d.c is None
    d.log("L")
    d.rule("R")
    d.kv({"a": 1}, title="T")
    d.kv({})  # 空 mapping → 无输出
    err = capsys.readouterr().err
    assert "L\n" in err
    assert "──── R ────" in err
    assert "T\n" in err and "  a: 1\n" in err


def test_debug_rich_path_uses_console(monkeypatch: pytest.MonkeyPatch) -> None:
    """rich 可用时 _emit/rule/kv 全落到 Console, 不走 stderr。"""
    from skeinlib.utils.debug import Debug

    d = Debug(True)
    if d.c is None:
        pytest.skip("环境无 rich")
    calls: list[str] = []
    monkeypatch.setattr(type(d.c), "print", lambda self, *a, **k: calls.append("print"))
    monkeypatch.setattr(type(d.c), "rule", lambda self, *a, **k: calls.append("rule"))
    d.log("x")
    d.rule("y")
    d.kv({"a": 1}, title="t")
    assert calls == ["print", "rule", "print"]


def test_debug_enable_is_idempotent_on_console() -> None:
    """重复 enable(True) 不重建 Console (self.c 已有就不动)。"""
    from skeinlib.utils.debug import Debug

    d = Debug(True)
    first = d.c
    d.enable(True)
    assert d.c is first


def test_est_tokens_and_budget_guard(capsys: pytest.CaptureFixture[str]) -> None:
    """est_tokens = 字符数//4; 未超预算原样返回, 超了硬截断并写 stderr 告警。"""
    from skeinlib.utils.debug import budget_guard, est_tokens

    assert est_tokens("a" * 40) == 10
    text = "a" * 40
    assert budget_guard(text, 10, "x") is text
    long = "b" * 400
    out = budget_guard(long, 10, "core")
    assert out.startswith("b" * 40) and "超预算已截断" in out
    assert "[skein hook:core]" in capsys.readouterr().err


# ── skeinlib.utils.token_conversion ───────────────────────────────────────────


def test_token_conversion_estimate_and_info() -> None:
    """字符→token 保守估算向上取整; info 文案含系数与误差范围。"""
    from skeinlib.utils.token_conversion import (CHAR_TO_TOKEN_RATIO, MAX_RATIO, MIN_RATIO,
                                                 estimate_tokens_from_chars, get_conversion_info)

    assert estimate_tokens_from_chars(0) == 0
    assert estimate_tokens_from_chars(1) == 1  # 0.58 向上取整
    assert estimate_tokens_from_chars(100) == 58
    info = get_conversion_info()
    assert str(CHAR_TO_TOKEN_RATIO) in info
    assert str(MIN_RATIO) in info and str(MAX_RATIO) in info


# ── skeinlib.hooks.__init__ (re-export + _run_hooks 引擎) ─────────────────────


def test_hooks_pkg_helpers_mirror_utils_fs(monkeypatch: pytest.MonkeyPatch) -> None:
    """hooks 包内的 git_root/load_stdin/prefix_lines 与 utils.fs 同行为 (历史 re-export 面)。"""
    import skeinlib.hooks as H

    monkeypatch.setattr("sys.stdin", io.StringIO('{"k": 1}'))
    assert H.load_stdin() == {"k": 1}
    monkeypatch.setattr("sys.stdin", io.StringIO("<xml/>"))
    assert H.load_stdin() is None
    assert H.prefix_lines("#", "x") == "# x\n"
    assert H._prefix_lines("#", "x") == "# x\n"


def test_hooks_pkg_getattr_lazy_maintain_policy() -> None:
    """__getattr__ 懒转 MAINTAIN_POLICY 到 spec.model; 其余名字仍 AttributeError。"""
    import skeinlib.hooks as H
    from skeinlib.spec.model import MAINTAIN_POLICY

    assert H.MAINTAIN_POLICY is MAINTAIN_POLICY
    with pytest.raises(AttributeError):
        H.nonexistent_symbol  # noqa: B018


def test_run_hooks_noop_without_hooks_or_when_nested(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 hooks 或已在 hook 内 (SKEIN_IN_HOOK) → 直接返回, 不起子进程 (防递归)。"""
    from skeinlib.hooks.runner import _run_hooks

    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    called: list[Any] = []
    monkeypatch.setattr("subprocess.run", lambda *a, **k: called.append(a))
    _run_hooks("task", "before", {"hooks": []})
    monkeypatch.setenv("SKEIN_IN_HOOK", "1")
    _run_hooks("task", "before", {"hooks": [{"command": "true"}]})
    assert called == []


def test_run_hooks_pipes_stdout_stderr_with_tag(capsys: pytest.CaptureFixture[str],
                                                monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """成功 hook 的 stdout/stderr 逐行带 [hook scope.when#N] 前缀转发。"""
    from skeinlib.hooks.runner import _run_hooks

    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    _run_hooks("task", "after", {"hooks": [{"command": "echo out; echo err >&2"}],
                                 "repo_root": str(tmp_path)})
    cap = capsys.readouterr()
    assert "[hook task.after#1] out\n" in cap.out
    assert "[hook task.after#1] err\n" in cap.err


def test_run_hooks_timeout_is_a_failure(capsys: pytest.CaptureFixture[str],
                                        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """超时按失败处理: 打「超时(>Ns)」, 且 before 阶段 (非 agent) 抛 HookBlocked 阻断。"""
    from skeinlib.hooks.runner import HookBlocked, _run_hooks

    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    hooks = [{"command": "sleep 5", "timeout": 1, "continue_on_error": False}]
    with pytest.raises(HookBlocked):
        _run_hooks("task", "before", {"hooks": hooks, "repo_root": str(tmp_path)})
    assert "超时(>1s)" in capsys.readouterr().err


def test_run_hooks_continue_on_error_keeps_going(capsys: pytest.CaptureFixture[str],
                                                 monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """continue_on_error=true 的失败 hook 只告警, 后续 hook 照跑。"""
    from skeinlib.hooks.runner import _run_hooks

    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    _run_hooks("task", "before", {"hooks": [
        {"command": "exit 3", "continue_on_error": True},
        {"command": "echo second"},
    ], "repo_root": str(tmp_path)})
    cap = capsys.readouterr()
    assert "continue_on_error=true, 继续" in cap.err
    assert "[hook task.before#2] second" in cap.out


def test_run_hooks_after_stage_warns_but_does_not_raise(capsys: pytest.CaptureFixture[str],
                                                        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """after 阶段失败不阻断: 打「仅告警, 不阻断」后 return (剩余 hook 不再跑)。"""
    from skeinlib.hooks.runner import _run_hooks

    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    _run_hooks("task", "after", {"hooks": [
        {"command": "exit 1", "continue_on_error": False},
        {"command": "echo never"},
    ], "repo_root": str(tmp_path)})
    cap = capsys.readouterr()
    assert "仅告警, 不阻断" in cap.err
    assert "never" not in cap.out


def test_run_hooks_exports_context_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """context 各字段落成 SKEIN_* 环境变量供 hook 命令读, 且 cwd 默认取 worktree。"""
    from skeinlib.hooks.runner import _run_hooks

    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    wt = tmp_path / "wt"
    wt.mkdir()
    out = tmp_path / "env.txt"
    _run_hooks("task", "after", {
        "hooks": [{"command": f'echo "$SKEIN_TID/$SKEIN_SID/$SKEIN_SCOPE/$PWD" > {out}'}],
        "tid": "t1", "sid": "s1", "worktree": str(wt),
    })
    assert out.read_text().strip() == f"t1/s1/task/{wt}"


# ── skeinlib.hooks.cli ────────────────────────────────────────────────────────


def test_hooks_cli_usage_on_unknown_subcommand(capsys: pytest.CaptureFixture[str],
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    """无子命令或子命令不在 DISPATCH → 打用法并 exit code 2。"""
    from skeinlib.hooks.cli import main

    monkeypatch.setattr("sys.argv", ["skein-hooks"])
    assert main() == 2
    monkeypatch.setattr("sys.argv", ["skein-hooks", "bogus"])
    assert main() == 2
    assert "用法: skein-hooks" in capsys.readouterr().err


def test_hooks_cli_resolves_every_dispatch_entry() -> None:
    """DISPATCH 表每条都能解析到真函数 — 表项写错在这里就红, 不用等运行时。"""
    from skeinlib.hooks.cli import DISPATCH, _resolve

    for name in DISPATCH:
        assert callable(_resolve(name))


def test_hooks_cli_argv_dispatch_passes_when(monkeypatch: pytest.MonkeyPatch) -> None:
    """agent-start/agent-stop 走 argv 分支: 传 'start'/'stop' 而非 stdin payload。"""
    import skeinlib.hooks.cli as C

    seen: list[str] = []

    def _record(which: str) -> int:
        seen.append(which)
        return 0

    monkeypatch.setattr("skeinlib.hooks.cli._resolve", lambda n: _record)
    monkeypatch.setattr("sys.argv", ["skein-hooks", "agent-start"])
    assert C.main() == 0
    monkeypatch.setattr("sys.argv", ["skein-hooks", "agent-stop"])
    assert C.main() == 0
    assert seen == ["start", "stop"]


def test_hooks_cli_stdin_dispatch_and_bad_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """stdin 分支: 合法 JSON 传给实现; 非 JSON → 直接 0 (不调实现)。"""
    import skeinlib.hooks.cli as C

    seen: list[dict[str, Any]] = []

    def _record(payload: dict[str, Any]) -> int:
        seen.append(payload)
        return 7

    monkeypatch.setattr("skeinlib.hooks.cli._resolve", lambda n: _record)
    monkeypatch.setattr("sys.argv", ["skein-hooks", "guard"])
    monkeypatch.setattr("sys.stdin", io.StringIO('{"tool_name": "Read"}'))
    assert C.main() == 7
    monkeypatch.setattr("sys.stdin", io.StringIO("nope"))
    assert C.main() == 0
    assert seen == [{"tool_name": "Read"}]
