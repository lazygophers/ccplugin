"""utils 纯函数覆盖 — fs / timefmt / debug / token_conversion。
全是无状态工具函数，直接调验证返回值。
"""
from __future__ import annotations

import io
import os
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from skeinlib.utils import fs, timefmt, debug, token_conversion


# ---- fs.py ----

def test_git_root_finds_repo(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert fs.git_root(str(sub)) == str(tmp_path)


def test_git_root_no_repo_returns_start(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    result = fs.git_root(str(tmp_path / "a"))
    assert result == str(tmp_path / "a")


def test_git_root_empty_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """空字符串 start 默认用 '.' — 在 skein scripts 目录下找 git。"""
    result = fs.git_root("")
    assert isinstance(result, str)


def test_load_stdin_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO('{"key": "value"}'))
    assert fs.load_stdin() == {"key": "value"}


def test_load_stdin_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert fs.load_stdin() is None


def test_load_stdin_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert fs.load_stdin() is None


def test_prefix_lines() -> None:
    assert fs.prefix_lines(">>", "a\nb") == ">> a\n>> b\n"
    assert fs.prefix_lines("X", "single") == "X single\n"
    assert fs.prefix_lines("", "") == ""


# ---- timefmt.py ----

def test_fmt_ts_none() -> None:
    assert timefmt.fmt_ts(None) == "-"


def test_fmt_ts_zero() -> None:
    assert timefmt.fmt_ts(0) == "-"


def test_fmt_ts_valid() -> None:
    result = timefmt.fmt_ts(1700000000)
    assert isinstance(result, str)
    assert len(result) > 5
    assert "-" in result  # 日期格式 YYYY-MM-DD


# ---- debug.py ----

def test_debug_enabled_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKEIN_DEBUG", "1")
    assert debug.debug_enabled() is True


def test_debug_disabled_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SKEIN_DEBUG", raising=False)
    assert debug.debug_enabled() is False


def test_debug_enabled_falsy_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for val in ("0", "false", "no", ""):
        monkeypatch.setenv("SKEIN_DEBUG", val)
        assert debug.debug_enabled() is False


def test_debug_enabled_from_args() -> None:
    class FakeArgs:
        debug = True
    assert debug.debug_enabled(FakeArgs()) is True


def test_debug_enable_disable() -> None:
    d = debug.Debug(False)
    d.enable(True)
    assert d.enabled is True
    d.enable(False)
    assert d.enabled is False


def test_debug_log_when_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.log("invisible")
    assert capsys.readouterr().err == ""


def test_debug_log_when_enabled_no_console(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.c = None  # 禁用 rich console
    d.enabled = True
    d.log("visible")
    assert "visible" in capsys.readouterr().err


def test_debug_warn(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.c = None
    d.warn("warning-msg")
    assert "warning-msg" in capsys.readouterr().err


def test_debug_error(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.c = None
    d.error("error-msg")
    assert "error-msg" in capsys.readouterr().err


def test_debug_rule_when_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.rule("title")
    assert capsys.readouterr().err == ""


def test_debug_rule_when_enabled_no_console(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.c = None
    d.enabled = True
    d.rule("section")
    assert "section" in capsys.readouterr().err


def test_debug_kv_when_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.kv({"a": "b"})
    assert capsys.readouterr().err == ""


def test_debug_kv_empty(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.enabled = True
    d.kv({})
    assert capsys.readouterr().err == ""


def test_debug_kv_no_console(capsys: pytest.CaptureFixture[str],
                             monkeypatch: pytest.MonkeyPatch) -> None:
    d = debug.Debug(False)
    # 禁 rich console init，强制走 stderr 路径
    monkeypatch.setattr("skeinlib.utils.debug.Debug._emit",
                        lambda self, msg, style=None: sys.stderr.write(f"{msg}\n"))
    d.enabled = True
    d.kv({"key1": "val1"})
    assert "key1" in capsys.readouterr().err


def test_debug_kv_with_title_no_console(capsys: pytest.CaptureFixture[str]) -> None:
    d = debug.Debug(False)
    d.c = None
    d.enabled = True
    d.kv({"k": "v"}, title="MyTitle")
    err = capsys.readouterr().err
    assert "MyTitle" in err
    assert "k" in err


def test_est_tokens() -> None:
    assert debug.est_tokens("") == 0
    assert debug.est_tokens("ab") == 0
    assert debug.est_tokens("abcd") == 1
    assert debug.est_tokens("abcdefgh") == 2


def test_budget_guard_within_budget() -> None:
    assert debug.budget_guard("short", 100, "test") == "short"


def test_budget_guard_exceeds_budget(capsys: pytest.CaptureFixture[str]) -> None:
    long_text = "x" * 1000
    result = debug.budget_guard(long_text, 10, "mylabel")
    err = capsys.readouterr().err
    assert "> 预算" in err
    assert "mylabel" in err
    assert len(result) < len(long_text)


# ---- token_conversion.py ----

def test_token_conversion_functions() -> None:
    assert token_conversion.estimate_tokens_from_chars(0) == 0
    assert token_conversion.estimate_tokens_from_chars(10) == 6  # ceil(10 * 0.58)
    info = token_conversion.get_conversion_info()
    assert "换算系数" in info
