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
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---- regex helpers ----
WIKILINK_RE = re.compile(
    r"(?<!\!)\[\[([^\[\]\n|#^]+)(?:[#^][^\[\]\n|]*)?(?:\|[^\[\]\n]*)?\]\]"
)
# Strip fenced code blocks (``` ... ```) and inline code (` ... `) so wikilink
# scan ignores shell snippets like `[[ "$x" == "y" ]]` which are not real links.
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def strip_code_for_wikilinks(text: str) -> str:
    """Return text with fenced + inline code replaced by blank-equivalent so
    wikilink scanning skips code snippets while keeping line numbers stable."""

    def _blank_keep_lines(m):
        return "".join("\n" if c == "\n" else " " for c in m.group(0))

    text = _FENCED_CODE_RE.sub(_blank_keep_lines, text)
    text = _INLINE_CODE_RE.sub(_blank_keep_lines, text)
    return text


BLOCK_ID_RE = re.compile(r"\s\^(cortex-[a-f0-9]{8})\b")
CALLOUT_RE = re.compile(r"^\s*>\s*\[!([a-zA-Z][\w-]*)\][+\-]?\s", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
ILLEGAL_CHARS = set(r':\|?*<>"')

CALLOUT_WHITELIST = {
    "note",
    "abstract",
    "summary",
    "tldr",
    "info",
    "todo",
    "tip",
    "hint",
    "important",
    "success",
    "check",
    "done",
    "question",
    "help",
    "faq",
    "warning",
    "caution",
    "attention",
    "failure",
    "fail",
    "missing",
    "danger",
    "error",
    "bug",
    "example",
    "quote",
    "cite",
}

EXCLUDE_DIRS = {
    "_meta", ".obsidian", ".trash", ".git",
    # AI 工具配置目录 (会话 / 缓存 / 工具私有状态), 不参与 lint
    ".claude", ".claude-plugin", ".codex", ".opencode", ".cursor",
    ".continue", ".windsurf", ".trae", ".copilot", ".sourcegraph",
    ".tabnine", ".sweep", ".trellis",
}

# ---- path-lang-mismatch (rule 18) ----
# CJK Unified Ideographs basic block; sufficient for zh-CN segment 判定
_CJK_RE = re.compile(r"[一-鿿]")
# Hiragana / Katakana for ja detection
_KANA_RE = re.compile(r"[぀-ゟ゠-ヿ]")
# Pure ASCII filename segment (letters/digits/dot/dash/underscore)
_ASCII_SEG_RE = re.compile(r"^[A-Za-z0-9._\-]+$")

# ASCII 专名 stem 豁免清单 (项目根级常见配置/元文档)
_ASCII_EXEMPT_STEMS = {
    "readme",
    "license",
    "licence",
    "changelog",
    "contributing",
    "code_of_conduct",
    "security",
    "authors",
    "maintainers",
    "notice",
    "pyproject",
    "package",
    "package-lock",
    "cargo",
    "go",
    "go.mod",
    "go.sum",
    "tsconfig",
    "jsconfig",
    "makefile",
    "dockerfile",
    "_index",
    "index",
    "hot",
}

# vault 顶层基础设施目录 — 永远豁免 path-lang 检查
_PATH_LANG_INFRA_TOPS = {
    "_meta",
    "_templates",
    "_assets",
    "locales",
    ".obsidian",
    ".trash",
    ".git",
    # 记忆体系 / 归档 / 仪表盘 — 内部 URI 命名固定, 不参与 vault lang 校验
    "记忆",
    "memory",
    "归档",
    "archive",
    "仪表盘",
    "dashboard",
}


def _is_exempt_filename_stem(name: str) -> bool:
    """文件名 stem (含/不含扩展) 是否在 ASCII 专名豁免清单内."""
    n = name.lower()
    # 去最后一个扩展 (保留 .md / .json 等)
    if "." in n:
        stem = n.rsplit(".", 1)[0]
    else:
        stem = n
    return stem in _ASCII_EXEMPT_STEMS or n in _ASCII_EXEMPT_STEMS


def _segment_matches_lang(seg: str, lang: str) -> bool:
    """检查单个 path segment 是否符合 vault lang.

    - zh-*: 含 CJK 字符即视为符合 (允许中英混排如 `Bases配置.md`)
    - en:   不含 CJK / Kana 即视为符合
    - ja:   含 Kana 或 CJK 之一即视为符合
    其他 lang 默认放行 (不检测).
    """
    if not seg:
        return True
    if lang.startswith("zh"):
        # 文件名 ext 部分忽略 (`.md` 等不影响)
        name = seg.rsplit(".", 1)[0] if "." in seg else seg
        if _CJK_RE.search(name):
            return True
        # 全 ASCII 段 → 不符
        if _ASCII_SEG_RE.match(name):
            return False
        # 既无 CJK 又含非 ASCII (其他语言) — 放行, 不属本规则关注
        return True
    if lang == "en":
        if _CJK_RE.search(seg) or _KANA_RE.search(seg):
            return False
        return True
    if lang == "ja":
        if _KANA_RE.search(seg) or _CJK_RE.search(seg):
            return True
        name = seg.rsplit(".", 1)[0] if "." in seg else seg
        if _ASCII_SEG_RE.match(name):
            return False
        return True
    return True


def _check_path_lang_mismatch(
    rel: str,
    fm: dict[str, Any],
    vault_lang: str,
) -> list[dict[str, Any]]:
    """rule 18: path-lang-mismatch — vault path segment 不符 vault.lang.

    豁免:
      - frontmatter `path_lang_exempt: true`
      - 顶层基础设施目录 (`_meta`/`_templates`/`_assets`/`locales`/`.obsidian`/...)
      - `知识库/项目/<host>/<org>/<repo>/` 前 4 段 (host/org/repo 由 git remote 决定)
      - ASCII 专名 stem (README / LICENSE / CHANGELOG / pyproject / tsconfig ...)
    """
    findings: list[dict[str, Any]] = []
    if not vault_lang:
        return findings
    # frontmatter 手动豁免
    v = fm.get("path_lang_exempt") if isinstance(fm, dict) else None
    if v in (True, "true", "True", "yes", 1, "1"):
        return findings

    parts = rel.split("/")
    if not parts:
        return findings
    # 顶层基础设施豁免
    if parts[0] in _PATH_LANG_INFRA_TOPS:
        return findings

    # 知识库 i18n 等价顶层名也豁免 (lang=en vault: `kb/`); 用 segment 检测处理
    # 项目子目录: 知识库/项目/<host>/<org>/<repo>/... — 前 5 段豁免
    # (parts[0]=知识库, parts[1]=项目, parts[2]=host, parts[3]=org, parts[4]=repo)
    project_prefix_zh = len(parts) >= 5 and parts[0] == "知识库" and parts[1] == "项目"
    project_prefix_en = (
        len(parts) >= 5
        and parts[0] in {"kb", "knowledge"}
        and parts[1] in {"projects", "project"}
    )
    if project_prefix_zh or project_prefix_en:
        check_parts = parts[5:]
    else:
        check_parts = parts

    for seg in check_parts:
        if not seg:
            continue
        # 文件名 ASCII 专名 stem 豁免
        if _is_exempt_filename_stem(seg):
            continue
        if not _segment_matches_lang(seg, vault_lang):
            finding = _f(
                "path-lang-mismatch",
                "warn",
                rel,
                0,
                (
                    f"path segment '{seg}' 不符 vault.lang={vault_lang} "
                    f"(豁免: 项目 host/org/repo / ASCII 专名 / frontmatter path_lang_exempt: true; "
                    f"重命名走 cortex-refactor rename)"
                ),
                False,
            )
            finding["segment"] = seg
            finding["vault_lang"] = vault_lang
            findings.append(finding)
            # 单文件每次只报一条 (避免 N 个 segment N 倍噪音)
            break
    return findings


# Shared root dirs (i18n whitelist; never reported by i18n-* rules)
SHARED_ROOT_DIRS = {
    "_meta",
    "_templates",
    "locales",
    ".obsidian",
    ".trash",
    ".git",
}
SHARED_ROOT_FILES = {"index.md", "hot.md"}
TIME_DIR_RE = re.compile(r"^\d{4}-\d{2}$")


def _load_vault_lang(vault: Path) -> str:
    """Resolve lang: vault _meta/version.json > config.lang > zh-CN.

    Env var lookup removed per PRD (config-only).
    """
    p = vault / "_meta" / "version.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        v = data.get("lang") if isinstance(data, dict) else None
        if isinstance(v, str) and v:
            return v
    except Exception:
        pass
    try:
        _hooks_lib = Path(__file__).resolve().parents[2] / "scripts" / "hooks" / "_lib"
        if str(_hooks_lib) not in sys.path:
            sys.path.insert(0, str(_hooks_lib))
        from cortex_config import load_config

        cfg_lang = load_config().get("lang")
        if isinstance(cfg_lang, str) and cfg_lang:
            return cfg_lang
    except ImportError:
        pass
    return "zh-CN"


def _load_vault_meta(vault: Path) -> dict[str, Any]:
    """Parse vault `_meta/version.json` into dict; return `{}` on any error."""
    p = vault / "_meta" / "version.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_vault_preset(vault: Path) -> str:
    """Deprecated — preset 系统已移除. 保留 stub 以兼容旧调用方."""
    return ""


_DEPRECATED_WHITELIST = {"log/", "folds/", "sessions/"}

# 结构标记 — 非内容相关 tag, lint 检测并 autofix 删除
_BANNED_TAGS = {"index", "meta", "template", "_index", "stub"}

# 裸时间 token: 2026 / 2026-05 / 2026-05-19 / 2026-Q2 / 2026-W21
_BANNED_TAG_TIME_RE = re.compile(
    r"^(?:\d{4}(?:-(?:Q[1-4]|W\d{1,2}|\d{1,2}(?:-\d{1,2})?))?|"
    r"\d{4}年(?:\d{1,2}月(?:\d{1,2}日)?)?)$"
)


def _is_banned_tag(tag: str) -> bool:
    """tag 是否命中结构/时间禁令 (仅裸结构 + 裸时间; hierarchical `xxx/yyy` 允许)."""
    if not isinstance(tag, str) or not tag.strip():
        return False
    low = tag.lower()
    if low in _BANNED_TAGS:
        return True
    if _BANNED_TAG_TIME_RE.match(tag.strip()):
        return True
    return False

# frontmatter 禁止字段 (preset 系统已移除, autofix 自动剥)
_BANNED_FM_FIELDS = {"preset"}

# fm-missing-tags autofix: tag 数量上界 (语义 tag, 不含模板/类型/时间)
_TAGS_MAX = 15

# 占位符模式 — 严禁出现在 autofix 输出
_PLACEHOLDER_RE = re.compile(
    r"<.*?>|placeholder|TODO|待填|待用户填|TBD|FIXME|XXX",
    re.I,
)


def _derive_tags_for_autofix(fm: dict, body: str) -> list[str] | None:
    """读 fm + 正文派生 tag, 严禁占位符。

    返回派生后 tag 列表 (可空), 派生异常返 None.
    """
    existing = list(fm.get("tags") or []) if isinstance(fm.get("tags"), list) else []
    derived: list[str] = []

    # 1. frontmatter 派生
    def _push(t: str) -> None:
        if t and isinstance(t, str):
            derived.append(t)

    if fm.get("type"):
        _push(f"type/{fm['type']}")
    if fm.get("lang"):
        _push(f"lang/{fm['lang']}")
    if fm.get("host"):
        _push(f"host/{fm['host']}")
    if fm.get("org"):
        _push(f"org/{fm['org']}")
    if fm.get("repo"):
        _push(f"repo/{fm['repo']}")
    if fm.get("kind"):
        _push(f"kind/{fm['kind']}")
    if fm.get("source_kind"):
        _push(f"source/{fm['source_kind']}")
    if fm.get("maturity"):
        _push(f"maturity/{fm['maturity']}")
    if fm.get("status"):
        _push(f"status/{fm['status']}")
    if fm.get("entity_kind"):
        _push(f"entity/{fm['entity_kind']}")
    if fm.get("score") is not None:
        _push(f"score/{fm['score']}")
    if fm.get("rating") not in (None, 0, "0"):
        _push(f"rating/{fm['rating']}")
    if fm.get("source_url"):
        m = re.search(r"://([^/]+)", str(fm["source_url"]))
        if m:
            _push(f"source/{m.group(1)}")
    if fm.get("url"):
        m = re.search(r"://([^/]+)", str(fm["url"]))
        if m:
            _push(f"host/{m.group(1)}")
    if fm.get("created"):
        y = str(fm["created"])[:4]
        if y.isdigit():
            _push(f"created/{y}")
    if fm.get("updated"):
        y = str(fm["updated"])[:4]
        if y.isdigit() and y != str(fm.get("created", ""))[:4]:
            _push(f"updated/{y}")

    # 2. 正文 h1/h2 → topic/<slug>
    for m in re.finditer(r"^#{1,2}\s+(.+?)$", body[:2000], re.M):
        title = m.group(1).strip()
        slug = re.sub(r"[\s/\\:*?\"<>|]+", "-", title)[:30]
        slug = slug.strip("-_")
        if slug and len(slug) >= 2:
            _push(f"topic/{slug}")

    # 3. 首 500 字: 中文 2-4 字短语 + 英文 PascalCase/camelCase
    head = body[:500]
    for ph in re.findall(r"[一-龥]{2,4}", head):
        if len(ph) >= 2:
            _push(f"keyword/{ph}")
    for ph in re.findall(r"\b[A-Z][a-zA-Z]{2,15}\b", head):
        _push(f"keyword/{ph.lower()}")

    # 合并 existing + derived, 去重保序, 过滤占位符
    seen: set[str] = set()
    merged: list[str] = []
    for t in list(existing) + derived:
        if not isinstance(t, str) or not t.strip():
            continue
        if _PLACEHOLDER_RE.search(t):
            continue
        if t in seen:
            continue
        seen.add(t)
        merged.append(t)

    merged = merged[:_TAGS_MAX]
    return merged


def _load_lint_whitelist(vault: Path) -> set[str]:
    """Return whitelist set from `_meta/version.json:.lint_whitelist[]`.

    Deprecated entries (log/, folds/, sessions/) are auto-stripped — these
    legacy roots must surface as vault-structure-violation so the autofix
    can mv them to lint-backup.
    """
    v = _load_vault_meta(vault).get("lint_whitelist")
    if isinstance(v, list):
        return {
            x for x in v if isinstance(x, str) and x and x not in _DEPRECATED_WHITELIST
        }
    return set()


def _prune_deprecated_whitelist(vault: Path) -> bool:
    """Remove deprecated entries from `_meta/version.json:lint_whitelist`.

    Returns True when the file was rewritten.
    """
    p = vault / "_meta" / "version.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    wl = data.get("lint_whitelist")
    if not isinstance(wl, list):
        return False
    pruned = [x for x in wl if not (isinstance(x, str) and x in _DEPRECATED_WHITELIST)]
    if len(pruned) == len(wl):
        return False
    data["lint_whitelist"] = pruned
    try:
        p.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return True
    except Exception:
        return False


def check_vault_structure(
    vault: Path,
    preset: str,
    whitelist: set[str],
    extra_allowed_dirs: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Scan vault root (non-recursive); return list of violations.

    Each violation uses the standard finding shape `{rule, severity, file,
    line, msg, fixable}` plus `{path, kind, reason}` extras so the
    cortex-lint skill can drive interactive fixes.

    Whitelist matches by exact relative-path string. Dirs are matched with
    a trailing `/` (e.g. `"foobar/"`); files without it.

    `extra_allowed_dirs` lets callers add i18n / locale-derived directory
    names (e.g. `概念`, `concepts`) so localized layouts don't get flagged.
    """
    try:
        from .schemas import get_schema
    except ImportError:
        try:
            from lint.schemas import get_schema  # type: ignore
        except ImportError:
            from schemas import get_schema  # type: ignore

    schema = get_schema(preset)
    allowed_dirs = set(schema["root_dirs"])
    if extra_allowed_dirs:
        allowed_dirs |= extra_allowed_dirs
    allowed_files = set(schema["root_files"])
    violations: list[dict[str, Any]] = []

    try:
        entries = sorted(vault.iterdir(), key=lambda p: p.name)
    except OSError:
        return violations

    for entry in entries:
        name = entry.name
        if entry.is_dir():
            rel = f"{name}/"
            if rel in whitelist or name in whitelist:
                continue
            if name in allowed_dirs:
                continue
            reason = f"目录 '{name}' 不在 vault schema 允许列表"
            violations.append(
                {
                    "rule": "vault-structure-violation",
                    "severity": "error",
                    "file": rel,
                    "line": 0,
                    "msg": reason,
                    "fixable": True,
                    "path": rel,
                    "kind": "dir",
                    "reason": reason,
                }
            )
        elif entry.is_file():
            rel = name
            if rel in whitelist:
                continue
            if name in allowed_files:
                continue
            reason = f"文件 '{name}' 不在 vault schema 允许列表"
            violations.append(
                {
                    "rule": "vault-structure-violation",
                    "severity": "error",
                    "file": rel,
                    "line": 0,
                    "msg": reason,
                    "fixable": True,
                    "path": rel,
                    "kind": "file",
                    "reason": reason,
                }
            )

    return violations


def _load_locale_dirs(plugin_root: Path, vault: Path, lang: str) -> set[str]:
    """Load `dirs` mapping; return ONLY top-level vault dir names (not sub-layer).

    Top-level keys (legitimate at vault root): knowledge/memory/dashboard/archive/
    meta/templates/assets. Sub-layer keys (projects/sources/domains/journal/
    reflection/inbox + flat alternates concepts/entities/...) MUST live under
    namespace dirs (e.g. 知识库/领域/), not at vault root.
    """
    _TOP_LEVEL_KEYS = {
        "knowledge",
        "memory",
        "dashboard",
        "archive",
        "meta",
        "templates",
        "assets",
    }
    sys.path.insert(0, str(plugin_root / "scripts" / "hooks" / "_lib"))
    try:
        from cortex_locale import load_locale  # type: ignore

        loc = load_locale(plugin_root, vault, lang)
        dirs_map = loc.get_dirs()
        return {
            v
            for k, v in dirs_map.items()
            if k in _TOP_LEVEL_KEYS and isinstance(v, str) and v
        }
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
        # multi-line list item: "- item" or "  - item" (with/without indent)
        stripped = line.lstrip()
        if stripped.startswith("- ") and cur_key:
            if fm.get(cur_key) is None:
                fm[cur_key] = []
            if isinstance(fm[cur_key], list):
                fm[cur_key].append(stripped[2:].strip().strip("\"'"))
            continue
        # indented continuation (non-list)
        if line.startswith(" ") and cur_key:
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


def index_wikilinks(
    vault: Path,
) -> tuple[dict[str, Path], dict[str, list[Path]], dict[str, set[str]]]:
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
        # collect outgoing wikilinks for referrer map (strip code blocks first)
        body = strip_code_for_wikilinks(text)
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
    fm_schema: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    fm, body_line = parse_frontmatter(text)

    # lint-skip: 模板/示例文件可通过 `lint-skip: true` 跳过全部检查 (仪表盘**不**豁免, 必须满足 tags ≥10 等强约束)
    _ls = fm.get("lint-skip") if fm else None
    if _ls in (True, "true", "True", "yes", 1, "1"):
        return findings

    # rule: frontmatter-schema-violation
    if fm_schema is not None:
        findings.extend(_check_frontmatter_schema(rel, fm, fm_schema))

    # rule 1: fm-missing-type
    if not fm.get("type"):
        findings.append(
            _f("fm-missing-type", "error", rel, 1, "frontmatter 缺 type 字段", True)
        )
    # rule 2: fm-missing-created
    if not fm.get("created"):
        findings.append(
            _f(
                "fm-missing-created",
                "warn",
                rel,
                1,
                "frontmatter 缺 created 字段",
                True,
            )
        )
    # rule: fm-banned-fields (preset 等废弃字段, autofix pop)
    _banned_fields = [k for k in _BANNED_FM_FIELDS if k in fm]
    if _banned_fields:
        findings.append(
            _f(
                "fm-banned-fields",
                "warn",
                rel,
                1,
                f"frontmatter 含禁止字段: {', '.join(_banned_fields)}",
                True,
            )
        )
    # rule: fm-missing-tags (tags 字段必须存在 + 类型 list)
    _tg_check = fm.get("tags") if "tags" in fm else None
    if "tags" not in fm:
        findings.append(
            _f(
                "fm-missing-tags",
                "warn",
                rel,
                1,
                "frontmatter 缺 tags 字段",
                True,
            )
        )
    elif not isinstance(_tg_check, list):
        findings.append(
            _f(
                "fm-missing-tags",
                "warn",
                rel,
                1,
                "frontmatter tags 非 list",
                True,
            )
        )
    # rule: fm-duplicate-tags + fm-banned-tags
    _tags = fm.get("tags")
    if isinstance(_tags, list) and _tags:
        _seen: set[str] = set()
        _dups: list[str] = []
        _banned: list[str] = []
        for _t in _tags:
            if not isinstance(_t, str):
                continue
            if _t in _seen and _t not in _dups:
                _dups.append(_t)
            _seen.add(_t)
            if _is_banned_tag(_t) and _t not in _banned:
                _banned.append(_t)
        if _dups:
            findings.append(
                _f(
                    "fm-duplicate-tags",
                    "warn",
                    rel,
                    1,
                    f"frontmatter tags 重复: {', '.join(_dups)}",
                    True,
                )
            )
        if _banned:
            findings.append(
                _f(
                    "fm-banned-tags",
                    "warn",
                    rel,
                    1,
                    f"frontmatter tags 含结构/裸时间标记 (非内容相关): {', '.join(_banned)}",
                    True,
                )
            )

    # rule 14: i18n-frontmatter-lang-mismatch
    if vault_lang:
        page_lang = fm.get("lang")
        # skip auto-generated where lang may legitimately mix
        skip_prefixes = ("_templates/",)
        if (
            isinstance(page_lang, str)
            and page_lang
            and page_lang != vault_lang
            and not any(rel.startswith(p) for p in skip_prefixes)
        ):
            findings.append(
                _f(
                    "i18n-frontmatter-lang-mismatch",
                    "warn",
                    rel,
                    1,
                    f"page lang='{page_lang}' != vault.lang='{vault_lang}'",
                    False,
                )
            )

    # rule 9: title-h1-mismatch
    title = fm.get("title")
    h1m = H1_RE.search(text)
    h1 = h1m.group(1).strip() if h1m else None
    if isinstance(title, str) and title and h1 and title.strip() != h1:
        findings.append(
            _f(
                "title-h1-mismatch",
                "warn",
                rel,
                body_line,
                f"H1='{h1}' != title='{title}'",
                True,
            )
        )

    # rule 3: dead-wikilink (skip code blocks — shell `[[ ... ]]` 不算 wikilink)
    _wikilink_scan_text = strip_code_for_wikilinks(text)
    for m in WIKILINK_RE.finditer(_wikilink_scan_text):
        tgt = m.group(1).strip()
        if tgt.lower().endswith(".md"):
            tgt = tgt[:-3]
        key = tgt.split("/")[-1].lower()
        if key not in by_name and key not in by_alias:
            line = text[: m.start()].count("\n") + 1
            findings.append(
                _f("dead-wikilink", "error", rel, line, f"dead link: [[{tgt}]]", True)
            )

    # rule 12: callout-unknown-type
    for m in CALLOUT_RE.finditer(text):
        ct = m.group(1).lower()
        if ct not in CALLOUT_WHITELIST:
            line = text[: m.start()].count("\n") + 1
            findings.append(
                _f(
                    "callout-unknown-type",
                    "warn",
                    rel,
                    line,
                    f"unknown callout type: [!{ct}]",
                    True,
                )
            )

    # rule 6 & 7: file length
    if rel == "hot.md":
        nlines = text.count("\n") + 1
        if nlines > 200:
            findings.append(
                _f(
                    "hot-too-long",
                    "warn",
                    rel,
                    nlines,
                    f"hot.md {nlines} lines > 200",
                    True,
                )
            )
    # rule 4: orphan-page (skip _meta/_templates files)
    skip_orphan = (
        rel.startswith("_templates/")
        or rel == "index.md"
        or rel == "hot.md"
        or path.name.startswith("_")
    )
    if not skip_orphan:
        key = path.stem.lower()
        tags = fm.get("tags") or []
        has_tag = bool(tags) if isinstance(tags, list) else bool(tags)
        if not referrers.get(key) and not has_tag:
            findings.append(
                _f(
                    "orphan-page",
                    "warn",
                    rel,
                    1,
                    "orphan page (no inbound link, no tag)",
                    True,
                )
            )

    # rule 10: filename-illegal
    if any(c in ILLEGAL_CHARS for c in path.name):
        findings.append(
            _f(
                "filename-illegal",
                "error",
                rel,
                1,
                f"filename has illegal chars: {path.name}",
                False,
            )
        )

    # rule 18: path-lang-mismatch — vault path segment 不符 vault.lang
    if vault_lang:
        findings.extend(_check_path_lang_mismatch(rel, fm, vault_lang))

    # rule: skill-references-exists — SKILL/AGENT/agent references/<x>.md 存在性
    findings.extend(check_skill_references_exists(path, rel, text))

    # rule: frontmatter-required-scores — 知识库 4 / 记忆 2 字段强制
    findings.extend(check_frontmatter_required_scores(rel, text))

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
            findings.append(
                _f(
                    "duplicate-alias",
                    "error",
                    "(global)",
                    0,
                    f"alias '{alias}' shared across: {ps}",
                    True,
                )
            )

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
                findings.append(
                    _f(
                        "index-missing-section",
                        "warn",
                        "index.md",
                        1,
                        f"index.md missing reference to {sub.name}/",
                        True,
                    )
                )

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
                findings.append(
                    _f(
                        "block-id-duplicate",
                        "error",
                        rel,
                        line,
                        f"^{bid} duplicated ({len(occ)}x)",
                        True,
                    )
                )

    # rule 13: path-naming-violation (per prd §9; only for time-pattern paths)
    for p in files:
        rel = str(p.relative_to(vault))
        violation = _check_naming(rel)
        if violation:
            findings.append(
                _f("path-naming-violation", "warn", rel, 1, violation, True)
            )

    # rule: repo-path-deprecated — `知识库/来源/代码仓库/...` should move to `知识库/项目/...`
    _DEPRECATED_PREFIX = "知识库/来源/代码仓库/"
    for p in files:
        rel = str(p.relative_to(vault))
        if rel.startswith(_DEPRECATED_PREFIX):
            findings.append(
                _f(
                    "repo-path-deprecated",
                    "warn",
                    rel,
                    1,
                    f"path under {_DEPRECATED_PREFIX} is deprecated; should move to 知识库/项目/",
                    True,
                )
            )

    # rule: reflection-path-deprecated — `知识库/反思/...` → autofix mv 到 `知识库/收件箱/`
    for p in files:
        rel = str(p.relative_to(vault))
        if rel.startswith("知识库/反思/"):
            findings.append(
                _f(
                    "reflection-path-deprecated",
                    "warn",
                    rel,
                    1,
                    "知识库/反思/ 已废弃, autofix mv 到 知识库/收件箱/<basename>.md (待 digest 重分配)",
                    True,
                )
            )

    # rule: question-fleeting-path-deprecated — `知识库/问题/...` 或 `知识库/临时/...` → autofix mv 到 `知识库/收件箱/`
    for p in files:
        rel = str(p.relative_to(vault))
        if rel.startswith("知识库/问题/") or rel.startswith("知识库/临时/"):
            findings.append(
                _f(
                    "question-fleeting-path-deprecated",
                    "warn",
                    rel,
                    1,
                    "知识库/问题/ 与 知识库/临时/ 已废弃, autofix mv 到 知识库/收件箱/<basename>.md",
                    True,
                )
            )

    # rule: entity-concept-path-deprecated — `知识库/实体/...` 或 `知识库/概念/...` → autofix mv 到 `知识库/领域/未分类/`
    for p in files:
        rel = str(p.relative_to(vault))
        if rel.startswith("知识库/实体/") or rel.startswith("知识库/概念/"):
            findings.append(
                _f(
                    "entity-concept-path-deprecated",
                    "warn",
                    rel,
                    1,
                    "知识库/实体/ 与 知识库/概念/ 已废弃, autofix mv 到 知识库/领域/未分类/<basename>.md (AI 后续可 cortex_refactor 改判到 6 域)",
                    True,
                )
            )

    # rule: journal-multi-freq-deprecated — `知识库/日记/{周|月|年}/...` → autofix mv 到 `归档/日记/<YYYY-QN>.md`
    for p in files:
        rel = str(p.relative_to(vault))
        if (
            rel.startswith("知识库/日记/周/")
            or rel.startswith("知识库/日记/月/")
            or rel.startswith("知识库/日记/年/")
        ):
            findings.append(
                _f(
                    "journal-multi-freq-deprecated",
                    "warn",
                    rel,
                    1,
                    "知识库/日记/{周|月|年}/ 已废弃 (仅日维度保留), autofix mv 到 归档/日记/<YYYY-QN>.md 季度桶",
                    True,
                )
            )

    # rule: source-non-repo-path-deprecated — `知识库/来源/{网页|论文|书籍}/...` → autofix mv 到 `知识库/收件箱/`
    for p in files:
        rel = str(p.relative_to(vault))
        if (
            rel.startswith("知识库/来源/网页/")
            or rel.startswith("知识库/来源/论文/")
            or rel.startswith("知识库/来源/书籍/")
        ):
            findings.append(
                _f(
                    "source-non-repo-path-deprecated",
                    "warn",
                    rel,
                    1,
                    "知识库/来源/{网页|论文|书籍}/ 已废弃, autofix mv 到 知识库/收件箱/<host>-<slug>.md (待 digest 分发)",
                    True,
                )
            )

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
                findings.append(
                    _f(
                        "i18n-path-not-in-locale",
                        "warn",
                        top + "/",
                        1,
                        f"top-level dir '{top}' not in vault.lang dirs map; consider migrate-locale",
                        True,
                    )
                )

    return findings


def _check_naming(rel: str) -> str | None:
    parts = rel.split("/")
    # skip shared roots (per prd §9 adjustment)
    if parts and parts[0] in SHARED_ROOT_DIRS:
        pass
    # 60_dashboards/<topic>-dashboard.md
    if (
        parts[0] == "60_dashboards"
        and len(parts) == 2
        and parts[1] not in ("_index.md",)
    ):
        if not parts[1].endswith("-dashboard.md"):
            return f"dashboard '{parts[1]}' must end with -dashboard.md"
    # zettels/YYYYMMDDHHMM-<slug>.md
    if parts[0] == "zettels" and len(parts) == 2 and parts[1] != "_index.md":
        if not re.match(r"^\d{12}-[a-z0-9-]+\.md$", parts[1]):
            return f"zettel '{parts[1]}' should be YYYYMMDDHHMM-<slug>.md"
    return None


def _f(
    rule: str, severity: str, file: str, line: int, msg: str, fixable: bool
) -> dict[str, Any]:
    return {
        "rule": rule,
        "severity": severity,
        "file": file,
        "line": line,
        "msg": msg,
        "fixable": fixable,
    }


# ---- rule: skill-references-exists ----

# ---- rule: base-format-yaml ----

# Dataview DQL 关键字 (行首, 大小写不敏感)
_DQL_KEYWORDS_RE = re.compile(
    r"^\s*(TABLE|LIST|TASK|FROM|WHERE|SORT|GROUP\s+BY|FLATTEN)\b",
    re.MULTILINE | re.IGNORECASE,
)
_BASES_SCHEMA_KEYS = {"filters", "views", "formulas", "properties"}
_BASE_LINT_SKIP_DIRS = (".obsidian/", "归档/", ".trash/")


def check_base_format_yaml(rel: Any, content: str) -> list[dict[str, Any]]:
    """rule base-format-yaml — .base 文件必须顶层 YAML object + 禁 markdown / Dataview DQL.

    `rel` 接受 Path 或 str (调用方传 vault-relative path)。
    """
    findings: list[dict[str, Any]] = []
    rel_path = rel if isinstance(rel, Path) else Path(str(rel))
    if rel_path.suffix != ".base":
        return findings

    rel_str = rel_path.as_posix()
    if any(p in rel_str for p in _BASE_LINT_SKIP_DIRS):
        return findings

    # 检 1: 首行 markdown header
    stripped = content.lstrip()
    if stripped.startswith("#"):
        first_line = stripped.split("\n", 1)[0][:50]
        findings.append(
            _f(
                "base-format-yaml",
                "warn",
                rel_str,
                1,
                f".base 首行不能是 markdown header (`{first_line}`), 必须 YAML object 顶层",
                False,
            )
        )
        return findings

    # 检 2: Dataview DQL 关键字
    m = _DQL_KEYWORDS_RE.search(content)
    if m:
        line_no = content[: m.start()].count("\n") + 1
        kw = re.sub(r"\s+", " ", m.group(1)).upper()
        findings.append(
            _f(
                "base-format-yaml",
                "warn",
                rel_str,
                line_no,
                f".base 含 Dataview DQL 关键字 `{kw}`, Bases ≠ Dataview, 两套插件语法",
                False,
            )
        )
        return findings

    # 检 3: YAML 解析
    try:
        import yaml  # type: ignore
    except ImportError:
        # PyYAML 未安装 — 跳过 (lint 不强依赖); 实际 cortex 部署带 PyYAML
        return findings
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        findings.append(
            _f(
                "base-format-yaml",
                "warn",
                rel_str,
                1,
                f".base YAML 解析失败: {e}",
                False,
            )
        )
        return findings

    # 检 4: 顶层必须 dict
    if not isinstance(data, dict):
        findings.append(
            _f(
                "base-format-yaml",
                "warn",
                rel_str,
                1,
                f".base 顶层必须 YAML object (dict), 实际 {type(data).__name__}",
                False,
            )
        )
        return findings

    # 检 5: Bases schema 字段
    if not (set(data.keys()) & _BASES_SCHEMA_KEYS):
        keys_preview = sorted(str(k) for k in data.keys())[:5]
        findings.append(
            _f(
                "base-format-yaml",
                "warn",
                rel_str,
                1,
                (
                    ".base 顶层缺 Bases schema 字段 "
                    f"(需 filters/views/formulas/properties 之一, 实际 keys: {keys_preview})"
                ),
                False,
            )
        )

    return findings


# ---- rule: frontmatter-required-scores ----

_SCORE_FIELDS_KB = ("score", "confidence", "source_credibility", "maturity")
_SCORE_FIELDS_MEM = ("importance", "confidence")
_MATURITY_ENUM = {"draft", "review", "stable", "deprecated"}
_SCORE_FIELDS_SKIP_PARTS = (
    "仪表盘/",
    "归档/",
    ".obsidian/",
    ".trash/",
    "_meta/",
    "_templates/",
    "_assets/",
)


def _scores_is_kb_path(rel_str: str) -> bool:
    """知识库 子树 (项目/领域/日记 — 不含 收件箱)."""
    return rel_str.startswith("知识库/") and "/收件箱/" not in rel_str


def _scores_is_mem_path(rel_str: str) -> bool:
    """记忆 L0-L4 子树."""
    return rel_str.startswith("记忆/L")


def _scores_coerce_value(val: Any) -> tuple[float, bool]:
    """Try coerce to float in [0, 10]. Returns (new_value, was_changed).

    bool 也按非法处理 (Python bool 是 int 子类)。
    """
    if isinstance(val, bool):
        return (0.0, True)
    if isinstance(val, int):
        v = float(val)
        if v < 0:
            return (0.0, True)
        if v > 10:
            return (10.0, True)
        return (v, True)  # int -> float counts as changed
    if isinstance(val, float):
        if val < 0:
            return (0.0, True)
        if val > 10:
            return (10.0, True)
        return (val, False)
    if isinstance(val, str):
        try:
            v = float(val)
        except (ValueError, TypeError):
            return (0.0, True)
        if v < 0:
            return (0.0, True)
        if v > 10:
            return (10.0, True)
        # NOTE: lint's parse_frontmatter returns all unquoted scalars as str,
        # so a string like "7.5" is the common-case write format and must NOT
        # flag as "needs change". Only out-of-range / non-numeric / bool flag.
        return (v, False)
    return (0.0, True)


def check_frontmatter_required_scores(
    rel: Any, content: str
) -> list[dict[str, Any]]:
    """rule frontmatter-required-scores — 知识库 4 字段 / 记忆 2 字段 强制.

    `rel` 接受 Path 或 str (vault-relative path)。
    """
    findings: list[dict[str, Any]] = []
    rel_path = rel if isinstance(rel, Path) else Path(str(rel))
    if rel_path.suffix != ".md":
        return findings
    rel_str = rel_path.as_posix()
    if any(p in rel_str for p in _SCORE_FIELDS_SKIP_PARTS):
        return findings
    is_kb = _scores_is_kb_path(rel_str)
    is_mem = _scores_is_mem_path(rel_str)
    if not (is_kb or is_mem):
        return findings

    fm, _body_line = parse_frontmatter(content)
    if not fm:
        # 无 frontmatter — 其他 rule (fm-missing-type 等) 已覆盖, 这里跳过
        return findings

    required = _SCORE_FIELDS_KB if is_kb else _SCORE_FIELDS_MEM
    for field in required:
        if field not in fm:
            findings.append(
                _f(
                    "frontmatter-required-scores",
                    "warn",
                    rel_str,
                    1,
                    f".md 缺强制评分字段 `{field}` (知识库={is_kb} 记忆={is_mem})",
                    True,
                )
            )
            continue
        val = fm[field]
        if field == "maturity":
            if not isinstance(val, str) or val not in _MATURITY_ENUM:
                findings.append(
                    _f(
                        "frontmatter-required-scores",
                        "warn",
                        rel_str,
                        1,
                        f"maturity={val!r} 非合法 enum (draft/review/stable/deprecated)",
                        True,
                    )
                )
        else:
            new_val, changed = _scores_coerce_value(val)
            if changed:
                findings.append(
                    _f(
                        "frontmatter-required-scores",
                        "warn",
                        rel_str,
                        1,
                        f"{field}={val!r} 非合法 0.0-10.0 浮点 (autofix 转 {new_val})",
                        True,
                    )
                )
    return findings


def _rebuild_frontmatter_text(fm: dict[str, Any], rest: str) -> str:
    """Rebuild text with new frontmatter using yaml.safe_dump."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return ""
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    return f"---\n{new_fm}---\n{rest}"


def autofix_frontmatter_required_scores(
    rel: Any, content: str
) -> str | None:
    """rule autofix — 缺字段加 stub 0.0 (maturity=draft); 类型/范围错 coerce.

    返回新 content, 或 None 表示无改动 / 不适用。
    """
    rel_path = rel if isinstance(rel, Path) else Path(str(rel))
    if rel_path.suffix != ".md":
        return None
    rel_str = rel_path.as_posix()
    if any(p in rel_str for p in _SCORE_FIELDS_SKIP_PARTS):
        return None
    is_kb = _scores_is_kb_path(rel_str)
    is_mem = _scores_is_mem_path(rel_str)
    if not (is_kb or is_mem):
        return None

    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.S)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None
    rest = m.group(2)

    required = _SCORE_FIELDS_KB if is_kb else _SCORE_FIELDS_MEM
    changed = False
    for field in required:
        if field == "maturity":
            v = fm.get(field)
            if not isinstance(v, str) or v not in _MATURITY_ENUM:
                fm[field] = "draft"
                changed = True
        elif field not in fm:
            fm[field] = 0.0
            changed = True
        else:
            new_val, was_changed = _scores_coerce_value(fm[field])
            if was_changed:
                fm[field] = new_val
                changed = True
    if not changed:
        return None
    return _rebuild_frontmatter_text(fm, rest)


# 仅捕获 `(references/<name>.md)` 形式的相对链接 (允许子目录), 跳过 http(s)/绝对/纯锚点
_REFERENCES_LINK_RE = re.compile(r"\]\(\s*(references/[^)\s#]+\.md)(?:#[^)]*)?\s*\)")


def check_skill_references_exists(
    abs_path: Path,
    rel: str,
    content: str,
) -> list[dict[str, Any]]:
    """rule skill-references-exists — SKILL/AGENT/agent markdown 引用 references/<x>.md 必须存在.

    仅对 `SKILL.md` / `AGENT.md` / 位于 `agents/` 目录下的 .md 生效。
    `abs_path` 用于相对解析 references/ 目标; `rel` 进 finding.file。
    """
    findings: list[dict[str, Any]] = []
    name = abs_path.name
    if name not in {"SKILL.md", "AGENT.md"} and abs_path.parent.name != "agents":
        return findings
    base_dir = abs_path.parent
    for m in _REFERENCES_LINK_RE.finditer(content):
        ref_rel = m.group(1)
        target = (base_dir / ref_rel).resolve()
        if not target.exists():
            line = content[: m.start()].count("\n") + 1
            findings.append(
                _f(
                    "skill-references-exists",
                    "warn",
                    rel,
                    line,
                    f"references 目标不存在: {ref_rel}",
                    False,
                )
            )
    return findings


# ---- backup-root helpers (PRD: lint backup must live outside vault) ----


def _vault_hash(vault: Path) -> str:
    return hashlib.sha256(str(vault.resolve()).encode()).hexdigest()[:8]


def _get_backup_root(vault: Path) -> Path:
    """Backup root, outside vault: ~/.cache/cortex/lint-backup/<vault-hash>/<ts>/."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = Path.home() / ".cache" / "cortex" / "lint-backup" / _vault_hash(vault) / ts
    base.mkdir(parents=True, exist_ok=True)
    return base


def _prune_old_backups(vault: Path, days: int = 30) -> None:
    """Best-effort: delete backup ts dirs older than `days` for this vault."""
    root = Path.home() / ".cache" / "cortex" / "lint-backup" / _vault_hash(vault)
    if not root.is_dir():
        return
    import time

    cutoff = time.time() - days * 86400
    for child in root.iterdir():
        try:
            if child.stat().st_mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
        except Exception:
            pass


# ---- frontmatter-schema helpers (rule frontmatter-schema-violation) ----


def _load_frontmatter_schema(vault: Path, plugin_root: Path) -> dict[str, Any] | None:
    """Load frontmatter schema YAML. vault `_meta/` overrides plugin templates."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    for p in (
        vault / "_meta" / "frontmatter-schema.yaml",
        plugin_root / "presets" / "seed" / "_templates" / "frontmatter-schema.yaml",
    ):
        if p.is_file():
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception:
                continue
    return None


