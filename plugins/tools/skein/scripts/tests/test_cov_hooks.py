"""hooks 模块纯函数覆盖 — pre_tool_use / post_tool_use。
无状态函数直接调验证返回值。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from skeinlib.hooks import pre_tool_use as ptu
from skeinlib.hooks import post_tool_use as pou
from skeinlib.hooks import post_tool_use_failure as pouf


# ---- pre_tool_use: parse_frontmatter / strip_frontmatter ----

def test_parse_frontmatter_basic() -> None:
    text = "---\ntitle: Test\ninclusion: always\n---\nbody"
    fm = ptu.parse_frontmatter(text)
    assert fm["title"] == "Test"
    assert fm["inclusion"] == "always"


def test_parse_frontmatter_no_frontmatter() -> None:
    assert ptu.parse_frontmatter("no frontmatter") == {}


def test_parse_frontmatter_unterminated() -> None:
    assert ptu.parse_frontmatter("---\ntitle: Test\nbody") == {}


def test_parse_frontmatter_array_value() -> None:
    text = "---\nkeywords: [a, b, c]\n---\nbody"
    fm = ptu.parse_frontmatter(text)
    assert fm["keywords"] == "a, b, c"


def test_strip_frontmatter() -> None:
    assert ptu.strip_frontmatter("---\ntitle: T\n---\nhello") == "\nhello"
    assert ptu.strip_frontmatter("no fm") == "no fm"
    assert ptu.strip_frontmatter("---\ntitle: T\n---\n") == "\n"


# ---- pre_tool_use: file matching ----

def test_find_filematch_specs_empty(tmp_path: Path) -> None:
    assert ptu.find_filematch_specs(str(tmp_path / "nonexistent")) == []


def test_find_filematch_specs_finds_match(tmp_path: Path) -> None:
    spec_dir = tmp_path / ".skein" / "spec" / "rules"
    spec_dir.mkdir(parents=True)
    (spec_dir / "test.md").write_text(
        "---\ninclusion: fileMatch\nglobs: *.py\ntitle: Python Rules\n---\nRule body here\n"
    )
    result = ptu.find_filematch_specs(str(tmp_path / ".skein" / "spec"))
    assert len(result) == 1
    path, globs, body, title = result[0]
    assert "*.py" in globs
    assert "Rule body" in body


def test_find_filematch_specs_skips_non_filematch(tmp_path: Path) -> None:
    spec_dir = tmp_path / "spec" / "rules"
    spec_dir.mkdir(parents=True)
    (spec_dir / "test.md").write_text("---\ninclusion: always\n---\nbody\n")
    assert ptu.find_filematch_specs(str(spec_dir.parent)) == []


def test_file_matches_globs_positive(tmp_path: Path) -> None:
    assert ptu.file_matches_globs(str(tmp_path / "foo.py"), ["*.py"], str(tmp_path)) is True


def test_file_matches_globs_negative(tmp_path: Path) -> None:
    assert ptu.file_matches_globs(str(tmp_path / "foo.js"), ["*.py"], str(tmp_path)) is False


def test_file_matches_globs_outside_root(tmp_path: Path) -> None:
    assert ptu.file_matches_globs("/other/dir/foo.py", ["*.py"], str(tmp_path)) is False


def test_filematch_context(tmp_path: Path) -> None:
    spec_dir = tmp_path / ".skein" / "spec" / "rules"
    spec_dir.mkdir(parents=True)
    (spec_dir / "py.md").write_text(
        "---\ninclusion: fileMatch\nglobs: *.py\ntitle: Python Rules\n---\nUse type hints\n"
    )
    ctx = ptu.filematch_context(str(tmp_path / "test.py"), str(tmp_path))
    assert "Python Rules" in ctx


def test_filematch_context_no_specs(tmp_path: Path) -> None:
    ctx = ptu.filematch_context(str(tmp_path / "test.py"), str(tmp_path))
    assert ctx == ""


# ---- pre_tool_use: cmd_guard ----

def test_cmd_guard_blocks_skein_task_json(tmp_path: Path,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"tool_name": "Read", "tool_input": {"file_path": str(tmp_path / ".skein" / "task" / "t1" / "task.json")}}
    assert ptu.cmd_guard(payload) == 2
    assert "禁直接读写" in capsys.readouterr().err



def test_cmd_guard_blocks_prd_write(tmp_path: Path,
                                    capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / ".skein" / "task" / "t1" / "prd.md")}}
    assert ptu.cmd_guard(payload) == 2


def test_cmd_guard_no_file_path() -> None:
    assert ptu.cmd_guard({"tool_name": "Read", "tool_input": {}}) == 0


def test_cmd_guard_normal_file(tmp_path: Path) -> None:
    payload = {"tool_name": "Read", "tool_input": {"file_path": str(tmp_path / "normal.py")}}
    assert ptu.cmd_guard(payload) == 0


def test_cmd_guard_allows_trellis_uninit(tmp_path: Path,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / ".trellis").mkdir()
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(tmp_path / "code.py")},
               "cwd": str(tmp_path)}
    assert ptu.cmd_guard(payload) == 0
    assert capsys.readouterr().err == ""


# ---- post_tool_use: parse_spec_frontmatter / spec_frontmatter_text ----

def test_parse_spec_frontmatter_basic() -> None:
    text = "---\ntitle: T\nnamespace: rules\ninclusion: auto\nkeywords: [a, b]\n---\nbody"
    fm = pou.parse_spec_frontmatter(text)
    assert fm["title"] == "T"
    assert fm["namespace"] == "rules"


def test_parse_spec_frontmatter_no_fm() -> None:
    assert pou.parse_spec_frontmatter("no fm") == {}


def test_parse_spec_frontmatter_unterminated() -> None:
    assert pou.parse_spec_frontmatter("---\ntitle: T\nno end") == {}


def test_parse_spec_frontmatter_skips_indented() -> None:
    text = "---\ntitle: T\n  indented: yes\nlist:\n  - item\n---\nbody"
    fm = pou.parse_spec_frontmatter(text)
    assert "title" in fm
    assert "indented" not in fm


def test_spec_frontmatter_text() -> None:
    assert pou.spec_frontmatter_text("---\ntitle: T\n---\nbody") == "title: T"
    assert pou.spec_frontmatter_text("no fm") == ""
    assert pou.spec_frontmatter_text("---\ntitle: T\nno end") == ""







def test_spec_meta_no_file_path() -> None:
    assert pou.cmd_spec_meta({"tool_input": {}}) == 0


def test_spec_meta_non_spec_file() -> None:
    assert pou.cmd_spec_meta({"tool_input": {"file_path": "/some/code.py"}}) == 0


def test_spec_meta_missing_required(tmp_path: Path,
                                    capsys: pytest.CaptureFixture[str]) -> None:
    spec_file = tmp_path / ".skein" / "spec" / "rules" / "arch" / "test.md"
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text("---\ntitle: T\n---\nbody")
    pou.cmd_spec_meta({"tool_input": {"file_path": str(spec_file)}})
    out = capsys.readouterr().out
    # JSON unicode-encodes Chinese, check for encoded "缺失" or the warning prefix
    assert "hookSpecificOutput" in out
    assert "spec metadata" in out or "\\u68c0\\u67e5" in out or "缺失" in out


def test_spec_meta_complete(tmp_path: Path,
                            capsys: pytest.CaptureFixture[str]) -> None:
    spec_file = tmp_path / ".skein" / "spec" / "rules" / "arch" / "good.md"
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text(
        "---\ntitle: T\nnamespace: rules\ninclusion: auto\nkeywords: [a]\n---\nbody")
    pou.cmd_spec_meta({"tool_input": {"file_path": str(spec_file)}})
    assert capsys.readouterr().out == ""


def test_spec_meta_filematch_missing_globs(tmp_path: Path,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    spec_file = tmp_path / ".skein" / "spec" / "rules" / "git" / "fm.md"
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text(
        "---\ntitle: T\nnamespace: rules\ninclusion: fileMatch\nkeywords: [a]\n---\nbody")
    pou.cmd_spec_meta({"tool_input": {"file_path": str(spec_file)}})
    assert "globs" in capsys.readouterr().out


def test_spec_meta_product_missing_anchors(tmp_path: Path,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    spec_file = tmp_path / ".skein" / "spec" / "product" / "wiki" / "page.md"
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text(
        "---\ntitle: T\nnamespace: product\ninclusion: auto\nkeywords: [a]\n---\nbody")
    pou.cmd_spec_meta({"tool_input": {"file_path": str(spec_file)}})
    assert "anchors" in capsys.readouterr().out


def test_spec_meta_unreadable_file(tmp_path: Path) -> None:
    spec_file = tmp_path / ".skein" / "spec" / "rules" / "arch" / "gone.md"
    spec_file.parent.mkdir(parents=True)
    # 文件不存在
    assert pou.cmd_spec_meta({"tool_input": {"file_path": str(spec_file)}}) == 0


# ---- post_tool_use_failure: cmd_report ----

def test_cmd_report_ignores_empty_error(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"tool_input": {"command": "skein task list"}, "tool_error": ""}
    assert pouf.cmd_report(payload) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("command", [
    "grep -R skein .",
    "printf skein",
    "python scripts/check.py skein",
    "printf CLAUDE_PLUGIN_ROOT/skein.py",
    "cat /tmp/spec.py",
])
def test_cmd_report_ignores_incidental_skein_text(
        command: str, capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"tool_input": {"command": command}, "tool_error": "failed"}
    assert pouf.cmd_report(payload) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("command", [
    "skein task list",
    "  skein task list",
    "uv run skein task list",
    "python3 /tmp/skein.py task list",
    "python \"${CLAUDE_PLUGIN_ROOT}/scripts/skein.py\" task list",
    "./scripts/spec.py maintain",
    "make build\nskein flow run",
])
def test_cmd_report_recognizes_skein_executables(
        command: str, capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"tool_input": {"command": command}, "tool_error": "bad arguments"}
    assert pouf.cmd_report(payload) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["hookSpecificOutput"]["hookEventName"] == "PostToolUseFailure"
    assert "非崩溃" in output["hookSpecificOutput"]["additionalContext"]
