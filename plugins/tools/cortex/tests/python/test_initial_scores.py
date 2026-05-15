"""Tests for PR3: compute_initial_scores / compute_memory_scores / host_credibility.

启发式权威表: skills/cortex-ingest/references/extract.md §3.1.
"""

from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = PLUGIN_ROOT / "scripts" / "cli"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from lib.remote import (  # noqa: E402
    compute_initial_scores,
    compute_memory_scores,
    host_credibility,
)


# ───────────── host_credibility ─────────────


def test_host_credibility_exact_official():
    assert host_credibility("anthropic.com") == 10.0
    assert host_credibility("openai.com") == 10.0


def test_host_credibility_exact_code_host():
    assert host_credibility("github.com") == 7.5
    assert host_credibility("gitlab.com") == 7.5


def test_host_credibility_exact_doc():
    assert host_credibility("docs.python.org") == 9.5
    assert host_credibility("react.dev") == 9.5


def test_host_credibility_www_strip():
    assert host_credibility("www.github.com") == 7.5
    assert host_credibility("www.anthropic.com") == 10.0


def test_host_credibility_subdomain_parent_fallback():
    # 子域不在表; 但 docs.python.org 在表 (精确); 这里测父域回退:
    # api.github.com → github.com (7.5)
    assert host_credibility("api.github.com") == 7.5
    # raw.githubusercontent.com → 不在表, 默认 4.0 (github.com 不是 githubusercontent.com 父域)
    assert host_credibility("raw.githubusercontent.com") == 4.0


def test_host_credibility_unknown_default():
    assert host_credibility("randomblog.example") == 4.0
    assert host_credibility("") == 4.0


def test_host_credibility_uppercase():
    assert host_credibility("GitHub.com") == 7.5


# ───────────── compute_initial_scores ─────────────


def test_compute_scores_high_coverage_official():
    s = compute_initial_scores(
        host="anthropic.com",
        coverage_ratio=1.0,
        tag_count=10,
        wikilink_count=5,
        when_to_read_len=30,
    )
    assert s["score"] == 10.0
    assert s["source_credibility"] == 10.0
    assert s["maturity"] == "stable"
    # tag 5 + wtr 3 + link 2 = 10.0
    assert s["confidence"] == 10.0


def test_compute_scores_low_coverage_medium():
    s = compute_initial_scores(
        host="medium.com",
        coverage_ratio=0.2,
        tag_count=2,
        wikilink_count=0,
        when_to_read_len=0,
    )
    assert s["score"] == 2.0
    assert s["maturity"] == "draft"
    assert s["source_credibility"] == 5.0


def test_compute_scores_mid_github_review():
    s = compute_initial_scores(
        host="github.com",
        coverage_ratio=0.6,
        tag_count=10,
        wikilink_count=5,
        when_to_read_len=30,
    )
    assert s["score"] == 6.0
    assert s["maturity"] == "review"
    assert s["source_credibility"] == 7.5


def test_compute_scores_clamp_high_coverage():
    # coverage_ratio > 1.0 → clamp 10.0
    s = compute_initial_scores(
        host="anthropic.com",
        coverage_ratio=1.5,
        tag_count=20,
        wikilink_count=20,
        when_to_read_len=100,
    )
    assert s["score"] == 10.0
    assert s["confidence"] == 10.0  # clamped


def test_compute_scores_clamp_negative_coverage():
    s = compute_initial_scores(
        host="github.com",
        coverage_ratio=-0.5,
        tag_count=0,
        wikilink_count=0,
        when_to_read_len=0,
    )
    assert s["score"] == 0.0
    assert s["maturity"] == "draft"
    assert s["confidence"] == 0.0


def test_compute_scores_unknown_host_default():
    s = compute_initial_scores(
        host="unknown-host.example",
        coverage_ratio=0.8,
        tag_count=10,
        wikilink_count=5,
        when_to_read_len=30,
    )
    assert s["source_credibility"] == 4.0
    assert s["score"] == 8.0
    assert s["maturity"] == "stable"


def test_compute_scores_boundary_score_5():
    # score==5 → maturity=review (边界: <5 draft, <8 review, ≥8 stable)
    s = compute_initial_scores(host="github.com", coverage_ratio=0.5)
    assert s["score"] == 5.0
    assert s["maturity"] == "review"


def test_compute_scores_boundary_score_8():
    s = compute_initial_scores(host="github.com", coverage_ratio=0.8)
    assert s["score"] == 8.0
    assert s["maturity"] == "stable"


# ───────────── compute_memory_scores ─────────────


def test_memory_scores_L0_core():
    s = compute_memory_scores(level="L0", user_confirmed=False, body_len=500)
    assert s["importance"] == 9.0
    assert s["confidence"] == 9.5


def test_memory_scores_L1_long_term():
    s = compute_memory_scores(level="L1", user_confirmed=False, body_len=500)
    assert s["importance"] == 7.0
    assert s["confidence"] == 8.0


def test_memory_scores_L4_ledger():
    s = compute_memory_scores(level="L4", user_confirmed=False, body_len=500)
    assert s["importance"] == 2.0
    assert s["confidence"] == 5.0


def test_memory_scores_user_confirmed_boost():
    s = compute_memory_scores(level="L1", user_confirmed=True, body_len=500)
    assert s["confidence"] == 9.0  # 8.0 + 1.0


def test_memory_scores_user_confirmed_clamp():
    # L0 confidence 9.5 + 1.0 = 10.5 → clamp 10.0
    s = compute_memory_scores(level="L0", user_confirmed=True, body_len=500)
    assert s["confidence"] == 10.0


def test_memory_scores_short_body_penalty():
    s = compute_memory_scores(level="L2", user_confirmed=False, body_len=50)
    assert s["importance"] == 4.5  # 5.0 - 0.5


def test_memory_scores_unknown_level_default_L3():
    s = compute_memory_scores(level="LX", user_confirmed=False, body_len=500)
    # 未知层 → 默认 L3
    assert s["importance"] == 3.0
    assert s["confidence"] == 4.5
