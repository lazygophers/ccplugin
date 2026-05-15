"""`cortex_search` CLI — multi-level fallback search over the vault.

Position in the wider search hierarchy (see `cortex-search` SKILL.md):

- L1/L2 (AI-facing): `mcp__obsidian__obsidian_simple_search` /
  `mcp__obsidian__obsidian_complex_search` — handled by the model, not here.
- **L3 (this CLI)**: invoked via `~/.cortex/scripts/search.sh` when MCP is
  unreachable. This CLI **cannot** call MCP itself (no protocol bridge from a
  Python subprocess), so it stays in the disk/REST fallback layer.
- L4: `rg` — last-ditch, also model-driven outside this CLI.

Internal fallback order (this CLI only):

1. `hot.md` grep — fast cache of recently-touched notes.
2. `index.md` grep — long-lived registry of canonical entries.
3. Smart Connections REST (`CORTEX_SC_URL`, default `http://127.0.0.1:27123`)
   semantic search if reachable within 1s.
4. `rg --json` over `知识库/`, capped at 50 hits.

Each hit is `{path, title, snippet, score, source}`. The tool returns a single
`TextContent` whose `.text` is the JSON-serialized list so models can parse it
deterministically.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Allow direct `python3 search.py`: add this dir to sys.path so `from lib...` works.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.cortex_common import SCOPE_GLOB as _SCOPE_GLOB  # noqa: E402
from lib.vault_path import resolve_vault  # noqa: E402


def _title_from(path: Path) -> str:
    # Prefer first `# heading` if present, else filename stem.
    try:
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if line.startswith("# "):
                    return line[2:].strip()
                # don't read forever
                if path.stat().st_size > 32_768:
                    break
    except OSError:
        pass
    return path.stem


def _snippet(text: str, query: str, ctx: int = 60) -> str:
    m = re.search(re.escape(query), text, re.IGNORECASE)
    if not m:
        return text[:ctx].replace("\n", " ")
    start = max(0, m.start() - ctx)
    end = min(len(text), m.end() + ctx)
    return text[start:end].replace("\n", " ")


def _grep_file(
    vault: Path, rel: str, query: str, source: str
) -> list[dict[str, Any]]:
    path = vault / rel
    if not path.is_file():
        return []
    hits: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    q = query.lower()
    for line in text.splitlines():
        if q in line.lower():
            hits.append(
                {
                    "path": str(path),
                    "title": _title_from(path),
                    "snippet": line.strip()[:240],
                    "score": 1.0,
                    "source": source,
                }
            )
    return hits


def _smart_connections(
    query: str, limit: int, base: str
) -> list[dict[str, Any]] | None:
    """Probe SC then POST /search. Return None if unreachable."""
    info_url = f"{base.rstrip('/')}/embeddings/info"
    try:
        urllib.request.urlopen(info_url, timeout=1.0).read()  # noqa: S310
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return None
    search_url = f"{base.rstrip('/')}/search"
    payload = json.dumps({"query": query, "top_k": limit}).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        search_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=5.0).read()  # noqa: S310
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return []
    try:
        data = json.loads(resp.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    hits: list[dict[str, Any]] = []
    items = data.get("hits") or data.get("results") or data
    if not isinstance(items, list):
        return []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        hits.append(
            {
                "path": item.get("path") or item.get("file") or "",
                "title": item.get("title") or item.get("name") or "",
                "snippet": (item.get("snippet") or item.get("text") or "")[:240],
                "score": float(item.get("score") or 0.0),
                "source": "smart-connections",
            }
        )
    return hits


def _ripgrep(vault: Path, scope_dir: str, query: str) -> list[dict[str, Any]]:
    target = vault / scope_dir
    if not target.is_dir():
        return []
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["rg", "--json", "-i", "--max-count", "1", query, str(target)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    hits: list[dict[str, Any]] = []
    for raw in proc.stdout.splitlines():
        if len(hits) >= 50:
            break
        try:
            evt = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if evt.get("type") != "match":
            continue
        data = evt.get("data") or {}
        path = (data.get("path") or {}).get("text") or ""
        line_text = (data.get("lines") or {}).get("text") or ""
        if not path:
            continue
        p = Path(path)
        hits.append(
            {
                "path": path,
                "title": _title_from(p),
                "snippet": line_text.strip()[:240],
                "score": 0.5,
                "source": "ripgrep",
            }
        )
    return hits


def _dedup(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for h in hits:
        key = (h.get("path", ""), h.get("snippet", "")[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def cli_search(args: dict) -> list[dict[str, Any]]:
    """CLI entry: returns hits list directly."""
    query = (args or {}).get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("cortex_search: 'query' required (non-empty string)")
    limit = int((args or {}).get("limit") or 10)
    scope = (args or {}).get("scope") or "all"
    if scope not in _SCOPE_GLOB:
        raise ValueError(f"cortex_search: invalid scope {scope!r}")

    vault = resolve_vault()
    hits: list[dict[str, Any]] = []

    if scope == "all":
        hits.extend(_grep_file(vault, "hot.md", query, "hot"))
    if len(hits) < limit:
        hits.extend(_grep_file(vault, "index.md", query, "index"))

    if len(hits) < limit:
        sc_base = os.environ.get("CORTEX_SC_URL", "http://127.0.0.1:27123")
        sc_hits = _smart_connections(query, limit, sc_base)
        if sc_hits:
            hits.extend(sc_hits)

    if len(hits) < limit:
        hits.extend(_ripgrep(vault, _SCOPE_GLOB[scope], query))

    return _dedup(hits)[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="cortex_search CLI: multi-level fallback search over vault.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--scope", default="all", choices=list(_SCOPE_GLOB.keys()))
    ns = parser.parse_args()
    hits = cli_search({"query": ns.query, "limit": ns.limit, "scope": ns.scope})
    print(json.dumps(hits, ensure_ascii=False))


if __name__ == "__main__":
    main()
