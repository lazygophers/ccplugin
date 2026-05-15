"""Tests for PR3 P4: extract_aliases / extract_keywords (召回率字段).

启发式权威: skills/cortex-ingest/references/extract.md §3.3.
"""

from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = PLUGIN_ROOT / "scripts" / "cli"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from lib.remote import extract_aliases, extract_keywords  # noqa: E402


# ───────────── extract_aliases ─────────────


def test_extract_aliases_cn_en_pair():
    """中→英: title 含 '认证' 应推 'authentication'."""
    out = extract_aliases("认证中间件", "")
    assert "authentication" in out


def test_extract_aliases_en_cn_pair():
    """英→中: title 含 'authentication' 应推 '认证'."""
    out = extract_aliases("authentication middleware", "")
    assert "认证" in out


def test_extract_aliases_abbr_to_full():
    """缩写→全称: desc 含 'RBAC' 应推 'Role-Based Access Control'."""
    out = extract_aliases("Access Control", "RBAC implementation guide")
    assert "Role-Based Access Control" in out


def test_extract_aliases_full_to_abbr():
    """全称→缩写: desc 含全称 应推 'RBAC'."""
    out = extract_aliases("Permission", "Role-Based Access Control architecture")
    assert "RBAC" in out


def test_extract_aliases_min_3_padding():
    """不足 3 个 alias 时, 回退到 title 词."""
    out = extract_aliases("FooBar Quux Baz", "no matches here")
    assert len(out) >= 3


def test_extract_aliases_empty_input():
    """空输入不抛, 返 list (可空)."""
    out = extract_aliases("", "")
    assert isinstance(out, list)


# ───────────── extract_keywords ─────────────


def test_extract_keywords_path_stem():
    """path 文件名 stem 入 keywords."""
    out = extract_keywords(
        title="auth",
        body="",
        path="src/auth_middleware.py",
        host="github.com",
        org="foo",
        repo="bar",
    )
    assert "auth_middleware" in out


def test_extract_keywords_repo_meta():
    """repo / org / host 入 keywords."""
    out = extract_keywords(
        title="t",
        body="",
        path="x.md",
        host="github.com",
        org="anthropic",
        repo="claude-code",
    )
    assert "claude-code" in out
    assert "anthropic" in out
    assert "github.com" in out


def test_extract_keywords_idents_from_fenced_code():
    """body 含 ``` fenced code 时, 优先抽 fence 内代码标识符 top 5."""
    body = """
some intro

```python
def handle_request(req):
    handle_request(req)
    handle_request(req)
    do_stuff()
```
"""
    out = extract_keywords(
        title="t",
        body=body,
        path="x.md",
    )
    # handle_request 出现 3 次, 应进 top 5
    assert "handle_request" in out


def test_extract_keywords_headings():
    """body 中 heading 入 keywords."""
    body = "## Foo Bar Heading\n\nintro text\n\n## Second Heading\n"
    out = extract_keywords(title="t", body=body, path="x.md")
    assert "Foo Bar Heading" in out


def test_extract_keywords_min_count():
    """典型场景应抽出 ≥ 5 keywords (path + 3 metadata + headings/idents)."""
    body = """## Architecture
some code:
```python
def authenticate(user):
    return validate_token(user)
```
"""
    out = extract_keywords(
        title="auth doc",
        body=body,
        path="docs/auth_module.md",
        host="github.com",
        org="acme",
        repo="api",
    )
    assert len(out) >= 5


def test_extract_keywords_empty_body():
    """空 body: 仅 path stem + repo meta, 仍不抛."""
    out = extract_keywords(
        title="",
        body="",
        path="readme.md",
        host="",
        org="",
        repo="",
    )
    assert isinstance(out, list)
    assert "readme" in out


def test_extract_keywords_no_fence_falls_back_to_plain():
    """body 无 fence 时, 退化扫全文标识符 (剥 fence 后)."""
    body = "Plain text with foo_bar_baz mentioned and foo_bar_baz again."
    out = extract_keywords(title="t", body=body, path="x.md")
    assert "foo_bar_baz" in out
