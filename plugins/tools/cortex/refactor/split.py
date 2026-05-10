#!/usr/bin/env python3
"""cortex refactor: split — break a page into one page per H2 section.

Usage:
    split.py --vault PATH --from REL [--out-dir REL] [--apply]

Default dry-run. stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import backup_file, make_backup_ts


H2_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w一-鿿-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:60] or "section"


def split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            return text[: end + 4], text[end + 4 :].lstrip("\n")
    return "", text


def split_by_h2(body: str) -> list[tuple[str, str]]:
    matches = list(H2_RE.finditer(body))
    if not matches:
        return []
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((title, body[start:end].rstrip() + "\n"))
    return sections


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--out-dir", default=None, help="vault-relative output dir (default: src parent)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    src = (vault / args.src).resolve()
    if not src.is_file():
        print(json.dumps({"error": f"source not found: {args.src}"}), file=sys.stderr)
        return 2

    text = src.read_text(encoding="utf-8", errors="replace")
    fm, body = split_frontmatter(text)
    sections = split_by_h2(body)
    if not sections:
        print(json.dumps({"error": "no H2 sections to split"}), file=sys.stderr)
        return 2

    out_dir = (vault / args.out_dir) if args.out_dir else src.parent
    plan: list[dict] = []
    for title, content in sections:
        slug = slugify(title)
        target = out_dir / f"{src.stem}--{slug}.md"
        page = (fm + ("\n\n" if fm else "") + f"# {title}\n\n" + content.split("\n", 1)[1]
                if "\n" in content else fm + "\n\n" + content)
        plan.append({
            "title": title,
            "path": str(target.relative_to(vault)),
            "lines": page.count("\n") + 1,
        })

    out = {
        "op": "split",
        "from": args.src,
        "sections": plan,
        "applied": False,
    }

    if args.apply:
        ts = make_backup_ts()
        backup_file(vault, "refactor-split", ts, src)
        out_dir.mkdir(parents=True, exist_ok=True)
        for (title, content), entry in zip(sections, plan):
            target = vault / entry["path"]
            if target.exists():
                continue  # never overwrite
            page_body = content.split("\n", 1)[1] if "\n" in content else ""
            page = (fm + "\n\n" if fm else "") + f"# {title}\n\n{page_body}"
            target.write_text(page, encoding="utf-8")
        # leave original in place with stub note appended
        stub = (text.rstrip() + "\n\n> [!info] split into:\n"
                + "\n".join(f"> - [[{Path(p['path']).stem}]]" for p in plan) + "\n")
        src.write_text(stub, encoding="utf-8")
        out["applied"] = True
        out["backup_ts"] = ts

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
