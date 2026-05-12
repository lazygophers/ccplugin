"""Tests for cortex_stream — CLI parsing, event rendering, tee, fallback."""

from __future__ import annotations

import io
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from cortex_stream import (
    _extract_prompts,
    _extract_skill_name,
    _render_event,
    _strip_separator,
    main,
    parse_args,
    run,
)


# ---------- CLI args ----------


def test_parse_args_defaults_label() -> None:
    ns = parse_args(["--", "echo", "hi"])
    assert ns.label == "cortex"
    assert ns.cmd == ["--", "echo", "hi"]


def test_parse_args_custom_label() -> None:
    ns = parse_args(["--label", "cortex-doctor", "--", "echo", "hi"])
    assert ns.label == "cortex-doctor"


def test_strip_separator_drops_leading_dashes() -> None:
    assert _strip_separator(["--", "claude", "-p"]) == ["claude", "-p"]


def test_strip_separator_passthrough_when_absent() -> None:
    assert _strip_separator(["claude", "-p"]) == ["claude", "-p"]


def test_strip_separator_empty() -> None:
    assert _strip_separator([]) == []


def test_main_missing_command_returns_4() -> None:
    assert main(["--label", "x"]) == 4


# ---------- event rendering ----------


def test_render_event_text_block() -> None:
    evt = {"type": "assistant", "message": {"content": [{"type": "text", "text": "hello"}]}}
    r = _render_event(evt)
    assert r is not None
    # rendering should not raise
    assert "hello" in repr(r) or hasattr(r, "renderables") or hasattr(r, "plain")


def test_render_event_tool_use_block() -> None:
    evt = {
        "type": "assistant",
        "message": {
            "content": [{"type": "tool_use", "name": "Read", "input": {"path": "/x"}}],
        },
    }
    r = _render_event(evt)
    assert r is not None  # Panel


def test_render_event_result_ok() -> None:
    r = _render_event({"type": "result", "is_error": False, "result": "ok"})
    assert r is not None
    assert "OK" in r.plain


def test_render_event_result_failed() -> None:
    r = _render_event({"type": "result", "is_error": True, "result": "boom"})
    assert r is not None
    assert "FAILED" in r.plain
    assert "boom" in r.plain


def test_render_event_unknown_returns_none() -> None:
    assert _render_event({"type": "system"}) is None


def test_render_event_empty_assistant_returns_none() -> None:
    assert _render_event({"type": "assistant", "message": {"content": []}}) is None


def test_render_event_strips_leading_newlines_and_caps_length() -> None:
    long_text = "\n\n" + ("x" * 3000)
    evt = {"type": "assistant", "message": {"content": [{"type": "text", "text": long_text}]}}
    r = _render_event(evt)
    assert r is not None
    # Should not contain leading newlines; capped at TEXT_CAP=2000 (+prefix).
    assert "\n\n" not in r.plain
    assert len(r.plain) < 2020  # 2000 cap + "[text] " prefix
    assert len(r.plain) > 1900  # 不再是旧 200 cap


def test_render_event_text_not_truncated_below_old_cap() -> None:
    # 500 chars 在旧 200 cap 会被截; 现在 2000 cap 应完整保留.
    txt = "a" * 500
    evt = {"type": "assistant", "message": {"content": [{"type": "text", "text": txt}]}}
    r = _render_event(evt)
    assert r is not None
    assert r.plain.count("a") == 500


def test_render_event_thinking_block() -> None:
    evt = {
        "type": "assistant",
        "message": {"content": [{"type": "thinking", "thinking": "let me reason about this"}]},
    }
    r = _render_event(evt)
    assert r is not None
    assert "thinking" in r.plain
    assert "let me reason" in r.plain


def test_render_event_thinking_capped() -> None:
    long_th = "z" * 5000
    evt = {"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": long_th}]}}
    r = _render_event(evt)
    assert r is not None
    # cap at 4000
    assert r.plain.count("z") == 4000


def test_render_event_tool_input_not_truncated_below_old_cap() -> None:
    # 旧 120 cap 会截; 现在 800 cap 应保留 ~400 chars 的 JSON.
    big_input = {"q": "x" * 400}
    evt = {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "Grep", "input": big_input}]},
    }
    r = _render_event(evt)
    assert r is not None
    # Panel renderable — 主要断言不抛异常 + 不在旧 120 边界出错;
    # 进一步: 直接读 Panel.renderable.plain 检查 input 字符串保留度.
    inner_plain = r.renderable.plain  # type: ignore[attr-defined]
    # 旧 120 cap 下绝不会保留 400 个 x; 新 800 cap 应保留.
    assert inner_plain.count("x") >= 300


def test_render_event_result_with_full_content() -> None:
    r = _render_event({"type": "result", "is_error": False, "result": "summary line 1\nsummary line 2"})
    assert r is not None
    assert "OK" in r.plain
    assert "summary line 1" in r.plain
    assert "summary line 2" in r.plain


def test_render_event_result_empty_falls_back_to_done() -> None:
    r = _render_event({"type": "result", "is_error": False, "result": ""})
    assert r is not None
    assert r.plain.strip() == "[OK] done"


# ---------- prompt extraction ----------


def test_extract_prompts_system_and_user() -> None:
    cmd = [
        "claude", "--bare", "-p",
        "--append-system-prompt", "SYS BODY",
        "--output-format", "stream-json", "--verbose",
        "user question",
    ]
    sys_p, user_p = _extract_prompts(cmd)
    assert sys_p == "SYS BODY"
    assert user_p == "user question"