def _resolve_schema_for_path(
    rel_path: str, schema: dict[str, Any] | None
) -> dict[str, Any] | None:
    """Walk namespaces by path segments (longest-prefix); return matched rule dict."""
    if not schema:
        return None
    ns = schema.get("namespaces", {})
    if not isinstance(ns, dict):
        return None
    parts = [p for p in rel_path.replace("\\", "/").split("/") if p]
    if not parts:
        return None
    dirs = parts[:-1]
    cur: Any = ns
    for p in dirs:
        if isinstance(cur, dict):
            if p in cur:
                nxt = cur[p]
                if isinstance(nxt, dict) and (
                    "required" in nxt or "defaults" in nxt or "tags_required" in nxt
                ):
                    return nxt
                cur = nxt
            elif "*" in cur:
                nxt = cur["*"]
                if isinstance(nxt, dict) and (
                    "required" in nxt or "defaults" in nxt or "tags_required" in nxt
                ):
                    return nxt
                cur = nxt
            else:
                return None
        else:
            return None
    if isinstance(cur, dict) and (
        "required" in cur or "defaults" in cur or "tags_required" in cur
    ):
        return cur
    if isinstance(cur, dict) and "*" in cur:
        leaf = cur["*"]
        if isinstance(leaf, dict):
            return leaf
    return None


