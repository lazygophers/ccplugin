"""cortex-digest evolution 抽取核心: 扫 jsonl + 抽 pattern + 写 patterns.md
+ 生 proposal markdown. 由 `cli/digest.py evolution` 子命令调度.

D1: patterns 落 `记忆/L0-核心/patterns.md` (single md, 多 section by category)
D4: 阈值硬编码 (MIN_CONFIDENCE / MIN_APPLICATIONS)
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Allow importing frontmatter helper when module is used directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from lib.frontmatter import dump as _fm_dump  # type: ignore
    from lib.frontmatter import parse as _fm_parse  # type: ignore
except ImportError:  # pragma: no cover
    from frontmatter import dump as _fm_dump  # type: ignore
    from frontmatter import parse as _fm_parse  # type: ignore

# ----- 硬编码常量 (D4) ----------------------------------------------------

MIN_CONFIDENCE = 0.8
MIN_APPLICATIONS = 3
DEFAULT_LOOKBACK_DAYS = 7

CATEGORIES = [
    "vault-write-contract",
    "ingest-failure",
    "digest-routing",
    "skill-trigger",
    "frontmatter-schema",
    "user-correction",
]

NEGATIVE_FEEDBACK_TOKENS = [
    "不对", "不是", "应该是", "改成", "错了",
    "wrong", "incorrect", "that's not", "no, ",
]

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "vault-write-contract": ["mcp__obsidian", "vault 写", "vault write", "write 工具"],
    "ingest-failure": ["ingest", "摄取", "webfetch", "defuddle"],
    "digest-routing": ["digest", "路由", "routing", "归属"],
    "skill-trigger": ["skill", "触发", "trigger"],
    "frontmatter-schema": ["frontmatter", "fm-", "schema"],
    "user-correction": [],
}

PATTERNS_REL = "记忆/L0-核心/patterns.md"
PROPOSALS_REL_DIR = "_assets/evolution-proposals"
SESSIONS_REL = "记忆/L4-流水账/sessions"


# ----- 数据类 -------------------------------------------------------------

@dataclass
class Episode:
    session_path: Path
    rel_path: str
    entries: list[dict[str, Any]] = field(default_factory=list)
    date: str = ""


@dataclass
class Pattern:
    id: str
    category: str
    name: str
    pattern: str
    problem: str
    solution: str
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    applications: int = 0
    created: str = ""
    updated: str = ""
    target_skills: list[str] = field(default_factory=list)


# ----- jsonl 扫描 ---------------------------------------------------------


def scan_sessions(vault: Path, lookback_days: int) -> list[Episode]:
    """扫 sessions 目录近 lookback_days 天的 jsonl. sessions 缺失返空."""
    root = vault / SESSIONS_REL
    if not root.is_dir():
        return []
    cutoff_ts = _dt.datetime.now().timestamp() - lookback_days * 86400
    out: list[Episode] = []
    for p in root.rglob("*.jsonl"):
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_mtime < cutoff_ts:
            continue
        entries: list[dict[str, Any]] = []
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict):
                        entries.append(obj)
        except OSError:
            continue
        rel = str(p.relative_to(vault))
        parts = p.parts
        date = ""
        if len(parts) >= 4:
            y, m, d = parts[-4], parts[-3], parts[-2]
            if y.isdigit() and m.isdigit() and d.isdigit():
                date = f"{y}-{m}-{d}"
        out.append(Episode(session_path=p, rel_path=rel, entries=entries, date=date))
    return out


# ----- pattern 抽取 -------------------------------------------------------


def _extract_text(entry: dict[str, Any], role_set: set[str]) -> str:
    role = entry.get("role") or entry.get("type") or ""
    if role not in role_set:
        msg = entry.get("message")
        if isinstance(msg, dict):
            return _extract_text(msg, role_set)
        return ""
    content = entry.get("content") or entry.get("text") or ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for blk in content:
            if isinstance(blk, dict):
                t = blk.get("text") or ""
                if isinstance(t, str):
                    parts.append(t)
        return "\n".join(parts)
    return ""


def _extract_user_text(entry: dict[str, Any]) -> str:
    return _extract_text(entry, {"user", "human"})


def _extract_assistant_text(entry: dict[str, Any]) -> str:
    return _extract_text(entry, {"assistant", "ai"})


def _categorize(signature_text: str, is_negative: bool) -> str:
    lowered = signature_text.lower()
    for cat, kws in _CATEGORY_KEYWORDS.items():
        if cat == "user-correction":
            continue
        for kw in kws:
            if kw.lower() in lowered:
                return cat
    if is_negative:
        return "user-correction"
    return "skill-trigger"


def _signature_key(text: str, category: str) -> str:
    tokens = re.findall(r"[\w一-鿿]+", text.lower())
    if not tokens:
        tokens = [text[:30]]
    tokens = [t for t in tokens if len(t) >= 2][:8]
    tokens.sort()
    raw = category + "|" + " ".join(tokens)
    return raw[:200]


def _signature_to_id(signature: str, date: str) -> str:
    h = hashlib.sha1(signature.encode("utf-8")).hexdigest()[:6]
    return f"pat-{date}-{h}"


def _guess_target_skills(category: str) -> list[str]:
    mapping = {
        "vault-write-contract": ["skills/cortex-save/SKILL.md", "AGENT.md"],
        "ingest-failure": ["skills/cortex-ingest/SKILL.md"],
        "digest-routing": ["skills/cortex-digest/SKILL.md"],
        "skill-trigger": ["AGENT.md"],
        "frontmatter-schema": [
            "skills/cortex-save/SKILL.md", "skills/cortex-lint/SKILL.md",
        ],
        "user-correction": ["AGENT.md"],
    }
    return mapping.get(category, ["AGENT.md"])


def extract_patterns(episodes: list[Episode]) -> list[Pattern]:
    """从 episodes 抽 pattern. 按 (category, signature) 聚合.

    confidence: user-correction 0.9 起步; 其他 0.5 + 0.05*applications (上限 1.0).
    """
    buckets: dict[tuple[str, str], dict[str, Any]] = {}

    for ep in episodes:
        prev_assistant: str = ""
        for entry in ep.entries:
            user_text = _extract_user_text(entry)
            if user_text:
                is_neg = any(tok in user_text for tok in NEGATIVE_FEEDBACK_TOKENS)
                signature_text = (
                    prev_assistant[:200] + " | " + user_text[:200]
                    if is_neg and prev_assistant else user_text[:300]
                )
                category = _categorize(signature_text, is_neg)
                sig_key = _signature_key(signature_text, category)
                b = buckets.setdefault((category, sig_key), {
                    "sessions": set(),
                    "samples": [],
                    "is_negative": False,
                    "first_text": signature_text[:200],
                })
                b["sessions"].add(ep.rel_path)
                if len(b["samples"]) < 5:
                    b["samples"].append(signature_text[:200])
                if is_neg:
                    b["is_negative"] = True
                prev_assistant = ""
                continue
            assistant_text = _extract_assistant_text(entry)
            if assistant_text:
                prev_assistant = assistant_text

    out: list[Pattern] = []
    today = _dt.date.today().isoformat()
    for (category, _sig_key), b in buckets.items():
        applications = len(b["sessions"])
        if applications < MIN_APPLICATIONS:
            continue
        if b["is_negative"]:
            base = 0.9
        else:
            base = 0.5 + min(0.4, applications * 0.05)
        confidence = round(min(1.0, base), 2)
        sig_id = _signature_to_id(_sig_key, today)
        first = b["first_text"]
        name = (first.split("\n", 1)[0])[:60] or category
        out.append(Pattern(
            id=sig_id,
            category=category,
            name=name,
            pattern=f"复发模式 ({applications} 次): {first}",
            problem=("用户纠正信号: " + first) if b["is_negative"]
                    else f"重复触发: {first}",
            solution="(待人工/PR4 patch 流程补充)",
            sources=sorted(b["sessions"]),
            confidence=confidence,
            applications=applications,
            created=today,
            updated=today,
            target_skills=_guess_target_skills(category),
        ))
    return out


# ----- patterns.md 写盘 ---------------------------------------------------


def _patterns_skeleton() -> str:
    lines = [
        "# Patterns (semantic memory)",
        "",
        "> 由 cortex-digest evolution 抽取维护. 每次 digest 跑会更新 "
        "applications/confidence/updated 字段. 手动编辑请保留 yaml block 完整性.",
        "",
    ]
    for cat in CATEGORIES:
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("(空)")
        lines.append("")
    return "\n".join(lines) + "\n"


_YAML_FENCE_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
_PATTERN_HEADING_RE = re.compile(r"^### (pat-[\w-]+)\b", re.MULTILINE)


def _parse_existing_patterns(text: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    matches = list(_PATTERN_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        pid = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end]
        ym = _YAML_FENCE_RE.search(section)
        if not ym:
            continue
        meta: dict[str, Any] = {}
        for line in ym.group(1).splitlines():
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k == "applications":
                try:
                    meta["applications"] = int(v)
                except ValueError:
                    pass
            elif k == "confidence":
                try:
                    meta["confidence"] = float(v)
                except ValueError:
                    pass
            elif k in ("category", "created"):
                meta[k] = v
        out[pid] = meta
    return out


def _render_pattern_block(p: Pattern) -> str:
    sources_yaml = (
        "\n".join(f"  - {s}" for s in p.sources) if p.sources else "  - (none)"
    )
    targets_yaml = (
        "\n".join(f"  - {s}" for s in p.target_skills)
        if p.target_skills else "  - (none)"
    )
    return (
        f"### {p.id} {p.name}\n\n"
        "```yaml\n"
        f"id: {p.id}\n"
        f"category: {p.category}\n"
        "source: episodic\n"
        f"confidence: {p.confidence}\n"
        f"applications: {p.applications}\n"
        f"created: {p.created}\n"
        f"updated: {p.updated}\n"
        "target_skills:\n"
        f"{targets_yaml}\n"
        "```\n\n"
        f"**Pattern**: {p.pattern}\n\n"
        f"**Problem**: {p.problem}\n\n"
        f"**Solution**: {p.solution}\n\n"
        "**Sources**:\n"
        f"{sources_yaml}\n"
    )


def write_patterns_md(
    patterns: list[Pattern], vault: Path, dry_run: bool = False,
) -> tuple[int, int]:
    """写 patterns.md. 返回 (added, updated). dry_run=True 仅统计."""
    p = vault / PATTERNS_REL
    if not p.exists():
        text = _patterns_skeleton()
    else:
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            text = _patterns_skeleton()

    existing = _parse_existing_patterns(text)
    today = _dt.date.today().isoformat()
    added = 0
    updated = 0

    by_cat: dict[str, list[Pattern]] = {}
    for pat in patterns:
        if pat.id in existing:
            old_app = int(existing[pat.id].get("applications", 0))
            old_conf = float(existing[pat.id].get("confidence", 0.0))
            pat.applications = max(pat.applications, old_app + 1)
            pat.confidence = max(pat.confidence, old_conf)
            pat.updated = today
            updated += 1
        else:
            added += 1
        by_cat.setdefault(pat.category, []).append(pat)

    new_text = text
    for pat in patterns:
        if pat.id in existing:
            heading_re = re.compile(
                rf"^### {re.escape(pat.id)}\b.*?(?=^### pat-|^## |\Z)",
                re.DOTALL | re.MULTILINE,
            )
            new_text = heading_re.sub("", new_text)

    for cat, pats in by_cat.items():
        if f"## {cat}" not in new_text:
            new_text = new_text.rstrip() + f"\n\n## {cat}\n\n"
        sec_re = re.compile(
            rf"(## {re.escape(cat)}\n)(.*?)(?=^## |\Z)",
            re.DOTALL | re.MULTILINE,
        )
        m = sec_re.search(new_text)
        if not m:
            continue
        head = m.group(1)
        body = m.group(2)
        body = re.sub(r"\(空\)\n?", "", body).rstrip() + "\n\n"
        for pat in pats:
            body += _render_pattern_block(pat) + "\n"
        new_text = new_text[:m.start()] + head + body + new_text[m.end():]

    if dry_run:
        return added, updated

    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(new_text, encoding="utf-8")
    except OSError as e:
        print(f"warn: write patterns.md failed: {e}", file=sys.stderr)
    return added, updated


# ----- proposal 生成 ------------------------------------------------------


def _slug(text: str) -> str:
    s = re.sub(r"[\s/\\:*?\"<>|]+", "-", text).strip("-_")
    return (s or "proposal")[:40].lower()


def _render_proposal(pat: Pattern) -> str:
    sources_yaml = (
        "\n".join(f"  - {s}" for s in pat.sources) if pat.sources else "  - (none)"
    )
    target = pat.target_skills[0] if pat.target_skills else "AGENT.md"
    diff_block = (
        "```diff\n"
        f"--- a/{target}\n"
        f"+++ b/{target}\n"
        "@@ <section to identify by reviewer> @@\n"
        " <context line>\n"
        f"+# auto-proposal from {pat.id}\n"
        f"+# pattern: {pat.name}\n"
        " <context line>\n"
        "```\n"
    )
    src_list = "\n".join(f"- [[{s}]] — episodic source" for s in pat.sources)
    return (
        "---\n"
        f"pattern_id: {pat.id}\n"
        f"target_skill: {target}\n"
        "target_section: (reviewer to fill)\n"
        f"confidence: {pat.confidence}\n"
        f"applications: {pat.applications}\n"
        f"category: {pat.category}\n"
        "sources:\n"
        f"{sources_yaml}\n"
        "---\n\n"
        f"# Proposal: {pat.name}\n\n"
        "## Pattern\n\n"
        f"{pat.pattern}\n\n"
        "## Problem\n\n"
        f"{pat.problem}\n\n"
        "## Suggested Patch (unified diff)\n\n"
        f"{diff_block}\n"
        "## Episodic Sources\n\n"
        f"{src_list}\n"
    )


def generate_proposals(
    patterns: list[Pattern], vault: Path, dry_run: bool = False,
) -> list[str]:
    """生 proposal markdown. 阈值过线才生. 返回 vault 相对路径列表."""
    out_dir = vault / PROPOSALS_REL_DIR
    today = _dt.date.today().isoformat()
    generated: list[str] = []
    for pat in patterns:
        if pat.confidence < MIN_CONFIDENCE:
            continue
        if pat.applications < MIN_APPLICATIONS:
            continue
        slug = _slug(pat.name) or _slug(pat.id)
        fname = f"{today}-{slug}.md"
        rel = f"{PROPOSALS_REL_DIR}/{fname}"
        if dry_run:
            generated.append(rel)
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        dst = out_dir / fname
        try:
            dst.write_text(_render_proposal(pat), encoding="utf-8")
            generated.append(rel)
        except OSError as e:
            print(f"warn: write proposal {rel} failed: {e}", file=sys.stderr)
    return generated


# ----- 双路评分更新 (PR4) ------------------------------------------------

_NEGATIVE_TOKENS = (
    "不对", "错了", "应该是", "不是", "改成",
    "wrong", "incorrect", "that's not",
)
_POSITIVE_TOKENS = (
    "对的", "正确", "很好", "exactly", "correct", "right",
)


def _coerce_float(v: Any, default: float = 0.0) -> float:
    if isinstance(v, bool):
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except (ValueError, AttributeError):
            return default
    return default


def _scan_session_mentions(
    doc_path: str,
    sessions_dir: Path,
    lookback_days: int = 7,
) -> tuple[int, list[str], list[str]]:
    """扫 sessions/*.jsonl 找 doc_path 提及.

    Returns (mention_count, negative_session_files, positive_session_files).
    """
    if not sessions_dir.exists() or not sessions_dir.is_dir():
        return (0, [], [])

    cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=lookback_days)
    doc_basename = Path(doc_path).stem

    mentions = 0
    neg_sessions: list[str] = []
    pos_sessions: list[str] = []

    for jsonl in sessions_dir.rglob("*.jsonl"):
        try:
            mtime = _dt.datetime.fromtimestamp(
                jsonl.stat().st_mtime, tz=_dt.timezone.utc,
            )
        except OSError:
            continue
        if mtime < cutoff:
            continue

        try:
            text = jsonl.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if doc_path in text or f"[[{doc_basename}" in text:
            mentions += 1
            if any(tok in text for tok in _NEGATIVE_TOKENS):
                neg_sessions.append(jsonl.name)
            if any(tok in text for tok in _POSITIVE_TOKENS):
                pos_sessions.append(jsonl.name)

    return (mentions, neg_sessions, pos_sessions)


def _count_vault_backlinks(doc_path: str, vault: Path) -> int:
    """count .md files in vault containing `[[<doc_basename>` (excluding self)."""
    doc_basename = Path(doc_path).stem
    pattern = re.compile(re.escape(f"[[{doc_basename}"))
    self_resolved: Path | None
    try:
        self_resolved = (vault / doc_path).resolve()
    except OSError:
        self_resolved = None
    count = 0
    for md in vault.rglob("*.md"):
        try:
            if self_resolved is not None and md.resolve() == self_resolved:
                continue
        except OSError:
            pass
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pattern.search(content):
            count += 1
    return count


def update_doc_scores(
    doc_path: str,
    vault: Path,
    sessions_dir: Path | None = None,
    lookback_days: int = 7,
    dry_run: bool = False,
) -> dict[str, Any]:
    """digest 跑时双路更新单 .md frontmatter 评分 (importance / confidence).

    使用信号: mentions (sessions/jsonl) + backlinks (vault .md) → importance ↑
              自然衰减: 每周 -0.1
    反馈信号: 正/负反馈语 + doc 同会话出现 → confidence ↑/↓

    Returns dict with old/new scores + signal counts + applied flag.
    """
    if sessions_dir is None:
        sessions_dir = vault / "记忆" / "L4-流水账" / "sessions"

    abs_path = vault / doc_path
    if not abs_path.exists() or not abs_path.is_file():
        return {"path": doc_path, "error": "not_found"}

    try:
        content = abs_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        return {"path": doc_path, "error": f"read_error: {e}"}

    fm, body = _fm_parse(content)
    if not fm:
        return {"path": doc_path, "error": "no_frontmatter"}

    old_importance = _coerce_float(fm.get("importance"), 0.0)
    old_confidence = _coerce_float(fm.get("confidence"), 0.0)

    mentions, neg_sessions, pos_sessions = _scan_session_mentions(
        doc_path, sessions_dir, lookback_days,
    )
    backlinks = _count_vault_backlinks(doc_path, vault)

    importance_delta = math.log10(mentions + backlinks + 1) - 0.1
    new_importance = max(0.0, min(10.0, old_importance + importance_delta))

    confidence_delta = len(pos_sessions) * 0.5 - len(neg_sessions) * 1.0
    new_confidence = max(0.0, min(10.0, old_confidence + confidence_delta))

    new_importance_r = round(new_importance, 2)
    new_confidence_r = round(new_confidence, 2)
    old_importance_r = round(old_importance, 2)
    old_confidence_r = round(old_confidence, 2)

    result: dict[str, Any] = {
        "path": doc_path,
        "old_importance": old_importance_r,
        "new_importance": new_importance_r,
        "old_confidence": old_confidence_r,
        "new_confidence": new_confidence_r,
        "mentions": mentions,
        "backlinks": backlinks,
        "negative_signals": len(neg_sessions),
        "positive_signals": len(pos_sessions),
        "applied": False,
    }

    changed = (
        new_importance_r != old_importance_r
        or new_confidence_r != old_confidence_r
    )
    if not dry_run and changed:
        fm["importance"] = new_importance_r
        fm["confidence"] = new_confidence_r
        try:
            new_content = _fm_dump(fm, body)
            abs_path.write_text(new_content, encoding="utf-8")
            result["applied"] = True
        except OSError as e:
            result["error"] = f"write_error: {e}"
    return result
