"""PDF extractor via pypdf (pure-python)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def extract(source: Path | str | bytes) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError as exc:  # pragma: no cover - dep declared in pyproject
        raise RuntimeError(f"pdf.extract: pypdf not installed: {exc}") from exc

    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise ValueError(f"pdf.extract: file not found: {path}")
        opener: Any = str(path)
    elif isinstance(source, bytes):
        import io

        opener = io.BytesIO(source)
    else:
        raise ValueError(f"pdf.extract: unsupported source type {type(source)!r}")

    try:
        reader = PdfReader(opener)
    except PdfReadError as exc:
        raise RuntimeError(f"pdf.extract: parse failure: {exc}") from exc

    if getattr(reader, "is_encrypted", False):
        # Try empty password before bailing — many PDFs are technically
        # encrypted but accept "" (common w/ exports).
        try:
            ok = reader.decrypt("")
        except Exception:
            ok = 0
        if not ok:
            raise RuntimeError("pdf.extract: encrypted PDF")

    body_parts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover - per-page failure
            text = ""
            body_parts.append(f"<!-- pdf-page-error: {exc} -->")
        if text:
            body_parts.append(text)

    body = "\n\n".join(p.strip() for p in body_parts if p.strip())

    md = reader.metadata
    title = None
    author = None
    if md:
        try:
            title = md.title or None
            author = md.author or None
        except Exception:
            pass

    warnings: list[str] = []
    if not body.strip():
        warnings.append("scan-only pdf, text empty")

    return {
        "title": title,
        "body": body,
        "meta": {
            "page_count": len(reader.pages),
            "author": author,
        },
        "warnings": warnings,
    }
