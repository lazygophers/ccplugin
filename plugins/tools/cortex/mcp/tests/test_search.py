"""Tests for cortex_search tool."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from tools import search as search_mod
from tools.search import handle_search


def _run(args: dict[str, Any]) -> list[dict[str, Any]]:
    result = asyncio.run(handle_search(args))
    assert len(result) == 1
    return json.loads(result[0].text)


def test_search_hot_hit(fake_vault: Path) -> None:
    (fake_vault / "hot.md").write_text(
        "## 最近落档\n- [[知识库/领域/foo-bar]] foo bar hit\n",
        encoding="utf-8",
    )
    hits = _run({"query": "foo bar"})
    assert any(h["source"] == "hot" for h in hits)
    assert hits[0]["snippet"]


def test_search_index_hit(fake_vault: Path) -> None:
    (fake_vault / "hot.md").write_text("## 最近落档\n", encoding="utf-8")
    (fake_vault / "index.md").write_text(
        "- [[知识库/领域/alpha]] alpha entry\n", encoding="utf-8"
    )
    hits = _run({"query": "alpha"})
    sources = {h["source"] for h in hits}
    assert "index" in sources


def test_search_rg_fallback(
    fake_vault: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if shutil.which("rg") is None:
        pytest.skip("ripgrep not installed")
    # Empty hot/index, content only in a concept file.
    (fake_vault / "hot.md").write_text("## 最近落档\n", encoding="utf-8")
    (fake_vault / "index.md").write_text("# index\n", encoding="utf-8")
    note = fake_vault / "知识库" / "领域" / "beta.md"
    note.write_text("# Beta\n\nunique-token here\n", encoding="utf-8")
    # Force SC unreachable
    monkeypatch.setenv("CORTEX_SC_URL", "http://127.0.0.1:1")
    hits = _run({"query": "unique-token"})
    assert any(h["source"] == "ripgrep" for h in hits)
    assert any("beta" in (h["path"] or "").lower() for h in hits)


def test_search_empty_result(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (fake_vault / "hot.md").write_text("## 最近落档\n", encoding="utf-8")
    (fake_vault / "index.md").write_text("# index\n", encoding="utf-8")
    monkeypatch.setenv("CORTEX_SC_URL", "http://127.0.0.1:1")
    # Stub ripgrep call to return no hits regardless of rg availability.
    monkeypatch.setattr(search_mod, "_ripgrep", lambda *a, **kw: [])
    hits = _run({"query": "nothing-matches-this-token-xyz"})
    assert hits == []


def test_search_missing_query() -> None:
    with pytest.raises(ValueError):
        asyncio.run(handle_search({}))


def test_search_invalid_scope(fake_vault: Path) -> None:
    with pytest.raises(ValueError):
        asyncio.run(handle_search({"query": "x", "scope": "bogus"}))
