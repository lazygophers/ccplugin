"""Unit tests for lib/extractors/*."""

from __future__ import annotations

from pathlib import Path

import pytest

from lib.extractors import docx as docx_extractor
from lib.extractors import epub as epub_extractor
from lib.extractors import html as html_extractor
from lib.extractors import pdf as pdf_extractor

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ---------- html ----------


def test_html_extract_picks_article() -> None:
    html = (
        "<html lang='en'><head><title>Doc</title></head><body>"
        "<nav><a href='/x'>nav</a></nav>"
        "<article><h1>Title</h1>"
        "<p>First paragraph with content.</p>"
        "<p>Second paragraph.</p></article>"
        "<footer>copyright</footer></body></html>"
    )
    r = html_extractor.extract(html)
    assert r["title"] == "Doc"
    assert r["meta"]["lang"] == "en"
    assert "First paragraph" in r["body"]
    assert "Second paragraph" in r["body"]
    # nav/footer should not dominate
    assert "copyright" not in r["body"] or r["body"].index("First") < r["body"].index(
        "copyright"
    )


def test_html_extract_empty_raises() -> None:
    with pytest.raises(ValueError):
        html_extractor.extract("   ")


def test_html_extract_bytes_decoded() -> None:
    r = html_extractor.extract(b"<html><body><p>hello</p></body></html>")
    assert "hello" in r["body"]


# ---------- pdf ----------


def test_pdf_extract_text() -> None:
    r = pdf_extractor.extract(FIXTURES / "sample.pdf")
    assert r["title"] == "Cortex Sample"
    assert r["meta"]["page_count"] == 1
    assert "Cortex Ingest Sample" in r["body"]
    assert "AKIAIOSFODNN7EXAMPLE" in r["body"]


def test_pdf_extract_missing_path() -> None:
    with pytest.raises(ValueError):
        pdf_extractor.extract(FIXTURES / "nonexistent.pdf")


def test_pdf_extract_corrupt(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf at all")
    with pytest.raises(RuntimeError):
        pdf_extractor.extract(bad)


# ---------- epub ----------


def test_epub_extract_chapters() -> None:
    r = epub_extractor.extract(FIXTURES / "sample.epub")
    assert r["title"] == "Cortex Sample"
    assert r["meta"]["lang"] == "en"
    assert r["meta"]["chapter_count"] >= 1
    assert "Cortex Ingest Sample" in r["body"]
    # script tag should be stripped by html_sanitize chained inside epub.extract
    assert "<script>" not in r["body"]
    assert "alert" not in r["body"] or "AKIAIOSFODNN7EXAMPLE" in r["body"]


def test_epub_extract_missing_path() -> None:
    with pytest.raises(ValueError):
        epub_extractor.extract(FIXTURES / "nonexistent.epub")


def test_epub_extract_corrupt(tmp_path: Path) -> None:
    bad = tmp_path / "bad.epub"
    bad.write_bytes(b"PK\x03\x04 garbage")
    with pytest.raises(RuntimeError):
        epub_extractor.extract(bad)


# ---------- docx ----------


def test_docx_extract_paragraphs() -> None:
    r = docx_extractor.extract(FIXTURES / "sample.docx")
    assert r["title"] == "Cortex Sample"
    assert r["meta"]["paragraph_count"] >= 1
    assert "Cortex Ingest Sample" in r["body"]


def test_docx_extract_missing_path() -> None:
    with pytest.raises(ValueError):
        docx_extractor.extract(FIXTURES / "nonexistent.docx")


def test_docx_extract_corrupt(tmp_path: Path) -> None:
    bad = tmp_path / "bad.docx"
    bad.write_bytes(b"not a real docx")
    with pytest.raises(RuntimeError):
        docx_extractor.extract(bad)