def _check_frontmatter_schema(
    rel_path: str,
    fm: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Check fm against resolved schema; return findings."""
    findings: list[dict[str, Any]] = []
    rule = _resolve_schema_for_path(rel_path, schema)
    if not rule:
        return findings
    required = rule.get("required", []) or []
    tags_required = rule.get("tags_required", []) or []
    for k in required:
        if k not in fm or fm.get(k) in (None, "", []):
            findings.append(
                _f(
                    "frontmatter-schema-violation",
                    "warn",
                    rel_path,
                    1,
                    f"frontmatter 缺 required 字段 '{k}'",
                    True,
                )
            )
    fm_tags = fm.get("tags", []) or []
    if isinstance(fm_tags, str):
        fm_tags = [fm_tags]
    for t in tags_required:
        prefix = str(t).split("/", 1)[0] + "/"
        if not any(str(ft).startswith(prefix) for ft in fm_tags):
            findings.append(
                _f(
                    "frontmatter-schema-violation",
                    "warn",
                    rel_path,
                    1,
                    f"frontmatter 缺 required tag prefix '{prefix}*'",
                    True,
                )
            )
    return findings


def _fix_frontmatter_schema(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    """Fill missing required (via defaults) + tags_required prefixes."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return False
    rel = finding["file"]
    p = vault / rel
    if not p.is_file():
        return False
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return False
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.S)
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            return False
        body = m.group(2)
        if not isinstance(fm, dict):
            return False
    else:
        fm = {}
        body = text

    schema = _load_frontmatter_schema(vault, plugin_root)
    rule = _resolve_schema_for_path(rel, schema)
    if not rule:
        return False

    defaults = rule.get("defaults", {}) or {}
    required = rule.get("required", []) or []
    tags_required = rule.get("tags_required", []) or []

    changed = False
    for k, v in defaults.items():
        if k not in fm or fm.get(k) in (None, ""):
            fm[k] = v
            changed = True
    if "created" in required and not fm.get("created"):
        fm["created"] = datetime.now(timezone.utc).isoformat()
        changed = True
    if "updated" in required and not fm.get("updated"):
        fm["updated"] = datetime.now(timezone.utc).isoformat()
        changed = True
    fm_tags = fm.get("tags", []) or []
    if isinstance(fm_tags, str):
        fm_tags = [fm_tags]
    for t in tags_required:
        prefix = str(t).split("/", 1)[0] + "/"
        if not any(str(ft).startswith(prefix) for ft in fm_tags):
            fm_tags.append(t)
            changed = True
    if changed:
        fm["tags"] = fm_tags
    for k in required:
        if k in fm and fm.get(k) not in (None, "", []):
            continue
        if k in ("created", "updated"):
            continue
        if k in defaults:
            continue
        fm[k] = ""
        changed = True

    if not changed:
        return False

    bak = backup_dir / rel
    bak.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(p, bak)
    except Exception:
        pass
    try:
        new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    except Exception:
        return False
    new_text = f"---\n{new_fm}---\n{body}"
    try:
        p.write_text(new_text, encoding="utf-8")
        return True
    except Exception:
        return False


