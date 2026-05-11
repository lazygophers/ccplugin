"""Content extractors for cortex ingest pipeline (P4).

Each extractor exposes `extract(source) -> dict` with shape:
    {"title": str|None, "body": str (markdown), "meta": dict, "warnings": list[str]}

Raise `ValueError` on unsupported/invalid input, `RuntimeError` on
unrecoverable extraction failure (encrypted/corrupt).
"""

from . import docx, epub, html, pdf  # noqa: F401

__all__ = ["html", "pdf", "epub", "docx"]
