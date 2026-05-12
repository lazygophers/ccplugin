"""`cortex_ingest_url` MCP tool — fetch URL, extract, save (P4).

Pipeline (order hard-locked):
  1. url_security.is_safe(url)  -- SSRF gate, fail-closed
  2. urllib.request.urlopen(url, timeout=10)
  3. Content-Type route:
       text/html or html-ish -> extractors.html.extract
       application/pdf or .pdf -> tempfile + extractors.pdf.extract
       else -> ValueError
  4. html_sanitize.sanitize(body)  (HTML path only)
  5. save._save_internal -> masking + write + index/hot patch
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from lib.extractors import html as html_extractor
from lib.extractors import pdf as pdf_extractor
from tools.save import _save_internal

INGEST_URL_TOOL = Tool(
    name="cortex_ingest_url",
    description=(
        "抓 URL 抽正文落档 cortex vault: url_security→fetch→"
        "html_sanitize→masking→save"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri"},
            "kind": {"type": "string", "enum": ["concept", "domain", "log"]},
            "title": {"type": "string", "description": "可选, 缺则用 HTML <title>"},
            "host": {"type": "string"},
            "org": {"type": "string"},
            "repo": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["url", "kind"],
    },
)

_TIMEOUT = 10.0
_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB cap


def _load_module(filename: str, mod_name: str) -> Any:
    here = Path(__file__).resolve()
    # mcp/tools/ingest_url.py -> mcp/ -> plugins/tools/cortex/
    candidate = here.parent.parent.parent / "hooks" / "_lib" / filename
    if not candidate.is_file():
        # Consult ~/.cortex/config.json (install_path) — env-free fallback.
        import json as _json

        cfg = Path.home() / ".cortex" / "config.json"
        hint = None
        if cfg.is_file():
            try:
                hint = _json.loads(cfg.read_text(encoding="utf-8")).get("install_path")
            except Exception:
                hint = None
        if hint:
            candidate = Path(hint).expanduser() / "hooks" / "_lib" / filename
    if not candidate.is_file():
        raise RuntimeError(
            f"cortex_ingest_url: {filename} not found. "
            "Set 'install_path' in ~/.cortex/config.json to the cortex plugin directory."
        )
    spec = importlib.util.spec_from_file_location(mod_name, candidate)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {filename} from {candidate}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _is_pdf(content_type: str, url: str) -> bool:
    ct = (content_type or "").lower().split(";", 1)[0].strip()
    if ct == "application/pdf":
        return True
    # Fallback to extension when server gave no/odd Content-Type.
    if url.lower().split("?", 1)[0].endswith(".pdf"):
        return True
    return False


def _is_html(content_type: str) -> bool:
    ct = (content_type or "").lower().split(";", 1)[0].strip()
    return ct in ("text/html", "application/xhtml+xml", "")


async def handle_ingest_url(args: dict) -> list[TextContent]:
    args = args or {}
    url = args.get("url")
    kind = args.get("kind")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("cortex_ingest_url: 'url' required (non-empty string)")
    if kind not in ("concept", "domain", "log"):
        raise ValueError(
            "cortex_ingest_url: 'kind' must be one of concept/domain/log"
        )

    # 1. SSRF gate -- fail closed before any fetch.
    url_security = _load_module("url_security.py", "cortex_url_security")
    safe, reason = url_security.is_safe(url)
    if not safe:
        raise ValueError(f"cortex_ingest_url: url_security rejected: {reason}")

    # 2. Fetch.
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "cortex-mcp/0.1 (+ingest)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read(_MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"cortex_ingest_url: http error {exc.code}: {url}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cortex_ingest_url: url error: {exc}") from exc
    if len(raw) > _MAX_BYTES:
        raise RuntimeError(
            f"cortex_ingest_url: payload exceeds {_MAX_BYTES} bytes"
        )

    warnings: list[str] = []
    extracted_title: str | None = None

    # 3. Route by Content-Type.
    if _is_pdf(content_type, url):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(raw)
            tmp_path = Path(tf.name)
        try:
            result = pdf_extractor.extract(tmp_path)
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass
        body = result["body"]
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
    elif _is_html(content_type):
        result = html_extractor.extract(raw)
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
        # 4. P0 html_sanitize -- post-extract, pre-save.
        html_sanitize = _load_module("html_sanitize.py", "cortex_html_sanitize")
        body = html_sanitize.sanitize(result["body"])
    else:
        raise ValueError(
            f"cortex_ingest_url: unsupported Content-Type {content_type!r}"
        )

    if not body or not body.strip():
        # Save needs non-empty body; surface clearly.
        raise RuntimeError("cortex_ingest_url: extracted body is empty")

    title = args.get("title") or extracted_title or url

    # 5. Save via shared internal (handles masking + write + patch).
    save_res = _save_internal(
        kind=kind,
        title=title,
        body=body,
        tags=args.get("tags") or [],
        host=args.get("host"),
        org=args.get("org"),
        repo=args.get("repo"),
        source_meta={"url": url, "content_type": content_type},
    )

    result_obj = {
        "path": save_res["path"],
        "source_url": url,
        "block_ids": save_res["block_ids"],
        "hits": save_res["hits"],
        "warnings": warnings,
    }
    return [TextContent(type="text", text=json.dumps(result_obj, ensure_ascii=False))]
