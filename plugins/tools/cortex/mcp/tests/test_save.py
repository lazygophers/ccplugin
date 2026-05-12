"""Tests for cortex_save tool."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import Any

import pytest

from tools.save import handle_save


def _run(args: dict[str, Any]) -> dict[str, Any]:
    result = asyncio.run(handle_save(args))
    assert len(result) == 1
    return json.loads(result[0].text)


def test_save_concept(fake_vault: Path) -> None:
    res = _run(
        {
            "kind": "concept",
            "title": "Test Concept",
            "body": "First paragraph.\n\nSecond paragraph here.\n",
            "tags": ["x", "y"],
        }
    )
    target = Path(res["path"])
    assert target.exists()
    assert target.relative_to(fake_vault).parts[:2] == ("知识库", "领域")
    text = target.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "type: concept" in text
    assert "tags:" in text
    assert len(res["block_ids"]) == 2
    for bid in res["block_ids"]:
        assert f"^{bid}" in text
    # index/hot patched
    assert (fake_vault / "hot.md").exists()
    assert (fake_vault / "index.md").exists()
    assert "test-concept" in (fake_vault / "index.md").read_text(encoding="utf-8")


def test_save_domain_requires_host(fake_vault: Path) -> None:
    with pytest.raises(ValueError):
        _run(
            {
                "kind": "domain",
                "title": "Doc",
                "body": "Body.\n",
            }
        )


def test_save_domain_path(fake_vault: Path) -> None:
    res = _run(
        {
            "kind": "domain",
            "title": "Doc Title",
            "body": "Some body.\n",
            "host": "github.com",
            "org": "lazygophers",
            "repo": "ccplugin",
        }
    )
    target = Path(res["path"])
    assert target.relative_to(fake_vault).parts[:6] == (
        "知识库", "来源", "代码仓库",
        "github.com",
        "lazygophers",
        "ccplugin",
    )


def test_save_log_path(fake_vault: Path) -> None:
    res = _run(
        {
            "kind": "log",
            "title": "Quick note",
            "body": "Hello.\n",
        }
    )
    target = Path(res["path"])
    parts = target.relative_to(fake_vault).parts
    assert parts[0] == "知识库" and parts[1] == "日记" and parts[2] == "日"
    # YYYY-MM directory
    assert len(parts[3]) == 7 and parts[3][4] == "-"


def test_save_masking_applied(fake_vault: Path) -> None:
    # AKIA pattern triggers aws_akid rule.
    secret_body = "Leaking: AKIA1234567890ABCDEF more text.\n"
    res = _run(
        {
            "kind": "log",
            "title": "secret leak",
            "body": secret_body,
        }
    )
    assert res["hits"] >= 1
    target = Path(res["path"])
    text = target.read_text(encoding="utf-8")
    assert "AKIA1234567890ABCDEF" not in text
    assert "<REDACTED:aws_akid>" in text


def test_save_flock_serializes(fake_vault: Path) -> None:
    """Two concurrent saves to the same slug must both succeed (last-write-wins
    on file contents, but no truncation/corruption mid-write)."""
    results: list[dict[str, Any]] = []
    errors: list[BaseException] = []

    def worker(suffix: str) -> None:
        try:
            res = _run(
                {
                    "kind": "concept",
                    "title": "Race Concept",
                    "body": f"Body {suffix}.\n",
                }
            )
            results.append(res)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(s,)) for s in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(results) == 2
    # Both writes targeted the same path (same slug).
    assert results[0]["path"] == results[1]["path"]
    final = Path(results[0]["path"]).read_text(encoding="utf-8")
    # Frontmatter intact, one of the two bodies present.
    assert final.startswith("---\n")
    assert "Body a." in final or "Body b." in final


def test_save_missing_fields(fake_vault: Path) -> None:
    with pytest.raises(ValueError):
        _run({"kind": "concept", "title": "", "body": "x"})
    with pytest.raises(ValueError):
        _run({"kind": "concept", "title": "x", "body": ""})


def test_save_rejects_path_traversal(fake_vault: Path) -> None:
    """host/org/repo containing path separators or `..` must be rejected."""
    for bad in {"host": "../../etc"}, {"host": "github.com", "org": ".."}, {
        "host": "github.com",
        "repo": "a/b",
    }:
        args = {
            "kind": "domain",
            "title": "x",
            "body": "x.\n",
            "host": "github.com",
        }
        args.update(bad)
        with pytest.raises(ValueError):
            _run(args)
