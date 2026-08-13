"""cortex lint 规则实现 (R1-R7).

每条规则一个 check_R<n>(vault_root, ctx) -> list[Violation].
ctx 共享文件索引避免重复 IO.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

from . import (
    KEBAB_RE, LEVEL_DIR_MAP, VAULT_REQUIRED_DIRS, WIKILINK_RE,
    Violation, find_md_files, parse_frontmatter,
)

# memory 路径正则: 捕获 L<n>-<suffix>
MEMORY_DIR_RE = re.compile(r"(?:^|/)memory/(L[0-9]+-[a-z]+)(?:/|$)")

ALL_RULES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]
ORPHAN_AGE_DAYS = 30
REQ_BY_TYPE = {
    "domain": ["area"],
    "rule": ["level"],
    "memory": ["level"],
    "project": ["source"],
}


def build_ctx(vault_root: Path) -> dict[str, Any]:
    """构建共享上下文: md 文件清单 + name/alias → path 索引 + 反向链接图."""
    md_files = find_md_files(vault_root)
    name_index: dict[str, list[Path]] = {}
    backlinks: dict[Path, list[Path]] = {p: [] for p in md_files}
    fm_cache: dict[Path, tuple[dict | None, int, str]] = {}
    for p in md_files:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        fm, end = parse_frontmatter(text)
        fm_cache[p] = (fm, end, text)
        name_index.setdefault(p.stem.lower(), []).append(p)
        if fm and isinstance(fm.get("aliases"), list):
            for a in fm["aliases"]:
                name_index.setdefault(str(a).lower(), []).append(p)
    for p, (_fm, _end, text) in fm_cache.items():
        for m in WIKILINK_RE.finditer(text):
            for t in name_index.get(m.group(1).strip().lower(), []):
                if t != p:
                    backlinks.setdefault(t, []).append(p)
    return {"md_files": md_files, "name_index": name_index,
            "backlinks": backlinks, "fm_cache": fm_cache, "vault_root": vault_root}


def _rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def _v(file: str, rule: str, level: str, msg: str, line: int | None = None, hint: dict | None = None) -> Violation:
    return Violation(file=file, rule=rule, level=level, msg=msg, line=line, hint=hint or {})


# ---------- R1 wikilink ----------
def check_R1(vault_root: Path, ctx: dict) -> list[Violation]:
    out: list[Violation] = []
    idx = ctx["name_index"]
    for p, (_fm, _end, text) in ctx["fm_cache"].items():
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
            if target and target.lower() not in idx:
                out.append(_v(_rel(p, vault_root), "R1", "warn",
                              f"dead wikilink: [[{target}]]", _line_of(text, m.start())))
    return out


# ---------- R2 frontmatter required ----------
def _infer_type(rel: str) -> str | None:
    if rel.startswith("memory/L0-core/"):
        return "rule"
    if re.match(r"memory/L[1-4]-", rel):
        return "memory"
    if rel.startswith("项目/"):
        return "project"
    if rel.startswith("领域/"):
        return "domain"
    if rel.startswith("脚本/"):
        return "vault-script"
    return None


def _infer_area(rel: str) -> str | None:
    m = re.match(r"领域/([^/]+)/", rel)
    return m.group(1) if m else None


def _infer_level(rel: str) -> str | None:
    m = MEMORY_DIR_RE.search("/" + rel)
    return LEVEL_DIR_MAP.get(m.group(1)) if m else None


def check_R2(vault_root: Path, ctx: dict) -> list[Violation]:
    out: list[Violation] = []
    for p, (fm, _end, _text) in ctx["fm_cache"].items():
        rel = _rel(p, vault_root)
        data = fm or {}
        missing: list[str] = []
        hint: dict = {}
        t = data.get("type")
        if not t:
            inferred = _infer_type(rel)
            if inferred:
                missing.append("type")
                hint["type"] = inferred
                t = inferred
        for f in REQ_BY_TYPE.get(t, []):
            if not data.get(f):
                missing.append(f)
                if f == "area" and (a := _infer_area(rel)):
                    hint["area"] = a
                elif f == "level" and (lv := _infer_level(rel)):
                    hint["level"] = lv
                elif f == "source":
                    hint["source"] = "TODO: fill source URL"
        if missing:
            out.append(_v(rel, "R2", "error",
                          f"frontmatter missing: {missing}", hint=hint))
    return out


# ---------- R3 naming ----------
def check_R3(vault_root: Path, ctx: dict) -> list[Violation]:
    out: list[Violation] = []
    for p in ctx["md_files"]:
        rel = _rel(p, vault_root)
        # 领域/<area>/<sub>/file.md  → 4 段; 少于即不够 2 级
        if rel.startswith("领域/") and len(rel.split("/")) < 4:
            out.append(_v(rel, "R3", "warn",
                          "领域/ must have >= 2 sub-levels (领域/<area>/<sub>/...)"))
    scripts_dir = vault_root / "脚本"
    if scripts_dir.is_dir():
        for f in scripts_dir.rglob("*"):
            if f.is_file() and f.suffix in (".sh", ".py") and not KEBAB_RE.match(f.stem):
                out.append(_v(_rel(f, vault_root), "R3", "warn",
                              f"script name must be kebab-case: {f.name}"))
    return out


# ---------- R4 isomorphic dirs ----------
def check_R4(vault_root: Path, _ctx: dict) -> list[Violation]:
    missing = [d for d in VAULT_REQUIRED_DIRS if not (vault_root / d).is_dir()]
    if not missing:
        return []
    return [_v(".", "R4", "error",
               f"required dirs missing: {missing}", hint={"mkdir": missing})]


# ---------- R5 orphans ----------
def check_R5(vault_root: Path, ctx: dict) -> list[Violation]:
    out: list[Violation] = []
    cutoff = time.time() - ORPHAN_AGE_DAYS * 86400
    for p in ctx["md_files"]:
        rel = _rel(p, vault_root)
        if rel.startswith("memory/L4-inbox/") or rel.startswith("memory/L0-core/"):
            continue
        try:
            if p.stat().st_mtime > cutoff:
                continue
        except OSError:
            continue
        if not ctx["backlinks"].get(p):
            out.append(_v(rel, "R5", "warn",
                          f"orphan (no backlinks, mtime > {ORPHAN_AGE_DAYS}d)"))
    return out


# ---------- R6 level semantics ----------
def check_R6(vault_root: Path, ctx: dict) -> list[Violation]:
    out: list[Violation] = []
    mem_root = vault_root / "memory"
    if mem_root.is_dir():
        for child in mem_root.iterdir():
            if child.is_dir() and child.name not in LEVEL_DIR_MAP:
                out.append(_v(f"memory/{child.name}", "R6", "error",
                              f"illegal memory subdir: '{child.name}' (allowed: {list(LEVEL_DIR_MAP)})"))
    for p, (fm, _end, _text) in ctx["fm_cache"].items():
        rel = _rel(p, vault_root)
        m = MEMORY_DIR_RE.search("/" + rel)
        if not m:
            continue
        dirname = m.group(1)
        expected = LEVEL_DIR_MAP.get(dirname)
        if expected is None:
            out.append(_v(rel, "R6", "error",
                          f"path uses non-canonical memory dir '{dirname}'"))
            continue
        if fm and fm.get("level") and fm["level"] != expected:
            out.append(_v(rel, "R6", "error",
                          f"path is {dirname} but frontmatter level={fm['level']} (expected {expected})"))
    return out


# ---------- R7 scripts purpose ----------
def check_R7(target_root: Path, vault_root: Path, ctx: dict) -> list[Violation]:
    out: list[Violation] = []
    home = Path(os.path.expanduser("~")).resolve()
    try:
        is_home_cortex = target_root.resolve() == (home / ".cortex").resolve()
    except Exception:
        is_home_cortex = False
    cortex_scripts = target_root / ".cortex" / "scripts"
    if cortex_scripts.is_dir() and not is_home_cortex:
        out.append(_v(str(cortex_scripts), "R7", "warn",
                      "project-level .cortex/scripts/ forbidden (user-facing scripts only at ~/.cortex/scripts/)"))
    for p, (fm, _end, _text) in ctx["fm_cache"].items():
        rel = _rel(p, vault_root)
        if rel.startswith("scripts/") and fm and fm.get("type") == "user-script":
            out.append(_v(rel, "R7", "warn",
                          "vault-internal scripts/ must not contain type=user-script"))
    return out


_DISPATCH = {
    "R1": lambda t, v, c: check_R1(v, c),
    "R2": lambda t, v, c: check_R2(v, c),
    "R3": lambda t, v, c: check_R3(v, c),
    "R4": lambda t, v, c: check_R4(v, c),
    "R5": lambda t, v, c: check_R5(v, c),
    "R6": lambda t, v, c: check_R6(v, c),
    "R7": lambda t, v, c: check_R7(t, v, c),
}


def run_rules(target_root: Path, vault_root: Path, rules: list[str]) -> list[Violation]:
    ctx = build_ctx(vault_root)
    out: list[Violation] = []
    for r in rules:
        fn = _DISPATCH.get(r)
        if fn:
            out.extend(fn(target_root, vault_root, ctx))
    return out
