"""Tests for cortex-digest evolution PR4 double-signal score updates.

覆盖: _scan_session_mentions / _count_vault_backlinks / update_doc_scores
+ clamp / dry_run / no_frontmatter 边界。
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = PLUGIN_ROOT / "scripts" / "cli"
sys.path.insert(0, str(CLI_DIR))

from lib.evolution import (  # noqa: E402
    _count_vault_backlinks,
    _scan_session_mentions,
    update_doc_scores,
)


def _mk_doc(vault: Path, rel: str, importance: float, confidence: float) -> Path:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\n"
        f"type: concept\n"
        f"title: foo\n"
        f"importance: {importance}\n"
        f"confidence: {confidence}\n"
        f"---\n\n"
        f"# foo\nbody\n",
        encoding="utf-8",
    )
    return p


def _mk_session(
    sessions: Path, name: str, content: str, *, mtime: float | None = None,
) -> Path:
    sessions.mkdir(parents=True, exist_ok=True)
    p = sessions / name
    p.write_text(content, encoding="utf-8")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def test_scan_mentions_empty(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    mentions, neg, pos = _scan_session_mentions("foo.md", sessions, lookback_days=7)
    assert mentions == 0
    assert neg == []
    assert pos == []


def test_scan_mentions_doc_in_session(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    _mk_session(sessions, "s1.jsonl", '{"role":"user","content":"see [[foo]]"}\n')
    mentions, _, _ = _scan_session_mentions("foo.md", sessions, lookback_days=7)
    assert mentions == 1


def test_scan_mentions_lookback_filter(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    old_mtime = time.time() - 30 * 86400
    _mk_session(
        sessions, "old.jsonl",
        '{"role":"user","content":"see [[foo]]"}\n',
        mtime=old_mtime,
    )
    mentions, _, _ = _scan_session_mentions("foo.md", sessions, lookback_days=7)
    assert mentions == 0


def test_scan_negative_feedback(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    _mk_session(
        sessions, "s1.jsonl",
        '{"role":"user","content":"[[foo]] 不对 应该是别的"}\n',
    )
    _, neg, _ = _scan_session_mentions("foo.md", sessions, lookback_days=7)
    assert len(neg) == 1


def test_scan_positive_feedback(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    _mk_session(
        sessions, "s1.jsonl",
        '{"role":"user","content":"[[foo]] 对的 很好"}\n',
    )
    _, _, pos = _scan_session_mentions("foo.md", sessions, lookback_days=7)
    assert len(pos) == 1


def test_count_backlinks_zero(tmp_path: Path) -> None:
    vault = tmp_path
    _mk_doc(vault, "知识库/领域/技术/foo.md", 5.0, 5.0)
    n = _count_vault_backlinks("知识库/领域/技术/foo.md", vault)
    assert n == 0


def test_count_backlinks_multi(tmp_path: Path) -> None:
    vault = tmp_path
    _mk_doc(vault, "知识库/领域/技术/foo.md", 5.0, 5.0)
    (vault / "知识库" / "领域" / "技术" / "ref1.md").write_text(
        "see [[foo]]", encoding="utf-8",
    )
    (vault / "知识库" / "领域" / "技术" / "ref2.md").write_text(
        "also [[foo|alias]]", encoding="utf-8",
    )
    n = _count_vault_backlinks("知识库/领域/技术/foo.md", vault)
    assert n == 2


def test_update_doc_scores_no_signals(tmp_path: Path) -> None:
    vault = tmp_path
    _mk_doc(vault, "知识库/领域/技术/foo.md", 5.0, 5.0)
    r = update_doc_scores("知识库/领域/技术/foo.md", vault, dry_run=False)
    # mentions=0, backlinks=0 → log10(1) - 0.1 = -0.1
    assert r["new_importance"] == 4.9
    assert r["new_confidence"] == 5.0
    assert r["applied"] is True


def test_update_doc_scores_high_mentions(tmp_path: Path) -> None:
    vault = tmp_path
    _mk_doc(vault, "知识库/领域/技术/foo.md", 5.0, 5.0)
    sessions = vault / "记忆" / "L4-流水账" / "sessions"
    for i in range(20):
        _mk_session(
            sessions, f"s{i}.jsonl",
            '{"role":"user","content":"see [[foo]]"}\n',
        )
    r = update_doc_scores("知识库/领域/技术/foo.md", vault, dry_run=True)
    # 20 mentions, 0 backlinks → log10(21) ~ 1.32 - 0.1 = 1.22
    assert r["new_importance"] > r["old_importance"]
    assert r["mentions"] == 20


def test_update_doc_scores_negative_dominant(tmp_path: Path) -> None:
    vault = tmp_path
    _mk_doc(vault, "知识库/领域/技术/foo.md", 5.0, 5.0)
    sessions = vault / "记忆" / "L4-流水账" / "sessions"
    for i in range(3):
        _mk_session(
            sessions, f"neg{i}.jsonl",
            '{"role":"user","content":"[[foo]] 不对"}\n',
        )
    r = update_doc_scores("知识库/领域/技术/foo.md", vault, dry_run=True)
    # 3 neg → confidence -3.0
    assert r["new_confidence"] == 2.0
    assert r["negative_signals"] == 3


def test_update_doc_scores_clamp_high(tmp_path: Path) -> None:
    vault = tmp_path
    _mk_doc(vault, "知识库/领域/技术/foo.md", 9.5, 9.5)
    sessions = vault / "记忆" / "L4-流水账" / "sessions"
    for i in range(50):
        _mk_session(
            sessions, f"s{i}.jsonl",
            '{"role":"user","content":"[[foo]] 对的 很好"}\n',
        )
    r = update_doc_scores("知识库/领域/技术/foo.md", vault, dry_run=True)
    assert r["new_importance"] <= 10.0
    assert r["new_confidence"] <= 10.0


def test_update_doc_scores_clamp_low(tmp_path: Path) -> None:
    vault = tmp_path
    _mk_doc(vault, "知识库/领域/技术/foo.md", 0.0, 0.5)
    sessions = vault / "记忆" / "L4-流水账" / "sessions"
    for i in range(5):
        _mk_session(
            sessions, f"neg{i}.jsonl",
            '{"role":"user","content":"[[foo]] 错了"}\n',
        )
    r = update_doc_scores("知识库/领域/技术/foo.md", vault, dry_run=True)
    assert r["new_confidence"] >= 0.0
    assert r["new_importance"] >= 0.0


def test_update_doc_scores_dry_run(tmp_path: Path) -> None:
    vault = tmp_path
    p = _mk_doc(vault, "知识库/领域/技术/foo.md", 5.0, 5.0)
    original = p.read_text(encoding="utf-8")
    r = update_doc_scores("知识库/领域/技术/foo.md", vault, dry_run=True)
    assert r["applied"] is False
    assert p.read_text(encoding="utf-8") == original


def test_update_doc_scores_no_frontmatter(tmp_path: Path) -> None:
    vault = tmp_path
    p = vault / "知识库" / "领域" / "技术" / "nofm.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# no frontmatter\nbody\n", encoding="utf-8")
    r = update_doc_scores("知识库/领域/技术/nofm.md", vault, dry_run=True)
    assert r.get("error") == "no_frontmatter"


def test_update_doc_scores_not_found(tmp_path: Path) -> None:
    vault = tmp_path
    r = update_doc_scores("知识库/missing.md", vault, dry_run=True)
    assert r.get("error") == "not_found"
