"""Shared test helpers for cortex python tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def add_paths() -> None:
    """Make plugin Python modules importable."""
    paths = [
        str(PLUGIN_ROOT / "hooks" / "_lib"),
        str(PLUGIN_ROOT / "lint"),
        str(PLUGIN_ROOT / "refactor"),
    ]
    for p in paths:
        if p not in sys.path:
            sys.path.insert(0, p)


def make_vault(root: Path, lang: str = "zh-CN", preset: str = "lyt",
               preserve_transcript: bool = False) -> Path:
    """Build a minimal vault skeleton at root. Return root."""
    root.mkdir(parents=True, exist_ok=True)
    (root / ".obsidian").mkdir(exist_ok=True)
    (root / "_meta").mkdir(exist_ok=True)
    meta = {"lang": lang, "preset": preset, "created": "2026-05-11"}
    if preserve_transcript:
        meta["preserve_transcript"] = True
    (root / "_meta" / "version.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    (root / "log").mkdir(exist_ok=True)
    (root / "folds").mkdir(exist_ok=True)
    (root / "index.md").write_text("# index\n", encoding="utf-8")
    return root


def write_md(path: Path, frontmatter: dict | None, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if frontmatter:
        lines = ["---"]
        for k, v in frontmatter.items():
            if isinstance(v, list):
                lines.append(f"{k}: [{', '.join(repr(x) for x in v)}]")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        text = "\n".join(lines) + "\n\n" + body
    else:
        text = body
    path.write_text(text, encoding="utf-8")
