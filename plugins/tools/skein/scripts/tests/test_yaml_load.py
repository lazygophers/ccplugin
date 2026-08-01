"""_yaml_load / _yaml_dump 单测 — 唯一允许直调纯函数的例外(design.md 测试接缝段)。

本 task (config-hooks) 里 _yaml_load 是唯一高风险项: 自研 mini YAML 解析器要撑
config.yaml 的 hooks 嵌套结构(≥4 层 dict + list of dict), 静默降级 = 用户配置无声
失效, 是最难查的一类故障, 所以单独一个文件、能独立回归。

覆盖: 4 层嵌套 / list of dict / 带引号键("*") / 引号内 # 不截断 / 5 类不支持语法
各自报错且含行号 / 往返一致 / 现有扁平结构不变(与 test_config_cli.py 互补, 那边走
CLI 边界, 这里走纯函数直调)。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skeinlib.config import _yaml_load, _yaml_dump  # noqa: E402


# ---------- 现有扁平结构零变化 ----------
def test_flat_scalars() -> None:
    text = "max_active: 2\nauto_commit: true\nworktree_root: .worktrees\n# 注释行\n"
    assert _yaml_load(text) == {"max_active": 2, "auto_commit": True, "worktree_root": ".worktrees"}


def test_flat_negative_int_and_false() -> None:
    assert _yaml_load("retain_days: -1\nweb_serve: false\n") == {"retain_days": -1, "web_serve": False}


# ---------- 4 层嵌套 dict ----------
def test_deep_nesting_4_levels() -> None:
    text = (
        "hooks:\n"
        "  agent:\n"
        "    skein-executor:\n"
        "      start: echo hi\n"
    )
    d = _yaml_load(text)
    assert d == {"hooks": {"agent": {"skein-executor": {"start": "echo hi"}}}}


# ---------- list of dict ----------
def test_list_of_dict() -> None:
    text = (
        "hooks:\n"
        "  check:\n"
        "    before:\n"
        "      - type: command\n"
        "        command: npm run lint\n"
        "        timeout: 120\n"
        "        continue_on_error: false\n"
    )
    d = _yaml_load(text)
    assert d == {
        "hooks": {"check": {"before": [
            {"type": "command", "command": "npm run lint", "timeout": 120, "continue_on_error": False}
        ]}}
    }


def test_list_of_dict_multiple_items() -> None:
    text = (
        "before:\n"
        "  - type: command\n"
        "    command: echo one\n"
        "  - type: command\n"
        "    command: echo two\n"
    )
    d = _yaml_load(text)
    assert d == {"before": [
        {"type": "command", "command": "echo one"},
        {"type": "command", "command": "echo two"},
    ]}


# ---------- 带引号的键 ----------
def test_quoted_key_star() -> None:
    text = 'agent:\n  "*":\n    stop: echo bye\n'
    d = _yaml_load(text)
    assert d == {"agent": {"*": {"stop": "echo bye"}}}
    assert "*" in d["agent"]  # 键是 * 不是 "*"


# ---------- 引号内 # 不截断 ----------
def test_hash_inside_quotes_not_truncated() -> None:
    text = 'command: "echo #1"\n'
    assert _yaml_load(text) == {"command": "echo #1"}


def test_hash_comment_after_quoted_value_still_stripped() -> None:
    text = 'command: "echo hi"  # 这是注释\n'
    assert _yaml_load(text) == {"command": "echo hi"}


# ---------- 完整 PRD 示例 (hooks 结构) ----------
def test_full_hooks_example() -> None:
    text = (
        "hooks:\n"
        "  check:\n"
        "    before:\n"
        "      - type: command\n"
        '        command: "npm run lint"\n'
        "        timeout: 120\n"
        "        continue_on_error: false\n"
        "  agent:\n"
        "    skein-executor:\n"
        "      start:\n"
        "        - type: command\n"
        '          command: "echo hi"\n'
        '    "*":\n'
        "      stop:\n"
        "        - type: command\n"
        '          command: "git status --short"\n'
    )
    d = _yaml_load(text)
    assert d == {
        "hooks": {
            "check": {"before": [
                {"type": "command", "command": "npm run lint", "timeout": 120, "continue_on_error": False}
            ]},
            "agent": {
                "skein-executor": {"start": [{"type": "command", "command": "echo hi"}]},
                "*": {"stop": [{"type": "command", "command": "git status --short"}]},
            },
        }
    }


# ---------- 5 类不支持语法, 各自报错且含行号 ----------
def test_anchor_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 2 行.*锚点/引用"):
        _yaml_load("a: 1\nb: &anchor foo\n")


def test_alias_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 1 行.*锚点/引用"):
        _yaml_load("b: *ref\n")


def test_multiline_scalar_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 3 行.*多行标量"):
        _yaml_load("a: 1\nb: 2\nc: |\n  text\n")


def test_flow_style_dict_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 1 行.*流式语法"):
        _yaml_load("a: {b: 1}\n")


def test_flow_style_list_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 1 行.*流式语法"):
        _yaml_load("a: [1, 2]\n")


def test_multi_doc_marker_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 2 行.*多文档"):
        _yaml_load("a: 1\n---\nb: 2\n")


def test_tab_indentation_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 2 行.*tab 缩进"):
        _yaml_load("a:\n\tb: 1\n")


# ---------- 往返一致 ----------
def test_roundtrip_flat() -> None:
    d = {"max_active": 2, "auto_commit": True, "worktree_root": ".worktrees", "retain_days": -1}
    assert _yaml_load(_yaml_dump(d)) == d


def test_roundtrip_nested_hooks() -> None:
    d = {
        "hooks": {
            "check": {"before": [
                {"type": "command", "command": "npm run lint", "timeout": 120, "continue_on_error": False}
            ]},
            "agent": {
                "skein-executor": {"start": [{"type": "command", "command": "echo hi"}]},
                "*": {"stop": [{"type": "command", "command": "git status --short"}]},
            },
        }
    }
    assert _yaml_load(_yaml_dump(d)) == d


def test_roundtrip_value_with_colon_and_hash() -> None:
    d = {"command": "curl http://x:1 #tag", "note": "  spaced  "}
    assert _yaml_load(_yaml_dump(d)) == d


# ---------- BOM 剥离 (c9 静默错 #1) ----------
def test_bom_stripped() -> None:
    """首行带 UTF-8 BOM (Windows 编辑器常见) → 首个键仍读到, 不带 BOM 前缀。"""
    assert _yaml_load("﻿a: 1\nb: 2\n") == {"a": 1, "b": 2}


# ---------- 未闭合引号报错 (c9 静默错 #2, 安全相关) ----------
def test_unclosed_double_quote_value_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 1 行.*未闭合引号"):
        _yaml_load('command: "echo hi\n')


def test_unclosed_single_quote_value_errors_with_lineno() -> None:
    with pytest.raises(ValueError, match=r"第 2 行.*未闭合引号"):
        _yaml_load("a: 1\ncommand: 'echo hi\n")


def test_malformed_quoted_key_errors_with_lineno() -> None:
    """键以引号开头但结尾非同引号 (如引号后带杂散文本) → 报错指行号, 不静默截断。"""
    with pytest.raises(ValueError, match=r"第 1 行.*未闭合引号"):
        _yaml_load('"bad" extra: 1\n')
