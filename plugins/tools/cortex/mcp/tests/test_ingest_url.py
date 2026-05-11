"""Tests for cortex_ingest_url tool (with mocked urlopen)."""

from __future__ import annotations

import asyncio
import io
import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from tools import ingest_url as ingest_url_mod
from tools.ingest_url import handle_ingest_url

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _run(args: dict[str, Any]) -> dict[str, Any]:
    result = asyncio.run(handle_ingest_url(args))
    assert len(result) == 1
    return json.loads(result[0].text)


class _FakeResp:
    def __init__(self, body: bytes, content_type: str = "text/html") -> None:
        self._body = body
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *_a: Any) -> None:
        pass

    def read(self, *_a: Any) -> bytes:
        return self._body


def _patch_safe(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Bypass SSRF check; return tracker so tests can assert urlopen was reached."""
    calls = {"urlopen": 0, "safe_calls": 0}

    fake_url_security = type("M", (), {})()

    def _is_safe(url: str) -> tuple[bool, str]:
        calls["safe_calls"] += 1
        return True, ""

    fake_url_security.is_safe = _is_safe  # type: ignore[attr-defined]

    real_load = ingest_url_mod._load_module

    def fake_load(filename: str, mod_name: str):
        if filename == "url_security.py":
            return fake_url_security
        return real_load(filename, mod_name)

    monkeypatch.setattr(ingest_url_mod, "_load_module", fake_load)
    return calls


def test_ingest_url_html(monkeypatch: pytest.MonkeyPatch, fake_vault: Path) -> None:
    calls = _patch_safe(monkeypatch)
    html = (
        b"<html><head><title>HelloDoc</title></head><body>"
        b"<article><h1>HelloDoc</h1>"
        b"<p>Some content with AKIAIOSFODNN7EXAMPLE inside.</p>"
        b"<script>alert('x')</script>"
        b"</article></body></html>"
    )

    def fake_urlopen(req: Any, timeout: float = 10.0) -> _FakeResp:
        calls["urlopen"] += 1
        return _FakeResp(html, "text/html; charset=utf-8")

    monkeypatch.setattr(ingest_url_mod.urllib.request, "urlopen", fake_urlopen)

    res = _run({"url": "https://example.com/x", "kind": "log"})
    target = Path(res["path"])
    text = target.read_text(encoding="utf-8")
    assert "HelloDoc" in text
    # html_sanitize strips script
    assert "<script>" not in text
    assert "alert" not in text
    # masking redacts AKID
    assert "AKIAIOSFODNN7EXAMPLE" not in text
    assert "<REDACTED:aws_akid>" in text
    assert res["source_url"] == "https://example.com/x"
    assert calls["urlopen"] == 1


def test_ingest_url_pdf(monkeypatch: pytest.MonkeyPatch, fake_vault: Path) -> None:
    _patch_safe(monkeypatch)
    pdf_bytes = (FIXTURES / "sample.pdf").read_bytes()

    def fake_urlopen(req: Any, timeout: float = 10.0) -> _FakeResp:
        return _FakeResp(pdf_bytes, "application/pdf")

    monkeypatch.setattr(ingest_url_mod.urllib.request, "urlopen", fake_urlopen)
    res = _run({"url": "https://example.com/x.pdf", "kind": "log"})
    text = Path(res["path"]).read_text(encoding="utf-8")
    assert "Cortex Ingest Sample" in text
    assert "<REDACTED:aws_akid>" in text


def test_ingest_url_ssrf_blocks_before_fetch(
    monkeypatch: pytest.MonkeyPatch, fake_vault: Path
) -> None:
    """SSRF gate must reject internal URLs before urlopen is called."""
    urlopen_called = {"n": 0}

    def fake_urlopen(req: Any, timeout: float = 10.0) -> _FakeResp:
        urlopen_called["n"] += 1
        return _FakeResp(b"", "text/html")

    monkeypatch.setattr(ingest_url_mod.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="url_security"):
        _run({"url": "http://127.0.0.1/secret", "kind": "log"})
    assert urlopen_called["n"] == 0


def test_ingest_url_unsupported_content_type(
    monkeypatch: pytest.MonkeyPatch, fake_vault: Path
) -> None:
    _patch_safe(monkeypatch)

    def fake_urlopen(req: Any, timeout: float = 10.0) -> _FakeResp:
        return _FakeResp(b"raw bytes", "application/octet-stream")

    monkeypatch.setattr(ingest_url_mod.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ValueError, match="Content-Type"):
        _run({"url": "https://example.com/blob", "kind": "log"})


def test_ingest_url_404(monkeypatch: pytest.MonkeyPatch, fake_vault: Path) -> None:
    _patch_safe(monkeypatch)

    def fake_urlopen(req: Any, timeout: float = 10.0) -> Any:
        raise urllib.error.HTTPError(
            "https://example.com/missing", 404, "Not Found", {}, io.BytesIO(b"")
        )

    monkeypatch.setattr(ingest_url_mod.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="http error 404"):
        _run({"url": "https://example.com/missing", "kind": "log"})


def test_ingest_url_invalid_kind(fake_vault: Path) -> None:
    with pytest.raises(ValueError):
        _run({"url": "https://example.com/", "kind": "bogus"})


def test_ingest_url_empty(fake_vault: Path) -> None:
    with pytest.raises(ValueError):
        _run({"url": "", "kind": "log"})
