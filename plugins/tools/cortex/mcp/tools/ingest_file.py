"""`cortex_ingest_file` MCP tool — read local file, extract, save (P4)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.types import TextContent, Tool

from lib.extractors import docx as docx_extractor
from lib.extractors import epub as epub_extractor
from lib.extractors import pdf as pdf_extractor
from tools.save import _save_internal

INGEST_FILE_TOOL = Tool(
    name="cortex_ingest_file",
    description=(
        "读本地文件抽正文落档 cortex vault: pdf/epub/docx/md/txt → "
        "extract → masking → save"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "本地文件路径"},
            "kind": {"type": "string", "enum": ["concept", "domain", "log"]},
            "title": {"type": "string"},
            "host": {"type": "string"},
            "org": {"type": "string"},
            "repo": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["path", "kind"],
    },
)

_SUPPORTED_EXTS = {".pdf", ".epub", ".docx", ".md", ".txt", ".markdown"}


async def handle_ingest_file(args: dict) -> list[TextContent]:
    args = args or {}
    raw_path = args.get("path")
    kind = args.get("kind")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("cortex_ingest_file: 'path' required (non-empty string)")
    if kind not in ("concept", "domain", "log"):
        raise ValueError(
            "cortex_ingest_file: 'kind' must be one of concept/domain/log"
        )

    path = Path(os.path.expanduser(raw_path)).resolve()
    if not path.exists():
        raise OSError(f"cortex_ingest_file: file not found: {path}")
    if not path.is_file():
        raise OSError(f"cortex_ingest_file: not a regular file: {path}")
    if not os.access(path, os.R_OK):
        raise OSError(f"cortex_ingest_file: not readable: {path}")

    ext = path.suffix.lower()
    if ext not in _SUPPORTED_EXTS:
        raise ValueError(f"cortex_ingest_file: unsupported extension: {ext}")

    warnings: list[str] = []
    extracted_title: str | None = None

    if ext == ".pdf":
        result = pdf_extractor.extract(path)
        body = result["body"]
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
    elif ext == ".epub":
        result = epub_extractor.extract(path)
        body = result["body"]
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
    elif ext == ".docx":
        result = docx_extractor.extract(path)
        body = result["body"]
        extracted_title = result.get("title")
        warnings.extend(result.get("warnings") or [])
    else:  # .md, .markdown, .txt -- read directly
        try:
            body = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            body = path.read_text(encoding="utf-8", errors="replace")
            warnings.append("encoding-fallback")
        extracted_title = None

    if not body or not body.strip():
        raise RuntimeError("cortex_ingest_file: extracted body is empty")

    title = args.get("title") or extracted_title or path.stem

    save_res = _save_internal(
        kind=kind,
        title=title,
        body=body,
        tags=args.get("tags") or [],
        host=args.get("host"),
        org=args.get("org"),
        repo=args.get("repo"),
        source_meta={"file": str(path), "ext": ext},
    )

    result_obj = {
        "path": save_res["path"],
        "source_file": str(path),
        "block_ids": save_res["block_ids"],
        "hits": save_res["hits"],
        "warnings": warnings,
    }
    return [TextContent(type="text", text=json.dumps(result_obj, ensure_ascii=False))]
