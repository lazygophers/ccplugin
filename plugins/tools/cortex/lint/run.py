#!/usr/bin/env python3
"""cortex lint runner — 13 vault health checks (prd §4.6 + §10.9).

Usage:
    run.py --vault PATH [--fix] [--scope GLOB] [--json]

Output (JSON to stdout):
    {"errors":[{rule,file,line,msg,fixable}], "warns":[...],
     "summary":{"errors":N,"warns":M,"fixed":F,"rules_hit":[...]}}

stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---- regex helpers ----
WIKILINK_RE = re.compile(r"(?<!\!)\[\[([^\[\]\n|#^]+)(?:[#^][^\[\]\n|]*)?(?:\|[^\[\]\n]*)?\]\]")
BLOCK_ID_RE = re.compile(r"\s\^(cortex-[a-f0-9]{8})\b")
CALLOUT_RE = re.compile(r"^\s*>\s*\[!([a-zA-Z][\w-]*)\][+\-]?\s", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
ILLEGAL_CHARS = set(r':\|?*<>"')

CALLOUT_WHITELIST = {
    "note", "abstract", "summary", "tldr", "info", "todo", "tip", "hint", "important",
    "success", "check", "done", "question", "help", "faq", "warning", "caution",
    "attention", "failure", "fail", "missing", "danger", "error", "bug", "example",
    "quote", "cite",
}

EXCLUDE_DIRS = {"_meta", ".obsidian", ".trash", ".git"}

# Shared root dirs (i18n whitelist; never reported by i18n-* rules)
SHARED_ROOT_DIRS = {
    "_meta", "_templates", "locales", "sessions",
    "log", "folds", "MOC", ".obsidian", ".trash", ".git",
}
SHARED_ROOT_FILES = {"index.md", "hot.md"}
TIME_DIR_RE = re.compile(r"^\d{4}-\d{2}$")


def _load_vault_lang(vault: Path) -> str:
    """Resolve lang: CORTEX_LANG env > vault _meta/version.json > config.lang > zh-CN."""
    import os as _os

    env_val = _os.environ.get("CORTEX_LANG")
    if env_val:
        return env_val
    p = vault / "_meta" / "version.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        v = data.get("lang") if isinstance(data, dict) else None
        if isinstance(v, str) and v:
            return v
    except Exception:
        pass
    try:
        _hooks_lib = Path(__file__).resolve().parent.parent / "hooks" / "_lib"
        if str(_hooks_lib) not in sys.path:
            sys.path.insert(0, str(_hooks_lib))
        from cortex_config import load_config
        cfg_lang = load_config().get("lang")
        if isinstance(cfg_lang, str) and cfg_lang:
            return cfg_lang
    except ImportError:
        pass
    return "zh-CN"


def _load_locale_dirs(plugin_root: Path, vault: Path, lang: str) -> set[str]:
    """Load `dirs` mapping for given lang; return set of localized dir names."""
    sys.path.insert(0, str(plugin_root / "hooks" / "_lib"))
    try:
        from cortex_locale import load_locale  # type: ignore
        loc = load_locale(plugin_root, vault, lang)
        dirs_map = loc.get_dirs()
        return {v for v in dirs_map.values() if isinstance(v, str) and v}
    except Exception:
        return set()


def parse_frontmatter(text: str) -> tuple[dict[str, Any], int]:
    """Return (frontmatter dict, body_start_line). Lightweight YAML."""
    if not text.startswith("---"):
        return {}, 0
    end = text.find("\n---", 3)
    if end < 0:
        return {}, 0
    fm_text = text[3:end].strip("\n")
    body_start = text[: end + 4].count("\n") + 1
    fm: dict[str, Any] = {}
    cur_key: str | None = None
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") and cur_key:
            v = line.strip()
            if v.startswith("- "):
                fm.setdefault(cur_key, [])
                if isinstance(fm[cur_key], list):
                    fm[cur_key].append(v[2:].strip().strip("\"'"))
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            cur_key = k
            if not v:
                fm[k] = None
                continue
            if v.startswith("[") and v.endswith("]"):
                inner = v[1:-1]
                fm[k] = [p.strip().strip("\"'") for p in inner.split(",") if p.strip()]
            else:
                fm[k] = v.strip("\"'")
    return fm, body_start


def iter_md_files(vault: Path, scope: str | None = None):
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault)
        if rel.parts and rel.parts[0] in EXCLUDE_DIRS:
            continue
        if scope and not fnmatch.fnmatch(str(rel), scope):
            continue
        yield p


def index_wikilinks(vault: Path) -> tuple[dict[str, Path], dict[str, list[Path]], dict[str, set[str]]]:
    """Build name index, alias->paths index, and target->referrers map."""
    by_name: dict[str, Path] = {}
    by_alias: dict[str, list[Path]] = {}
    referrers: dict[str, set[str]] = {}
    for md in iter_md_files(vault):
        rel = str(md.relative_to(vault))
        stem = md.stem.lower()
        by_name.setdefault(stem, md)
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        fm, _ = parse_frontmatter(text)
        title = fm.get("title")
        aliases = fm.get("aliases") or []
        if isinstance(title, str) and title:
            by_alias.setdefault(title.lower(), []).append(md)
        if isinstance(aliases, list):
            for a in aliases:
                if isinstance(a, str) and a:
                    by_alias.setdefault(a.lower(), []).append(md)
        # collect outgoing wikilinks for referrer map
        body = text
        for m in WIKILINK_RE.finditer(body):
            tgt = m.group(1).strip()
            if tgt.lower().endswith(".md"):
                tgt = tgt[:-3]
            key = tgt.split("/")[-1].lower()
            referrers.setdefault(key, set()).add(rel)
    return by_name, by_alias, referrers


def file_mtime_date(p: Path) -> str:
    try:
        ts = p.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


# ---- per-rule checkers ----

def check_file(
    path: Path,
    rel: str,
    text: str,
    by_name: dict[str, Path],
    by_alias: dict[str, list[Path]],
    referrers: dict[str, set[str]],
    vault_lang: str | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    fm, body_line = parse_frontmatter(text)

    # rule 1: fm-missing-type
    if not fm.get("type"):
        findings.append(_f("fm-missing-type", "error", rel, 1, "frontmatter 缺 type 字段", True))
    # rule 2: fm-missing-created
    if not fm.get("created"):
        findings.append(_f("fm-missing-created", "warn", rel, 1, "frontmatter 缺 created 字段", True))

    # rule 14: i18n-frontmatter-lang-mismatch
    if vault_lang:
        page_lang = fm.get("lang")
        # skip log/folds/sessions auto-generated where lang may legitimately mix
        skip_prefixes = ("log/", "folds/", "sessions/", "_templates/")
        if (
            isinstance(page_lang, str)
            and page_lang
            and page_lang != vault_lang
            and not any(rel.startswith(p) for p in skip_prefixes)
        ):
            findings.append(_f(
                "i18n-frontmatter-lang-mismatch", "warn", rel, 1,
                f"page lang='{page_lang}' != vault.lang='{vault_lang}'", False,
            ))

    # rule 9: title-h1-mismatch
    title = fm.get("title")
    h1m = H1_RE.search(text)
    h1 = h1m.group(1).strip() if h1m else None
    if isinstance(title, str) and title and h1 and title.strip() != h1:
        findings.append(_f("title-h1-mismatch", "warn", rel, body_line, f"H1='{h1}' != title='{title}'", True))

    # rule 3: dead-wikilink
    for m in WIKILINK_RE.finditer(text):
        tgt = m.group(1).strip()
        if tgt.lower().endswith(".md"):
            tgt = tgt[:-3]
        key = tgt.split("/")[-1].lower()
        if key not in by_name and key not in by_alias:
            line = text[: m.start()].count("\n") + 1
            findings.append(_f("dead-wikilink", "error", rel, line, f"dead link: [[{tgt}]]", False))

    # rule 12: callout-unknown-type
    for m in CALLOUT_RE.finditer(text):
        ct = m.group(1).lower()
        if ct not in CALLOUT_WHITELIST:
            line = text[: m.start()].count("\n") + 1
            findings.append(_f("callout-unknown-type", "warn", rel, line, f"unknown callout type: [!{ct}]", False))

    # rule 6 & 7: file length
    if rel == "hot.md":
        nlines = text.count("\n") + 1
        if nlines > 200:
            findings.append(_f("hot-too-long", "warn", rel, nlines, f"hot.md {nlines} lines > 200", True))
    if rel.startswith("log/") and rel.endswith(".md"):
        nlines = text.count("\n") + 1
        if nlines > 2000:
            findings.append(_f("log-too-long", "warn", rel, nlines, f"log {nlines} lines > 2000, fold needed", False))

    # rule 4: orphan-page (skip log/folds/_index/_meta/_templates files)
    skip_orphan = (
        rel.startswith("log/") or rel.startswith("folds/") or rel.startswith("_templates/")
        or rel == "index.md" or rel == "hot.md" or path.name.startswith("_")
    )
    if not skip_orphan:
        key = path.stem.lower()
        tags = fm.get("tags") or []
        has_tag = bool(tags) if isinstance(tags, list) else bool(tags)
        if not referrers.get(key) and not has_tag:
            findings.append(_f("orphan-page", "warn", rel, 1, "orphan page (no inbound link, no tag)", False))

    # rule 10: filename-illegal
    if any(c in ILLEGAL_CHARS for c in path.name):
        findings.append(_f("filename-illegal", "error", rel, 1, f"filename has illegal chars: {path.name}", False))

    return findings


def check_global(
    vault: Path,
    files: list[Path],
    by_alias: dict[str, list[Path]],
    locale_dirs: set[str] | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    # rule 5: duplicate-alias
    for alias, paths in by_alias.items():
        if len(paths) > 1:
            ps = ", ".join(str(p.relative_to(vault)) for p in paths)
            findings.append(_f("duplicate-alias", "error", "(global)", 0,
                              f"alias '{alias}' shared across: {ps}", False))

    # rule 8: index-missing-section
    idx = vault / "index.md"
    if idx.exists():
        try:
            idx_text = idx.read_text(encoding="utf-8", errors="replace").lower()
        except Exception:
            idx_text = ""
        for sub in vault.iterdir():
            if not sub.is_dir():
                continue
            if sub.name in EXCLUDE_DIRS or sub.name.startswith("."):
                continue
            if sub.name in ("_templates", "log", "folds"):
                continue
            if sub.name.lower() not in idx_text:
                findings.append(_f("index-missing-section", "warn", "index.md", 1,
                                   f"index.md missing reference to {sub.name}/", True))

    # rule 11: block-id-duplicate
    block_map: dict[str, list[tuple[str, int]]] = {}
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(vault))
        for m in BLOCK_ID_RE.finditer(text):
            bid = m.group(1)
            line = text[: m.start()].count("\n") + 1
            block_map.setdefault(bid, []).append((rel, line))
    for bid, occ in block_map.items():
        if len(occ) > 1:
            for rel, line in occ:
                findings.append(_f("block-id-duplicate", "error", rel, line,
                                   f"^{bid} duplicated ({len(occ)}x)", True))

    # rule 13: path-naming-violation (per prd §9; only for time-pattern paths)
    for p in files:
        rel = str(p.relative_to(vault))
        violation = _check_naming(rel)
        if violation:
            findings.append(_f("path-naming-violation", "warn", rel, 1, violation, False))

    # rule 15: i18n-path-not-in-locale (top-level business dirs not in vault.lang dirs map)
    if locale_dirs is not None:
        seen: set[str] = set()
        for p in files:
            rel = str(p.relative_to(vault))
            top = rel.split("/", 1)[0]
            if top in seen:
                continue
            seen.add(top)
            if top in SHARED_ROOT_DIRS or top in SHARED_ROOT_FILES:
                continue
            if TIME_DIR_RE.match(top):
                continue
            if "." in top and "/" not in rel:
                # top-level file (non-md handled elsewhere; md shared files already gated)
                continue
            if top not in locale_dirs:
                findings.append(_f(
                    "i18n-path-not-in-locale", "warn", top + "/", 1,
                    f"top-level dir '{top}' not in vault.lang dirs map; consider migrate-locale",
                    False,
                ))

    return findings


def _check_naming(rel: str) -> str | None:
    parts = rel.split("/")
    # skip shared roots (per prd §9 adjustment)
    if parts and parts[0] in SHARED_ROOT_DIRS:
        # only check time-formatted children of log/folds (already covered below)
        pass
    # log/YYYY-MM/DD-HHMM-<slug>.md
    if parts[0] == "log" and len(parts) == 3:
        if not re.match(r"^\d{4}-\d{2}$", parts[1]):
            return f"log/<{parts[1]}>/ should match YYYY-MM"
        if not re.match(r"^\d{2}-\d{4}-[a-z0-9-]+\.md$", parts[2]):
            return f"log file '{parts[2]}' should be DD-HHMM-<slug>.md"
    # folds/YYYY-MM-fold-NNN.md
    if parts[0] == "folds" and len(parts) == 2 and parts[1] != "_index.md":
        if not re.match(r"^\d{4}-\d{2}-fold-\d{3}\.md$", parts[1]):
            return f"fold file '{parts[1]}' should be YYYY-MM-fold-NNN.md"
    # 60_dashboards/<topic>-dashboard.md
    if parts[0] == "60_dashboards" and len(parts) == 2 and parts[1] not in ("_index.md",):
        if not parts[1].endswith("-dashboard.md"):
            return f"dashboard '{parts[1]}' must end with -dashboard.md"
    # zettels/YYYYMMDDHHMM-<slug>.md
    if parts[0] == "zettels" and len(parts) == 2 and parts[1] != "_index.md":
        if not re.match(r"^\d{12}-[a-z0-9-]+\.md$", parts[1]):
            return f"zettel '{parts[1]}' should be YYYYMMDDHHMM-<slug>.md"
    return None


def _f(rule: str, severity: str, file: str, line: int, msg: str, fixable: bool) -> dict[str, Any]:
    return {"rule": rule, "severity": severity, "file": file, "line": line, "msg": msg, "fixable": fixable}


# ---- autofix ----

def apply_fixes(vault: Path, findings: list[dict[str, Any]], backup_dir: Path) -> int:
    """Apply fixes for autofix-eligible findings. Backup before write."""
    fixed = 0
    by_file: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        if not f.get("fixable"):
            continue
        if f["rule"] not in {
            "fm-missing-type", "fm-missing-created", "hot-too-long",
            "index-missing-section", "title-h1-mismatch", "block-id-duplicate",
        }:
            continue
        by_file.setdefault(f["file"], []).append(f)

    for relfile, items in by_file.items():
        if relfile == "(global)":
            continue
        path = vault / relfile
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # backup
        bpath = backup_dir / relfile
        bpath.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(path, bpath)
        except Exception:
            pass

        new_text = text
        for it in items:
            rule = it["rule"]
            if rule == "fm-missing-type":
                inferred = _infer_type(relfile)
                new_text = _ensure_fm_field(new_text, "type", inferred)
                fixed += 1
            elif rule == "fm-missing-created":
                new_text = _ensure_fm_field(new_text, "created", file_mtime_date(path))
                fixed += 1
            elif rule == "title-h1-mismatch":
                fm, _bs = parse_frontmatter(new_text)
                title = fm.get("title")
                if isinstance(title, str) and title:
                    new_text = H1_RE.sub(lambda m: f"# {title}", new_text, count=1)
                    fixed += 1
            elif rule == "hot-too-long":
                lines = new_text.splitlines()
                if len(lines) > 200:
                    archive_dir = vault / "folds"
                    archive_dir.mkdir(exist_ok=True)
                    arch = archive_dir / f"hot-archive-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
                    arch.write_text("\n".join(lines[200:]) + "\n", encoding="utf-8")
                    new_text = "\n".join(lines[:200]) + "\n"
                    fixed += 1
            elif rule == "index-missing-section":
                m = re.search(r"missing reference to (\S+?)/", it["msg"])
                if m:
                    section = m.group(1)
                    if not new_text.endswith("\n"):
                        new_text += "\n"
                    new_text += f"\n- [[{section}/_index]]\n"
                    fixed += 1
            elif rule == "block-id-duplicate":
                # rehash by appending file path to make unique
                bid_match = re.search(r"\^(cortex-[a-f0-9]{8})", it["msg"])
                if bid_match:
                    old = bid_match.group(1)
                    new_h = hashlib.sha1((relfile + str(it["line"]) + old).encode()).hexdigest()[:8]
                    new_bid = f"cortex-{new_h}"
                    # only replace one occurrence at the given line
                    lines = new_text.splitlines()
                    if 0 < it["line"] <= len(lines):
                        lines[it["line"] - 1] = lines[it["line"] - 1].replace(f"^{old}", f"^{new_bid}", 1)
                        new_text = "\n".join(lines) + ("\n" if new_text.endswith("\n") else "")
                        fixed += 1

        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
    return fixed


def _infer_type(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] == "log":
        return "log"
    if parts[0] == "folds":
        return "fold"
    if "concepts" in parts[0] or parts[0] == "10_concepts":
        return "concept"
    if "entities" in parts[0] or parts[0] == "20_entities":
        return "entity"
    if "domains" in parts[0] or parts[0] == "30_domains":
        return "domain"
    if "sources" in parts[0] or parts[0] == "40_sources":
        return "source"
    if "questions" in parts[0] or parts[0] == "50_questions":
        return "question"
    if "dashboards" in parts[0] or parts[0] == "60_dashboards":
        return "dashboard"
    return "concept"


def _ensure_fm_field(text: str, key: str, value: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            fm = text[3:end]
            if re.search(rf"^{re.escape(key)}\s*:", fm, re.MULTILINE):
                return text
            new_fm = fm.rstrip("\n") + f"\n{key}: {value}\n"
            return "---" + new_fm + text[end:]
    # no frontmatter — prepend
    return f"---\n{key}: {value}\n---\n\n" + text


# ---- main ----

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, help="Obsidian vault absolute path")
    ap.add_argument("--fix", action="store_true", help="apply autofix (writes to disk + backup)")
    ap.add_argument("--scope", default=None, help="glob filter, e.g. '10_concepts/*'")
    ap.add_argument("--json", action="store_true", help="JSON output (default)")
    ap.add_argument("--lang", default=None, help="override vault.lang for i18n checks")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"vault not found: {vault}"}), file=sys.stderr)
        return 2

    files = list(iter_md_files(vault, args.scope))
    by_name, by_alias, referrers = index_wikilinks(vault)

    vault_lang = args.lang or _load_vault_lang(vault)
    plugin_root = Path(__file__).resolve().parent.parent
    locale_dirs = _load_locale_dirs(plugin_root, vault, vault_lang)

    findings: list[dict[str, Any]] = []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(vault))
        findings.extend(check_file(p, rel, text, by_name, by_alias, referrers, vault_lang))

    findings.extend(check_global(vault, files, by_alias, locale_dirs if locale_dirs else None))

    fixed = 0
    if args.fix:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = vault / "_meta" / ".cortex-backup" / "lint" / ts
        backup_dir.mkdir(parents=True, exist_ok=True)
        fixed = apply_fixes(vault, findings, backup_dir)

    errors = [f for f in findings if f["severity"] == "error"]
    warns = [f for f in findings if f["severity"] == "warn"]
    rules_hit = sorted({f["rule"] for f in findings})

    out = {
        "errors": errors,
        "warns": warns,
        "summary": {
            "errors": len(errors),
            "warns": len(warns),
            "fixed": fixed,
            "rules_hit": rules_hit,
            "files_scanned": len(files),
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
