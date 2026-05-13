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

import argparse
import importlib.util
import json
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Allow direct CLI invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.extractors import html as html_extractor  # noqa: E402
from lib.extractors import pdf as pdf_extractor  # noqa: E402
from save import _save_internal  # noqa: E402

_TIMEOUT = 10.0
_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB cap


def _load_module(filename: str, mod_name: str) -> Any:
    here = Path(__file__).resolve()
    # cli/ingest_url.py -> cli/ -> scripts/ -> scripts/hooks/_lib/<filename>
    candidate = here.parent.parent / "hooks" / "_lib" / filename
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


_REPO_PATH_RE = re.compile(r"^/+(?P<org>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


def _route_url(url: str) -> dict:
    """Decide kind + host/org/repo from URL.

    GitHub/GitLab/含 gitlab 子串 host → kind=project, 抽 org/repo from path.
    arxiv.org / 其他 host → kind=inbox (统一落 知识库/收件箱/, 等 digest 分发).
    host 字段保留用于 _save_internal 生成 收件箱/<host>-<slug>.md.
    """
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        return {"kind": "inbox", "host": "unknown"}
    if host in ("github.com", "gitlab.com") or "gitlab" in host:
        m = _REPO_PATH_RE.match(parsed.path or "")
        if m:
            return {
                "kind": "project",
                "host": host,
                "org": m.group("org"),
                "repo": m.group("repo"),
            }
        return {"kind": "inbox", "host": host}
    # arxiv / 其他外站 → 统一落收件箱 (待 digest 分发到 领域/<域> 或 项目/笔记)
    return {"kind": "inbox", "host": host}


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


def cli_ingest_url(args: dict) -> dict:
    args = args or {}
    url = args.get("url")
    kind = args.get("kind")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("cortex_ingest_url: 'url' required (non-empty string)")
    if kind is None:
        # Auto-route by URL host.
        routed = _route_url(url)
        kind = routed["kind"]
        for k in ("host", "org", "repo", "source_sub"):
            if routed.get(k) and not args.get(k):
                args[k] = routed[k]
    if kind not in (
        "entity", "concept", "project", "domain", "source",
        "reflection", "question", "fleeting", "inbox", "log", "journal",
    ):
        raise ValueError(
            "cortex_ingest_url: 'kind' must be one of entity/concept/project/domain/source/reflection/question/fleeting/inbox/log/journal"
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
        source_sub=args.get("source_sub"),
        source_meta={"url": url, "content_type": content_type},
    )

    result_obj = {
        "path": save_res["path"],
        "source_url": url,
        "block_ids": save_res["block_ids"],
        "hits": save_res["hits"],
        "warnings": warnings,
    }
    return result_obj


def main() -> None:
    parser = argparse.ArgumentParser(description="cortex_ingest_url CLI.")
    parser.add_argument("--url", required=True)
    parser.add_argument(
        "--kind",
        choices=[
            "entity", "concept", "project", "domain", "source",
            "reflection", "question", "fleeting", "inbox", "log", "journal",
        ],
        default=None,
        help="If omitted, auto-route by URL host (github/gitlab → project, 其他 → inbox 落 知识库/收件箱/)",
    )
    parser.add_argument("--title")
    parser.add_argument("--host")
    parser.add_argument("--org")
    parser.add_argument("--repo")
    parser.add_argument(
        "--source-sub",
        dest="source_sub",
        default=None,
        help="source subdir (网页/论文/书籍)",
    )
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    ns = parser.parse_args()
    tags = [t.strip() for t in ns.tags.split(",") if t.strip()] if ns.tags else []
    result = cli_ingest_url(
        {
            "url": ns.url,
            "kind": ns.kind,
            "title": ns.title,
            "host": ns.host,
            "org": ns.org,
            "repo": ns.repo,
            "source_sub": ns.source_sub,
            "tags": tags,
        }
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
