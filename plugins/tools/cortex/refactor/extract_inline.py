#!/usr/bin/env python3
"""cortex refactor: extract / inline — split H2 section out or fold back.

Usage:
    extract_inline.py --vault PATH --page REL --section H2 \
        --direction extract [--out-path REL] [--apply]
    extract_inline.py --vault PATH --page REL --child REL \
        --direction inline [--section H2] [--apply]

stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    backup_file,
    iter_md_files,
    make_backup_ts,
    rewrite_wikilinks,
)


def _split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            return text[: end + 4], text[end + 4 :].lstrip("\n")
    return "", text


def _slugify(title: str) -> str:
    slug = re.sub(r"[^\w一-鿿\-]+", "-", title.strip(), flags=re.UNICODE)
    slug = re.sub(r"-+", "-", slug).strip("-").lower()
    return slug or "section"


def _find_section(body: str, section: str) -> tuple[int, int, str] | None:
    """Return (start_lineidx, end_lineidx_exclusive, section_body)."""
    lines = body.splitlines(keepends=True)
    header_re = re.compile(r"^##\s+(.+?)\s*$")
    start = None
    target = section.strip()
    for i, line in enumerate(lines):
        m = header_re.match(line)
        if m and m.group(1).strip() == target:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = header_re.match(lines[j])
        if m:
            end = j
            break
    section_body = "".join(lines[start + 1 : end]).rstrip() + "\n"
    return start, end, section_body


def _parent_tags(fm_text: str) -> list[str]:
    """Best-effort: grab a 'tags' line from frontmatter."""
    for line in fm_text.splitlines():
        if line.lower().startswith("tags:"):
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("[") and rest.endswith("]"):
                items = [
                    s.strip().strip("'\"")
                    for s in rest[1:-1].split(",")
                ]
                return [s for s in items if s]
    return []


def _archive_dir(vault: Path) -> Path:
    if (vault / "80_archive").is_dir():
        return vault / "80_archive"
    return vault / ".archive"


def do_extract(args, vault: Path, page: Path) -> dict:
    if not args.section:
        return {"error": "--section required for extract"}
    try:
        page_text = page.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"error": f"read page failed: {e}"}
    fm, body = _split_frontmatter(page_text)
    found = _find_section(body, args.section)
    if not found:
        return {"error": f"section not found: {args.section}"}
    start, end, section_body = found

    out_rel = args.out_path or f"10_concepts/{_slugify(args.section)}.md"
    out_path = (vault / out_rel).resolve()
    try:
        out_path.relative_to(vault)
    except ValueError:
        return {"error": "out-path escapes vault"}

    if out_path.exists():
        return {"error": f"out-path exists: {out_rel}"}

    tags = _parent_tags(fm)
    page_stem = page.stem
    child_fm_lines = ["---", "type: concept", f"source: [[{page_stem}]]"]
    if tags:
        child_fm_lines.append(
            "tags: [" + ", ".join(f"'{t}'" for t in tags) + "]"
        )
    child_fm_lines.append("---")
    child_text = "\n".join(child_fm_lines) + "\n\n" + section_body

    lines = body.splitlines(keepends=True)
    transclusion = f"![[{out_path.stem}]]\n"
    new_body_lines = (
        lines[:start]
        + [lines[start]]  # keep H2 header? per PRD: 替换为 ![[child-stem]]
    )
    # Per PRD: 删除 section body → 替换为 ![[child-stem]]; replace whole section
    new_body_lines = lines[:start] + [transclusion] + lines[end:]
    new_text = (fm + "\n" if fm else "") + "".join(new_body_lines)

    output = {
        "op": "extract",
        "page": str(page.relative_to(vault)),
        "child_path": str(out_path.relative_to(vault)),
        "section": args.section,
        "applied": False,
    }

    if args.apply:
        ts = make_backup_ts()
        backup_file(vault, "extract", ts, page)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(child_text, encoding="utf-8")
        page.write_text(new_text, encoding="utf-8")
        output["applied"] = True

    return output


def do_inline(args, vault: Path, page: Path) -> dict:
    if not args.child:
        return {"error": "--child required for inline"}
    child = (vault / args.child).resolve()
    try:
        child.relative_to(vault)
    except ValueError:
        return {"error": "child path escapes vault"}
    if not child.is_file():
        return {"error": f"child not found: {args.child}"}

    warnings: list[str] = []
    try:
        child_text = child.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"error": f"read child failed: {e}"}
    _cfm, child_body = _split_frontmatter(child_text)
    child_stem = child.stem
    title = args.section or child_stem
    inline_block = f"## {title}\n\n{child_body.rstrip()}\n"

    if re.search(r"!\[\[[^\[\]\n]+\]\]", child_body):
        warnings.append("nested_transclusion")

    try:
        page_text = page.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"error": f"read page failed: {e}"}

    patterns = [
        re.compile(
            r"!\[\[" + re.escape(child_stem)
            + r"(?:#[^\[\]\n|]*)?(?:\|[^\[\]\n]*)?\]\]"
        ),
        re.compile(
            r"(?<!\!)\[\[" + re.escape(child_stem)
            + r"(?:#[^\[\]\n|]*)?(?:\|[^\[\]\n]*)?\]\]"
        ),
    ]
    matched = False
    new_page_text = page_text
    for pat in patterns:
        if pat.search(new_page_text):
            new_page_text = pat.sub(inline_block, new_page_text, count=1)
            matched = True
            break

    output = {
        "op": "inline",
        "page": str(page.relative_to(vault)),
        "child": str(child.relative_to(vault)),
        "applied": False,
        "warnings": warnings,
    }

    if not matched:
        warnings.append("no_reference_in_page; appended at end")
        new_page_text = page_text.rstrip() + "\n\n" + inline_block

    if args.apply:
        ts = make_backup_ts()
        backup_file(vault, "inline", ts, page)
        backup_file(vault, "inline", ts, child)
        page.write_text(new_page_text, encoding="utf-8")
        # move child to archive
        adir = _archive_dir(vault)
        adir.mkdir(parents=True, exist_ok=True)
        archive_target = adir / child.name
        if archive_target.exists():
            archive_target = adir / f"{child.stem}.{ts}{child.suffix}"
        child.rename(archive_target)
        # rewrite remaining wikilinks
        mapping = {child_stem: page.stem}
        for md in iter_md_files(vault):
            try:
                txt = md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            new_txt, n = rewrite_wikilinks(txt, mapping)
            if n:
                md.write_text(new_txt, encoding="utf-8")
        output["applied"] = True

    return output


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--page", required=True)
    ap.add_argument("--direction", required=True,
                    choices=["extract", "inline"])
    ap.add_argument("--section")
    ap.add_argument("--child")
    ap.add_argument("--out-path", dest="out_path")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"vault not found: {vault}"}),
              file=sys.stderr)
        return 2
    page = (vault / args.page).resolve()
    try:
        page.relative_to(vault)
    except ValueError:
        print(json.dumps({"error": "page path escapes vault"}),
              file=sys.stderr)
        return 2
    if not page.is_file():
        print(json.dumps({"error": f"page not found: {args.page}"}),
              file=sys.stderr)
        return 2

    if args.direction == "extract":
        out = do_extract(args, vault, page)
    else:
        out = do_inline(args, vault, page)

    print(json.dumps(out, ensure_ascii=False))
    return 0 if not out.get("error") else 2


if __name__ == "__main__":
    sys.exit(main())
