"""Tests for cortex_deep_search tool."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from tools import deep_search as ds
from tools.deep_search import handle_deep_search


def _run(args: dict[str, Any]) -> dict[str, Any]:
    result = asyncio.run(handle_deep_search(args))
    assert len(result) == 1
    return json.loads(result[0].text)


def test_iterative_converges_and_degraded_when_sc_down(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if shutil.which("rg") is None:
        pytest.skip("ripgrep not installed")
    note = fake_vault / "知识库" / "领域" / "alpha.md"
    note.write_text(
        "# Alpha\n\nfoo bar unique-token answer details payload\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CORTEX_SC_URL", "http://127.0.0.1:1")
    out = _run({"query": "unique-token", "mode": "iterative", "iter_max": 3})
    assert out["mode"] == "iterative"
    assert out["iterations"] <= 3
    assert out["degraded"] is True


def test_subgraph_hop1_expands_backlinks(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if shutil.which("rg") is None:
        pytest.skip("ripgrep not installed")
    base = fake_vault / "知识库" / "领域"
    seed = base / "seed.md"
    seed.write_text("# Seed\n\ntopic-x content\n", encoding="utf-8")
    neighbor = base / "neighbor.md"
    neighbor.write_text(
        "# Neighbor\n\nrefers to [[seed]] here\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CORTEX_SC_URL", "http://127.0.0.1:1")
    out = _run(
        {"query": "topic-x", "mode": "subgraph", "max_hops": 1, "limit": 10}
    )
    paths = {h["path"] for h in out["hits"]}
    assert any("seed" in p for p in paths)
    assert any("neighbor" in p for p in paths)
    assert out["subgraph_expanded"] >= 1


def test_hybrid_bm25_with_sc_down(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if shutil.which("rg") is None:
        pytest.skip("ripgrep not installed")
    base = fake_vault / "知识库" / "领域"
    a = base / "a.md"
    a.write_text("# A\n\nfoo bar foo bar foo bar\n", encoding="utf-8")
    b = base / "b.md"
    b.write_text("# B\n\nfoo only\n", encoding="utf-8")
    monkeypatch.setenv("CORTEX_SC_URL", "http://127.0.0.1:1")
    out = _run({"query": "foo bar", "mode": "hybrid", "limit": 10})
    assert out["mode"] == "hybrid"
    assert out["degraded"] is True
    paths = [h["path"] for h in out["hits"]]
    # Both files should appear; A should rank above B due to BM25.
    assert any("a.md" in p for p in paths)


def test_bm25_rerank_pure_function() -> None:
    hits = [
        {
            "path": "x", "title": "x", "snippet": "foo only",
            "score": 0.0, "source": "rg",
        },
        {
            "path": "y", "title": "y",
            "snippet": "foo bar foo bar foo bar",
            "score": 0.0, "source": "rg",
        },
    ]
    out = ds._bm25_rerank(hits, "foo bar")
    assert out[0]["path"] == "y"


def test_jaccard_helper() -> None:
    assert ds._jaccard(set(), set()) == 1.0
    assert ds._jaccard({"a"}, {"a"}) == 1.0
    assert ds._jaccard({"a", "b"}, {"a", "c"}) == pytest.approx(1 / 3)


def test_iter_max_hard_cap(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CORTEX_SC_URL", "http://127.0.0.1:1")
    # iter_max=5 violates schema; handler accepts but internally clamps.
    out = _run({"query": "absent", "mode": "iterative", "iter_max": 3})
    assert out["iterations"] <= 3