def test_extract_prompts_user_only() -> None:
    cmd = ["claude", "-p", "ask me something"]
    sys_p, user_p = _extract_prompts(cmd)
    assert sys_p is None
    assert user_p == "ask me something"


def test_extract_prompts_neither() -> None:
    cmd = ["/usr/bin/claude"]
    sys_p, user_p = _extract_prompts(cmd)
    assert sys_p is None
    assert user_p is None


def test_extract_prompts_alt_system_flag() -> None:
    cmd = ["claude", "--system-prompt", "ALT SYS", "hello"]
    sys_p, user_p = _extract_prompts(cmd)
    assert sys_p == "ALT SYS"
    assert user_p == "hello"


# ---------- skill name extraction ----------


def test_extract_skill_name_basic() -> None:
    sp = "---\nname: cortex-lint\ndescription: x\n---\n\nbody here"
    assert _extract_skill_name(sp) == "cortex-lint"


def test_extract_skill_name_quoted() -> None:
    sp = "---\nname: \"my-skill\"\nx: y\n---\n\nbody"
    assert _extract_skill_name(sp) == "my-skill"


def test_extract_skill_name_no_frontmatter() -> None:
    assert _extract_skill_name("just plain text") is None


def test_extract_skill_name_empty() -> None:
    assert _extract_skill_name(None) is None
    assert _extract_skill_name("") is None


# ---------- run() with mocked subprocess ----------


class _FakeProc:
    """Minimal stand-in for subprocess.Popen."""

    def __init__(self, lines: list[str], rc: int = 0) -> None:
        self.stdout = io.StringIO("\n".join(lines) + ("\n" if lines else ""))
        self.stderr = io.StringIO("")
        self._rc = rc
        self.killed = False

    def wait(self, timeout: float | None = None) -> int:  # noqa: ARG002
        return self._rc

    def kill(self) -> None:
        self.killed = True


def _stream_lines() -> list[str]:
    return [
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}),
        json.dumps({
            "type": "assistant",
            "message": {"content": [{"type": "tool_use", "name": "Grep", "input": {"q": "x"}}]},
        }),
        "not-json-garbage",
        json.dumps({"type": "result", "is_error": False, "result": "done"}),
    ]


def test_run_invokes_subprocess_with_stream_json_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_popen(cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _FakeProc(_stream_lines(), rc=0)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    rc = run(["claude", "-p", "hi"], label="t", tee_path=None, stderr=io.StringIO())
    assert rc == 0
    assert captured["cmd"][:3] == ["claude", "-p", "hi"]
    assert captured["cmd"][-3:] == ["--output-format", "stream-json", "--verbose"]
    assert captured["kwargs"]["bufsize"] == 1
    assert captured["kwargs"]["text"] is True


def test_run_writes_tee_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _FakeProc(_stream_lines(), rc=0))
    tee = tmp_path / "out.ndjson"
    rc = run(["claude"], label="t", tee_path=str(tee), stderr=io.StringIO())
    assert rc == 0
    contents = tee.read_text(encoding="utf-8").splitlines()
    # All four input lines (including the garbage one) are tee'd raw.
    assert len(contents) == 4
    assert json.loads(contents[0])["type"] == "assistant"
    assert json.loads(contents[3])["type"] == "result"


def test_run_propagates_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _FakeProc(_stream_lines(), rc=2))
    rc = run(["claude"], label="t", tee_path=None, stderr=io.StringIO())
    assert rc == 2


def test_run_handles_empty_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _FakeProc([], rc=0))
    rc = run(["claude"], label="t", tee_path=None, stderr=io.StringIO())
    assert rc == 0


def test_parse_args_timeout_default_zero() -> None:
    ns = parse_args(["--", "echo", "hi"])
    assert ns.timeout == 0


def test_parse_args_timeout_explicit() -> None:
    ns = parse_args(["--timeout", "30", "--", "echo", "hi"])
    assert ns.timeout == 30


def test_run_timeout_zero_disables_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    """timeout=0 → no deadline check; runs to natural EOF."""
    fake = _FakeProc(_stream_lines(), rc=0)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: fake)
    rc = run(["claude"], label="t", tee_path=None, stderr=io.StringIO(), timeout=0)
    assert rc == 0
    assert fake.killed is False


def test_run_timeout_triggers_kill_and_returns_124(monkeypatch: pytest.MonkeyPatch) -> None:
    """When deadline elapses mid-loop, child is killed and 124 returned."""
    fake = _FakeProc(_stream_lines(), rc=0)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: fake)

    # Force time.monotonic to jump past the deadline on the second call so the
    # loop's per-line deadline check fires.
    import cortex_stream as cs

    calls = {"n": 0}
    real_mono = time.monotonic

    def fake_mono() -> float:
        calls["n"] += 1
        # 1st call: run() start. 2nd+: well past deadline.
        return real_mono() + (0.0 if calls["n"] == 1 else 10_000.0)

    monkeypatch.setattr(cs.time, "monotonic", fake_mono)

    rc = run(["claude"], label="t", tee_path=None, stderr=io.StringIO(), timeout=1)
    assert rc == 124
    assert fake.killed is True


def test_main_reads_tee_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tee = tmp_path / "x.ndjson"
    monkeypatch.setenv("CORTEX_STREAM_TEE_FILE", str(tee))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _FakeProc(_stream_lines(), rc=0))

    rc = main(["--label", "test", "--", "claude", "-p", "hi"])
    assert rc == 0
    assert tee.exists()
    assert len(tee.read_text(encoding="utf-8").splitlines()) == 4
