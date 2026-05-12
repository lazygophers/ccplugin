"""Resolve the Obsidian vault path.

Mirrors the logic in `hooks/_lib/resolve_vault.sh` so MCP tools agree with
hooks/CLI on which directory is "the vault":

1. `CORTEX_VAULT_PATH` / `OBSIDIAN_VAULT` env — **platform contract**.
   MCP servers are launched by Claude Code via `.claude-plugin/plugin.json`
   `mcpServers.env`, which injects these. Per PRD this is the only
   exception to the env-free rule for MCP business code.
2. `~/.cortex/config.json` `vault` key (canonical, env-free).
3. Single `.obsidian/` match under `~/Documents/` or
   `~/Library/Mobile Documents/`.

Returns `None` when nothing matches; callers raise.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _is_vault(p: Path) -> bool:
    return p.is_dir() and (p / ".obsidian").is_dir()


def _from_env() -> Path | None:
    # MCP platform-contract env (set by Claude Code via plugin.json).
    for key in ("CORTEX_VAULT_PATH", "OBSIDIAN_VAULT"):
        raw = os.environ.get(key)
        if not raw:
            continue
        p = Path(os.path.expanduser(raw))
        if _is_vault(p):
            return p
    return None


def _from_config() -> Path | None:
    cfg = Path.home() / ".cortex" / "config.json"
    if not cfg.is_file():
        return None
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    raw = data.get("vault") or ""
    if not raw:
        return None
    p = Path(os.path.expanduser(raw))
    return p if _is_vault(p) else None


def _autodetect() -> Path | None:
    home = Path(os.path.expanduser("~"))
    roots = [home / "Documents", home / "Library" / "Mobile Documents"]
    hits: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        # rglob can be slow on huge trees; cap by walking shallowly.
        for entry in root.glob("*/.obsidian"):
            hits.append(entry.parent)
        for entry in root.glob("*/*/.obsidian"):
            hits.append(entry.parent)
    if len(hits) == 1:
        return hits[0]
    return None


def resolve_vault() -> Path:
    """Return the absolute vault Path. Raise `RuntimeError` if unresolved."""
    for source in (_from_env, _from_config, _autodetect):
        p = source()
        if p is not None:
            return p
    raise RuntimeError(
        "cortex: vault path unresolved. "
        "Set 'vault' in ~/.cortex/config.json (or CORTEX_VAULT_PATH via plugin.json mcpServers.env)."
    )
