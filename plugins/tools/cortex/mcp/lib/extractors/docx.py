"""DOCX extractor via python-docx."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def extract(source: Path | str) -> dict[str, Any]:
    try:
        import docx  # python-docx
    except ImportError as exc:  # pragma: no cover - dep declared in pyproject
        raise RuntimeError(
            f"docx.extract: python-docx not installed: {exc}"
        ) from exc

    if not isinstance(source, (str, Path)):
        raise ValueError(f"docx.extract: unsupported source type {type(source)!r}")
    path = Path(source)
    if not path.is_file():
        raise ValueError(f"docx.extract: file not found: {path}")

    try:
        doc = docx.Document(str(path))
    except Exception as exc:
        raise RuntimeError(f"docx.extract: parse failure: {exc}") from exc

    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    body = "\n\n".join(paragraphs)

    props = doc.core_properties
    title = (props.title or None) if props else None
    author = (props.author or None) if props else None

    warnings: list[str] = []
    if not body.strip():
        warnings.append("docx-empty-body")

    return {
        "title": title,
        "body": body,
        "meta": {
            "author": author,
            "paragraph_count": len(paragraphs),
        },
        "warnings": warnings,
    }
