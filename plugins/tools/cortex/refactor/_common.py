"""Shared helpers for cortex refactor scripts. stdlib only."""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

WIKILINK_RE = re.compile(r"(?<!\!)\[\[([^\[\]\n|#^]+)((?:[#^][^\[\]\n|]*)?(?:\|[^\[\]\n]*)?)\]\]")
TRANSCLUSION_RE = re.compile(r"(?<!\\)!\[\[([^\[\]\n|#^]+)((?:[#^][^\[\]\n|]*)?(?:\|[^\[\]\n]*)?)\]\]")

EXCLUDE_DIRS = {"_meta", ".obsidian", ".trash", ".git"}


def iter_md_files(vault: Path):
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault)
        if rel.parts and rel.parts[0] in EXCLUDE_DIRS:
            continue
        yield p


def backup_file(vault: Path, op: str, ts: str, src: Path) -> Path:
    rel = src.relative_to(vault)
    bdir = vault / "_meta" / ".cortex-backup" / op / ts
    bpath = bdir / rel
    bpath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, bpath)
    return bpath


def make_backup_ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def rewrite_wikilinks(text: str, mapping: dict[str, str]) -> tuple[str, int]:
    """Rewrite wikilink targets per `mapping` (lowercase basename → new target).

    Returns (new_text, replacements).
    """
    n = 0
    mapping_lc = {k.lower(): v for k, v in mapping.items()}

    def repl(m: re.Match) -> str:
        nonlocal n
        target = m.group(1).strip()
        suffix = m.group(2) or ""
        bare = target
        if bare.lower().endswith(".md"):
            bare = bare[:-3]
        key = bare.split("/")[-1].lower()
        if key in mapping_lc:
            n += 1
            return f"[[{mapping_lc[key]}{suffix}]]"
        # also try full-path key
        if bare.lower() in mapping_lc:
            n += 1
            return f"[[{mapping_lc[bare.lower()]}{suffix}]]"
        return m.group(0)

    new_text = WIKILINK_RE.sub(repl, text)

    def repl_t(m: re.Match) -> str:
        nonlocal n
        target = m.group(1).strip()
        suffix = m.group(2) or ""
        bare = target
        if bare.lower().endswith(".md"):
            bare = bare[:-3]
        key = bare.split("/")[-1].lower()
        if key in mapping_lc:
            n += 1
            return f"![[{mapping_lc[key]}{suffix}]]"
        if bare.lower() in mapping_lc:
            n += 1
            return f"![[{mapping_lc[bare.lower()]}{suffix}]]"
        return m.group(0)

    new_text = TRANSCLUSION_RE.sub(repl_t, new_text)
    return new_text, n