# ---- template/seed manifest helpers (rules 17/18/19) ----

TEMPLATE_END_MARKER = "<!-- TEMPLATE_END -->"


def _sha256_normalized(p: Path) -> str:
    """sha256 of file content with CRLF normalized to LF (matches manifest gen)."""
    try:
        return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except Exception:
        return ""


def _load_manifest(p: Path) -> dict[str, Any]:
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_template_version(p: Path) -> int:
    """Read frontmatter template_version (default 1)."""
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 1
    fm_match = re.match(r"^(?:<!--[^\n]*-->\n)*---\n(.*?)\n---", text, re.S)
    if fm_match:
        vm = re.search(r"^template_version\s*:\s*(\d+)", fm_match.group(1), re.M)
        if vm:
            return int(vm.group(1))
    hm = re.search(r"<!--\s*cortex-template-version:\s*(\d+)\s*-->", text)
    if hm:
        return int(hm.group(1))
    return 1


def _check_template_outdated(vault: Path, plugin_root: Path) -> list[dict[str, Any]]:
    """Rule template-outdated/template-missing — vault/_templates vs plugin manifest."""
    findings: list[dict[str, Any]] = []
    manifest = _load_manifest(
        plugin_root / "presets" / "seed" / "_templates" / "_manifest.json"
    )
    if not manifest:
        return findings
    entries = manifest.get("entries", {}) if isinstance(manifest, dict) else {}
    for rel, info in entries.items():
        if not isinstance(info, dict):
            continue
        vault_file = vault / "_templates" / rel
        plugin_sha = info.get("sha256", "")
        if not vault_file.exists():
            findings.append(
                _f(
                    "template-missing",
                    "warn",
                    f"_templates/{rel}",
                    1,
                    f"vault 缺少模板 {rel} (plugin 有最新版)",
                    True,
                )
            )
            continue
        vault_sha = _sha256_normalized(vault_file)
        if vault_sha != plugin_sha:
            findings.append(
                _f(
                    "template-outdated",
                    "warn",
                    f"_templates/{rel}",
                    1,
                    f"模板 _templates/{rel} 与 plugin source 不一致 "
                    f"(vault sha={vault_sha[:8]} plugin sha={plugin_sha[:8]})",
                    True,
                )
            )
    return findings


def _seed_rel_to_vault_rel(seed_rel: str) -> str | None:
    """Map presets manifest key (e.g. 'seed/root/主页.md') → vault rel path."""
    if seed_rel.startswith("seed/root/"):
        return seed_rel[len("seed/root/") :]
    if seed_rel.startswith("seed/_meta/"):
        # _meta files (memory-policy.yaml etc.) excluded from manifest scope
        return seed_rel[len("seed/") :]
    if seed_rel.startswith("seed/"):
        return seed_rel[len("seed/") :]
    return None


