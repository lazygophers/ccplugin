"""EPUB extractor via ebooklib — chapters HTML → markdown via html.extract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import html as html_extractor


def _meta_first(book: Any, namespace: str, name: str) -> str | None:
    try:
        items = book.get_metadata(namespace, name)
    except Exception:
        return None
    if not items:
        return None
    try:
        val = items[0][0]
    except (IndexError, TypeError):
        return None
    return val or None


def extract(source: Path | str) -> dict[str, Any]:
    try:
        from ebooklib import ITEM_DOCUMENT, epub
    except ImportError as exc:  # pragma: no cover - dep declared in pyproject
        raise RuntimeError(f"epub.extract: ebooklib not installed: {exc}") from exc

    if not isinstance(source, (str, Path)):
        raise ValueError(f"epub.extract: unsupported source type {type(source)!r}")
    path = Path(source)
    if not path.is_file():
        raise ValueError(f"epub.extract: file not found: {path}")

    try:
        book = epub.read_epub(str(path))
    except Exception as exc:
        raise RuntimeError(f"epub.extract: parse failure: {exc}") from exc

    # Lazy-import P0 html_sanitize so epub chapters get script/iframe stripped
    # before we hand text downstream. We import here (not at module top) to
    # avoid pulling hooks/_lib for non-epub extractors.
    sanitize = _load_html_sanitize()

    chapters: list[str] = []
    warnings: list[str] = []
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        raw = item.get_content()
        try:
            html_doc = raw.decode("utf-8", errors="replace")
        except Exception:
            html_doc = raw.decode("latin-1", errors="replace")
            warnings.append("epub-chapter-decode-fallback")
        try:
            result = html_extractor.extract(html_doc)
        except (ValueError, RuntimeError) as exc:
            warnings.append(f"epub-chapter-skip: {exc}")
            continue
        body_md = sanitize(result["body"])
        if body_md.strip():
            chapters.append(body_md.rstrip())

    body = "\n\n---\n\n".join(chapters)
    if not body.strip():
        warnings.append("epub-empty-body")

    title = _meta_first(book, "DC", "title")
    author = _meta_first(book, "DC", "creator")
    lang = _meta_first(book, "DC", "language")

    return {
        "title": title,
        "body": body,
        "meta": {
            "author": author,
            "lang": lang,
            "chapter_count": len(chapters),
        },
        "warnings": warnings,
    }


def _load_html_sanitize():
    """Load P0 html_sanitize.sanitize from hooks/_lib (lazy)."""
    import importlib.util
    import json as _json
    import sys

    here = Path(__file__).resolve()
    # mcp/lib/extractors/epub.py -> mcp/ -> plugins/tools/cortex/
    candidate = here.parent.parent.parent.parent / "hooks" / "_lib" / "html_sanitize.py"
    if not candidate.is_file():
        # Env-free: consult ~/.cortex/config.json (install_path).
        cfg = Path.home() / ".cortex" / "config.json"
        hint = None
        if cfg.is_file():
            try:
                hint = _json.loads(cfg.read_text(encoding="utf-8")).get("install_path")
            except Exception:
                hint = None
        if hint:
            candidate = Path(hint).expanduser() / "hooks" / "_lib" / "html_sanitize.py"
    if not candidate.is_file():
        # Fall back to identity if filter missing — extractors must still work.
        return lambda s: s
    spec = importlib.util.spec_from_file_location(
        "cortex_html_sanitize", candidate
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        return lambda s: s
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cortex_html_sanitize"] = mod
    spec.loader.exec_module(mod)
    return mod.sanitize
