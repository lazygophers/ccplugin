#!/usr/bin/env python3
"""regen_template_manifest.py — 扫 templates/ + presets/seed/, 生成 sha256 + version manifest.

Outputs:
- plugins/tools/cortex/presets/seed/_templates/_manifest.json
- plugins/tools/cortex/presets/_manifest.json
- plugins/tools/cortex/_manifest.json  (global, top-level summary)

Run after editing any template/seed file. CI / pre-commit can verify clean.
stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # plugins/tools/cortex/


def sha256_normalized(p: Path) -> str:
    """sha256 of content with normalized line endings (CRLF -> LF)."""
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def extract_template_version(p: Path) -> int:
    """Read frontmatter `template_version` or HTML `<!-- cortex-template-version: N -->`.

    Default: 1.
    """
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 1
    # Find first frontmatter block (allow leading HTML comments)
    fm_match = re.match(r"^(?:<!--[^\n]*-->\n)*---\n(.*?)\n---", text, re.S)
    if fm_match:
        vm = re.search(r"^template_version\s*:\s*(\d+)", fm_match.group(1), re.M)
        if vm:
            return int(vm.group(1))
    hm = re.search(r"<!--\s*cortex-template-version:\s*(\d+)\s*-->", text)
    if hm:
        return int(hm.group(1))
    return 1


def gen_entries(base: Path, patterns: list[str]) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    for pat in patterns:
        for p in sorted(base.glob(pat)):
            if not p.is_file():
                continue
            name = p.name
            # skip the manifest itself + non-template artefacts
            if name == "_manifest.json":
                continue
            if name == "memory-policy.yaml":
                continue
            rel = str(p.relative_to(base))
            entries[rel] = {
                "sha256": sha256_normalized(p),
                "template_version": extract_template_version(p),
            }
    return entries


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # templates/
    tpl_base = ROOT / "presets" / "seed" / "_templates"
    tpl_entries = gen_entries(tpl_base, ["**/*.md", "**/*.html"])
    tpl_version = max(
        (e["template_version"] for e in tpl_entries.values()), default=1
    )
    tpl_manifest = {
        "version": tpl_version,
        "generated": ts,
        "entries": tpl_entries,
    }
    (tpl_base / "_manifest.json").write_text(
        json.dumps(tpl_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # presets/seed/
    seed_base = ROOT / "presets"
    seed_entries = gen_entries(seed_base, ["seed/**/*.md"])
    seed_version = max(
        (e["template_version"] for e in seed_entries.values()), default=1
    )
    seed_manifest = {
        "version": seed_version,
        "generated": ts,
        "entries": seed_entries,
    }
    (seed_base / "_manifest.json").write_text(
        json.dumps(seed_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # global top-level summary
    global_manifest = {
        "version": max(tpl_version, seed_version),
        "templates_version": tpl_version,
        "seed_version": seed_version,
        "generated": ts,
    }
    (ROOT / "_manifest.json").write_text(
        json.dumps(global_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"templates: {len(tpl_entries)} entries, version={tpl_version}")
    print(f"seed:      {len(seed_entries)} entries, version={seed_version}")
    print(f"global:    version={global_manifest['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