def _check_structure_missing(vault: Path, plugin_root: Path) -> list[dict[str, Any]]:
    """Scan _structure.json directories nesting; report missing vault dirs."""
    findings: list[dict[str, Any]] = []
    sf = plugin_root / "presets" / "_structure.json"
    if not sf.exists():
        return findings
    try:
        d = json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return findings

    def walk(node: Any, prefix: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{prefix}/{k}" if prefix else k
                if not (vault / p).is_dir():
                    findings.append(
                        _f(
                            "structure-missing",
                            "warn",
                            p,
                            1,
                            f"vault 缺目录 {p} (plugin _structure.json 要求)",
                            True,
                        )
                    )
                walk(v, p)
        elif isinstance(node, list):
            for item in node:
                walk(item, prefix)

    walk(d.get("directories", {}))
    return findings


def _check_seed_missing(vault: Path, plugin_root: Path) -> list[dict[str, Any]]:
    """Scan _structure.json seed_files; report missing vault target paths."""
    findings: list[dict[str, Any]] = []
    sf = plugin_root / "presets" / "_structure.json"
    if not sf.exists():
        return findings
    try:
        d = json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return findings
    for s in d.get("seed_files", []):
        if not isinstance(s, dict):
            continue
        dst_key = s.get("dst_key", ".")
        name = s.get("name")
        if not name:
            continue
        rel = name if dst_key == "." else f"{dst_key}/{name}"
        if not (vault / rel).exists():
            findings.append(
                _f(
                    "seed-missing",
                    "warn",
                    rel,
                    1,
                    f"vault 缺 seed 文件 {rel}",
                    True,
                )
            )
    return findings


def _check_meta_missing(vault: Path, plugin_root: Path) -> list[dict[str, Any]]:
    """Report missing core _meta files."""
    findings: list[dict[str, Any]] = []
    targets = [
        (
            "_meta/memory-policy.yaml",
            plugin_root / "presets" / "seed" / "_meta" / "memory-policy.yaml",
        ),
        (
            "_meta/triggers.yaml",
            plugin_root / "presets" / "seed" / "_templates" / "triggers.yaml",
        ),
        (
            "_meta/template-manifest.json",
            plugin_root / "presets" / "seed" / "_templates" / "_manifest.json",
        ),
        (
            "_meta/frontmatter-schema.yaml",
            plugin_root / "presets" / "seed" / "_templates" / "frontmatter-schema.yaml",
        ),
    ]
    for rel, src in targets:
        if src.exists() and not (vault / rel).exists():
            findings.append(
                _f(
                    "meta-missing",
                    "warn",
                    rel,
                    1,
                    f"vault 缺 _meta 文件 {rel}",
                    True,
                )
            )
    return findings


def _fix_structure_missing(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    p = vault / finding["file"]
    try:
        p.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def _fix_seed_missing(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    rel = finding["file"]
    sf = plugin_root / "presets" / "_structure.json"
    if not sf.exists():
        return False
    try:
        d = json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return False
    src_path: Path | None = None
    for s in d.get("seed_files", []):
        if not isinstance(s, dict):
            continue
        dst_key = s.get("dst_key", ".")
        name = s.get("name")
        if not name:
            continue
        cand_rel = name if dst_key == "." else f"{dst_key}/{name}"
        if cand_rel == rel:
            src_path = plugin_root / "presets" / s["src"]
            break
    if src_path is None or not src_path.exists():
        return False
    now = datetime.now(timezone.utc).isoformat()
    try:
        content = src_path.read_text(encoding="utf-8")
    except Exception:
        return False
    content = content.replace("{{LAST_UPDATED}}", now)
    content = content.replace("{{UPDATED}}", now)
    content = content.replace("{{CREATED}}", now)
    content = content.replace("{{TITLE}}", Path(rel).stem)
    content = content.replace("{{CURRENT_PATH}}", str(Path(rel).parent))
    dst = vault / rel
    if dst.exists():
        return False  # don't overwrite user content
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        dst.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def _fix_meta_missing(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    rel = finding["file"]
    src_map = {
        "_meta/memory-policy.yaml": plugin_root
        / "presets"
        / "seed"
        / "_meta"
        / "memory-policy.yaml",
        "_meta/triggers.yaml": plugin_root
        / "presets"
        / "seed"
        / "_templates"
        / "triggers.yaml",
        "_meta/template-manifest.json": plugin_root
        / "presets"
        / "seed"
        / "_templates"
        / "_manifest.json",
        "_meta/frontmatter-schema.yaml": plugin_root
        / "presets"
        / "seed"
        / "_templates"
        / "frontmatter-schema.yaml",
    }
    src = src_map.get(rel)
    if src is None or not src.exists():
        return False
    dst = vault / rel
    if dst.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        dst.write_bytes(src.read_bytes())
        return True
    except Exception:
        return False


# ---- backup-in-vault: migrate legacy <vault>/_meta/.cortex-backup/ ----


def _check_backup_in_vault(vault: Path, plugin_root: Path) -> list[dict[str, Any]]:
    """Rule backup-in-vault — legacy lint backup dir found inside vault."""
    findings: list[dict[str, Any]] = []
    bak = vault / "_meta" / ".cortex-backup"
    if bak.is_dir():
        findings.append(
            _f(
                "backup-in-vault",
                "warn",
                "_meta/.cortex-backup",
                1,
                "vault 内有 lint backup 目录, 应迁出到 ~/.cache/cortex/lint-backup/",
                True,
            )
        )
    return findings


def _fix_backup_in_vault(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    """mv vault/_meta/.cortex-backup → ~/.cache/cortex/lint-backup/<hash>/migrated-<ts>/."""
    src = vault / "_meta" / ".cortex-backup"
    if not src.is_dir():
        return False
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = (
        Path.home()
        / ".cache"
        / "cortex"
        / "lint-backup"
        / _vault_hash(vault)
        / f"migrated-{ts}"
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dst))
        return True
    except Exception:
        return False


# Fix priority — backup-in-vault must run first (migrate legacy backup out),
# then structure must precede seed (seed write needs dir tree).
RULE_PRIORITY = {
    "backup-in-vault": 0,
    "vault-structure-violation": 1,
    "structure-missing": 2,
    "meta-missing": 3,
    "seed-missing": 4,
    "vault-misaligned": 5,
    "template-outdated": 6,
    "seed-outdated": 6,
    "callout-unknown-type": 7,
    "orphan-page": 8,
    "path-naming-violation": 9,
    "i18n-path-not-in-locale": 9,
    "repo-path-deprecated": 10,
    "reflection-path-deprecated": 11,
    "question-fleeting-path-deprecated": 11,
    "entity-concept-path-deprecated": 11,
    "journal-multi-freq-deprecated": 11,
    "source-non-repo-path-deprecated": 11,
}


def _check_seed_outdated(vault: Path, plugin_root: Path) -> list[dict[str, Any]]:
    """Rule seed-outdated — vault seed files' template_version < plugin manifest."""
    findings: list[dict[str, Any]] = []
    manifest = _load_manifest(plugin_root / "presets" / "_manifest.json")
    if not manifest:
        return findings
    entries = manifest.get("entries", {}) if isinstance(manifest, dict) else {}
    for seed_rel, info in entries.items():
        if not isinstance(info, dict):
            continue
        vault_rel = _seed_rel_to_vault_rel(seed_rel)
        if not vault_rel:
            continue
        vault_file = vault / vault_rel
        if not vault_file.exists():
            # User may not have installed this seed — don't warn (lint isn't doctor)
            continue
        plugin_ver = int(info.get("template_version", 1))
        vault_ver = _read_template_version(vault_file)
        if vault_ver < plugin_ver:
            findings.append(
                _f(
                    "seed-outdated",
                    "warn",
                    vault_rel,
                    1,
                    f"seed 文件 template_version={vault_ver} < plugin={plugin_ver}",
                    True,
                )
            )
    return findings


def _find_plugin_seed_source(plugin_root: Path, vault_rel: str) -> Path | None:
    """Reverse map vault rel → plugin seed/<...> path."""
    # root entries (主页.md / 焦点.md) live under seed/root/
    candidates = [
        plugin_root / "presets" / "seed" / "root" / vault_rel,
        plugin_root / "presets" / "seed" / vault_rel,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _fix_template_outdated(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    """Copy plugin template over vault template (backup existing)."""
    file_path = finding["file"]
    if not file_path.startswith("_templates/"):
        return False
    rel = file_path[len("_templates/") :]
    src = plugin_root / "presets" / "seed" / "_templates" / rel
    dst = vault / "_templates" / rel
    if not src.exists():
        return False
    if dst.exists():
        bak = backup_dir / "_templates" / rel
        bak.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(dst, bak)
        except Exception:
            pass
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False


def _fix_seed_outdated(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    """Rewrite vault seed file's template-owned region (up to TEMPLATE_END marker)."""
    vault_rel = finding["file"]
    src = _find_plugin_seed_source(plugin_root, vault_rel)
    if src is None:
        return False
    dst = vault / vault_rel
    if not dst.exists():
        return False
    try:
        src_text = src.read_text(encoding="utf-8")
        dst_text = dst.read_text(encoding="utf-8")
    except Exception:
        return False
    # backup
    bak = backup_dir / vault_rel
    bak.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(dst, bak)
    except Exception:
        pass
    if TEMPLATE_END_MARKER in src_text:
        src_head = src_text.split(TEMPLATE_END_MARKER, 1)[0] + TEMPLATE_END_MARKER
    else:
        src_head = src_text
    if TEMPLATE_END_MARKER in dst_text:
        dst_tail = dst_text.split(TEMPLATE_END_MARKER, 1)[1]
    else:
        dst_tail = ""  # legacy file w/o marker → full replace
    try:
        dst.write_text(src_head + dst_tail, encoding="utf-8")
        return True
    except Exception:
        return False


# ---- vault-misaligned (强制对齐) ----


def _sha256_normalized_part(p: Path, part: str = "head") -> str:
    """sha256 of TEMPLATE_END head ('<...>MARKER') or tail (after MARKER).

    若文件无 marker, head=全文 sha, tail=空串 sha。CRLF→LF 归一化。
    """
    try:
        txt = p.read_bytes().replace(b"\r\n", b"\n")
    except Exception:
        return ""
    MARKER = TEMPLATE_END_MARKER.encode("utf-8")
    if MARKER not in txt:
        if part == "head":
            return hashlib.sha256(txt).hexdigest()
        return hashlib.sha256(b"").hexdigest()
    head, _, tail = txt.partition(MARKER)
    if part == "head":
        return hashlib.sha256(head + MARKER).hexdigest()
    return hashlib.sha256(tail).hexdigest()


def _resolve_plugin_source(rel: str, plugin_root: Path) -> Path | None:
    """vault relpath → plugin 源路径反查。"""
    if rel.startswith("_meta/"):
        name = rel[len("_meta/") :]
        for cand in (
            plugin_root / "presets" / "seed" / "_meta" / name,
            plugin_root / "presets" / "seed" / "_templates" / name,
        ):
            if cand.exists():
                return cand
        # 特例: template-manifest.json ← templates/_manifest.json
        if name == "template-manifest.json":
            cand = plugin_root / "presets" / "seed" / "_templates" / "_manifest.json"
            if cand.exists():
                return cand
        return None
    if rel.startswith("_templates/"):
        cand = (
            plugin_root / "presets" / "seed" / "_templates" / rel[len("_templates/") :]
        )
        return cand if cand.exists() else None
    # seed_files 反查
    sf = plugin_root / "presets" / "_structure.json"
    if sf.exists():
        try:
            d = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        for s in d.get("seed_files", []):
            if not isinstance(s, dict):
                continue
            dst_key = s.get("dst_key", ".")
            name = s.get("name")
            if not name:
                continue
            cand_rel = name if dst_key == "." else f"{dst_key}/{name}"
            if cand_rel == rel:
                cand = plugin_root / "presets" / s["src"]
                return cand if cand.exists() else None
    return None


def _check_vault_misaligned(vault: Path, plugin_root: Path) -> list[dict[str, Any]]:
    """检测 vault 内 plugin-managed 文件与 plugin 源 sha 不一致 (任意偏差强制对齐)。"""
    findings: list[dict[str, Any]] = []

    # 1) seed 文件 — 对比 TEMPLATE_END 前 head 部分 (保留用户尾段语义)
    sf = plugin_root / "presets" / "_structure.json"
    if sf.exists():
        try:
            d = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        for s in d.get("seed_files", []):
            if not isinstance(s, dict):
                continue
            dst_key = s.get("dst_key", ".")
            name = s.get("name")
            src_rel = s.get("src")
            if not name or not src_rel:
                continue
            rel = name if dst_key == "." else f"{dst_key}/{name}"
            src = plugin_root / "presets" / src_rel
            dst = vault / rel
            if not (src.is_file() and dst.is_file()):
                continue
            if _sha256_normalized_part(src, "head") != _sha256_normalized_part(
                dst, "head"
            ):
                findings.append(
                    _f(
                        "vault-misaligned",
                        "warn",
                        rel,
                        1,
                        f"vault 文件 {rel} 头部 (TEMPLATE_END 之前) 与 plugin 源不一致",
                        True,
                    )
                )

    # 2) _meta 固定文件 — 整体 sha 比对
    meta_pairs = [
        (
            "_meta/memory-policy.yaml",
            plugin_root / "presets" / "seed" / "_meta" / "memory-policy.yaml",
        ),
        (
            "_meta/triggers.yaml",
            plugin_root / "presets" / "seed" / "_templates" / "triggers.yaml",
        ),
        (
            "_meta/frontmatter-schema.yaml",
            plugin_root / "presets" / "seed" / "_templates" / "frontmatter-schema.yaml",
        ),
    ]
    for rel, src in meta_pairs:
        dst = vault / rel
        if not (src.is_file() and dst.is_file()):
            continue
        if _sha256_normalized(src) != _sha256_normalized(dst):
            findings.append(
                _f(
                    "vault-misaligned",
                    "warn",
                    rel,
                    1,
                    f"vault _meta 文件 {rel} 与 plugin 源不一致 (强制对齐)",
                    True,
                )
            )

    # 3) _templates/* — 整体 sha 比对 (补 template-outdated 漏掉的: 同版本号但内容被改)
    tpl_dir = plugin_root / "presets" / "seed" / "_templates"
    if tpl_dir.is_dir():
        for src in tpl_dir.rglob("*"):
            if not src.is_file():
                continue
            if src.name == "_manifest.json":
                continue
            rel_tpl = src.relative_to(tpl_dir).as_posix()
            dst = vault / "_templates" / rel_tpl
            if not dst.is_file():
                continue
            if _sha256_normalized(src) != _sha256_normalized(dst):
                vault_rel = f"_templates/{rel_tpl}"
                findings.append(
                    _f(
                        "vault-misaligned",
                        "warn",
                        vault_rel,
                        1,
                        f"vault {vault_rel} 与 plugin 源不一致",
                        True,
                    )
                )

    return findings


def _fix_vault_misaligned(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path,
    backup_dir: Path,
) -> bool:
    """强制对齐: TEMPLATE_END 拼接 (有 marker 时保留用户尾段); backup 原始。"""
    rel = finding["file"]
    dst = vault / rel
    if not dst.is_file():
        return False
    src = _resolve_plugin_source(rel, plugin_root)
    if src is None or not src.exists():
        return False
    # backup
    bak = backup_dir / rel
    bak.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(dst, bak)
    except Exception:
        pass
    try:
        src_text = src.read_text(encoding="utf-8")
        dst_text = dst.read_text(encoding="utf-8")
    except Exception:
        return False
    if TEMPLATE_END_MARKER in src_text:
        src_head = src_text.split(TEMPLATE_END_MARKER, 1)[0] + TEMPLATE_END_MARKER
        if TEMPLATE_END_MARKER in dst_text:
            dst_tail = dst_text.split(TEMPLATE_END_MARKER, 1)[1]
        else:
            dst_tail = ""
        new_text = src_head + dst_tail
    else:
        # plugin 源无 marker → 整体覆盖 (backup 已存)
        new_text = src_text
    try:
        dst.write_text(new_text, encoding="utf-8")
        return True
    except Exception:
        return False


# ---- dead-wikilink / duplicate-alias autofix helpers ----

_STUB_CAP = 1000


def _wikilink_freq(vault: Path, all_files: list[Path] | None = None) -> dict[str, int]:
    """Count wikilink target occurrences across the vault (key=lowercased stem)."""
    WL = re.compile(
        r"(?<!\!)\[\[([^\[\]\n|#^]+)(?:[#^][^\[\]\n|]*)?(?:\|[^\[\]\n]*)?\]\]"
    )
    freq: dict[str, int] = defaultdict(int)
    files = (
        all_files
        if all_files is not None
        else [
            p
            for p in vault.rglob("*.md")
            if p.is_file()
            and not any(part in EXCLUDE_DIRS for part in p.relative_to(vault).parts)
        ]
    )
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in WL.finditer(txt):
            tgt = m.group(1).strip()
            if tgt.lower().endswith(".md"):
                tgt = tgt[:-3]
            key = tgt.split("/")[-1].lower()
            freq[key] += 1
    return dict(freq)


def _slug(name: str) -> str:
    """Safe filename slug — preserve CJK, replace illegal/space chars."""
    s = re.sub(r'[\\/:*?"<>|]', "_", name)
    s = re.sub(r"\s+", "-", s).strip("-_")
    return s or "stub"


def _fix_dead_wikilink(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
    freq_cache: dict[str, int] | None = None,
    stub_counter: dict[str, int] | None = None,
) -> bool:
    """freq≥2 → create stub in 知识库/收件箱/; freq=1 → strip wikilink to plain text."""
    rel = finding["file"]
    p = vault / rel
    if not p.is_file():
        return False
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    m = re.search(r"\[\[([^\]]+)\]\]", finding.get("msg", ""))
    if not m:
        return False
    target = m.group(1).strip()
    target_stem = target[:-3] if target.lower().endswith(".md") else target
    key = target_stem.split("/")[-1].lower()

    if freq_cache is None:
        freq_cache = _wikilink_freq(vault)
    freq = freq_cache.get(key, 1)

    if freq >= 2:
        if stub_counter is None:
            stub_counter = {"n": 0}
        if stub_counter["n"] >= _STUB_CAP:
            return False
        slug = _slug(target_stem.split("/")[-1])
        stub_path = vault / "知识库" / "收件箱" / f"{slug}.md"
        if stub_path.exists():
            return False  # already there — not a new fix
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        content = (
            f"---\n"
            f"type: stub\n"
            f"title: {target_stem}\n"
            f"created: {now}\n"
            f"auto_created_by: lint-autofix\n"
            f"status: draft\n"
            f"tags: [inbox]\n"
            f"---\n\n"
            f"# {target_stem}\n\n"
            f"> [!warning] 由 lint autofix 自动创建 — 因被 ≥2 文件引用为 wikilink, 创建占位。"
            f"完善后删除 stub 标签。\n"
        )
        try:
            stub_path.write_text(content, encoding="utf-8")
        except Exception:
            return False
        stub_counter["n"] += 1
        return True
    else:
        # freq=1 → strip wikilink to plain text
        # Backup
        bak = backup_dir / rel
        bak.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(p, bak)
        except Exception:
            pass
        # Match [[target]], [[target|label]], [[target#anchor]], [[target#anchor|label]]
        esc = re.escape(target)
        pattern = re.compile(rf"\[\[{esc}(?:[#^][^\[\]\n|]*)?(?:\|([^\[\]\n]*))?\]\]")

        def _repl(mm: re.Match) -> str:
            label = mm.group(1)
            return label if label else target_stem.split("/")[-1]

        new_text = pattern.sub(_repl, text)
        if new_text == text:
            return False
        try:
            p.write_text(new_text, encoding="utf-8")
            return True
        except Exception:
            return False


def _fix_duplicate_alias_group(
    alias: str,
    file_rels: list[str],
    vault: Path,
    backup_dir: Path,
) -> int:
    """Rename duplicate alias across files: keep earliest (by created/mtime), suffix others."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return 0
    if len(file_rels) < 2:
        return 0

    file_info = []
    for rel in file_rels:
        p = vault / rel
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.S)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue
        body = m.group(2)
        created = fm.get("created") or ""
        try:
            mtime = p.stat().st_mtime
        except Exception:
            mtime = 0.0
        file_info.append(
            {
                "rel": rel,
                "path": p,
                "fm": fm,
                "body": body,
                "created": str(created) if created else "",
                "mtime": mtime,
            }
        )
    if len(file_info) < 2:
        return 0

    # Sort: created ASC (empty → after via "~" prefix tiebreaker by mtime ASC)
    def _sort_key(info: dict) -> tuple:
        c = info["created"]
        if c:
            return (0, c, info["mtime"])
        return (1, "", info["mtime"])

    file_info.sort(key=_sort_key)

    # Keep first; rename alias in others
    fixed = 0
    # Track suffix collisions
    used_aliases: set[str] = {alias}
    for info in file_info[1:]:
        bak = backup_dir / info["rel"]
        bak.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(info["path"], bak)
        except Exception:
            pass

        old_aliases = info["fm"].get("aliases") or []
        if isinstance(old_aliases, str):
            old_aliases = [old_aliases]
        if not isinstance(old_aliases, list):
            continue

        parent = Path(info["rel"]).parent.name or "root"
        new_aliases = []
        changed = False
        for a in old_aliases:
            a_str = str(a)
            if a_str.lower() == alias.lower():
                candidate = f"{a_str} ({parent})"
                if candidate in used_aliases:
                    sha8 = hashlib.sha1(info["rel"].encode("utf-8")).hexdigest()[:8]
                    candidate = f"{a_str} ({parent}-{sha8})"
                used_aliases.add(candidate)
                new_aliases.append(candidate)
                changed = True
            else:
                new_aliases.append(a_str)
        if not changed:
            continue
        info["fm"]["aliases"] = new_aliases
        try:
            new_fm = yaml.safe_dump(info["fm"], allow_unicode=True, sort_keys=False)
        except Exception:
            continue
        try:
            info["path"].write_text(
                f"---\n{new_fm}---\n{info['body']}", encoding="utf-8"
            )
            fixed += 1
        except Exception:
            continue
    return fixed


# ---- new autofix helpers: structure / callout / orphan / path-rename ----

# 14 Obsidian-standard callout types (rewrite anything else to `info`)
_STANDARD_CALLOUTS = {
    "info",
    "tip",
    "warning",
    "note",
    "abstract",
    "summary",
    "todo",
    "success",
    "question",
    "failure",
    "danger",
    "bug",
    "example",
    "quote",
}


# 知识库 sub-namespace dirs — vault root 上出现的同名目录应 merge 入 知识库/, 非备份
# 仅 4 子目录: 项目 / 领域 / 日记 / 收件箱 (zh-CN) + 英文 locale 等价
_KB_SUB_NAMES = {
    "项目",
    "领域",
    "日记",
    "收件箱",  # zh-CN canonical
    "projects",
    "domains",
    "journal",
    "inbox",
}

# 知识库/ 子层允许的目录白名单 (与 _KB_SUB_NAMES 对齐, 用于 vault-structure 子检查)
_KB_ALLOWED_SUBDIRS = {"项目", "领域", "日记", "收件箱"}


def _fix_vault_structure_violation(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """优先 merge: vault root 上的 知识库 子层名 → mv 到 知识库/<name>/ (合并内容).
    否则 mv 到 ~/.cache/cortex/lint-backup/<hash>/structure-<ts>/<rel>.
    """
    rel = finding.get("path") or finding.get("file")
    if not rel:
        return False
    rel = rel.rstrip("/")
    src = vault / rel
    if not src.exists():
        return False
    # 路径 = 单层目录名且匹配 知识库 子层 → merge
    if "/" not in rel and src.is_dir() and rel in _KB_SUB_NAMES:
        kb = vault / "知识库"
        dst = kb / rel
        try:
            dst.mkdir(parents=True, exist_ok=True)
            for entry in src.iterdir():
                target = dst / entry.name
                if target.exists():
                    # 冲突 → 加 ts 后缀避免覆盖
                    ts2 = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    target = dst / f"{entry.stem}-merged-{ts2}{entry.suffix}"
                shutil.move(str(entry), str(target))
            # 源目录现应为空, 删
            try:
                src.rmdir()
            except OSError:
                pass
            return True
        except Exception:
            pass
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    structure_root = (
        Path.home()
        / ".cache"
        / "cortex"
        / "lint-backup"
        / _vault_hash(vault)
        / f"structure-{ts}"
    )
    dst = structure_root / rel
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True
    except Exception:
        return False


def _fix_callout_unknown_type(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Unknown callout type → `info` (keeps 14 standard types untouched)."""
    rel = finding["file"]
    p = vault / rel
    if not p.is_file():
        return False
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    def _sub(m: re.Match) -> str:
        ctype = m.group(1).lower()
        if ctype in _STANDARD_CALLOUTS:
            return m.group(0)
        return m.group(0).replace(m.group(1), "info", 1)

    new_text = CALLOUT_RE.sub(_sub, text)
    if new_text == text:
        return False
    bak = backup_dir / rel
    bak.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(p, bak)
    except Exception:
        pass
    try:
        p.write_text(new_text, encoding="utf-8")
        return True
    except Exception:
        return False


def _fix_orphan_page(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Orphan page → append wikilink to sibling `_index.md`.

    No sibling _index.md → skip (returns False). Already linked → True (idempotent).
    """
    rel = finding["file"]
    p = vault / rel
    if not p.is_file():
        return False
    parent = p.parent
    idx = parent / "_index.md"
    if not idx.is_file():
        return False
    try:
        idx_text = idx.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    link = f"[[{p.stem}]]"
    if link in idx_text:
        return True
    # backup the _index.md (namespaced under "_index/<rel>" so it never collides
    # with a real file's backup)
    bak = backup_dir / "_index" / str(idx.relative_to(vault))
    bak.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(idx, bak)
    except Exception:
        pass
    new_text = idx_text.rstrip() + f"\n\n- {link}\n"
    try:
        idx.write_text(new_text, encoding="utf-8")
        return True
    except Exception:
        return False


def _slug_path_component(name: str) -> str:
    """Slug-safe rename for a single path segment.

    Rules: space → '-', non-[\\w 中文] → '_', collapse repeats, strip edges.
    """
    s = re.sub(r"\s+", "-", name)
    # keep word chars + CJK; everything else → _
    s = re.sub(r"[^\w一-鿿\-]", "_", s)
    s = re.sub(r"_+", "_", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("_-")


def _fix_path_violation(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Rename file (or top-level dir) to a slug-safe form.

    For `i18n-path-not-in-locale`, finding.file is `<top>/`; rename the dir.
    Otherwise finding.file is a regular file path; rename the basename.
    Conflict → append `-<sha8>`.
    """
    rel = finding["file"]
    is_dir_target = rel.endswith("/")
    rel_clean = rel.rstrip("/")
    src = vault / rel_clean
    if not src.exists():
        return False

    parent = src.parent
    if is_dir_target or src.is_dir():
        stem = src.name
        ext = ""
    else:
        stem = src.stem
        ext = src.suffix

    new_stem = _slug_path_component(stem)
    if not new_stem or new_stem == stem:
        return False

    new_path = parent / f"{new_stem}{ext}"
    if new_path.exists():
        sha8 = hashlib.sha256(rel_clean.encode("utf-8")).hexdigest()[:8]
        new_path = parent / f"{new_stem}-{sha8}{ext}"
        if new_path.exists():
            return False
    try:
        src.rename(new_path)
        return True
    except Exception:
        return False


def _fix_repo_path_deprecated(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Move `知识库/来源/代码仓库/<rest>` → `知识库/项目/<rest>`.

    Preserves <host>/<org>/<repo>/... structure (rest unchanged, prefix swapped).
    Updates frontmatter type=project if it was `domain` and fills host/org/repo
    from path segments when missing.
    """
    rel = finding["file"]
    deprecated_prefix = "知识库/来源/代码仓库/"
    new_prefix = "知识库/项目/"
    if not rel.startswith(deprecated_prefix):
        return False
    rest = rel[len(deprecated_prefix) :]
    src = vault / rel
    dst = vault / (new_prefix + rest)
    if not src.exists():
        return False
    if dst.exists():
        # Conflict: skip to avoid clobber.
        return False
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
    except Exception:
        return False

    # Best-effort: update frontmatter type/host/org/repo from path segments.
    try:
        text = dst.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return True
    parts = rest.split("/")
    host = parts[0] if len(parts) >= 1 else None
    org = parts[1] if len(parts) >= 2 else None
    repo = parts[2] if len(parts) >= 3 else None
    if not text.startswith("---\n"):
        return True
    end = text.find("\n---\n", 4)
    if end == -1:
        return True
    fm_block = text[4:end]
    rest_text = text[end + len("\n---\n") :]
    # Rewrite type if `type: domain`
    fm_block = re.sub(r"(?m)^type:\s*domain\s*$", "type: project", fm_block)

    # Add missing host/org/repo lines
    def _ensure_field(block: str, key: str, value: str | None) -> str:
        if value is None:
            return block
        if re.search(rf"(?m)^{re.escape(key)}\s*:", block):
            return block
        return block.rstrip() + f"\n{key}: {value}\n"

    fm_block = _ensure_field(fm_block, "host", host)
    fm_block = _ensure_field(fm_block, "org", org)
    fm_block = _ensure_field(fm_block, "repo", repo)
    new_text = f"---\n{fm_block.rstrip()}\n---\n{rest_text}"
    try:
        dst.write_text(new_text, encoding="utf-8")
    except Exception:
        pass
    return True


def _fix_mv_to_inbox(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Move a file under `知识库/反思|问题|临时/<rest>` to `知识库/收件箱/<basename>.md`.

    Adds `was_path:` frontmatter field tracking original path.
    """
    rel = finding.get("path") or finding.get("file")
    if not rel:
        return False
    src = vault / rel
    if not src.is_file():
        return False
    inbox_dir = vault / "知识库" / "收件箱"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    basename = Path(rel).name
    dst = inbox_dir / basename
    if dst.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dst = inbox_dir / f"{Path(basename).stem}-merged-{ts}{Path(basename).suffix}"
    try:
        src.rename(dst)
    except Exception:
        return False
    # Best-effort: prepend was_path into frontmatter.
    try:
        text = dst.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end > 0:
                fm_block = text[4:end]
                rest = text[end + len("\n---\n") :]
                if not re.search(r"(?m)^was_path:\s*", fm_block):
                    fm_block = fm_block.rstrip() + f"\nwas_path: {rel}\n"
                    dst.write_text(
                        f"---\n{fm_block.rstrip()}\n---\n{rest}", encoding="utf-8"
                    )
    except Exception:
        pass
    return True


def _fix_mv_source_non_repo_to_inbox(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Move `知识库/来源/{网页|论文|书籍}/<rest>` → `知识库/收件箱/<host>-<slug>.md`.

    Tries to extract host from frontmatter source.url; falls back to path segment.
    """
    rel = finding.get("path") or finding.get("file")
    if not rel:
        return False
    src = vault / rel
    if not src.is_file():
        return False
    # try host from frontmatter
    host = None
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?m)^\s*url:\s*([^\s]+)", text)
        if m:
            mh = re.search(r"://([^/]+)", m.group(1))
            if mh:
                host = mh.group(1)
    except Exception:
        text = ""
    if not host:
        # path segments: 知识库/来源/网页/<host>/<slug>.md or 知识库/来源/论文/<slug>.md
        parts = rel.split("/")
        if len(parts) >= 5:
            host = parts[3] if parts[2] in {"网页"} else "unknown"
        else:
            host = "unknown"
    slug = Path(rel).stem
    inbox_dir = vault / "知识库" / "收件箱"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    dst = inbox_dir / f"{host}-{slug}.md"
    if dst.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dst = inbox_dir / f"{host}-{slug}-merged-{ts}.md"
    try:
        src.rename(dst)
    except Exception:
        return False
    return True


def _cleanup_empty_deprecated_dirs(vault: Path) -> None:
    """autofix 后清空已废弃且无文件残留的 vault 根级目录。

    安全策略: 仅 rmdir 空目录 (含空子目录), 不递归删非空内容。
    覆盖 rule 14/17/19/20 等迁移留下的废弃路径。
    """
    deprecated_roots = [
        vault / "知识库" / "实体",
        vault / "知识库" / "概念",
        vault / "知识库" / "来源",
        vault / "知识库" / "反思",
        vault / "知识库" / "问题",
        vault / "知识库" / "临时",
        vault / "知识库" / "日记" / "周",
        vault / "知识库" / "日记" / "月",
        vault / "知识库" / "日记" / "年",
    ]
    for root in deprecated_roots:
        if not root.is_dir():
            continue
        # bottom-up: 先删空子目录, 再尝试删 root
        try:
            for sub in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
                if sub.is_dir() and not any(sub.iterdir()):
                    sub.rmdir()
            if not any(root.iterdir()):
                root.rmdir()
        except Exception:
            continue


def _fix_kb_entity_concept_to_domain(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Move `知识库/{实体|概念}/<rest>` → `知识库/领域/未分类/<basename>.md`.

    Default to 未分类 since AI domain selection is not available at lint time.
    Records `was_path:` in frontmatter for later refactor.
    """
    rel = finding.get("path") or finding.get("file")
    if not rel:
        return False
    src = vault / rel
    if not src.is_file():
        return False
    basename = Path(rel).name
    domain_dir = vault / "知识库" / "领域" / "未分类"
    domain_dir.mkdir(parents=True, exist_ok=True)
    dst = domain_dir / basename
    if dst.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dst = domain_dir / f"{Path(basename).stem}-merged-{ts}{Path(basename).suffix}"
    try:
        src.rename(dst)
    except Exception:
        return False
    # Best-effort: prepend was_path so AI/refactor 可知原 type
    try:
        text = dst.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end > 0:
                fm_block = text[4:end]
                rest = text[end + len("\n---\n") :]
                if not re.search(r"(?m)^was_path:\s*", fm_block):
                    fm_block = fm_block.rstrip() + f"\nwas_path: {rel}\n"
                    dst.write_text(
                        f"---\n{fm_block.rstrip()}\n---\n{rest}", encoding="utf-8"
                    )
    except Exception:
        pass
    return True


def _fix_journal_multi_freq_to_archive(
    finding: dict[str, Any],
    vault: Path,
    plugin_root: Path | None,
    backup_dir: Path,
) -> bool:
    """Move `知识库/日记/{周|月|年}/<rest>` → `归档/日记/<YYYY-QN>.md` 季度桶.

    Quarter inferred from frontmatter `date:` field or filename (YYYY-MM, YYYY-Www).
    """
    rel = finding.get("path") or finding.get("file")
    if not rel:
        return False
    src = vault / rel
    if not src.is_file():
        return False
    text = ""
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    year = None
    month = None
    m = re.search(r"(?m)^\s*date:\s*['\"]?(\d{4})-(\d{2})", text)
    if m:
        year, month = m.group(1), int(m.group(2))
    else:
        # filename like 2026-W19.md / 2026-05.md / 2026.md
        name = Path(rel).stem
        mn = re.match(r"^(\d{4})(?:-W(\d{1,2})|-(\d{2}))?", name)
        if mn:
            year = mn.group(1)
            if mn.group(2):  # ISO week → approx quarter
                wk = int(mn.group(2))
                month = max(1, min(12, (wk - 1) // 4 + 1))
            elif mn.group(3):
                month = int(mn.group(3))
    if not year:
        return False
    if not month:
        month = 1
    quarter = (month - 1) // 3 + 1
    archive_dir = vault / "归档" / "日记"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dst = archive_dir / f"{year}-Q{quarter}.md"
    # If quarter file exists, append source content under a separator.
    if dst.exists():
        try:
            existing = dst.read_text(encoding="utf-8", errors="replace")
        except Exception:
            existing = ""
        sep = "\n\n<!-- merged from {} -->\n\n".format(rel)
        try:
            dst.write_text(existing.rstrip() + sep + text, encoding="utf-8")
            src.unlink()
        except Exception:
            return False
        return True
    try:
        src.rename(dst)
    except Exception:
        return False
    return True


# ---- autofix ----


def apply_fixes(
    vault: Path,
    findings: list[dict[str, Any]],
    backup_dir: Path,
    plugin_root: Path | None = None,
    rules_filter: set[str] | None = None,
) -> int:
    """Apply fixes for autofix-eligible findings. Backup before write.

    `rules_filter`: if set, only fix findings whose rule is in this set
    (used by `--sync-templates` to limit autofix to template/seed rules).
    """
    fixed = 0

    # 0) Constructive sync rules — structure-missing → meta-missing → seed-missing.
    #    Order matters: seed-missing writes files into dirs created by
    #    structure-missing. Sort by RULE_PRIORITY (default 99).
    sync_rules = {
        "backup-in-vault": _fix_backup_in_vault,
        "structure-missing": _fix_structure_missing,
        "meta-missing": _fix_meta_missing,
        "seed-missing": _fix_seed_missing,
    }
    sync_findings = [
        f
        for f in findings
        if f.get("fixable")
        and f["rule"] in sync_rules
        and (rules_filter is None or f["rule"] in rules_filter)
    ]
    sync_findings.sort(key=lambda f: RULE_PRIORITY.get(f["rule"], 99))
    for f in sync_findings:
        fn = sync_rules[f["rule"]]
        if fn(f, vault, plugin_root, backup_dir):
            fixed += 1

    # 1) template-outdated / template-missing / seed-outdated / vault-misaligned
    #    — whole-file or TEMPLATE_END-head replacement
    for f in findings:
        if not f.get("fixable"):
            continue
        rule = f["rule"]
        if rule not in {
            "template-outdated",
            "template-missing",
            "seed-outdated",
            "vault-misaligned",
        }:
            continue
        if rules_filter is not None and rule not in rules_filter:
            continue
        if plugin_root is None:
            continue
        ok = False
        if rule in ("template-outdated", "template-missing"):
            ok = _fix_template_outdated(f, vault, plugin_root, backup_dir)
        elif rule == "seed-outdated":
            ok = _fix_seed_outdated(f, vault, plugin_root, backup_dir)
        elif rule == "vault-misaligned":
            ok = _fix_vault_misaligned(f, vault, plugin_root, backup_dir)
        if ok:
            fixed += 1

    # 1b) frontmatter-schema-violation — dedupe per file (one fix call covers all
    #     missing keys/tags for that file).
    seen_fm_schema: set[str] = set()
    for f in findings:
        if not f.get("fixable"):
            continue
        if f["rule"] != "frontmatter-schema-violation":
            continue
        if (
            rules_filter is not None
            and "frontmatter-schema-violation" not in rules_filter
        ):
            continue
        if plugin_root is None:
            continue
        key = f["file"]
        if key in seen_fm_schema:
            continue
        seen_fm_schema.add(key)
        if _fix_frontmatter_schema(f, vault, plugin_root, backup_dir):
            fixed += 1

    # 1bb) frontmatter-required-scores — dedupe per file (one fix call covers
    #      all missing/invalid score fields).
    seen_scores: set[str] = set()
    for f in findings:
        if not f.get("fixable"):
            continue
        if f["rule"] != "frontmatter-required-scores":
            continue
        if (
            rules_filter is not None
            and "frontmatter-required-scores" not in rules_filter
        ):
            continue
        key = f["file"]
        if key in seen_scores:
            continue
        seen_scores.add(key)
        p = vault / key
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        new_text = autofix_frontmatter_required_scores(Path(key), text)
        if new_text is None or new_text == text:
            continue
        bak = backup_dir / key
        bak.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(p, bak)
        except Exception:
            pass
        try:
            p.write_text(new_text, encoding="utf-8")
            fixed += 1
        except Exception:
            continue

    # 1c) dead-wikilink — per-finding fix with shared freq cache + stub counter
    dead_findings = [
        f
        for f in findings
        if f.get("fixable")
        and f["rule"] == "dead-wikilink"
        and (rules_filter is None or "dead-wikilink" in rules_filter)
    ]
    if dead_findings:
        freq_cache = _wikilink_freq(vault)
        stub_counter = {"n": 0}
        for f in dead_findings:
            if _fix_dead_wikilink(
                f,
                vault,
                plugin_root,
                backup_dir,
                freq_cache=freq_cache,
                stub_counter=stub_counter,
            ):
                fixed += 1

    # 1d) duplicate-alias — group by alias name (parsed from msg) → batch rename
    dup_alias_findings = [
        f
        for f in findings
        if f.get("fixable")
        and f["rule"] == "duplicate-alias"
        and (rules_filter is None or "duplicate-alias" in rules_filter)
    ]
    if dup_alias_findings:
        for f in dup_alias_findings:
            msg = f.get("msg", "")
            m = re.match(r"alias '([^']+)' shared across:\s*(.+)$", msg)
            if not m:
                continue
            alias_name = m.group(1)
            file_list_str = m.group(2)
            file_rels = [s.strip() for s in file_list_str.split(",") if s.strip()]
            fixed += _fix_duplicate_alias_group(
                alias_name,
                file_rels,
                vault,
                backup_dir,
            )

    # 1e) vault-structure-violation → mv 违规路径到 backup
    #     callout-unknown-type / orphan-page / path-naming-violation /
    #     i18n-path-not-in-locale → per-finding fix (priority sorted)
    extra_fixers = {
        "vault-structure-violation": _fix_vault_structure_violation,
        "callout-unknown-type": _fix_callout_unknown_type,
        "orphan-page": _fix_orphan_page,
        "path-naming-violation": _fix_path_violation,
        "i18n-path-not-in-locale": _fix_path_violation,
        "repo-path-deprecated": _fix_repo_path_deprecated,
        "reflection-path-deprecated": _fix_mv_to_inbox,
        "question-fleeting-path-deprecated": _fix_mv_to_inbox,
        "journal-multi-freq-deprecated": _fix_journal_multi_freq_to_archive,
        "source-non-repo-path-deprecated": _fix_mv_source_non_repo_to_inbox,
        "entity-concept-path-deprecated": _fix_kb_entity_concept_to_domain,
    }
    extra_findings = [
        f
        for f in findings
        if f.get("fixable")
        and f["rule"] in extra_fixers
        and (rules_filter is None or f["rule"] in rules_filter)
    ]
    extra_findings.sort(key=lambda f: RULE_PRIORITY.get(f["rule"], 99))
    for f in extra_findings:
        fn = extra_fixers[f["rule"]]
        try:
            if fn(f, vault, plugin_root, backup_dir):
                fixed += 1
        except Exception:
            continue

    # post-autofix: 清空已迁空的废弃根目录 (rmdir 递归, 仅删空目录)
    _cleanup_empty_deprecated_dirs(vault)

    by_file: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        if not f.get("fixable"):
            continue
        if f["rule"] not in {
            "fm-missing-type",
            "fm-missing-created",
            "fm-duplicate-tags",
            "fm-banned-tags",
            "fm-banned-fields",
            "fm-missing-tags",
            "hot-too-long",
            "index-missing-section",
            "title-h1-mismatch",
            "block-id-duplicate",
        }:
            continue
        if rules_filter is not None and f["rule"] not in rules_filter:
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
            elif rule == "fm-duplicate-tags":
                try:
                    import yaml as _yaml  # type: ignore
                except ImportError:
                    _yaml = None
                m_fm = re.match(r"^---\n(.*?)\n---\n?(.*)", new_text, re.S)
                if m_fm and _yaml is not None:
                    try:
                        _fm = _yaml.safe_load(m_fm.group(1)) or {}
                    except Exception:
                        _fm = None
                    if isinstance(_fm, dict):
                        _tg = _fm.get("tags")
                        if isinstance(_tg, list):
                            _seen2: set[str] = set()
                            _new_tg: list[Any] = []
                            for _t in _tg:
                                _key = _t if isinstance(_t, str) else repr(_t)
                                if _key in _seen2:
                                    continue
                                _seen2.add(_key)
                                _new_tg.append(_t)
                            if len(_new_tg) != len(_tg):
                                _fm["tags"] = _new_tg
                                _new_fm = _yaml.safe_dump(
                                    _fm,
                                    allow_unicode=True,
                                    sort_keys=False,
                                )
                                new_text = f"---\n{_new_fm}---\n{m_fm.group(2)}"
                                fixed += 1
            elif rule == "fm-banned-fields":
                try:
                    import yaml as _yaml3  # type: ignore
                except ImportError:
                    _yaml3 = None
                m_fm3 = re.match(r"^---\n(.*?)\n---\n?(.*)", new_text, re.S)
                if m_fm3 and _yaml3 is not None:
                    try:
                        _fm3 = _yaml3.safe_load(m_fm3.group(1)) or {}
                    except Exception:
                        _fm3 = None
                    if isinstance(_fm3, dict):
                        removed = False
                        for _k in list(_fm3.keys()):
                            if _k in _BANNED_FM_FIELDS:
                                _fm3.pop(_k, None)
                                removed = True
                        if removed:
                            _new_fm3 = _yaml3.safe_dump(
                                _fm3,
                                allow_unicode=True,
                                sort_keys=False,
                            )
                            new_text = f"---\n{_new_fm3}---\n{m_fm3.group(2)}"
                            fixed += 1
            elif rule == "fm-missing-tags":
                try:
                    import yaml as _yaml4  # type: ignore
                except ImportError:
                    _yaml4 = None
                m_fm4 = re.match(r"^---\n(.*?)\n---\n?(.*)", new_text, re.S)
                if m_fm4 and _yaml4 is not None:
                    try:
                        _fm4 = _yaml4.safe_load(m_fm4.group(1)) or {}
                    except Exception:
                        _fm4 = None
                    if isinstance(_fm4, dict):
                        _body4 = m_fm4.group(2) or ""
                        _derived = _derive_tags_for_autofix(_fm4, _body4)
                        if _derived:
                            _fm4["tags"] = _derived
                            _new_fm4 = _yaml4.safe_dump(
                                _fm4,
                                allow_unicode=True,
                                sort_keys=False,
                            )
                            new_text = f"---\n{_new_fm4}---\n{_body4}"
                            fixed += 1
                        # 派生不足 → 不写盘, 保留 warn 待人工/AI 补
            elif rule == "fm-banned-tags":
                try:
                    import yaml as _yaml2  # type: ignore
                except ImportError:
                    _yaml2 = None
                m_fm2 = re.match(r"^---\n(.*?)\n---\n?(.*)", new_text, re.S)
                if m_fm2 and _yaml2 is not None:
                    try:
                        _fm2 = _yaml2.safe_load(m_fm2.group(1)) or {}
                    except Exception:
                        _fm2 = None
                    if isinstance(_fm2, dict):
                        _tg2 = _fm2.get("tags")
                        if isinstance(_tg2, list):
                            _filt = [
                                _t
                                for _t in _tg2
                                if not (isinstance(_t, str) and _is_banned_tag(_t))
                            ]
                            if len(_filt) != len(_tg2):
                                if _filt:
                                    _fm2["tags"] = _filt
                                else:
                                    _fm2.pop("tags", None)
                                _new_fm2 = _yaml2.safe_dump(
                                    _fm2,
                                    allow_unicode=True,
                                    sort_keys=False,
                                )
                                new_text = f"---\n{_new_fm2}---\n{m_fm2.group(2)}"
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
                    archive_dir = vault / "归档"
                    archive_dir.mkdir(exist_ok=True)
                    arch = (
                        archive_dir
                        / f"hot-archive-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
                    )
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
                    new_h = hashlib.sha1(
                        (relfile + str(it["line"]) + old).encode()
                    ).hexdigest()[:8]
                    new_bid = f"cortex-{new_h}"
                    # only replace one occurrence at the given line
                    lines = new_text.splitlines()
                    if 0 < it["line"] <= len(lines):
                        lines[it["line"] - 1] = lines[it["line"] - 1].replace(
                            f"^{old}", f"^{new_bid}", 1
                        )
                        new_text = "\n".join(lines) + (
                            "\n" if new_text.endswith("\n") else ""
                        )
                        fixed += 1

        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
    return fixed


def _infer_type(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] == "知识库":
        if len(parts) >= 2:
            sub = parts[1]
            if sub == "项目":
                return "project"
            if sub == "来源":
                return "source"
            if sub == "领域":
                return "concept"
            if sub == "日记":
                return "log"
            if sub == "反思":
                return "reflection"
            if sub == "收件箱":
                return "fleeting"
        return "concept"
    if parts[0] == "记忆":
        return "memory"
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
    ap.add_argument(
        "--fix", action="store_true", help="apply autofix (writes to disk + backup)"
    )
    ap.add_argument(
        "--sync-templates",
        action="store_true",
        dest="sync_templates",
        help="only auto-fix template-outdated/template-missing/seed-outdated (no other rules)",
    )
    ap.add_argument("--scope", default=None, help="glob filter, e.g. '知识库/领域/*'")
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
    plugin_root = Path(__file__).resolve().parents[2]
    locale_dirs = _load_locale_dirs(plugin_root, vault, vault_lang)
    fm_schema = _load_frontmatter_schema(vault, plugin_root)

    findings: list[dict[str, Any]] = []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(vault))
        findings.extend(
            check_file(
                p, rel, text, by_name, by_alias, referrers, vault_lang, fm_schema
            )
        )

    findings.extend(
        check_global(vault, files, by_alias, locale_dirs if locale_dirs else None)
    )

    # rule: base-format-yaml — 扫 vault 内全部 .base 文件
    for bp in vault.rglob("*.base"):
        try:
            rel_b = bp.relative_to(vault)
        except ValueError:
            continue
        # 顶层 EXCLUDE_DIRS (.obsidian/.trash/.git/_meta) 跳过
        if rel_b.parts and rel_b.parts[0] in EXCLUDE_DIRS:
            continue
        if args.scope and not fnmatch.fnmatch(str(rel_b), args.scope):
            continue
        try:
            base_text = bp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        findings.extend(check_base_format_yaml(rel_b, base_text))

    # rule #16: vault-structure-violation — strict preset schema check at root
    preset = _load_vault_preset(vault)
    whitelist = _load_lint_whitelist(vault)
    findings.extend(check_vault_structure(vault, preset, whitelist, locale_dirs))

    # rule #17/18/19: template-outdated / template-missing / seed-outdated
    findings.extend(_check_template_outdated(vault, plugin_root))
    findings.extend(_check_seed_outdated(vault, plugin_root))

    # rule backup-in-vault: legacy lint backup inside vault → migrate out
    findings.extend(_check_backup_in_vault(vault, plugin_root))

    # rule #20/21/22: structure-missing / seed-missing / meta-missing
    # (constructive sync — fills vault from plugin _structure.json + seeds)
    findings.extend(_check_structure_missing(vault, plugin_root))
    findings.extend(_check_meta_missing(vault, plugin_root))
    findings.extend(_check_seed_missing(vault, plugin_root))

    # rule #23: vault-misaligned — 强制对齐 (sha 任意偏差即覆盖)
    findings.extend(_check_vault_misaligned(vault, plugin_root))

    # vault-structure-violation: attach backup_target + emit structure_purge
    # mv plan (executed by cortex-lint skill, never by this python process).
    # Backup root lives OUTSIDE the vault (PRD: vault stays clean).
    structure_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    structure_backup_root = str(
        Path.home()
        / ".cache"
        / "cortex"
        / "lint-backup"
        / _vault_hash(vault)
        / f"structure-{structure_ts}"
    )
    sp_violations = [
        f for f in findings if f.get("rule") == "vault-structure-violation"
    ]
    for v in sp_violations:
        v["backup_target"] = f"{structure_backup_root}/{v['path']}"

    fixed = 0
    if args.fix or args.sync_templates:
        backup_dir = _get_backup_root(vault)
        # Best-effort prune of old backups (>30 days) for this vault
        _prune_old_backups(vault, days=30)
        # Prune deprecated whitelist entries (log/, folds/, sessions/)
        if _prune_deprecated_whitelist(vault):
            fixed += 1
        rules_filter: set[str] | None = None
        if args.sync_templates and not args.fix:
            rules_filter = {"template-outdated", "template-missing", "seed-outdated"}
        fixed = apply_fixes(
            vault,
            findings,
            backup_dir,
            plugin_root=plugin_root,
            rules_filter=rules_filter,
        )

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
    if sp_violations:
        out["structure_purge"] = {
            "violation_count": len(sp_violations),
            "backup_root": structure_backup_root,
            "mv_plan": [
                {"from": v["path"], "to": v["backup_target"]} for v in sp_violations
            ],
        }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
