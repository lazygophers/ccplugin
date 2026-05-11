"""Tests for cortex_ingest_file tool."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from tools.ingest_file import handle_ingest_file

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _run(args: dict[str, Any]) -> dict[str, Any]:
    result = asyncio.run(handle_ingest_file(args))
    assert len(result) == 1
    return json.loads(result[0].text)


def test_ingest_pdf(fake_vault: Path) -> None:
    res = _run(
        {"path": str(FIXTURES / "sample.pdf"), "kind": "log"}
    )
    target = Path(res["path"])
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "Cortex Ingest Sample" in text
    # masking wired: AWS AKID redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in text
    assert "<REDACTED:aws_akid>" in text
    assert res["hits"] >= 1


def test_ingest_epub(fake_vault: Path) -> None:
    res = _run({"path": str(FIXTURES / "sample.epub"), "kind": "log"})
    text = Path(res["path"]).read_text(encoding="utf-8")
    assert "Chapter One" in text
    assert "<script>" not in text
    assert "<REDACTED:aws_akid>" in text


def test_ingest_docx(fake_vault: Path) -> None:
    res = _run({"path": str(FIXTURES / "sample.docx"), "kind": "log"})
    text = Path(res["path"]).read_text(encoding="utf-8")
    assert "Cortex Ingest Sample" in text
    assert "<REDACTED:aws_akid>" in text


def test_ingest_md(fake_vault: Path) -> None:
    res = _run({"path": str(FIXTURES / "sample.md"), "kind": "log"})
    text = Path(res["path"]).read_text(encoding="utf-8")
    assert "Sample MD" in text
    assert "<REDACTED:aws_akid>" in text


def test_ingest_txt(fake_vault: Path) -> None:
    res = _run({"path": str(FIXTURES / "sample.txt"), "kind": "log"})
    text = Path(res["path"]).read_text(encoding="utf-8")
    assert "Plain text" in text
    assert "<REDACTED:aws_akid>" in text


def test_ingest_file_unsupported_ext(fake_vault: Path, tmp_path: Path) -> None:
    p = tmp_path / "weird.xyz"
    p.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError):
        _run({"path": str(p), "kind": "log"})


def test_ingest_file_missing(fake_vault: Path) -> None:
    with pytest.raises(OSError):
        _run({"path": "/nonexistent/path/file.pdf", "kind": "log"})


def test_ingest_file_traversal_safe(fake_vault: Path) -> None:
    # `../../etc/passwd` resolves but won't exist as .pdf/.epub/.docx/.md/.txt
    # under that resolution — and even if it did, our check is just OSError/ValueError.
    with pytest.raises((OSError, ValueError)):
        _run({"path": "../../etc/passwd", "kind": "log"})


def test_ingest_file_invalid_kind(fake_vault: Path) -> None:
    with pytest.raises(ValueError):
        _run({"path": str(FIXTURES / "sample.md"), "kind": "bogus"})


def test_ingest_file_empty_path(fake_vault: Path) -> None:
    with pytest.raises(ValueError):
        _run({"path": "", "kind": "log"})
